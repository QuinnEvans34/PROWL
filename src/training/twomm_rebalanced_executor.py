"""Single-attempt training/evaluation transaction, completion-last and no implicit resume."""
from pathlib import Path
import json
import os
import time
import nibabel as nib
import numpy as np
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.training.twomm_rebalanced_training import payload,weight_digest
from src.training.twomm_inference_export import export_prediction,verify_export
from src.training.native_localizer_metrics import measure


def put(path,raw):
    with Path(path).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())


class Journal:
    def __init__(self,path,identity):
        self.path=Path(path);self.stream=self.path.open('xb')
        self.previous=digest(canonical(identity));self.sequence=0
    def append(self,event):
        row=dict(sequence=self.sequence,previous_sha256=self.previous,event=event)
        raw=canonical(row);self.stream.write(raw);self.stream.flush();os.fsync(self.stream.fileno())
        self.previous=digest(raw);self.sequence+=1
    def close(self):self.stream.close()


def verify_journal(raw,identity):
    previous=digest(canonical(identity));rows=[]
    for n,line in enumerate(raw.splitlines()):
        row=json.loads(line);require(set(row)=={'sequence','previous_sha256','event'} and
            type(row['sequence']) is int and row['sequence']==n and row['previous_sha256']==previous,
            'Journal chain differs')
        previous=digest(canonical(row));rows.append(row['event'])
    require(rows and rows[0]['state']=='attempt_started', 'Missing attempt start')
    return rows,previous


def evaluate(session,cache,references,stage,path,*,guard=lambda:None):
    """References are opened once for this frozen stage by the scoped launcher."""
    session.verify(cache);require(stage in session.plan['evaluations'] and session.step==stage['step'], 'Wrong evaluation stage')
    require(set(references)==set(stage['roles']), 'Wrong reference role scope')
    path=Path(path);path.mkdir();before=weight_digest(session);rows=[]
    # Check all descriptors before the first target read.
    for role in stage['roles']:
        ds=references[role];entries=session.binding['roles'][role]
        require(len(ds)==len(entries) and [ds.descriptor(i) for i in range(len(ds))]==
            [e['descriptor'] for e in entries], 'Reference/cache qualification differs')
    for role in stage['roles']:
        for index,sid in enumerate(cache.members(role)):
            guard();started=time.monotonic();item=cache.get(role,index)
            probability,padding=session.predict(item['image']);guard()
            name=f'{role}-{index:04d}.nii.gz';record=item['transform_record']
            exported=export_prediction(path/name,probability,record);del probability
            guard();target,affine,provenance=references[role].load(index,operation=role)
            require(provenance['descriptor']==item['descriptor'] and
                list(target.shape)==record['source_shape'] and np.allclose(affine,record['source_affine'],rtol=0,atol=1e-5),
                'Native reference differs from prediction geometry/identity')
            prediction=np.asarray(nib.load(path/name).dataobj)
            m=measure(prediction,target,affine);del prediction,target
            row=dict(role=role,index=index,study_id=sid,step=session.step,metrics=m,
                descriptor_sha256=digest(canonical(item['descriptor'])),transform=record,padding=padding,
                export=exported,filename=name,reference=provenance,seconds=time.monotonic()-started)
            put(path/f'{role}-{index:04d}.json',canonical(row));rows.append(row);guard()
    require(weight_digest(session)==before, 'Evaluation changed weights')
    receipt=dict(schema_version='twomm-training-evaluation-1',identity_sha256=session._identity_pin,
        step=session.step,roles=stage['roles'],weight_sha256=before,
        cases=[dict(role=r['role'],index=r['index'],study_id=r['study_id']) for r in rows],
        files={p.name:dict(bytes=p.stat().st_size,sha256=digest(p.read_bytes())) for p in sorted(path.iterdir())})
    put(path/'complete.json',canonical(receipt))
    return dict(directory=path.name,receipt_sha256=digest(canonical(receipt)),step=session.step)


def verify_evaluation(path,pin,identity,binding,stage):
    raw=(path/'complete.json').read_bytes();require(digest(raw)==pin, 'Evaluation completion differs')
    r=json.loads(raw)
    require(r['schema_version']=='twomm-training-evaluation-1' and r['identity_sha256']==digest(canonical(identity)) and
        r['step']==stage['step'] and r['roles']==stage['roles'], 'Evaluation binding differs')
    expected=[dict(role=role,index=i,study_id=e['descriptor']['study_id']) for role in stage['roles']
        for i,e in enumerate(binding['roles'][role])]
    require(r['cases']==expected, 'Evaluation membership differs')
    names={f"{c['role']}-{c['index']:04d}.{suffix}" for c in expected for suffix in ('json','nii.gz')}
    require(set(r['files'])==names and {p.name for p in path.iterdir()}==names|{'complete.json'}, 'Evaluation file inventory differs')
    for name,ref in r['files'].items():
        p=path/name;require(p.is_file() and not p.is_symlink() and p.stat().st_size==ref['bytes'] and
            digest(p.read_bytes())==ref['sha256'], 'Evaluation member differs')
    for c in expected:
        prefix=f"{c['role']}-{c['index']:04d}";row=json.loads((path/(prefix+'.json')).read_bytes())
        e=binding['roles'][c['role']][c['index']]
        require(all(row[k]==v for k,v in c.items()) and row['step']==stage['step'] and
            row['transform']==e['transform_record'] and row['reference']['descriptor']==e['descriptor'] and
            row['descriptor_sha256']==digest(canonical(e['descriptor'])), 'Evaluation case binding differs')
        require(row['filename']==prefix+'.nii.gz', 'Export path differs')
        verify_export(path/row['filename'],row['transform'],expected_sha256=row['export']['sha256'],
            expected_foreground=row['metrics']['predicted_voxels'])
    return r


def execute(session,cache,destination,*,open_references,save_checkpoint,keep_evaluation=None,
            check_parent=None,guard=lambda:None,clock=time.monotonic):
    """Fresh attempt only. save_checkpoint must return verified primary AND backup refs.

    A failed attempt is retained. Recovery inspection does not authorize continuing it.
    The outer native supervisor enforces process/driver/power/storage/time limits.
    """
    require(keep_evaluation is not None or session.identity['purpose']=='synthetic-training-transaction', 'Real evaluation keeper required')
    require(session.identity['schema_version']=='twomm-training-5' and session.plan['execution_mode']=='tail_training','Wrong parented execution scope')
    require(check_parent is not None,'Parent inference verifier required')
    session.verify(cache);require(session.step==0 and not session.history, 'Fresh attempt required; no implicit resume')
    dest=Path(destination);require(dest.is_absolute() and dest.is_dir() and dest.resolve()==dest and
        not any(dest.iterdir()), 'Attempt destination must be empty and canonical')
    put(dest/'identity.json',canonical(session.identity))
    for name,raw in session.controls.items():put(dest/name,raw)
    journal=Journal(dest/'events.jsonl',session.identity);started=clock();refs=[];evals=[];coverage=[];parent_reviews=[]
    def check():
        guard();require(clock()-started<session.plan['total_seconds'], 'Training transaction time cap')
        size=sum(p.stat().st_size for p in dest.rglob('*') if p.is_file())
        require(size<=session.plan['output_bytes'], 'Training transaction output cap')
    def event(**row):journal.append(row)
    try:
        event(state='attempt_started',step=0);check()
        for boundary in session.plan['checkpoint_steps']:
            while session.step<boundary:
                check();event(state='update_started',step=session.step)
                row=session.update(cache,guard=check);event(state='update_complete',**row);check()
            check();event(state='checkpoint_started',step=session.step)
            ref=save_checkpoint(payload(session),session.identity)
            require(set(ref)=={'primary','backup'} and ref['primary']['step']==session.step and
                all(ref[k].get('receipt_sha256') for k in ('primary','backup')), 'Incomplete checkpoint/backup')
            refs.append(ref);event(state='checkpoint_complete',step=session.step,reference=ref);check()
            stage=next(s for s in session.plan['evaluations'] if s['step']==boundary)
            event(state='evaluation_started',step=session.step)
            references=open_references(stage,check)
            ref=evaluate(session,cache,references,stage,dest/f'evaluation-{boundary:04d}',guard=check)
            if keep_evaluation is not None:
                kept=keep_evaluation(dest/ref['directory'],session.identity)
                require(set(kept)=={'primary','backup'} and all(kept[k].get('receipt_sha256') for k in kept), 'Incomplete evaluation keeper')
                ref['keeper']=kept
            evals.append(ref);event(state='evaluation_complete',step=session.step,reference=ref);check()
            if session.identity['schema_version']=='twomm-training-5':
                from src.training.twomm_coverage_guard import review
                rows=[json.loads(p.read_bytes()) for p in sorted((dest/ref['directory']).glob('evaluator-*.json'))]
                require([r['study_id'] for r in rows]==cache.members('evaluator'), 'Coverage review omitted/reordered members')
                decision=review(rows,session.plan['coverage_guard'],boundary,coverage);coverage.append(decision)
                put(dest/f'coverage-review-{boundary:04d}.json',canonical(decision))
                event(state='coverage_review_complete',decision=decision)
                if boundary==0:
                    from src.training.twomm_rebalanced_parity import validate_decision
                    parent=check_parent(session,dest/ref['directory'],ref['receipt_sha256'])
                    validate_decision(parent,session.identity,session.binding)
                    require(parent['weight_sha256']==weight_digest(session),'Parent review model differs')
                    parent_reviews.append(parent);put(dest/'parent-review-0000.json',canonical(parent))
                    event(state='parent_review_complete',decision=parent)
                    if parent['state']=='stop':
                        event(state='parent_stop',step=0,reasons=parent['reasons']);break
                if decision['state']=='stop':
                    event(state='coverage_stop',step=boundary,reasons=decision['reasons']);break
        for stage,ref in zip(session.plan['evaluations'][:len(evals)],evals):
            verify_evaluation(dest/ref['directory'],ref['receipt_sha256'],session.identity,session.binding,stage)
        check();event(state='transaction_verified',step=session.step)
        journal.close();events,pin=verify_journal((dest/'events.jsonl').read_bytes(),session.identity)
        require([r['completed_step'] for r in events if r['state']=='update_complete']==list(range(1,session.step+1)), 'Incomplete update journal')
        result=dict(schema_version='twomm-training-completion-1',state='complete',identity_sha256=session._identity_pin,
            completed_steps=session.step,checkpoints=refs,evaluations=evals,history_sha256=digest(canonical(session.history)),
            journal_sha256=digest((dest/'events.jsonl').read_bytes()),last_event_sha256=pin,
            weight_sha256=weight_digest(session),seconds=clock()-started)
        if session.identity['schema_version']=='twomm-training-5':
            result.update(coverage_reviews=coverage,planned_steps=session.config['max_steps'],
                state='stopped_coverage_guard' if coverage[-1]['state']=='stop' else 'complete')
        require(len(parent_reviews)==1,'Missing parent review')
        result.update(parent_reviews=parent_reviews,absolute_completed_steps=session.config['parent_steps']+session.step,
            state='stopped_parent_mismatch' if parent_reviews[0]['state']=='stop' else result['state'])
        put(dest/'complete.json',canonical(result))
        if result['state'].startswith('stopped_'):session.poisoned=True
        return result
    except BaseException as exc:
        session.poisoned=True
        if not journal.stream.closed:
            event(state='failed_or_interrupted',completed_steps=session.step,error_type=type(exc).__name__,
                message=str(exc),last_complete_checkpoint=refs[-1] if refs else None)
        raise
    finally:journal.close()
