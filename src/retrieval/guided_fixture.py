"""Explicit synthetic adapter and append-only response store; no retrieval or generation."""
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

FIXTURE = Path(__file__).resolve().parents[2] / "configs/evidence/guided-fixture-v1.json"


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def request_fields(request):
    if not isinstance(request, dict) or set(request) != {"request_id", "question_id"}:
        raise ValueError("Only request_id and a guided question_id are accepted.")
    request_id = request["request_id"]
    if not isinstance(request_id, str) or str(UUID(request_id)) != request_id:
        raise ValueError("Invalid request ID.")
    fixture = json.loads(FIXTURE.read_text())
    question = next((q for q in fixture["questions"] if q["id"] == request["question_id"]), None)
    if question is None:
        raise ValueError("Unknown guided question.")
    return request_id, fixture, question


def build_response(request):
    request_id, fixture, question = request_fields(request)
    passages = {p["id"]: p for p in fixture["passages"]}
    citations = [dict(passages[pid], sha256=digest(passages[pid])) for pid in question["passage_ids"]]
    response = {
        "schema_version": "prowl-guided-fixture-response-v1",
        "response_id": request_id,
        "request": request,
        "question": question["label"],
        "state": question["state"],
        "message": question["message"],
        "claims": [{"id": f"claim-{i + 1}", "text": p["text"], "passage_id": p["id"]} for i, p in enumerate(citations)],
        "citations": citations,
        "limitations": [fixture["notice"], "No live search, generation, diagnostic assessment, or model evaluation was performed."],
        "provenance": {"adapter": "fixed-extractive-v1", "corpus": fixture["version"], "fixture_sha256": digest(fixture), "index": None, "model": None},
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    response["content_sha256"] = digest(response)
    return response


def verify_response(response):
    """Fail closed on stored corruption or unsupported claims, including recomputed hashes."""
    payload = dict(response)
    if payload.pop("content_sha256", None) != digest(payload):
        raise ValueError("Response integrity check failed.")
    expected = build_response(response["request"])
    for key in expected:
        if key not in {"content_sha256", "completed_at"} and response.get(key) != expected[key]:
            raise ValueError("Response does not match the fixed evidence policy.")
    if set(response) != set(expected):
        raise ValueError("Unexpected response fields.")
    return response


class ResponseStore:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def read(self, request_id):
        if not isinstance(request_id, str) or str(UUID(request_id)) != request_id:
            raise ValueError("Invalid response ID.")
        return verify_response(json.loads((self.directory / f"{request_id}.json").read_text()))

    def save(self, request):
        request_id, _, _ = request_fields(request)
        destination = self.directory / f"{request_id}.json"
        if destination.exists():
            existing = self.read(request_id)
            if existing["request"] != request:
                raise FileExistsError("Request ID already belongs to a different question.")
            return existing
        response = build_response(request)
        # Publish a complete file atomically without overwriting another request/retry.
        fd, temporary = tempfile.mkstemp(prefix=".response-", dir=self.directory)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(canonical(response))
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary, destination)
            except FileExistsError:
                return self.save(request)
            directory_fd = os.open(self.directory, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            os.unlink(temporary)
        return self.read(request_id)
