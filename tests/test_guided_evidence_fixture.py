import json
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest

from src.retrieval.guided_fixture import FIXTURE, ResponseStore, build_response, canonical, digest, verify_response


def request(question="workflow"):
    return {"request_id": str(uuid4()), "question_id": question}


@pytest.mark.parametrize("question", json.loads(FIXTURE.read_text())["questions"])
def test_all_guided_paths_have_only_exact_supported_claims(question):
    response = verify_response(build_response(request(question["id"])))
    assert response["state"] == question["state"]
    if response["state"] == "answered":
        assert response["claims"]
        assert response["claims"][0]["text"] == response["citations"][0]["text"]
    else:
        assert response["claims"] == response["citations"] == []
    assert response["provenance"]["model"] is None


def test_concurrent_retry_one_artifact_and_cold_reload(tmp_path):
    store = ResponseStore(tmp_path)
    req = request()
    with ThreadPoolExecutor(max_workers=4) as executor:
        responses = list(executor.map(store.save, [req] * 8))
    assert all(item == responses[0] for item in responses)
    assert len(list(tmp_path.glob("*.json"))) == 1
    assert ResponseStore(tmp_path).read(req["request_id"]) == responses[0]
    assert not list(tmp_path.glob(".response-*"))
    with pytest.raises(FileExistsError):
        store.save(dict(req, question_id="measurement"))
    store.save(request())
    assert len(list(tmp_path.glob("*.json"))) == 2


@pytest.mark.parametrize("bad", [
    {"request_id": "../escape", "question_id": "workflow"},
    {"request_id": str(uuid4()), "question_id": "invented"},
    dict(request(), patient_id="private"),
    dict(request(), question="Diagnose me"),
    [], None,
])
def test_rejects_unknown_questions_identifiers_and_extra_context(tmp_path, bad):
    with pytest.raises((ValueError, TypeError)):
        ResponseStore(tmp_path).save(bad)
    assert list(tmp_path.iterdir()) == []


def test_tampering_rejected_even_with_recomputed_hash(tmp_path):
    store = ResponseStore(tmp_path)
    response = store.save(request())
    response["claims"][0]["text"] = "Unsupported assertion"
    response.pop("content_sha256")
    response["content_sha256"] = digest(response)
    (tmp_path / f'{response["response_id"]}.json').write_bytes(canonical(response))
    with pytest.raises(ValueError, match="fixed evidence policy"):
        store.read(response["response_id"])


def test_failed_write_never_returns_saved_response(tmp_path, monkeypatch):
    def fail(*args):
        raise OSError("disk full")
    monkeypatch.setattr("src.retrieval.guided_fixture.os.link", fail)
    with pytest.raises(OSError):
        ResponseStore(tmp_path).save(request())
    assert list(tmp_path.iterdir()) == []
