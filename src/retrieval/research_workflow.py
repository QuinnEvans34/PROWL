"""Local research workflow slice; immutable attempts, explicit recovery, no automatic retry.

This adapter does not implement the full imaging DAG or select an orchestration framework.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
from pathlib import Path
from uuid import UUID

from .direct_ingestion import digest, validate_row, write_once
from .guided_research import ResearchStore, request_fields
from . import grounded_answer

STAGES = ('retrieve', 'select', 'validate', 'save')
SCHEMA = 'prowl-research-workflow-v1'


def identifier(value):
    if not isinstance(value, str) or str(UUID(value)) != value:
        raise ValueError('Invalid workflow ID')
    return value


def checked(path):
    value = json.loads(path.read_text())
    payload = dict(value)
    if payload.pop('content_sha256', None) != digest(payload):
        raise ValueError('Workflow artifact integrity failed')
    return value


def publish(path, payload):
    value = dict(payload, content_sha256=digest(payload))
    write_once(path, value)
    return value


@contextmanager
def exclusive(path):
    # OS-owned locks release on process death; never delete/reassign stale lock files.
    with path.open('a+b') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise OSError('Research workflow busy') from exc
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def active(path):
    try:
        with exclusive(path):
            return False
    except OSError:
        return True


class ResearchWorkflow:
    def __init__(self, directory, retrieve, collection, encoder_id, retrieval_identity,
                 generate=grounded_answer.generate_answer, generation_identity=None):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.retrieve, self.generate = retrieve, generate
        self.collection, self.encoder_id = collection, encoder_id
        # Explicit producer identities prevent reuse across changed corpus/query/model code.
        self.binding = dict(collection=collection, encoder_id=encoder_id,
            retrieval_identity=retrieval_identity, generation_identity=generation_identity or dict(
                model=grounded_answer.MODEL, model_sha256=grounded_answer.MODEL_SHA,
                policy=grounded_answer.POLICY, prompt_sha256=digest(grounded_answer.SYSTEM)),
            code_sha256={p: hashlib.sha256(Path(__file__).with_name(p).read_bytes()).hexdigest()
                         for p in ('research_workflow.py', 'grounded_answer.py', 'guided_research.py',
                                   'direct_ingestion.py')})

    def _request(self, request):
        if not isinstance(request, dict) or set(request) not in (
                {'request_id', 'question_id'}, {'request_id', 'question_id', 'resume_of'}):
            raise ValueError('Only guided workflow requests accepted')
        rid, question = request_fields({k: request[k] for k in ('request_id', 'question_id')})
        if 'resume_of' in request:
            if identifier(request['resume_of']) == rid:
                raise ValueError('Cannot resume self')
        return rid, question

    def _snapshot(self, rid):
        folder = self.directory / identifier(rid)
        manifest = checked(folder / 'request.json')
        found, question = self._request(manifest['request'])
        if (found != rid or manifest['schema_version'] != SCHEMA
                or manifest['question'] != question['label']):
            raise ValueError('Workflow request mismatch')
        stages = {s: dict(stage=s, state='pending') for s in STAGES}
        artifacts, events = {}, []
        previous = None
        for n, path in enumerate(sorted(folder.glob('event-*.json')), 1):
            event = checked(path)
            if (path.name != f'event-{n:04d}.json' or event['sequence'] != n
                    or event['run_id'] != rid or event['previous_sha256'] != previous
                    or event['manifest_sha256'] != manifest['content_sha256']):
                raise ValueError('Workflow event chain mismatch')
            s, state = event['stage'], event['state']
            if s not in stages or any(stages[p]['state'] not in ('completed', 'reused') for p in STAGES[:STAGES.index(s)]):
                raise ValueError('Workflow dependency mismatch')
            before = stages[s]['state']
            if not ((before == 'pending' and state in ('running', 'reused')) or
                    (before == 'running' and state in ('completed', 'failed'))):
                raise ValueError('Workflow transition mismatch')
            if state in ('completed', 'reused'):
                artifact = checked(folder / f'{s}.json')
                inputs = {k: v['content_sha256'] for k, v in artifacts.items()}
                if (artifact['stage'] != s or artifact['run_id'] != rid
                        or artifact['manifest_sha256'] != manifest['content_sha256']
                        or artifact['inputs'] != inputs or event['artifact_sha256'] != artifact['content_sha256']):
                    raise ValueError('Workflow artifact binding mismatch')
                self._validate(s, artifact['value'], artifacts, rid, manifest)
                artifacts[s] = artifact
            stages[s] = dict(stage=s, state=state, **{k: event[k] for k in ('reason', 'reused_from') if k in event})
            events.append(event)
            previous = event['content_sha256']
        return manifest, stages, artifacts, events

    def _validate(self, stage, value, artifacts, rid, manifest):
        if stage == 'retrieve':
            if not isinstance(value, list) or len(value) > 5:
                raise ValueError('Invalid retrieved passages')
            for item in value:
                validate_row(item['record'])
            ids = [p['record']['passage']['passage_id'] for p in value]
            if len(set(ids)) != len(ids):
                raise ValueError('Duplicate passage')
        elif stage == 'select':
            if not isinstance(value, dict) or not isinstance(value.get('provenance'), dict):
                raise ValueError('Invalid generation record')
            expected = manifest['binding']['generation_identity']
            if any(value['provenance'].get(k) != v for k, v in expected.items()):
                raise ValueError('Generation identity mismatch')
            if value.get('validation') not in ('exact_quotes_verified', 'no_passages', 'generation_rejected'):
                raise ValueError('Unknown generation validation')
        elif stage == 'validate':
            generation = artifacts['select']['value']
            passages = artifacts['retrieve']['value']
            grounded_answer.validate_answer(generation['answer'], passages)
            if generation['validation'] == 'generation_rejected':
                raise ValueError('Invalid generation')
            if generation['validation'] == 'no_passages' and passages:
                raise ValueError('Incorrect empty-evidence claim')
            if value != dict(status=generation['answer']['status'], selection_sha256=artifacts['select']['content_sha256']):
                raise ValueError('Validation binding mismatch')
        elif stage == 'save':
            saved = self._responses().read(rid)
            if (value != dict(response_id=rid, content_sha256=saved['content_sha256'])
                    or saved['request']['question_id'] != manifest['request']['question_id']
                    or saved['passages'] != artifacts['retrieve']['value']
                    or saved['generation'] != artifacts['select']['value']):
                raise ValueError('Published response mismatch')

    def _responses(self, passages=None, generation=None):
        return ResearchStore(self.directory / 'responses', lambda _: passages,
            self.collection, self.encoder_id, lambda *_: generation)

    def read(self, rid):
        manifest, stages, artifacts, events = self._snapshot(rid)
        states = [x['state'] for x in stages.values()]
        state = ('completed' if states[-1] in ('completed', 'reused') else
                 'failed' if 'failed' in states else
                 'running' if active(self.directory / rid / 'owner.lock') else 'interrupted')
        result = dict(schema_version=SCHEMA, run_id=rid, request=manifest['request'],
            question=manifest['question'], state=state, stages=list(stages.values()),
            events=events, manifest_sha256=manifest['content_sha256'])
        if state == 'completed':
            result['response'] = self._responses().read(rid)
        return result

    def save(self, request):
        rid, question = self._request(request)
        folder = self.directory / rid
        # Same-ID delivery retries are reads, never fresh model attempts.
        if (folder / 'request.json').exists():
            result = self.read(rid)
            if result['request'] != request:
                raise FileExistsError('Workflow request conflict')
            return result
        with exclusive(self.directory / 'worker.lock'):
            if (folder / 'request.json').exists():
                return self.save(request)
            parent = None
            if 'resume_of' in request:
                parent_id = request['resume_of']
                status = self.read(parent_id)
                if status['state'] not in ('failed', 'interrupted'):
                    raise ValueError('Only failed/interrupted workflows can be recovered')
                parent = self._snapshot(parent_id)
                if parent[0]['binding'] != self.binding or parent[0]['question'] != question['label']:
                    raise ValueError('Recovery configuration mismatch')
            folder.mkdir(exist_ok=True)
            with exclusive(folder / 'owner.lock'):
                manifest = publish(folder / 'request.json', dict(schema_version=SCHEMA, request=request,
                    question=question['label'], binding=self.binding,
                    parent_manifest_sha256=parent[0]['content_sha256'] if parent else None))
                artifacts, events = {}, []
                def event(stage, state, **extra):
                    value = publish(folder / f'event-{len(events)+1:04d}.json', dict(
                        run_id=rid, sequence=len(events)+1, manifest_sha256=manifest['content_sha256'],
                        previous_sha256=events[-1]['content_sha256'] if events else None,
                        timestamp=datetime.now(timezone.utc).isoformat(), stage=stage, state=state, **extra))
                    events.append(value)
                def artifact(stage, value):
                    self._validate(stage, value, artifacts, rid, manifest)
                    item = publish(folder / f'{stage}.json', dict(run_id=rid, stage=stage,
                        manifest_sha256=manifest['content_sha256'],
                        inputs={k: v['content_sha256'] for k, v in artifacts.items()}, value=value))
                    artifacts[stage] = item
                    return item
                for stage in STAGES:
                    # Reuse only successful ancestors. Rejected selection is evidence, not reusable work.
                    reuse = parent and stage in parent[2] and stage != 'save'
                    if stage == 'select' and reuse:
                        reuse = (parent[2][stage]['value']['validation'] != 'generation_rejected'
                                 and parent[1]['validate']['state'] != 'failed')
                    if stage == 'validate' and reuse:
                        # Rebind validation to the child's exact selection artifact.
                        value = dict(status=artifacts['select']['value']['answer']['status'],
                                     selection_sha256=artifacts['select']['content_sha256'])
                    elif reuse:
                        value = parent[2][stage]['value']
                    if reuse:
                        item = artifact(stage, value)
                        event(stage, 'reused', artifact_sha256=item['content_sha256'],
                              reused_from=dict(run_id=request['resume_of'], artifact_sha256=parent[2][stage]['content_sha256']))
                        continue
                    event(stage, 'running')
                    try:
                        if stage == 'retrieve':
                            value = self.retrieve(question['label'])
                        elif stage == 'select':
                            value = self.generate(question['label'], artifacts['retrieve']['value'])
                        elif stage == 'validate':
                            value = dict(status=artifacts['select']['value']['answer']['status'],
                                         selection_sha256=artifacts['select']['content_sha256'])
                        else:
                            response = self._responses(artifacts['retrieve']['value'], artifacts['select']['value']).save(
                                dict(request_id=rid, question_id=request['question_id']))
                            value = dict(response_id=rid, content_sha256=response['content_sha256'])
                        item = artifact(stage, value)
                        event(stage, 'completed', artifact_sha256=item['content_sha256'])
                    except Exception as exc:
                        reason = ('invalid_generation' if stage in ('select', 'validate') and
                                  isinstance(exc, (ValueError, KeyError, TypeError)) else
                                  'service_unavailable' if isinstance(exc, OSError) else 'stage_failed')
                        event(stage, 'failed', reason=reason, error_type=type(exc).__name__)
                        break
                return self.read(rid)
