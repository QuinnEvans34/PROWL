from contextlib import nullcontext
import numpy as np
import pytest
import torch
from src.data.verifier_candidate_inputs_v1 import CandidateInputs, partition_roles
from src.data.segmenter_native_windows_v1 import geometry
from src.training.verifier_candidate_export_v1 import hard_codes,native_embed,predict
from src.training.segmenter_physical_windows_session_v1 import predict_native
from src.training.candidate_verifier_v1 import candidates,retain_candidates

def partition():
    return dict(roles=dict(generator_train=['g'],verifier_fit=['f'],verifier_tune=['t'],verifier_calibration=['c']),development=['d'])

def test_roles():
    p=CandidateInputs.__new__(CandidateInputs);p.roles=partition_roles(partition())
    for n,r in p.roles.items():p.check(n,r)
    for n,r in [('g','verifier_fit'),('d','verifier_fit'),('t','verifier_fit'),('f','optimizer')]:
        with pytest.raises(ValueError):p.check(n,r)
    for r,n in [('verifier_tune','t'),('verifier_calibration','c')]:
        with pytest.raises(ValueError):p.check(n,r,labels=True)
    p.check('f','verifier_fit',labels=True)

def test_overlap_refused():
    p=partition();p['roles']['verifier_fit']=['g']
    with pytest.raises(ValueError):partition_roles(p)

def test_ties():
    p=np.full((3,2,3,4),.25,np.float32)
    assert not hard_codes(p).any()
    p[1:]=.4
    assert (hard_codes(p)==1).all()
    p[2]=.5
    assert (hard_codes(p)==2).all()

@pytest.mark.parametrize('value',[np.nan,-.1,1.1])
def test_invalid_probabilities(value):
    p=np.zeros((3,1,1,1),np.float32);p[0]=value
    with pytest.raises(ValueError):hard_codes(p)

def test_embedding_orientation():
    affine=np.diag([-1.,1.,2.,1.]);g=geometry((5,6,7),affine)
    case=dict(parent_geometry=g,region_low=[1,2,3],region_high=[3,4,5])
    a=native_embed(np.ones((2,2,2),np.uint8),case)
    assert a.shape==(5,6,7) and a.sum()==8
    assert (a[2:4,2:4,3:5]==1).all()
    with pytest.raises(ValueError):native_embed(np.ones((3,2,2)),case)

def test_baseline_components_and_empty():
    for mask in [np.zeros((5,5,5),bool),np.eye(5,dtype=bool)[:,:,None].repeat(5,2)]:
        labels,parts=candidates(mask)
        assert np.array_equal(retain_candidates(labels,{p['component_id']:0 for p in parts},0),mask)

def test_export_matches_original_cpu():
    class Model(torch.nn.Module):
        def forward(self,x):return torch.cat((x,1-x,x*.5),dim=1)
    class Session:
        model=Model();device='cpu'
        def _clean(self):pass
        def rng_scope(self):return nullcontext()
    g=geometry((12,15,17),np.eye(4));image=np.random.default_rng(42).random((12,15,17),dtype=np.float32)
    expected,info=predict_native(Session(),image,g)
    actual,prob,got=predict(Session(),image,g)
    assert np.array_equal(actual,expected) and got==info and prob.shape==image.shape
    assert got['gap_voxels']==0

def test_three_role_provenance():
    from src.training.verifier_candidate_provenance_v1 import validate_records
    records=[dict(case_id=n,role=r,checkpoint_sha256='a'*64,generator_receipt_sha256='b'*64,
        prediction_sha256='c'*64,ct_sha256='d'*64,pancreas_sha256='e'*64,gap_voxels=0,candidate_count=0)
        for n,r in partition_roles(partition()).items()]
    kwargs=dict(checkpoint_sha256='a'*64,receipt_sha256='b'*64,actual_generator_ids=['g'],required_ids=['f','t','c'])
    assert validate_records(records,partition(),**kwargs)
    with pytest.raises(ValueError):validate_records(records[:-1],partition(),**kwargs)
    with pytest.raises(ValueError):validate_records(records+records[:1],partition(),**kwargs)
    kwargs['actual_generator_ids']=['g','c']
    with pytest.raises(ValueError):validate_records(records,partition(),**kwargs)

def test_real_loader_never_reads_lesion(tmp_path):
    import nibabel as nib
    from src.training.experiment_config import sha256
    shape=(20,22,24);affine=np.diag([1.,1.,2.,1.])
    image=np.arange(np.prod(shape),dtype=np.float32).reshape(shape)%400-120
    pancreas=np.zeros(shape,np.uint8);pancreas[6:12,7:14,8:16]=1
    paths={}
    for k,a in [('ct',image),('pancreas',pancreas)]:
        paths[k]=tmp_path/(k+'.nii.gz');nib.save(nib.Nifti1Image(a,affine),paths[k])
    p=CandidateInputs.__new__(CandidateInputs);p.roles={'f':'verifier_fit'}
    p.rows={'f':{k+'_path':str(v) for k,v in paths.items()}}
    p.rows['f']['lesion_path']=str(tmp_path/'does-not-exist.nii.gz')
    p.observations={'f':{}}
    for k,path in paths.items():
        s=path.stat();p.observations['f'][k]=dict(bytes=s.st_size,modified_ns=s.st_mtime_ns,inode=s.st_ino,device=s.st_dev)
    meta=dict(transform=dict(source_shape=shape,source_affine=affine.tolist()),source_sha256={k:sha256(v) for k,v in paths.items()})
    p.metadata=lambda n,r:meta
    case=p.load('f',role='verifier_fit')
    assert case['image'].dtype==np.float32 and case['image'].min()>=0 and case['image'].max()<=1
    assert 'target' not in case and 'lesion' not in case['source_sha256']
    assert case['region_low']==[0,0,0] and case['region_high']==list(shape)

def test_protected_role_refused_before_file_access():
    p=CandidateInputs.__new__(CandidateInputs);p.roles={'f':'verifier_fit'}
    with pytest.raises(ValueError):p.load('d',role='verifier_fit')

def test_missing_tiles_refused():
    from src.data.segmenter_physical_windows_v1 import PhysicalReconstructor,physical_geometry
    r=PhysicalReconstructor(physical_geometry(geometry((10,10,10),np.eye(4))))
    with pytest.raises(ValueError):r.finish([(0,0,0)])
