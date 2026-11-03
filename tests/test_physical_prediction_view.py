import json
import nibabel as nib
import numpy as np
import pytest
from scripts import prepare_physical_prediction_view as pack
from src.data.segmenter_native_windows_v1 import geometry


def fixture(tmp_path, monkeypatch):
    shape=(9,10,11);affine=np.array([[0,-3,0,27],[2,0,0,0],[0,0,-4,40],[0,0,0,1.]])
    ct=tmp_path/'ct.nii.gz';pred=tmp_path/'prediction.nii.gz'
    for path in (ct,pred):
        n=nib.Nifti1Image(np.zeros(shape,np.uint8),affine);n.header.set_xyzt_units('mm');nib.save(n,path)
    r=dict(version='four-case-exception-1',probability_equivalence='UNQUALIFIED',
        models={k:dict(sha256=h*64) for k,h in [('localizer','a'),('segmenter','b')]},
        cases=[dict(case_id=c,identity=dict(source_sha256={'ct':pack.sha(ct)}),
                    header=dict(ct=dict(shape=list(shape),affine=affine.tolist(),units='mm'))) for c in pack.CASES])
    request=tmp_path/'request.json';request.write_text(json.dumps(r));monkeypatch.setattr(pack,'REQUEST',pack.sha(request))
    parent=geometry(shape,affine)
    result=dict(status='COMPLETED',arm='autonomous',reference_inputs_used=False,optimizer_updates=0,
        case_id=pack.CASES[0],request_sha256=pack.REQUEST,artifacts={'prediction.nii.gz':pack.sha(pred)},
        source_shape=list(shape),source_affine=affine.tolist(),units='mm',
        evidence=dict(component='predicted-physical-region-v1',reference_inputs_used=False,localizer_policy='all_support',
            parent_geometry=parent,region_low=[2,1,3],region_high=[8,7,9],
            reconstruction=dict(gap_voxels=0,output_decision='native_center_probability_blend_then_argmax')))
    path=tmp_path/'result.json';path.write_text(json.dumps(result))
    return ct,pred,path,request,result


def test_preserves_producer_bytes_and_maps_permuted_flipped_roi(tmp_path,monkeypatch):
    ct,pred,result,request,_=fixture(tmp_path,monkeypatch)
    m=pack.prepare(ct,pred,result,request,tmp_path/'view')
    assert m['native_region']==[[1,2,2],[7,8,8]]
    assert (tmp_path/'view/result.json').read_bytes()==result.read_bytes()
    assert (tmp_path/'view/evidence.json').read_bytes()==request.read_bytes()
    assert m['probability_equivalence']=='UNQUALIFIED'
    assert m['schema_version']=='physical-prediction-view-v1'
    with pytest.raises(FileExistsError):pack.prepare(ct,pred,result,request,tmp_path/'view')


@pytest.mark.parametrize('fault',['case','arm','reference','request','prediction','shape','affine','region','orientation','gap','model'])
def test_rejects_mixed_or_invalid_records_before_publication(tmp_path,monkeypatch,fault):
    ct,pred,result,request,r=fixture(tmp_path,monkeypatch)
    if fault=='case':r['case_id']='another'
    if fault=='arm':r['arm']='provided_region'
    if fault=='reference':r['reference_inputs_used']=True
    if fault=='request':r['request_sha256']='0'*64
    if fault=='prediction':r['artifacts']['prediction.nii.gz']='0'*64
    if fault=='shape':r['source_shape']=[1,2,3]
    if fault=='affine':r['source_affine'][0][3]+=2
    if fault=='region':r['evidence']['region_low'][0]=-1
    if fault=='orientation':r['evidence']['parent_geometry']['forward'][0][0]=2
    if fault=='gap':r['evidence']['reconstruction']['gap_voxels']=1
    if fault=='model':
        q=json.loads(request.read_text());q['models']['segmenter']['sha256']='bad';request.write_text(json.dumps(q))
        monkeypatch.setattr(pack,'REQUEST',pack.sha(request));r['request_sha256']=pack.REQUEST
    result.write_text(json.dumps(r))
    with pytest.raises(ValueError):pack.prepare(ct,pred,result,request,tmp_path/'view')
    assert not (tmp_path/'view').exists()
