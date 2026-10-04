"""Exact inference qualification from imported immutable weights; no fresh replay."""
import json
import nibabel as nib
import numpy as np
from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.training.twomm_rebalanced_training import weight_digest


def decision(i,b,*,weight_sha256,expected_weight_sha256,mismatched_masks):
    r=dict(schema_version='twomm-parent-review-1',step=0,parent_reference_sha256=i['parent_reference_sha256'],
        weight_sha256=weight_sha256,expected_weight_sha256=expected_weight_sha256,
        expected_members=[e['descriptor']['study_id'] for e in b['roles']['evaluator']],mismatched_masks=mismatched_masks)
    r['reasons']=(['imported_weights_differ'] if weight_sha256!=expected_weight_sha256 else [])+(['parent_native_masks_differ'] if mismatched_masks else [])
    r['state']='stop' if r['reasons'] else 'matched';validate_decision(r,i,b);return r


def validate_decision(r,i,b):
    require(set(r)=={'schema_version','step','parent_reference_sha256','weight_sha256','expected_weight_sha256','expected_members','mismatched_masks','reasons','state'} and
        r['schema_version']=='twomm-parent-review-1' and type(r['step']) is int and r['step']==0 and
        r['parent_reference_sha256']==i['parent_reference_sha256'],'Parent inference decision differs')
    for k in ('weight_sha256','expected_weight_sha256'):
        require(isinstance(r[k],str) and len(r[k])==64 and all(z in '0123456789abcdef' for z in r[k]),'Invalid parent weight pin')
    ids=r['expected_members'];miss=r['mismatched_masks']
    require(isinstance(ids,list) and ids and len(set(ids))==len(ids) and all(isinstance(s,str) and s for s in ids) and
        isinstance(miss,list) and len(set(miss))==len(miss) and all(s in ids for s in miss),'Parent mask membership differs')
    if b is not None:require(ids==[e['descriptor']['study_id'] for e in b['roles']['evaluator']],'Parent review members differ')
    if i['purpose']=='qualified-twomm-training':
        require(len(ids)==40 and r['expected_weight_sha256']=='8db271a2f458386e4fd33af7bd3540bade4ebd23a19e79b565c9b8715c8ea988','Real parent review scope differs')
    reasons=(['imported_weights_differ'] if r['weight_sha256']!=r['expected_weight_sha256'] else [])+(['parent_native_masks_differ'] if miss else [])
    require(r['reasons']==reasons and r['state']==('stop' if reasons else 'matched'),'Parent inference result differs')


def check(session,path,pin):
    from src.training.twomm_rebalanced_executor import verify_evaluation
    require(session.step==0,'Wrong imported-model stage')
    verify_evaluation(path,pin,session.identity,session.binding,session.plan['evaluations'][0])
    refs=session.parent_reference['prefix_reference']['cases'];miss=[]
    require([(r['index'],r['study_id']) for r in refs]==[(j,e['descriptor']['study_id']) for j,e in enumerate(session.binding['roles']['evaluator'])],'Parent baseline masks differ')
    for r in refs:
        a=np.asarray(nib.load(path/f"evaluator-{r['index']:04d}.nii.gz").dataobj)
        if list(a.shape)!=r['shape'] or digest(a.tobytes())!=r['native_mask_sha256']:miss.append(r['study_id'])
    return decision(session.identity,session.binding,weight_sha256=weight_digest(session),
        expected_weight_sha256=session.parent_reference['weight_sha256'],mismatched_masks=miss)
