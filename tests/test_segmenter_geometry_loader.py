from copy import deepcopy
import os
from pathlib import Path
import numpy as np
import pytest
from scripts.diagnostics import segmenter_source_verification as source
from scripts.diagnostics.segmenter_content_pilot import invented_file
from src.data import segmenter_geometry_loader_v1 as loader
from src.data.source_inventory_records import content_hash


def synthetic(tmp_path):
    rows=[]
    for kind in ('ct','pancreas','lesion'):
        blob,row=invented_file(kind,'fragmented',(5,6,7));path=tmp_path/(kind+'.nii.gz');path.write_bytes(blob)
        row.update(uri=path.name,study_id='invented',protected_role='train',observation=source.observation(path.stat()))
        rows.append(row)
    refs={r['kind']:dict(root_alias='followup_source',uri=r['uri'],bytes=r['compressed_bytes'],content_sha256=r['sha256']) for r in rows}
    d=dict(study_id='invented',subject_id='invented-subject',protected_role='train',purpose='pancreas_lesion_segmenter_training',
        operation='optimizer',lesion_target_state='positive',roi_source='pancreas_only',class_precedence='lesion_over_pancreas',
        image=refs['ct'],pancreas=refs['pancreas'],lesion=refs['lesion'],geometry=rows[0]['geometry'])
    records=dict(optimizer=[d],evaluator=[])
    counts=dict(hash_bytes=0,decode_bytes=0,expanded_bytes=0)
    limits=dict(hash_bytes=sum(r['compressed_bytes'] for r in rows),decode_bytes=sum(r['compressed_bytes'] for r in rows),
        expanded_bytes=sum(r['expanded_bytes'] for r in rows))
    return records,d,rows,counts,limits


def test_scaled_native_read_with_exact_counts_shapes_and_semantics(tmp_path):
    records,d,rows,count,limits=synthetic(tmp_path)
    assert loader.checked_descriptor(records,content_hash(records),'invented','optimizer')==d
    with source.directory(tmp_path) as root:
        ct,pan,les,a,report=loader.read_triple(root,d,rows,count,limits)
    assert count==limits and ct.shape==pan.shape==les.shape==(5,6,7)
    assert ct.dtype==np.float32 and les[0,0,0]==1 and les.sum()==1 and pan.sum()>0
    assert report['lesion_decode']['max_endpoint_residual']<1e-6 and np.array_equal(a,np.diag([1,1,2,1]))


@pytest.mark.parametrize('fault',['wrong_role','held_member','no_operation','stale_descriptor','wrong_purpose','empty_unknown'])
def test_consumer_denial_precedes_file_access(tmp_path,fault):
    records,d,_,_,_=synthetic(tmp_path);pin=content_hash(records);op='optimizer';sid='invented'
    if fault=='wrong_role':op='evaluator'
    if fault=='held_member':sid='absent-held'
    if fault=='no_operation':op=None
    if fault=='stale_descriptor':d['image']['content_sha256']='0'*64
    if fault=='wrong_purpose':d['purpose']='pancreas_localizer_training';pin=content_hash(records)
    if fault=='empty_unknown':d['lesion_target_state']='unknown';pin=content_hash(records)
    with pytest.raises(ValueError):loader.checked_descriptor(records,pin,sid,op)


@pytest.mark.parametrize('fault',['missing','duplicate','wrong_role','stale_hash','stale_size','wrong_geometry','unsafe_path','wrong_source'])
def test_rows_are_checked_before_any_source_open(tmp_path,monkeypatch,fault):
    _,d,rows,count,limits=synthetic(tmp_path)
    if fault=='missing':rows.pop()
    if fault=='duplicate':rows[2]=deepcopy(rows[1])
    if fault=='wrong_role':rows[0]['protected_role']='validation'
    if fault=='stale_hash':rows[0]['sha256']='0'*64
    if fault=='stale_size':rows[0]['compressed_bytes']+=1
    if fault=='wrong_geometry':rows[0]['geometry']=deepcopy(rows[0]['geometry']);rows[0]['geometry']['shape_xyz'][0]+=1
    if fault=='unsafe_path':rows[0]['uri']='../ct.nii.gz'
    if fault=='wrong_source':d['image']['root_alias']='unqualified'
    def forbidden(*args,**kwargs):pytest.fail('Source open after scope rejection')
    monkeypatch.setattr(source,'source_stream',forbidden)
    with pytest.raises(ValueError):loader.read_triple(-1,d,rows,count,limits)
    assert all(n==0 for n in count.values())


@pytest.mark.parametrize('key',['hash_bytes','decode_bytes','expanded_bytes'])
def test_full_triple_budget_reserved_before_open(tmp_path,monkeypatch,key):
    _,d,rows,count,limits=synthetic(tmp_path);limits[key]-=1
    monkeypatch.setattr(source,'source_stream',lambda *args:pytest.fail('Open after budget failure'))
    with pytest.raises(RuntimeError):loader.read_triple(-1,d,rows,count,limits)


@pytest.mark.parametrize('fault',['symlink','missing','replaced','changed_bytes','nonregular'])
def test_filesystem_identity_or_hash_fault_refused(tmp_path,fault):
    _,d,rows,count,limits=synthetic(tmp_path);path=tmp_path/'ct.nii.gz'
    if fault=='symlink':path.rename(tmp_path/'other');path.symlink_to(tmp_path/'other')
    if fault=='missing':path.unlink()
    if fault=='replaced':raw=path.read_bytes();path.unlink();path.write_bytes(raw)
    if fault=='changed_bytes':
        raw=bytearray(path.read_bytes());raw[15]^=1;path.write_bytes(raw)
        # Re-bind invented stat evidence to reach the independent content-hash guard.
        rows[0]['observation']=source.observation(path.stat())
    if fault=='nonregular':path.unlink();path.mkdir()
    with source.directory(tmp_path) as root:
        with pytest.raises((ValueError,FileNotFoundError)):loader.read_triple(root,d,rows,count,limits)


def test_bare_session_or_prepared_request_cannot_read(tmp_path,monkeypatch):
    records,_,_,count,limits=synthetic(tmp_path)
    kwargs=dict(trusted_request_sha256='a'*64,study_id='invented',operation='optimizer',rootfd=-1,counts=count)
    with pytest.raises(ValueError,match='Bare'):loader.read_case(records,{},**kwargs)
    with pytest.raises(ValueError):loader.ResolvedInputs(records,object())
    session=loader.ResolvedInputs(records,loader._TOKEN)
    request=dict(cohort_completion_sha256=loader.COMPLETION,descriptor_sha256=loader.DESCRIPTORS,stage='segmenter_geometry_fidelity',
        source_reads_approved=False,capability={})
    kwargs['trusted_request_sha256']=source.sha(source.encoded(request))
    monkeypatch.setattr(source,'mount_guard',lambda *args:pytest.fail('Mount read after approval rejection'))
    with pytest.raises(ValueError,match='Prepared'):loader.read_case(session,request,**kwargs)
