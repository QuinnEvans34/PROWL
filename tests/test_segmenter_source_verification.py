"""Invented files only: source boundaries and bounded reads; no licensed data."""
from copy import deepcopy
import gzip
import io
import json
import os
import resource
import sys
from pathlib import Path
import pytest
import nibabel as nib
import numpy as np
from scripts.diagnostics import segmenter_source_verification as v


def row(uri='a/label.nii.gz', size=None):
    return dict(uri=uri, expected_bytes=size)


def test_stat_missing_nonregular_changed_and_regular_without_open(tmp_path, monkeypatch):
    (tmp_path/'a').mkdir(); p=tmp_path/'a/label.nii.gz';p.write_bytes(b'abc')
    with v.directory(tmp_path) as fd:
        monkeypatch.setattr(Path,'read_bytes',lambda *_:pytest.fail('stat job opened payload'))
        assert v.observe(fd,row(size=3))['state']=='observed'
        assert v.observe(fd,row(size=4))['reasons']==['retained_size_changed']
        assert v.observe(fd,row('a/missing.nii.gz'))['reasons']==['missing_exact_path']
        assert v.observe(fd,row('a'))['reasons']==['not_regular_file']


@pytest.mark.parametrize('kind',['leaf','parent','root'])
def test_symlink_paths_never_followed(tmp_path,kind):
    target=tmp_path/'real';target.mkdir();(target/'label.nii.gz').write_bytes(b'payload')
    if kind=='root':
        link=tmp_path/'root';link.symlink_to(target)
        with pytest.raises(OSError):
            with v.directory(link):pass
    else:
        (tmp_path/'a').mkdir()
        if kind=='leaf':(tmp_path/'a/label.nii.gz').symlink_to(target/'label.nii.gz')
        else:
            (tmp_path/'a').rmdir();(tmp_path/'a').symlink_to(target)
        with v.directory(tmp_path) as fd:
            assert v.observe(fd,row())['state']=='held'


@pytest.mark.parametrize('uri',['../a','/a','a/../b','a//b','./a',''])
def test_unsafe_relative_names_rejected(uri):
    with pytest.raises(ValueError):v.member_name(uri)


def test_observation_changed_or_replaced_refused_and_read_mutation_detected(tmp_path):
    p=tmp_path/'f';p.write_bytes(b'original')
    with v.directory(tmp_path) as fd:
        r=dict(uri='f',observation=v.observation(p.stat()))
        with v.source_stream(fd,r) as stream:assert stream.read()==b'original'
        with pytest.raises(ValueError,match='during read'):
            with v.source_stream(fd,r):p.write_bytes(b'changed!')
        with pytest.raises(ValueError,match='since M1'):
            with v.source_stream(fd,r):pass
        p.unlink();p.write_bytes(b'original')
        with pytest.raises(ValueError):
            with v.source_stream(fd,r):pass


def test_hash_reads_exact_bytes_and_checks_every_chunk():
    data=b'x'*(2*1024**2+3); count=dict(hash_bytes=0); calls=[]
    assert v.hash_stream(io.BytesIO(data),len(data),count,lambda:calls.append(1))==v.sha(data)
    assert count['hash_bytes']==len(data) and len(calls)==3
    with pytest.raises(ValueError,match='Truncated'):v.hash_stream(io.BytesIO(b'a'),3,dict(hash_bytes=0),lambda:None)


def header_blob(shape=(4,5,6),dtype=np.uint8,mutate=None):
    h=nib.Nifti1Header();h.set_data_shape(shape);h.set_data_dtype(dtype);h.set_sform(np.diag([1,2,3,1]),code=1)
    h['vox_offset']=352;h.set_xyzt_units('mm');h['scl_slope']=1;h['scl_inter']=0
    if mutate:mutate(h)
    # Header plus a fake large payload: reader must never decode the array.
    return gzip.compress(h.binaryblock+b'\x00'*4+b'\xff'*100_000,mtime=0)


def parse(blob):
    c=dict(header_bytes=0);return v.lesion_header(io.BytesIO(blob),c),c


def test_header_only_payload_and_scaling_sizes_are_measured():
    h,c=parse(header_blob(dtype=np.int16))
    assert h['payload_bytes']==4*5*6*2 and h['projected_nifti_bytes']==352+240
    assert h['shape']==[4,5,6] and h['units'][0]=='mm' and h['effective_slope']==1
    assert c['header_bytes']<=65536 and len(h['decompressed_header_sha256'])==64


def test_scaled_binary_header_does_not_claim_binary_or_nonempty():
    h,_=parse(header_blob(mutate=lambda h:h.__setitem__('scl_slope',1/255)))
    assert h['effective_slope']==pytest.approx(1/255)
    assert 'foreground_count' not in h and 'negative' not in h


@pytest.mark.parametrize('fault',['four_dimensional','offset','magic','complex','oversized','bad_spacing','singular_affine'])
def test_unsupported_headers_held(fault):
    def mutate(h):
        if fault=='four_dimensional':h.set_data_shape((2,2,2,2))
        if fault=='offset':h['vox_offset']=351
        if fault=='magic':h['magic']=b'ni1\x00'
        if fault=='complex':h.set_data_dtype(np.complex64)
        if fault=='oversized':h.set_data_shape((500,500,500))
        if fault=='bad_spacing':h['pixdim'][1]=0
        if fault=='singular_affine':h.set_sform(np.zeros((4,4)),code=1)
    with pytest.raises((ValueError,nib.spatialimages.HeaderDataError)):parse(header_blob(mutate=mutate))


def test_truncated_and_header_cap_refused():
    with pytest.raises(__import__('zlib').error):parse(b'not gzip')
    with pytest.raises(ValueError,match='Truncated'):parse(gzip.compress(b'a'*100))
    # Extra gzip field consumes the cap before any NIfTI bytes can be returned.
    blob=bytearray(header_blob());blob[3]=4
    blob=bytes(blob[:10])+b'\xff\xff'+b'x'*65535+bytes(blob[10:])
    with pytest.raises(ValueError,match='header cap'):parse(blob)


def test_geometry_requires_shape_and_absolute_affine_match_with_supported_units():
    h,_=parse(header_blob());g=dict(shape_xyz=h['shape'],affine_ras=np.array(h['affine']).ravel().tolist())
    assert v.grid_reasons(h,g)==[]
    changed=deepcopy(h);changed['affine'][0][3]=.0001
    assert v.grid_reasons(changed,g)==['lesion_ct_grid_mismatch']
    changed=deepcopy(h);changed['units'][0]='unknown';assert v.grid_reasons(changed,g)==[]
    changed['units'][0]='meter';assert v.grid_reasons(changed,g)==['unsupported_lesion_spatial_units']


def test_receipt_changes_and_extra_members_refused(tmp_path):
    v.put(tmp_path/'result.json',dict(stage='metadata'))
    raw=(tmp_path/'result.json').read_bytes()
    v.put(tmp_path/'receipt.json',dict(state='complete',files={'result.json':dict(bytes=len(raw),sha256=v.sha(raw))}))
    pin=v.sha((tmp_path/'receipt.json').read_bytes());assert v.verify_package(tmp_path,pin)==dict(stage='metadata')
    (tmp_path/'extra').write_text('extra')
    with pytest.raises(ValueError,match='membership'):v.verify_package(tmp_path,pin)
    (tmp_path/'extra').unlink();(tmp_path/'result.json').write_text('{}')
    with pytest.raises(ValueError,match='member changed'):v.verify_package(tmp_path,pin)


def test_put_exclusive_consumption_and_no_overwrite(tmp_path):
    v.put(tmp_path/'consumed.json',{'state':'consumed'})
    with pytest.raises(FileExistsError):v.put(tmp_path/'consumed.json',{'state':'retry'})


def test_changed_request_refused_before_source_calls(tmp_path,monkeypatch):
    p=tmp_path/'request.json';v.put(p,dict(stage='metadata',unexpected='expanded scope'))
    monkeypatch.setattr(v,'build_request',lambda stage:dict(stage=stage))
    monkeypatch.setattr(v,'mount_guard',lambda *_:pytest.fail('source accessed'))
    with pytest.raises(ValueError,match='scope'):v.execute(p,v.sha(p.read_bytes()))
    with pytest.raises(ValueError,match='Request changed'):v.execute(p,'0'*64)


@pytest.mark.parametrize('fault',['none','changed_hash','changed_stat','bad_header'])
def test_identity_transaction_retains_all_inputs_and_propagates_companion_holds(tmp_path,monkeypatch,fault):
    source=tmp_path/'source';source.mkdir();out=tmp_path/'out';out.mkdir()
    h,_=parse(header_blob());g=dict(shape_xyz=h['shape'],affine_ras=np.array(h['affine']).ravel().tolist())
    rows=[]
    for kind in ['ct','pancreas','lesion']:
        raw=header_blob() if kind=='lesion' else b'companion bytes'
        if fault=='bad_header' and kind=='lesion':raw=b'bad header'
        p=source/(kind+'.nii.gz');p.write_bytes(raw)
        rows.append(dict(uri=p.name,kind=kind,study_id='invented',expected_sha256=v.sha(raw) if kind!='lesion' else None,
                         retained_lesion_sha256=None,observation=v.observation(p.stat()),retained_ct_geometry=g))
    if fault=='changed_hash':rows[0]['expected_sha256']='0'*64
    if fault=='changed_stat':rows[0]['observation']['mtime_ns']+=1
    request=dict(stage='identity',output=str(out),capability=dict(source_root=str(source)),files=rows,
                 budget=dict(seconds=10,rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)+1024**3,output_bytes=4*1024**2,
                             hash_bytes=sum(r['observation']['bytes'] for r in rows),header_bytes=65536))
    monkeypatch.setattr(v,'build_request',lambda *_:request)
    monkeypatch.setattr(v,'mount_guard',lambda _:dict(root_device=source.stat().st_dev,root_inode=source.stat().st_ino))
    v.put(out/'request.json',request);pin=v.sha((out/'request.json').read_bytes())
    v.execute(out/'request.json',pin)
    result=v.verify_package(out,v.sha((out/'receipt.json').read_bytes()))
    assert len(result['files'])==3 and result['arrays_read']==result['model_updates']==result['real_qualifications']==0
    assert result['files'][2]['state']==('verified' if fault=='none' else 'held')
    assert result['hash_bytes']<=request['budget']['hash_bytes']
    with pytest.raises(FileExistsError):v.execute(out/'request.json',pin)


@pytest.mark.parametrize('fault',['rss','hash_bytes','output_bytes'])
def test_resource_limits_leave_consumed_failure_without_completion(tmp_path,monkeypatch,fault):
    source=tmp_path/'source';source.mkdir();out=tmp_path/'out';out.mkdir()
    p=source/'ct.nii.gz';p.write_bytes(b'abc')
    r=dict(uri=p.name,kind='ct',study_id='invented',expected_sha256=v.sha(b'abc'),retained_lesion_sha256=None,observation=v.observation(p.stat()))
    request=dict(stage='identity',output=str(out),capability=dict(source_root=str(source)),files=[r],
                 budget=dict(seconds=10,rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)+1024**3,
                             hash_bytes=3,header_bytes=0,output_bytes=100000))
    if fault=='rss':request['budget']['rss_bytes']=0
    if fault=='hash_bytes':request['budget']['hash_bytes']=0
    if fault=='output_bytes':request['budget']['output_bytes']=1
    monkeypatch.setattr(v,'build_request',lambda *_:request)
    monkeypatch.setattr(v,'mount_guard',lambda _:dict(root_device=source.stat().st_dev,root_inode=source.stat().st_ino))
    v.put(out/'request.json',request)
    with pytest.raises(ValueError):v.execute(out/'request.json',v.sha((out/'request.json').read_bytes()))
    assert (out/'consumed.json').is_file() and (out/'failure.json').is_file() and not (out/'receipt.json').exists()
