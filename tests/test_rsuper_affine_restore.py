import json
import pytest
from scripts.diagnostics import resume_rsuper_affine_restore_v1 as m
from scripts.diagnostics import build_rsuper_affine_checked_v1 as qualified

def test_preserved_ancestor_and_partial_identity(tmp_path,monkeypatch):
    previous=tmp_path/'failed';source=tmp_path/'source';source.mkdir()
    r=dict(teacher='t',train=['a','b'],preprocessing_policy='p',preprocessing_extension='e')
    (source/'request.json').write_text(json.dumps(r))
    r['pins']={str(source/'request.json'):m.sha(source/'request.json')}
    row=dict(payload_sha256='h',native_geometry='g',source_ct_sha256='c')
    monkeypatch.setattr(m,'completed_members',lambda root,req:{'a':row,'b':row} if root==source else {'a':row})
    assert set(m.preserved_members(previous,source,r))=={'a','b'}
    monkeypatch.setattr(m,'completed_members',lambda root,req:{'a':row} if root==source else {'b':row})
    with pytest.raises(ValueError,match='divergent'):m.preserved_members(previous,source,r)
    r['teacher']='changed'
    with pytest.raises(ValueError,match='recipe'):m.preserved_members(previous,source,r)
    r['pins']={}
    with pytest.raises(ValueError,match='bound'):m.preserved_members(previous,source,r)
    assert m.frozen is qualified
