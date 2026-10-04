"""Predeclared CAP-EXP-007 prefix comparator; no updates or primary-drive access."""
import json
import math
import nibabel as nib
import numpy as np
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require

REAL_REFERENCE_SHA256='9bd634420038d6cba9ab1533ca54224b6dffc3f9edd6d41fe659f30d9124dbbf'


def validate_reference(reference,binding):
    require(digest(canonical(reference))==REAL_REFERENCE_SHA256,'Unverified prefix reference')
    require(reference['step']==300 and reference['weight_max_abs_tolerance']==1e-6 and
        reference['identity']['inputs_sha256']==digest(canonical(binding)), 'Prefix input/step differs')
    require([(r['index'],r['study_id']) for r in reference['cases']]==
        [(j,e['descriptor']['study_id']) for j,e in enumerate(binding['roles']['evaluator'])],
        'Prefix reference membership differs')


def decision(*,step,reference_sha256,weight_difference,weight_tolerance,history_matches,
             expected_masks,mismatched_masks,baseline_weight_sha256,candidate_weight_sha256):
    reasons=[]
    if weight_difference>weight_tolerance:reasons.append('prefix_weights_differ')
    if not history_matches:reasons.append('prefix_history_differs')
    if mismatched_masks:reasons.append('prefix_native_masks_differ')
    result=dict(schema_version='twomm-prefix-review-1',step=step,reference_sha256=reference_sha256,
        model_max_abs_difference=weight_difference,weight_tolerance=weight_tolerance,
        history_matches=history_matches,expected_masks=expected_masks,
        matched_masks=expected_masks-len(mismatched_masks),mismatched_masks=mismatched_masks,
        baseline_weight_sha256=baseline_weight_sha256,candidate_weight_sha256=candidate_weight_sha256,
        reasons=reasons,state='stop' if reasons else 'matched')
    validate_decision(result);return result


def validate_decision(r):
    fields={'schema_version','step','reference_sha256','model_max_abs_difference','weight_tolerance',
        'history_matches','expected_masks','matched_masks','mismatched_masks','baseline_weight_sha256',
        'candidate_weight_sha256','reasons','state'}
    require(set(r)==fields and r['schema_version']=='twomm-prefix-review-1' and type(r['step']) is int and r['step']>0,
        'Invalid prefix review')
    for name in ('reference_sha256','baseline_weight_sha256','candidate_weight_sha256'):
        require(isinstance(r[name],str) and len(r[name])==64 and all(c in '0123456789abcdef' for c in r[name]),'Invalid prefix pin')
    require(type(r['history_matches']) is bool and type(r['expected_masks']) is int and r['expected_masks']>0 and
        type(r['matched_masks']) is int and isinstance(r['mismatched_masks'],list) and
        all(isinstance(s,str) and s for s in r['mismatched_masks']) and
        len(set(r['mismatched_masks']))==len(r['mismatched_masks']) and
        r['matched_masks']==r['expected_masks']-len(r['mismatched_masks'])>=0,'Invalid prefix mask accounting')
    for name in ('model_max_abs_difference','weight_tolerance'):
        require(type(r[name]) in (float,int) and math.isfinite(r[name]) and r[name]>=0,'Invalid prefix difference')
    reasons=[]
    if r['model_max_abs_difference']>r['weight_tolerance']:reasons.append('prefix_weights_differ')
    if not r['history_matches']:reasons.append('prefix_history_differs')
    if r['mismatched_masks']:reasons.append('prefix_native_masks_differ')
    require(r['reasons']==reasons and r['state']==('stop' if reasons else 'matched'),'Prefix outcome differs')


def check_real(session,path,pin):
    """Compare the kept prefix with a validated independent backup and frozen mask digests."""
    from scripts.diagnostics.expanded_localizer_launch import stores
    from src.operations.localizer_backup import validate_backup,EXTRA
    from src.training.twomm_training import validate_payload,decode,weight_digest
    from src.training.twomm_training_executor import verify_evaluation
    reference=session.plan['prefix_reference'];validate_reference(reference,session.binding)
    require(session.step==300 and session.identity['schema_version']=='twomm-training-3','Wrong prefix session')
    stage=next(e for e in session.plan['evaluations'] if e['step']==300)
    receipt=verify_evaluation(path,pin,session.identity,session.binding,stage)
    require(receipt['weight_sha256']==weight_digest(session),'Prefix evaluation weights differ')
    _,backup,_=stores(recovery_only=True);ref=reference['checkpoint'];br=ref['backup'];pr=ref['primary'];i=reference['identity']
    files,_=backup.resolve(br['artifact_id'],receipt_sha256=br['receipt_sha256'],expected_derivation=br['derivation_sha256'],
        validate=lambda f:validate_backup(f,i,pr,validate_payload))
    baseline,_=decode({k:v for k,v in files.items() if k not in EXTRA},i)
    before=weight_digest(session);state=session.model.state_dict();old=baseline.model.state_dict()
    difference=max(float((v.detach().cpu()-old[n]).abs().max()) for n,v in state.items())
    history_matches=len(baseline.history)==len(session.history)==300
    for j,(a,b) in enumerate(zip(session.history,baseline.history)):
        fields=('completed_step','member_index','pass_index','pass_offset','sampling')
        applied=i['config']['learning_rate'] if j==0 else baseline.history[j-1]['learning_rate']
        history_matches &= all(a[k]==b[k] for k in fields) and abs(a['learning_rate_used']-applied)<1e-12
    mismatched=[]
    for row in reference['cases']:
        p=path/f"evaluator-{row['index']:04d}.nii.gz";a=np.asarray(nib.load(p).dataobj)
        if list(a.shape)!=row['shape'] or digest(a.tobytes())!=row['native_mask_sha256']:
            mismatched.append(row['study_id'])
    require(weight_digest(session)==before,'Prefix comparison changed weights')
    return decision(step=300,reference_sha256=REAL_REFERENCE_SHA256,weight_difference=difference,
        weight_tolerance=reference['weight_max_abs_tolerance'],history_matches=bool(history_matches),
        expected_masks=len(reference['cases']),mismatched_masks=mismatched,
        baseline_weight_sha256=weight_digest(baseline),candidate_weight_sha256=before)
