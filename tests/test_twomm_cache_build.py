from retained_diagnostic_metadata import metadata as retained_metadata
from copy import deepcopy
import json
from pathlib import Path
import pytest
from scripts.diagnostics import twomm_cache_build as job
from src.data.twomm_cache_inputs import ExpandedDataset,ReadBudget,open_expanded_inputs
from src.data.manifest_records import digest
from test_twomm_localizer_inputs import scoped,recipe

@pytest.mark.parametrize('role',['optimizer','evaluator'])
def test_new_factory_keeps_single_use_roles(tmp_path,role):
    d,_,root=scoped(tmp_path,role);budget=ReadBudget([d]);ds=ExpandedDataset([d],root,lambda:None,recipe(),budget,role)
    with pytest.raises(ValueError):ds.load(0,operation='optimizer' if role=='evaluator' else 'evaluator')
    ds.load(0,operation=role);assert budget.files==2
    with pytest.raises(ValueError):ds.load(0,operation=role)

def test_old_capability_refused_before_real_resolution():
    raw=Path('docs/capstone/data/TWOMM-LOCALIZER-INPUT-CAPABILITY-2026-09-30.json').read_bytes()
    with pytest.raises(ValueError,match='Unsupported read scope'):
        open_expanded_inputs(repo=Path.cwd(),capability_bytes=raw,trusted_capability_sha256=digest(raw),recipe_bytes=b'',trusted_recipe_sha256='',batch_id='pilot')

def test_exact_partition_and_read_limits():
    c=json.loads(job.CAP.read_bytes());flat=[sid for b in c['batches'] for sid in b['study_ids']]
    assert len(flat)==len(set(flat))==153 and [len(b['study_ids']) for b in c['batches']]==[8,145]
    assert set(flat)==set(sum(c['members'].values(),[])) and c['approval']=='D-300'
    b=retained_metadata()['binding']
    for name in ['pilot','remainder']:
        sub=job.subset(b,c,name);assert all(sub['roles'].values())
        assert sum(len(v) for v in sub['roles'].values())==(8 if name=='pilot' else 145)
    assert job.subset(b,c,'assembly')==b

@pytest.mark.parametrize('fault',['pin','member','path'])
def test_prior_receipt_corruption_refused(tmp_path,monkeypatch,fault):
    monkeypatch.setattr(job,'ROOT',tmp_path)
    p=tmp_path/'result';p.mkdir();(p/'results.json').write_bytes(b'{}')
    raw=job.encoded(dict(state='complete',files={'results.json':dict(bytes=2,sha256=job.sha(b'{}'))}));(p/'receipt.json').write_bytes(raw);pin=job.sha(raw)
    if fault=='pin':pin='0'*64
    elif fault=='member':(p/'results.json').write_bytes(b'bad')
    else:p=p/'..'
    with pytest.raises(ValueError):job.result_checked(p,pin)

def test_subset_copies_without_mutating_full_binding():
    b=retained_metadata()['binding'];c=json.loads(job.CAP.read_bytes());sub=job.subset(b,c,'pilot');sub['recipe']['spacing_mm'][0]=99
    assert b['recipe']['spacing_mm'][0]==2

def test_aggregate_counts_all_retained_attempts(tmp_path,monkeypatch):
    monkeypatch.setattr(job,'ROOT',tmp_path);p=tmp_path/'retained';p.mkdir();(p/'x').write_bytes(b'123')
    (tmp_path/'twomm-cache-build-claim-abc-pilot.json').write_text(json.dumps({'result':'retained'}))
    assert job.aggregate_guard('abc')==3
    assert job.aggregate_guard('other')==0
