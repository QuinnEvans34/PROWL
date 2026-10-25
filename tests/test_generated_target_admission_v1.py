from copy import deepcopy
import numpy as np
import pytest
from test_distillation_integration_v1 import Provider
from src.data.segmenter_generated_target_admission_v1 import admit
from src.data.segmenter_teacher_cache_v1 import sha, TeacherTargetStore
from src.data.manifest_records import canonical


def inputs(tmp_path):
    p = Provider(); rows = {}
    for name in p.control['train']:
        path = tmp_path/(name+'.npz')
        np.savez_compressed(path, probability=np.zeros((16,)*3, np.uint16))
        rows[name] = dict(case_id=name, native_geometry=p.small['geometry'],
            source_ct_sha256='a'*64, payload_sha256=sha(path), bytes=path.stat().st_size,
            reconstruction=dict(method='RAS_world_linear_slabbed', native_voxels=4096,
                                covered_voxels=4096, out_of_field_voxels=0))
    request = dict(train=p.control['train'], teacher=dict(weights={'sha256':'a'*64},
                   config={}, labels={}), preprocessing_policy={})
    return p, request, dict(success=True, complete=True, members=rows), dict(success=True, workers_reaped=True, exit_code=0)


def test_full_manifest_is_accepted_by_optimizer_store(tmp_path):
    p, req, result, resources = inputs(tmp_path)
    manifest, common = admit(tmp_path, req, result, resources, p)
    path = tmp_path/'manifest.json'; path.write_bytes(canonical(manifest))
    TeacherTargetStore(tmp_path, sha(path), control=p.control, common_identity=common)


@pytest.mark.parametrize('fault', ['missing', 'protected', 'live', 'failure', 'grid', 'ct', 'coverage', 'payload'])
def test_invalid_generation_rejected(tmp_path, fault):
    p, req, result, resources = inputs(tmp_path)
    row = result['members']['A']
    if fault == 'missing': del result['members']['B']
    if fault == 'protected': result['members']['V'] = deepcopy(row)
    if fault == 'live': resources['workers_reaped'] = False
    if fault == 'failure': resources['success'] = False
    if fault == 'grid': row['native_geometry'] = {}
    if fault == 'ct': row['source_ct_sha256'] = 'b'*64
    if fault == 'coverage': row['reconstruction']['covered_voxels'] = 4095
    if fault == 'payload': (tmp_path/'A.npz').write_bytes(b'changed')
    with pytest.raises(ValueError): admit(tmp_path, req, result, resources, p)


def test_partial_qualification_cannot_be_used_as_full_training(tmp_path):
    p, req, result, resources = inputs(tmp_path)
    del result['members']['B']; result['complete'] = False
    manifest, common = admit(tmp_path, req, result, {}, p, qualification_only=True)
    path = tmp_path/'manifest.json'; path.write_bytes(canonical(manifest))
    assert manifest['complete'] is False
    with pytest.raises(ValueError, match='Incomplete'):
        TeacherTargetStore(tmp_path, sha(path), control=p.control, common_identity=common)
