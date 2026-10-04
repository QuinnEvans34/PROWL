from copy import deepcopy
from io import BytesIO
import numpy as np
import pytest
from src.training import segmenter_native_scoring_v1 as c
from scripts.diagnostics import segmenter_content_pilot as p
from src.data import segmenter_content_v1 as binary

@pytest.fixture
def fixture():
 pan=np.zeros((4,4,4),np.uint8);pan[1:3,1:3,1:3]=1;les=np.zeros_like(pan);les[1,1,1]=les[3,3,3]=1
 pred=np.zeros_like(pan);pred[1,1,1]=pred[0,0,0]=2;pred[1,1,2]=pred[1,2,1]=1
 return pred,pan,les

def test_analytic_class_precedence_and_counts(fixture):
 r=c.score(*fixture,target_state='positive');assert r['confusion_matrix']==[[54,0,1],[5,2,0],[1,0,1]]
 assert r['metrics']['lesion']==dict(target_voxels=2,predicted_voxels=2,true_positive=1,dice=.5,recall=.5)
 assert r['metrics']['pancreas_parenchyma']['dice']==4/9 and r['metrics']['pancreas_parenchyma']['recall']==2/7
 assert r['metrics']['pancreas_lesion_union']['dice']==6/13 and r['outside_pancreas_voxels']==1
 assert len(r['components'])==2 and [v['native_voxels'] for v in r['components']]==[1,1]

def test_disconnected_tiny_boundary_outside_components():
 pan=np.ones((8,8,8),np.uint8);les=np.zeros_like(pan);les[0,0,0]=1;les[4,4,4]=1;les[7,7,7]=1;pan[7,7,7]=0;pred=np.zeros_like(pan);pred[4,4,4]=2
 r=c.score(pred,pan,les,target_state='positive');assert len(r['components'])==3
 assert [v['true_positive'] for v in r['components']]==[0,1,0] and [v['missed'] for v in r['components']]==[True,False,True]
 assert r['outside_pancreas_voxels']==1 and r['components'][0]['source_boundary_contact']

@pytest.mark.parametrize('value',[0,1,2])
def test_dense_empty_wrong_failures_scored(fixture,value):
 x,pan,les=fixture;x[:]=value;r=c.score(x,pan,les,target_state='positive')
 assert r['metrics']['lesion']['predicted_voxels']==(64 if value==2 else 0)
 assert r['metrics']['lesion']['true_positive']==(2 if value==2 else 0)
 assert sum(sum(row) for row in r['confusion_matrix'])==64

def test_predicted_fragmentation_above_old4096_limit():
 pan=np.zeros((48,48,48),np.uint8);pan[5:20,5:20,5:20]=1;les=np.zeros_like(pan);les[10,10,10]=1;pred=np.zeros_like(pan);pred[::2,::2,::2]=2
 r=c.score(pred,pan,les,target_state='positive');assert r['metrics']['lesion']['predicted_voxels']==24**3 and len(r['components'])==1

@pytest.mark.parametrize('state',['unknown_empty','positive',''])
def test_empty_not_fabricated_negative(state):
 a=np.zeros((4,4,4),np.uint8)
 with pytest.raises(ValueError):c.score(a,a,a,target_state=state)

def test_explicit_negative_foreground_metrics_undefined():
 a=np.zeros((4,4,4),np.uint8);r=c.score(a,a,a,target_state='verified_negative');assert r['metrics']['lesion']['dice'] is None and r['components']==[]

@pytest.mark.parametrize('fault',['grid','class','nan','pan_values','les_values'])
def test_bad_native_arrays(fixture,fault):
 a,p,l=fixture
 if fault=='grid':a=a[:3]
 if fault=='class':a[0,0,0]=3
 if fault=='nan':a=a.astype(float);a[0,0,0]=np.nan
 if fault=='pan_values':p[0,0,0]=2
 if fault=='les_values':l[0,0,0]=2
 with pytest.raises(ValueError):c.score(a,p,l,target_state='positive')

@pytest.mark.parametrize('fault',['negative','float','shape','bool'])
def test_bad_confusion(fault):
 m=[[0,0,0] for _ in range(3)]
 if fault=='negative':m[0][0]=-1
 if fault=='float':m[0][0]=1.
 if fault=='shape':m.pop()
 if fault=='bool':m[0][0]=True
 with pytest.raises(ValueError):c.from_confusion(m)

def test_role_macro_and_pooled_are_distinct(fixture):
 a=c.score(*fixture,target_state='positive');b=deepcopy(a);b['confusion_matrix']=[[54,0,1],[5,2,0],[1,0,100]];b['metrics']=c.from_confusion(b['confusion_matrix']);a['protected_role']=b['protected_role']='train'
 r=c.aggregates([a,b]);assert r['train']['cases']==2 and r['train']['macro']['lesion']['dice']!=r['train']['pooled']['lesion']['dice']

@pytest.mark.parametrize('fault',['shape','dtype','trailing','truncated','codes'])
def test_native_header_first(fault):
 a=np.zeros((4,4,4),np.uint8)
 if fault=='dtype':a=a.astype(np.float32)
 if fault=='codes':a[0,0,0]=4
 if fault=='shape':a=a[:3]
 b=BytesIO();np.save(b,a,allow_pickle=False);raw=b.getvalue()
 if fault=='trailing':raw+=b'x'
 if fault=='truncated':raw=raw[:-1]
 with pytest.raises(ValueError):c.decode_prediction(raw,[4,4,4])

@pytest.mark.parametrize('kind',['pancreas','lesion'])
def test_verified_scaled_original_decode(kind):
 raw,row=p.invented_file(kind,'boundary',(16,16,16));counts=dict(hash_bytes=0,decode_bytes=0,expanded_bytes=0);limits=dict(hash_bytes=len(raw),decode_bytes=len(raw),expanded_bytes=row['expanded_bytes'])
 binary.hash_exact(BytesIO(raw),row,counts,limits,lambda:None);stored,h,r=binary.decode_exact(BytesIO(raw),row,counts,limits,lambda:None);mask,dec=binary.target_content(stored,h)
 assert set(np.unique(mask))<= {0,1} and dec['foreground_voxels']>0 and counts==limits and r['gzip_eof_crc_verified']

@pytest.mark.parametrize('fault',['hash','budget','truncated'])
def test_original_decode_rejects_fault(fault):
 raw,row=p.invented_file('lesion','boundary',(16,16,16));limits=dict(hash_bytes=len(raw),decode_bytes=len(raw),expanded_bytes=row['expanded_bytes']);counts=dict(hash_bytes=0,decode_bytes=0,expanded_bytes=0)
 if fault=='hash':row['sha256']='0'*64
 if fault=='budget':limits['expanded_bytes']-=1
 if fault=='truncated':raw=raw[:-1]
 with pytest.raises((ValueError,binary.BudgetError)):binary.decode_exact(BytesIO(raw),row,counts,limits,lambda:None)

def test_corner_connected_reference_uses26():
 a=np.zeros((4,4,4),np.uint8);l=a.copy();l[1,1,1]=l[2,2,2]=1;r=c.score(l*2,a,l,target_state='positive')
 assert len(r['components'])==1 and r['components'][0]['native_voxels']==2 and r['components'][0]['true_positive']==2
