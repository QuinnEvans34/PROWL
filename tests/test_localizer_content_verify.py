import copy
import hashlib
import json
from pathlib import Path
import time

import pytest

from scripts.diagnostics import localizer_content_verify as job
from scripts.diagnostics.followup_voxel_audit import Package


@pytest.fixture(autouse=True)
def deterministic_in_process_rss(monkeypatch):
    # Hash/path unit tests must not inherit the whole pytest process's earlier torch high-water mark.
    # Subprocess worker/supervisor tests below still observe native process memory.
    monkeypatch.setattr(job,'peak_rss',lambda:16*1024**2)


def test_memory_boundary(monkeypatch):
    monkeypatch.setattr(job,'peak_rss',lambda:8)
    job.check_memory(8)
    with pytest.raises(ValueError,match='RSS'):job.check_memory(7)


def fixture(tmp_path):
    root = tmp_path.resolve() / 'source'; root.mkdir()
    p = root / 'ct.nii.gz'; p.write_bytes(b'not-actually-nifti' * 100)
    obs = job.signature(p.stat()); size = obs.pop('bytes')
    row = dict(uri=p.name, protected_role='train', kind='ct', bytes=size, observation=obs,
               expected_content_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    kwargs = dict(chunk_bytes=19, remaining_bytes=10000, memory_limit=512*1024**2)
    return root, row, kwargs


def test_streams_exact_bytes_without_decoding(tmp_path):
    root, row, kwargs = fixture(tmp_path)
    result = job.hash_file(root, row, **kwargs)
    assert result['sha256'] == row['expected_content_sha256']
    assert result['bytes'] == row['bytes']


@pytest.mark.parametrize('field,value', [('protected_role','validation'), ('protected_role','test'),
    ('kind','pancreatic_lesion'), ('expected_content_sha256','0'*64)])
def test_rejects_wrong_request_or_hash(tmp_path, field, value):
    root, row, kwargs = fixture(tmp_path); row[field] = value
    with pytest.raises(ValueError): job.hash_file(root, row, **kwargs)


@pytest.mark.parametrize('change', ['missing','resize','replace','symlink','parent_symlink'])
def test_changed_identity_and_paths_rejected(tmp_path, change):
    root, row, kwargs = fixture(tmp_path); p = root/row['uri']
    if change == 'missing': p.unlink()
    if change == 'resize': p.write_bytes(b'changed')
    if change == 'replace':
        data=p.read_bytes(); p.unlink(); p.write_bytes(data)
    if change == 'symlink':
        p.rename(root/'real'); p.symlink_to(root/'real')
    if change == 'parent_symlink':
        alias=tmp_path.resolve()/'alias'; alias.symlink_to(root, target_is_directory=True); root=alias
    with pytest.raises((ValueError,OSError)): job.hash_file(root, row, **kwargs)


@pytest.mark.parametrize('uri', ['../escape', '/etc/passwd', 'a/../ct.nii.gz'])
def test_traversal_refused(tmp_path, uri):
    root, row, kwargs = fixture(tmp_path); row['uri']=uri
    with pytest.raises(ValueError): job.hash_file(root, row, **kwargs)


def test_mutation_mid_read(tmp_path):
    root, row, kwargs = fixture(tmp_path); count=0
    def mutate():
        nonlocal count
        count += 1
        if count == 2:
            with (root/row['uri']).open('r+b') as f: f.write(b'x')
    with pytest.raises(ValueError, match='mutated'): job.hash_file(root, row, tick=mutate, **kwargs)


@pytest.mark.parametrize('limit', ['remaining_bytes', 'memory_limit'])
def test_resource_limits(tmp_path, limit):
    root,row,kwargs=fixture(tmp_path); kwargs[limit]=1
    with pytest.raises(ValueError): job.hash_file(root,row,**kwargs)


def test_altered_spec_pin(tmp_path):
    p=tmp_path/'spec.json';p.write_text('{}')
    with pytest.raises(ValueError,match='specification pin'):job.load_spec(p)


def test_changed_control_pin(tmp_path, monkeypatch):
    monkeypatch.setattr(job,'REPO',tmp_path.resolve())
    p=tmp_path/'control';p.write_text('changed')
    spec=tmp_path/'spec.json';spec.write_text(json.dumps(dict(inputs=[dict(path='control',sha256='0'*64)])))
    with pytest.raises(ValueError,match='Retained control'):job.load_spec(spec,job.digest(spec.read_bytes()))


def test_real_worker_and_supervisor(tmp_path):
    root,row,kwargs=fixture(tmp_path)
    request=dict(root=str(root),row=row,**kwargs)
    result=job.supervised_hash(request,10,kwargs['memory_limit'])
    assert result['bytes']==row['bytes']


def test_worker_timeout(tmp_path):
    root,row,kwargs=fixture(tmp_path)
    with pytest.raises(TimeoutError):
        job.supervised_hash(dict(root=str(root),row=row,**kwargs),.001,kwargs['memory_limit'])


def test_supervisor_memory_ceiling(tmp_path):
    root,row,kwargs=fixture(tmp_path)
    with pytest.raises(ValueError,match='RSS'):
        job.supervised_hash(dict(root=str(root),row=row,**kwargs),10,1)


@pytest.mark.parametrize('failure', ['worker','result','time','output','read_cap','mount'])
def test_failed_execute_never_completes(tmp_path,failure):
    root,row,kwargs=fixture(tmp_path)
    package=Package(tmp_path.resolve()/'output',max_bytes=1 if failure=='output' else 10000)
    spec=dict(files=[row],unique_input_bytes=row['bytes'],limits=dict(process_rss_bytes=512*1024**2,
        source_read_bytes=1 if failure=='read_cap' else 10000,per_file_seconds=10,chunk_bytes=19))
    def worker(request,*_):
        if failure=='worker':raise ValueError('worker failed')
        r=job.hash_file(root,row,**kwargs)
        if failure=='result':r['sha256']='0'*64
        return r
    def mount():
        if failure=='mount':raise ValueError('mount changed')
    deadline=time.monotonic()+(-1 if failure=='time' else 10)
    with pytest.raises((ValueError,TimeoutError)):
        job.execute(spec,root,package,mount,deadline,worker)
    assert not (package.path/'verification.json').exists()
