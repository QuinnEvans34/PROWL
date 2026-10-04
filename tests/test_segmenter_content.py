"""Invented data only: bounded gzip, semantic decoding, components, native display and recovery."""
from copy import deepcopy
import io
import json
import gzip
import sys
import zlib
from pathlib import Path
import nibabel as nib
import numpy as np
import pytest
from PIL import Image
from scripts.diagnostics import segmenter_content_pilot as runner
from src.data import segmenter_content_v1 as core


def fixture(kind='lesion',pattern='fragmented',shape=(5,6,7)):
    return runner.invented_file(kind,pattern,shape)


def limits():return dict(hash_bytes=1024**2,decode_bytes=1024**2,expanded_bytes=1024**2)


def counters():return dict(hash_bytes=0,decode_bytes=0,expanded_bytes=0)


def decode(blob,row):
    c=counters();result=core.decode_exact(io.BytesIO(blob),row,c,limits(),lambda:None)
    return result,c


def test_exact_stream_preserves_native_fortran_coordinates_and_crc():
    blob,row=fixture();(data,header,report),count=decode(blob,row)
    assert data.shape==(5,6,7) and data.dtype==np.int8 and data[0,0,0]==127 and data[0,0,1]==-128
    assert report['gzip_eof_crc_verified'] and report['expanded_bytes']==352+210
    assert count['decode_bytes']==len(blob) and count['expanded_bytes']==562
    mask,r=core.target_content(data,header)
    assert mask.sum()==1 and mask[0,0,0]==1 and r['max_endpoint_residual']<1e-6


@pytest.mark.parametrize('fault',['crc','truncated','trailing','second_member','extra_voxel','header_change','extension'])
def test_bad_gzip_and_header_inputs_refused(fault):
    blob,row=fixture()
    if fault=='crc':blob=blob[:-8]+bytes([blob[-8]^1])+blob[-7:]
    elif fault=='truncated':blob=blob[:-2]
    elif fault=='trailing':blob+=b'extra'
    elif fault=='second_member':blob+=gzip.compress(b'extra')
    else:
        raw=bytearray(gzip.decompress(blob))
        if fault=='extra_voxel':raw+=b'x'
        elif fault=='header_change':raw[80]^=1
        elif fault=='extension':raw[348]=1
        blob=gzip.compress(raw)
    row['compressed_bytes']=len(blob);row['sha256']=__import__('hashlib').sha256(blob).hexdigest()
    with pytest.raises((ValueError,zlib.error,nib.spatialimages.HeaderDataError)):decode(blob,row)


@pytest.mark.parametrize('key',['hash_bytes','decode_bytes','expanded_bytes'])
def test_budget_checked_before_read_or_allocation(key):
    blob,row=fixture();l=limits();l[key]=0;c=counters()
    class Forbidden:
        def read(self,*_):pytest.fail('Read after cap rejection')
    with pytest.raises(core.BudgetError):
        if key=='hash_bytes':core.hash_exact(Forbidden(),row,c,l,lambda:None)
        else:core.decode_exact(Forbidden(),row,c,l,lambda:None)
    assert c==counters()


def test_hash_mismatch_and_short_input_refused():
    blob,row=fixture();core.hash_exact(io.BytesIO(blob),row,counters(),limits(),lambda:None)
    with pytest.raises(ValueError):core.hash_exact(io.BytesIO(blob[:-1]),row,counters(),limits(),lambda:None)
    row['sha256']='0'*64
    with pytest.raises(ValueError):core.hash_exact(io.BytesIO(blob),row,counters(),limits(),lambda:None)
    with pytest.raises(ValueError):decode(blob,row)


@pytest.mark.parametrize('fault',['shape','dtype','offset','affine','scaling','ct_units'])
def test_native_header_binding_rejects_changed_field(fault):
    blob,row=fixture('ct');raw=gzip.decompress(blob)[:348];r=deepcopy(row)
    if fault=='shape':r['geometry']['shape_xyz'][0]+=1
    if fault=='dtype':r['dtype']='float32'
    if fault=='offset':r['expanded_bytes']+=1
    if fault=='affine':r['geometry']['affine_ras'][3]+=.01
    if fault=='scaling':r['retained_content']['effective_scaling']['slope']=2
    if fault=='ct_units':r['retained_content']['units']=['unknown','unknown']
    with pytest.raises(ValueError):core.parse_header(raw,r)


@pytest.mark.parametrize('order',['C','F','strided'])
def test_semantic_decoding_preserves_coordinates_in_memory_layouts(order):
    a=np.full((3,4,5),-128,dtype=np.int8,order='F' if order=='F' else 'C');a[1,2,3]=127
    if order=='strided':a=a[::-1]
    mask,r=core.target_content(a,dict(slope=float(np.float32(1/255)),intercept=float(np.float32(128/255))))
    assert np.array_equal(mask,a==127) and r['foreground_voxels']==1


@pytest.mark.parametrize('value',[.1,.5,2,np.nan,np.inf])
def test_unsupported_semantic_values_not_rounded_or_thresholded(value):
    a=np.zeros((2,2,2));a[1,1,1]=value
    with pytest.raises(ValueError):core.target_content(a,dict(slope=1.,intercept=0.))


def test_multi_component_outside_pancreas_and_world_bounds_preserved():
    lesion=np.zeros((5,6,7),np.uint8);lesion[0,0,0]=1;lesion[3,4,5:7]=1
    pancreas=np.zeros_like(lesion);pancreas[0,0,0]=1;original=lesion.copy()
    affine=np.diag([-2,3,4,1]);affine[:3,3]=[20,-10,2]
    r=core.component_content(lesion,pancreas,affine)
    assert r['component_count']==2 and sorted(x['voxels'] for x in r['components'])==[1,2]
    assert r['inside_pancreas_voxels']==1 and r['outside_pancreas_voxels']==2
    assert r['bounds_xyz']==[[0,3],[0,4],[0,6]] and r['world_center_bounds_mm']==[[14.,20.],[-10.,2.],[2.,26.]]
    assert np.array_equal(lesion,original) and all(c['source_boundary_contact'] for c in r['components'])
    for c in r['components']:assert lesion[tuple(c['representative_xyz'])]==1


def test_connectivity26_and_empty_unknown_never_negative():
    mask=np.zeros((3,3,3),np.uint8);mask[0,0,0]=mask[1,1,1]=1
    assert core.component_content(mask,mask,np.eye(4))['component_count']==1
    r=core.component_content(np.zeros_like(mask),mask,np.eye(4))
    assert r['component_count']==0 and r['components']==[] and r['bounds_xyz'] is None
    assert r['lesion_reference_status']=='unknown_empty_not_verified_negative'


def test_component_output_limit_is_explicit_hold_not_truncation(monkeypatch):
    mask=np.zeros((5,5,5),np.uint8);mask[0,0,0]=mask[4,4,4]=1
    monkeypatch.setattr(core,'MAX_COMPONENTS',1)
    with pytest.raises(core.BudgetError,match='no truncation'):core.component_content(mask,mask,np.eye(4))


def test_orientation_and_tiny_detail_have_independent_world_coordinate_oracle():
    # Native X is physical -Y; native Y physical +Z; native Z physical -X.
    shape=(4,5,6);a=np.array([[0,0,-3,30],[-2,0,0,8],[0,4,0,-12],[0,0,0,1]],float)
    ct=np.zeros(shape,np.float32);pan=np.ones(shape,np.uint8);les=np.zeros(shape,np.uint8);point=[1,2,4];les[tuple(point)]=1
    r=core.component_content(les,pan,a);png,views=core.render_native(ct,pan,les,a,'invented',r['components'])
    forward=np.array(views['native_to_ras_voxel_affine']);ras=forward@np.array(point+[1])
    assert np.allclose(ras[:3],[shape[2]-1-point[2],shape[0]-1-point[0],point[1]])
    assert np.allclose(np.array(views['ras_affine'])@ras,a@np.array(point+[1]))
    assert views['ras_spacing']==[3.,2.,4.] and any(p['detail_box'] for p in views['panels'])
    assert Image.open(io.BytesIO(png)).width==1440 and les.sum()==1


def test_empty_reference_sheet_records_unknown_context():
    a=np.zeros((3,4,5));png,views=core.render_native(a,np.ones_like(a,dtype=np.uint8),a.astype(np.uint8),np.eye(4),'empty',[])
    assert len(views['panels'])==6 and not views['unshown_component_ids'] and png.startswith(b'\x89PNG')


def test_output_limit_before_write(tmp_path):
    (tmp_path/'existing').write_bytes(b'abc')
    runner.check_output(tmp_path,4,1)
    with pytest.raises(core.BudgetError):runner.check_output(tmp_path,4,2)


@pytest.mark.parametrize('mode',['success','failure','timeout','memory'])
def test_supervised_process_failure_and_interruption_preserve_logs(tmp_path,monkeypatch,mode):
    # Stub native ps for these invented children; native full suite also covers real supervisors.
    from types import SimpleNamespace
    monkeypatch.setattr(runner.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=0,stdout='999999' if mode=='memory' else '1'))
    code="print('started',flush=True)"
    if mode=='failure':code+='; raise ValueError("invented")'
    if mode in ['timeout','memory']:code+='; import time; time.sleep(20)'
    log=tmp_path/'log';command=[sys.executable,'-c',code]
    if mode=='success':assert runner.supervise(command,3,1024**3,log)['seconds']<3
    else:
        with pytest.raises((RuntimeError,core.BudgetError)):runner.supervise(command,.6 if mode=='timeout' else 3,10 if mode=='memory' else 1024**3,log)
    assert log.is_file() and b'started' in log.read_bytes()


@pytest.mark.parametrize('fault',['wrong_role','omitted_file','duplicate_case','changed_code'])
def test_exact_request_scope_mutation_refused_before_claim_or_source(tmp_path,monkeypatch,fault):
    dest=tmp_path/'fixed';dest.mkdir();path=dest/'request.json'
    good=dict(profile_receipt_sha256='invented',cases=['one','two'],files=[dict(role='train'),dict(role='validation')],code_pins={'code':'original'})
    bad=deepcopy(good)
    if fault=='wrong_role':bad['files'][0]['role']='test'
    if fault=='omitted_file':bad['files'].pop()
    if fault=='duplicate_case':bad['cases']=['one','one']
    if fault=='changed_code':bad['code_pins']['code']='changed'
    monkeypatch.setattr(runner,'DEST',dest);monkeypatch.setattr(runner,'build_request',lambda _:good)
    runner.source.put(path,bad)
    with pytest.raises(ValueError,match='scope changed'):runner.checked_request(path,runner.source.sha(path.read_bytes()))
    assert not (dest/'consumed.json').exists()


def test_decode_handles_short_bounded_stream_chunks():
    blob,row=fixture();count=counters()
    class Short(io.BytesIO):
        def read(self,n=-1):return super().read(min(7,n))
    array,header,report=core.decode_exact(Short(blob),row,count,limits(),lambda:None)
    assert count['decode_bytes']==len(blob) and report['gzip_eof_crc_verified'] and array[0,0,0]==127
