from retained_diagnostic_metadata import metadata as retained_metadata
from copy import deepcopy
import json
import nibabel as nib
import numpy as np
import pytest
from scripts.diagnostics.localizer_candidate_content_v2 import (
    BATCH_PLAN,HEADERS,candidate_controls,checked_selection,validate_batch,validate_decoded_header)


def test_exact_pilot():
    saved=retained_metadata();batch=validate_batch(json.loads(BATCH_PLAN.read_bytes())['batches'][0],saved['header_job']['cases'],saved['header_cases'])
    s=saved['selections'][batch['batch_id']]
    assert s['candidates']['train']==[dict(r['candidate'],header_evidence=r['header_evidence']) for r in batch['cases']]
    assert s['batch_id']=='batch-01' and len(s['candidates']['train'])==16


@pytest.mark.parametrize('fault',['role','id','duplicate','held','header','limits','category'])
def test_substitutions_refused(fault):
    batch=deepcopy(json.loads(BATCH_PLAN.read_bytes())['batches'][0])
    saved=retained_metadata();candidates=saved['header_job']['cases'];headers=saved['header_cases']
    if fault=='role':batch['cases'][0]['candidate']['protected_role']='validation'
    if fault=='id':batch['batch_id']='batch-02'
    if fault=='duplicate':batch['cases'][1]=batch['cases'][0]
    if fault=='held':batch['cases'][0]['candidate']['study_id']='pants:study:PanTS_00006350'
    if fault=='header':batch['cases'][0]['header_evidence']['headers'][0]['shape'][0]+=1
    if fault=='limits':batch['limits']['voxel_count']=96000000
    if fault=='category':batch['category']='large_singleton'
    with pytest.raises(ValueError):validate_batch(batch,candidates,headers)


@pytest.mark.parametrize('fault',['shape','dtype','units','affine'])
def test_decoded_header_binding(fault):
    im=nib.Nifti1Image(np.zeros((2,3,4),np.int16),np.eye(4));im.header.set_xyzt_units('mm')
    h=dict(shape=[2,3,4],dtype='int16',units=['mm','unknown'],affine=np.eye(4).tolist())
    validate_decoded_header(im,h)
    if fault=='shape':h['shape'][0]+=1
    if fault=='dtype':h['dtype']='float32'
    if fault=='units':h['units'][0]='unknown'
    if fault=='affine':h['affine'][0][3]=1
    with pytest.raises(ValueError):validate_decoded_header(im,h)
