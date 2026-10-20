import json
from pathlib import Path

import pytest

from src.retrieval import public_exposure as public


@pytest.mark.parametrize('mutation', ['ready','path','report','packet_bytes'])
def test_acceptance_cannot_bypass_review_or_admit_private_content(monkeypatch, mutation):
    root=Path(__file__).resolve().parents[2]
    original=public.public_bytes
    def altered(root, path, expected=None):
        raw=original(root,path,expected)
        if path.endswith('development-v6-delta-acceptance-v1.json'):
            receipt=json.loads(raw)
            if mutation=='ready':receipt['ready_for_private_authoring']=True
            if mutation=='path':receipt['packet']['path']='elsewhere.md'
            if mutation=='report':receipt['report']['event_count']=0
            if mutation=='packet_bytes':receipt['packet']['sha256']='0'*64
            return json.dumps(receipt).encode()
        return raw
    monkeypatch.setattr(public,'public_bytes',altered)
    with pytest.raises(ValueError): public.accepted_public_preflight(root)


def test_actual_acceptance_recognized_without_private_admission():
    result=public.accepted_public_preflight(Path(__file__).resolve().parents[2])
    assert result['development_review_attested_complete']
    assert not result['ready_for_private_authoring']
    assert not result['ready_for_tuning']
    assert not result['private_content_read']
