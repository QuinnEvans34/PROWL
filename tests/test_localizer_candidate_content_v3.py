from retained_diagnostic_metadata import metadata as retained_metadata
from copy import deepcopy
import json
import pytest
from scripts.diagnostics.localizer_candidate_content_v3 import (checked_selection,batch_limits,validate_batch,BATCH_PLAN,HEADERS,candidate_controls,large_gate)


@pytest.mark.parametrize('batch',[f'batch-{i:02}' for i in range(2,16)])
def test_exact_batches(batch):
    saved=retained_metadata();row=validate_batch(next(b for b in json.loads(BATCH_PLAN.read_bytes())['batches'] if b['batch_id']==batch),saved['header_job']['cases'],saved['header_cases'])
    s=saved['selections'][batch];assert s['batch_id']==batch
    assert s['candidates'][row['role']]==[dict(r['candidate'],header_evidence=r['header_evidence']) for r in row['cases']]
    assert len(s['candidates'])==1


@pytest.mark.parametrize('bad',['batch-01','batch-16',None])
def test_consumed_or_unknown_refused(bad):
    with pytest.raises(ValueError):batch_limits(bad)


@pytest.mark.parametrize('fault',['role','duplicate','limits','header'])
def test_faults(fault):
    b=deepcopy(json.loads(BATCH_PLAN.read_bytes())['batches'][1])
    if fault=='role':b['role']='validation'
    if fault=='duplicate':b['cases'][1]=b['cases'][0]
    if fault=='limits':b['limits']['voxel_count']=96000000
    if fault=='header':b['cases'][0]['header_evidence']['headers'][0]['shape'][0]+=1
    with pytest.raises(ValueError):validate_batch(b,retained_metadata()['header_job']['cases'],retained_metadata()['header_cases'])


def test_large_gate_required():
    with pytest.raises(ValueError):large_gate(None,None)
