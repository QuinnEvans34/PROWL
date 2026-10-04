"""Small independent keepers for evaluation records; native masks remain derived scratch.

The keeper explicitly inventories omitted reproducible masks by hash. It never claims
those bytes were backed up. Checkpoints, metrics, reference receipts and controls are kept.
"""
import json
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require


def validate(files,identity):
    require(set(files)=={'record.json'},'Evidence inventory differs');r=json.loads(files['record.json'])
    require(set(r)=={'schema_version','identity_sha256','kind','content'} and
        r['schema_version']=='twomm-training-evidence-1' and
        r['identity_sha256']==digest(canonical(identity)) and r['kind'] in ('evaluation','terminal','qualification'), 'Wrong evidence identity/type')
    c=r['content']
    if r['kind']=='evaluation':
        require(set(c)=={'completion','cases','derived_masks_not_backed_up'} and
            c['completion']['identity_sha256']==r['identity_sha256'],'Evaluation evidence identity differs')
        receipt=c['completion'];rows=c['cases'];expected=receipt['cases']
        require([{k:row[k] for k in ('role','index','study_id')} for row in rows]==expected,'Evidence membership differs')
        omitted={row['filename']:row['export']['sha256'] for row in rows}
        require(c['derived_masks_not_backed_up']==omitted,'Derived mask accounting differs')
        for row in rows:
            name=f"{row['role']}-{row['index']:04d}.json";raw=canonical(row)
            require(receipt['files'][name]==dict(bytes=len(raw),sha256=digest(raw)) and
                row['step']==receipt['step'] and receipt['files'][row['filename']]['sha256']==row['export']['sha256'], 'Evidence content differs')
            m=row['metrics'];n=m['reference_voxels'];v=m['predicted_voxels'];tp=m['true_positive']
            require(type(n) is int and n>0 and type(v) is int and v>=0 and type(tp) is int and 0<=tp<=min(n,v) and
                m['false_positive']==v-tp and m['false_negative']==n-tp and m['dice']==2*tp/(n+v) and
                m['recall']==tp/n and m['volume_ratio']==v/n,'Invalid retained count arithmetic')
    elif r['kind']=='qualification':
        from src.training.twomm_rebalanced_parity import validate_decision
        result=c['result'];require(set(c)=={'result','probe_sha256'} and result['state'] in ('qualified','refused') and
            result['completed_steps']==0 and result['absolute_completed_steps']==identity['config']['parent_steps'] and
            result['identity_sha256']==r['identity_sha256'] and len(result['parent_reviews'])==1 and len(result['coverage_reviews'])==1,
            'Wrong zero-update qualification evidence')
        validate_decision(result['parent_reviews'][0],identity,None)
        require((result['state']=='qualified')==(result['parent_reviews'][0]['state']=='matched' and result['coverage_reviews'][0]['state']=='pass') and
            result['weight_sha256']==result['parent_reviews'][0]['weight_sha256'] and len(result['checkpoints'])==len(result['evaluations'])==1,
            'Qualification outcome differs')
    else:
        result=c['result'];require(identity['schema_version']=='twomm-training-5','Wrong parented evidence');extended=True
        require(set(c)=={'result','journal','probe_sha256'} and
            result['state'] in ('complete','stopped_coverage_guard','stopped_parent_mismatch') and
            result['identity_sha256']==r['identity_sha256'],'Incomplete terminal record')
        if extended:
            # The identity pins plan bytes; journal must match every recorded review and boundary.
            require(result['planned_steps']==identity['config']['max_steps'] and result['coverage_reviews'] and
                result['coverage_reviews'][-1]['step']==result['completed_steps'] and
                (result['state']=='stopped_parent_mismatch' or
                 (result['state']=='stopped_coverage_guard')==(result['coverage_reviews'][-1]['state']=='stop')),
                'Stopped/completed coverage record differs')
        if result['state']=='complete':
            require(result['completed_steps']==identity['config']['max_steps'],'Incomplete terminal record')
        raw=c['journal'].encode();require(digest(raw)==c['result']['journal_sha256'],'Terminal journal differs')
        from src.training.twomm_rebalanced_executor import verify_journal
        rows,pin=verify_journal(raw,identity)
        require(pin==c['result']['last_event_sha256'] and rows[-1]['state']=='transaction_verified','Incomplete terminal journal')
        if extended:
            require([e['decision'] for e in rows if e['state']=='coverage_review_complete']==result['coverage_reviews'] and
                [e['completed_step'] for e in rows if e['state']=='update_complete']==list(range(1,result['completed_steps']+1)),
                'Coverage/update journal differs')
        from src.training.twomm_rebalanced_parity import validate_decision
        reviews=result['parent_reviews'];require(len(reviews)==1,'Missing parent review')
        validate_decision(reviews[0],identity,None)
        require((result['state']=='stopped_parent_mismatch')==(reviews[0]['state']=='stop') and
            [e['decision'] for e in rows if e['state']=='parent_review_complete']==reviews and
            result['absolute_completed_steps']==identity['config']['parent_steps']+result['completed_steps'] and
            (result['state']!='stopped_parent_mismatch' or result['completed_steps']==0),'Parent terminal accounting differs')
    return dict(identity_sha256=r['identity_sha256'],kind=r['kind'],content_sha256=digest(canonical(c)))


def evaluation_files(path,identity):
    receipt=json.loads((path/'complete.json').read_bytes())
    rows=[json.loads((path/f"{e['role']}-{e['index']:04d}.json").read_bytes()) for e in receipt['cases']]
    content=dict(completion=receipt,cases=rows,derived_masks_not_backed_up={r['filename']:r['export']['sha256'] for r in rows})
    return encode(identity,'evaluation',content)


def encode(identity,kind,content):
    files={'record.json':canonical(dict(schema_version='twomm-training-evidence-1',identity_sha256=digest(canonical(identity)),kind=kind,content=content))}
    validate(files,identity);return files


def publish(store,files,identity,suffix):
    validate(files,identity);artifact_id=identity['run_id']+':evidence:'+suffix
    derivation=digest(canonical(dict(identity=identity,suffix=suffix)))
    metadata=dict(artifact_type='training-evidence',schema_version='twomm-training-evidence-1',component='twomm-training',
        code_sha256=identity['source_sha256'],parents=[identity['inputs_sha256'],identity['plan_sha256']],
        retention='research-keeper',sensitivity='private-research',run_id=identity['run_id'],stage_id=suffix)
    pin,status=store.publish(artifact_id,derivation_sha256=derivation,files=files,metadata=metadata,
        validate=lambda f:validate(f,identity))
    return dict(artifact_id=artifact_id,receipt_sha256=pin,derivation_sha256=derivation,status=status)
