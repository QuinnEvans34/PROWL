"""Synthetic provenance check; does not admit the active teacher outputs."""
import json
import pytest
from test_teacher_target_publication_v1 import fixture
from src.data.manifest_records import canonical,digest
from src.data.segmenter_teacher_cache_v1 import sha
from src.data.teacher_target_publication_v1 import publish


def test_affine_extension_and_continuation_are_bound_to_manifest(tmp_path):
    root,provider,pins=fixture(tmp_path)
    path=root/'request.json';request=json.loads(path.read_text())
    request.update(preprocessing_extension='invented-qualified-affine-policy',continuation={'prior_stage_seconds_charged':2241,'remaining_seconds':171727})
    path.write_bytes(canonical(request));pins['request_sha256']=sha(path)
    output=tmp_path/'admitted';publish(root,output,provider,**pins)
    manifest=json.loads((output/'manifest.json').read_text());receipt=json.loads((output/'admission.json').read_text())
    assert manifest['producer_request_sha256']==digest(canonical(request))
    assert receipt['source_record_hashes']['request.json']==sha(path)
    request['preprocessing_extension']='changed'
    path.write_bytes(canonical(request))
    with pytest.raises(ValueError,match='record changed'):
        publish(root,tmp_path/'changed',provider,**pins)
    assert not (tmp_path/'changed').exists()
