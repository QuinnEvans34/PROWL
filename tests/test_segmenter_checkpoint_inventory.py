from copy import deepcopy
import pytest
from scripts.diagnostics import segmenter_checkpoint_inventory as c

@pytest.mark.parametrize('name',['outputs/checkpoints/last.pt','outputs/prowl/rehearsal/state.pt','pretrained_weights/supervised_suprem_segresnet_2100.pth','MedFormerPanTS/pants_pancreas_release/fold_0_latest.pth'])
def test_known_checkpoint_candidates_denied_for_import(name):assert c.category(name)!='excluded_tensor_cache_payload'
@pytest.mark.parametrize('name',['../bad.pt','/bad.pt','outputs/checkpoints/a.nii.gz','unknown/state.pt'])
def test_inventory_scope_refuses_unknown_or_array(name):
 with pytest.raises(ValueError):c.category(name)
@pytest.mark.parametrize('fault',['cache','duplicate','bytes','stage','limit'])
def test_inventory_request_refusal(fault):
 r=dict(decision='D-326',stage='checkpoint_byte_inventory',limits=c.LIMITS.copy(),files=[dict(uri='outputs/checkpoints/a.pt',category='prior_project_checkpoint_import_denied',observation={'bytes':2})],excluded_cache_count=0,code_sha256='0'*64)
 if fault=='cache':r['files'][0].update(uri='outputs/cache/x.pt',category='excluded_tensor_cache_payload')
 if fault=='duplicate':r['files']*=2
 if fault=='bytes':r['files'][0]['observation']['bytes']=c.LIMITS['hash_bytes']+1
 if fault=='stage':r['stage']='training'
 if fault=='limit':r['limits']['max_files']+=1
 with pytest.raises(ValueError):c.validate_request(r)
def test_closed_inventory_request():
 r=dict(decision='D-326',stage='checkpoint_byte_inventory',limits=c.LIMITS.copy(),files=[dict(uri='outputs/checkpoints/a.pt',category='prior_project_checkpoint_import_denied',observation={'bytes':2})],excluded_cache_count=0,code_sha256='0'*64);c.validate_request(r)
