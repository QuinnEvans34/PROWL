from copy import deepcopy
import pytest
from segmenter_short_fixtures import request,approval
from src.data.manifest_records import canonical,digest
from src.data import segmenter_final_targets_v1 as t
from src.training import segmenter_short_executor_v1 as e
@pytest.fixture(scope='module')
def real():return request(real=True)
def test_exact_original_scope_valid(real):e.validate_request(real[0])
@pytest.mark.parametrize('fault',['ct','missing','duplicate','hash','role','bytes','grid','budget','stage','capability','image','component'])
def test_fresh_final_scope_rejects_invalid_uses(real,fault):
 r,p=deepcopy(real);scope=r['targets']
 if fault=='ct':scope['files'][0]['kind']='ct'
 if fault=='missing':scope['files'].pop()
 if fault=='duplicate':scope['files'][1]=scope['files'][0]
 if fault=='hash':scope['files'][0]['sha256']='0'*64
 if fault=='role':scope['cases'][0]['protected_role']='validation'
 if fault=='bytes':scope['files'][0]['compressed_bytes']+=1
 if fault=='grid':scope['cases'][0]['transform']['source_shape'][0]+=1
 if fault=='budget':scope['limits']['decode_bytes']+=1
 if fault=='stage':scope['stage']='old_original_native_scoring'
 if fault=='capability':scope['capability']['operations'].append('CT')
 if fault=='image':scope['cases'][0]['image_sha256']='0'*64
 if fault=='component':scope['cases'][0]['reference_components'].pop()
 with pytest.raises((ValueError,KeyError)):e.validate_request(r)
def test_original_reader_denies_without_launch_grant(real,monkeypatch):
 r,p=real;monkeypatch.setattr(t.source,'source_stream',lambda *a:pytest.fail('Original payload read'))
 with pytest.raises(ValueError):t.RealTargets(p,r,None)
def test_original_reader_denies_before_terminal_and_repeated_case(real,monkeypatch):
 from types import SimpleNamespace
 r,p=real;raw=approval(r);g=e.authorize(r,raw,trusted_approval_sha256=digest(raw));reader=t.RealTargets(p,r,g);sid=r['targets']['cases'][0]['study_id'];monkeypatch.setattr(t.source,'mount_guard',lambda *a:pytest.fail('Premature source mount'))
 with pytest.raises(ValueError):reader.read(SimpleNamespace(identity=r['identity'],step=0,dirty=False),sid)
 with pytest.raises(ValueError):reader.read(SimpleNamespace(identity=r['identity'],step=48,dirty=True),sid)
 reader.used.add(sid)
 with pytest.raises(ValueError):reader.read(SimpleNamespace(identity=r['identity'],step=48,dirty=False),sid)
def test_whole_pair_budget_reserved_before_any_stream(real,monkeypatch):
 from src.training.segmenter_native_scoring_v1 import read_targets
 from src.data.segmenter_content_v1 import BudgetError
 r,p=real;c=r['targets']['cases'][0];rows=[v for v in r['targets']['files'] if v['study_id']==c['study_id']];monkeypatch.setattr(t.source,'source_stream',lambda *a:pytest.fail('Partial pair payload read'))
 with pytest.raises(BudgetError):read_targets(None,c['descriptor'],rows,dict(hash_bytes=0,decode_bytes=0,expanded_bytes=0),dict(hash_bytes=rows[0]['compressed_bytes'],decode_bytes=10**9,expanded_bytes=10**9))
def test_invented_full_gzip_and_binary_pipeline():
 import io
 import numpy as np
 from src.data import segmenter_content_v1 as content
 pan,les=t.invented_arrays();blob,row=t.invented_blob(les,'lesion');counts=dict(hash_bytes=0,decode_bytes=0,expanded_bytes=0);limits=dict(hash_bytes=len(blob),decode_bytes=len(blob),expanded_bytes=row['expanded_bytes']);content.hash_exact(io.BytesIO(blob),row,counts,limits,lambda:None);stored,h,read=content.decode_exact(io.BytesIO(blob),row,counts,limits,lambda:None);mask,report=content.target_content(stored,h);assert np.array_equal(mask,les) and report['foreground_voxels']==28 and counts==limits and read['gzip_eof_crc_verified']
