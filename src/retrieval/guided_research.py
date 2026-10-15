"""Saved retrieval snapshots for fixed research questions; no generated claims."""
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from uuid import UUID
from .direct_ingestion import digest, validate_row, write_once

QUESTIONS = json.loads((Path(__file__).resolve().parents[2] / 'configs/evidence/research-questions-v1.json').read_text())


def request_fields(request):
    if not isinstance(request, dict) or set(request) != {'request_id', 'question_id'}:
        raise ValueError('Only guided question IDs accepted')
    identifier = request['request_id']
    if not isinstance(identifier, str) or str(UUID(identifier)) != identifier:
        raise ValueError('Invalid request ID')
    question = next((q for q in QUESTIONS if q['id'] == request['question_id']), None)
    if question is None:
        raise ValueError('Unknown question')
    return identifier, question


class ResearchStore:
    def __init__(self, directory, retrieve, collection, encoder_id, generate=None):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.retrieve, self.collection, self.encoder_id = retrieve, collection, encoder_id
        self.generate = generate
        self.schema = "prowl-research-answer-v1" if generate else "prowl-research-search-v1"
        self.lock = Lock()

    def read(self, identifier):
        if not isinstance(identifier, str) or str(UUID(identifier)) != identifier:
            raise ValueError('Invalid response ID')
        result = json.loads((self.directory / f'{identifier}.json').read_text())
        payload = dict(result)
        if payload.pop('content_sha256', None) != digest(payload):
            raise ValueError('Saved response integrity failed')
        rid, question = request_fields(result['request'])
        if rid != identifier or result['question'] != question['label'] or result['schema_version'] != self.schema:
            raise ValueError('Saved request mismatch')
        for item in result['passages']:
            validate_row(item['record'])
        if self.generate:
            from .grounded_answer import validate_answer
            validate_answer(result['generation']['answer'], result['passages'])
        return result

    def save(self, request):
        identifier, question = request_fields(request)
        # Serialize encoder access and retries; reject overload rather than queue indefinitely.
        if not self.lock.acquire(blocking=False):
            raise OSError('Research search is busy')
        try:
            if (self.directory / f'{identifier}.json').exists():
                result = self.read(identifier)
                if result['request'] != request:
                    raise FileExistsError('Request ID conflict')
                return result
            passages = self.retrieve(question['label'])
            for item in passages:
                validate_row(item['record'])
            result = dict(schema_version=self.schema, response_id=identifier,
                request=request, question=question['label'], passages=passages,
                state='retrieved' if passages else 'no_results',
                provenance=dict(collection=self.collection, encoder_id=self.encoder_id, generation_model=None),
                completed_at=datetime.now(timezone.utc).isoformat())
            if self.generate:
                from .grounded_answer import validate_answer
                result['generation'] = self.generate(question['label'], passages)
                # Reject invalid model output before publishing an immutable response.
                validate_answer(result['generation']['answer'], passages)
                result['provenance']['generation_model'] = result['generation']['provenance']['model']
            result['content_sha256'] = digest(result)
            write_once(self.directory / f'{identifier}.json', result)
            return self.read(identifier)
        finally:
            self.lock.release()
