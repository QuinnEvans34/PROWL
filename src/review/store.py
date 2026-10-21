"""Local append-only decisions and retained, hash-bound native prediction packages.

No model calls, patient catalog discovery, browser paths or evaluation labels.
The existing review-event v1 schema remains the persisted event contract.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import tempfile
import uuid
from urllib.request import urlopen

from jsonschema import Draft202012Validator, FormatChecker

REPO = Path(__file__).resolve().parents[2]
HASH = re.compile(r'^[a-f0-9]{64}$')
FILES = {'ct': 'ct.nii.gz', 'pred': 'prediction.nii.gz', 'result': 'result.json', 'evidence': 'evidence.json'}
REASONS = {
    'accept': {'contour_acceptable'},
    'edit_required': {'boundary_correction', 'missed_lesion', 'false_positive_lesion', 'pancreas_localization_error', 'pancreas_contour_error', 'measurement_error', 'other'},
    'reject': {'boundary_correction', 'missed_lesion', 'false_positive_lesion', 'pancreas_localization_error', 'pancreas_contour_error', 'measurement_error', 'insufficient_image_quality', 'other'},
}
VALIDATOR = Draft202012Validator(json.loads((REPO/'docs/capstone/contracts/review-event.schema.json').read_text()), format_checker=FormatChecker())


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


class ReviewError(Exception):
    def __init__(self, message, status=409):
        super().__init__(message)
        self.status = status


def sync_dir(path):
    fd = os.open(path, os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)


def write_new(path, data):
    with path.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


def read_file(root, name, cap):
    path = root/name
    if root.is_symlink() or path.is_symlink() or not path.is_file() or path.resolve().parent != root.resolve():
        raise ReviewError('Prediction files are unavailable or unsafe.')
    with path.open('rb') as stream: data = stream.read(cap+1)
    if not 0 < len(data) <= cap: raise ReviewError('Prediction file exceeds its limit.')
    return data


class ReviewStore:
    def __init__(self, root, saved=None, *, floor_bytes=100*1024**3):
        self.root = Path(root).absolute()
        if self.root.resolve() != self.root: raise ValueError('Review directory cannot contain symlinks')
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.saved = Path(saved).resolve() if saved else None
        self.floor_bytes = floor_bytes

    @contextmanager
    def locked(self):
        with (self.root/'.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            yield

    def reader(self, source):
        if source == 'saved' and self.saved:
            return lambda name, cap: read_file(self.saved, name, cap)
        if re.fullmatch(r'archive/[a-f0-9]{64}', source):
            root = self.root/source.split('/')[1]/'package'
            return lambda name, cap: read_file(root, name, cap)
        if re.fullmatch(r'job/[a-f0-9]{32}', source):
            # Fixed local service and allowlisted filenames; never fetch a client URL.
            base = 'http://127.0.0.1:8017/scan-inference/jobs/'+source.split('/')[1]+'/files/'
            def read(name, cap):
                with urlopen(base+name, timeout=15) as response: data = response.read(cap+1)
                if not 0 < len(data) <= cap: raise ReviewError('Prediction file exceeds its limit.')
                return data
            return read
        raise ReviewError('Review source is unavailable.', 404)

    def manifest(self, source):
        raw = self.reader(source)('manifest.json', 1024**2)
        m = json.loads(raw)
        if (m.get('schema_version') not in ('saved-prediction-view-v2', 'assisted-prediction-view-v1')
                or m.get('status') not in ('completed', 'completed_with_warnings')
                or not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', m.get('case_id', ''))):
            raise ReviewError('Only completed native prediction packages can be reviewed.')
        assisted = m['schema_version'] == 'assisted-prediction-view-v1'
        if (m.get('prediction_mode') != ('pancreas_assisted' if assisted else 'autonomous')
                or m.get('reference_inputs_used') is not assisted
                or not all(isinstance(m.get('model_sha256', {}).get(k), str) and HASH.fullmatch(m['model_sha256'][k])
                           for k in (('segmenter',) if assisted else ('segmenter','localizer')))):
            raise ReviewError('Invalid model or prediction mode.')
        if assisted and (not re.fullmatch(r'[a-f0-9]{32}', m.get('prediction_id',''))
                         or not all(HASH.fullmatch(m.get(k,'')) for k in ('request_identity','recipe_sha256','assistance_sha256'))):
            raise ReviewError('Invalid assisted prediction identity.')
        if source.startswith('job/') and (not assisted or m['prediction_id'] != source.split('/')[1]):
            raise ReviewError('Prediction belongs to another job.')
        g = m.get('geometry', {})
        shape, affine = g.get('shape',[]), g.get('affine',[])
        if (g.get('units') != 'mm' or len(shape) != 3 or not all(type(n) is int and n > 0 for n in shape)
                or math.prod(shape) > 32000000 or len(affine) != 4
                or not all(isinstance(row,list) and len(row) == 4 and all(type(n) in (int,float) and math.isfinite(n) for n in row) for row in affine)
                or m.get('ct_window') != [-100,300] or m.get('labels') != {'0':'background','1':'pancreas','2':'lesion'}
                or not isinstance(m.get('warnings'),list) or not all(isinstance(w,str) for w in m['warnings'])):
            raise ReviewError('Invalid native display geometry.')
        for key, name in FILES.items():
            ref = m['files'][key]
            cap = 64*1024**2 if key in ('ct','pred') else 1024**2
            if (ref['uri'] != name or not HASH.fullmatch(ref['content_sha256'])
                    or type(ref['bytes']) is not int or not 0 < ref['bytes'] <= cap):
                raise ReviewError('Invalid prediction file identity.')
        if m['files']['result']['content_sha256'] != m['result_sha256'] or m['files']['evidence']['content_sha256'] != m['inference_evidence_sha256']:
            raise ReviewError('Invalid prediction provenance identity.')
        identity = digest(raw)
        if source.startswith('archive/') and identity != source.split('/')[1]:
            raise ReviewError('Retained package identity changed.')
        return raw, m, identity

    def history(self, identity):
        folder = self.root/identity
        events = []
        previous = None
        for index, path in enumerate(sorted(folder.glob('event-*.json')), 1):
            record = json.loads(read_file(folder, path.name, 16384))
            e, r = record['event'], record['receipt']
            VALIDATOR.validate(e)
            if (path.name != f'event-{index:06}.json' or e['revision'] != index
                    or e['case_package_id'] != 'case-package:'+identity or e['prediction_id'] != 'prediction:'+identity
                    or e.get('supersedes_review_event_id') != previous
                    or r != self.receipt(e, identity)):
                raise ReviewError('Stored review history failed its integrity check.')
            events.append(record)
            previous = e['review_event_id']
        return events

    @staticmethod
    def receipt(event, identity):
        return dict(review_event_id=event['review_event_id'], revision=event['revision'],
                    content_sha256=digest(encode(event)), sequence=event['revision'],
                    location=f"{identity}/event-{event['revision']:06}.json",
                    case_package_id=event['case_package_id'], prediction_id=event['prediction_id'])

    def target(self, source):
        with self.locked():
            _, m, identity = self.manifest(source)
            return dict(manifest_sha256=identity, case_id=m['case_id'], case_package_id='case-package:'+identity,
                        prediction_id='prediction:'+identity, history=[dict(event=r['event'], receipt=r['receipt']) for r in self.history(identity)])

    def retain(self, source, raw, m, identity):
        destination = self.root/identity
        if destination.exists():
            # A retry must verify the retained files too, not silently trust their presence.
            read = self.reader('archive/'+identity)
            if read('manifest.json', 1024**2) != raw: raise ReviewError('Retained manifest changed.')
            for key, name in FILES.items():
                data = read(name, m['files'][key]['bytes'])
                if len(data) != m['files'][key]['bytes'] or digest(data) != m['files'][key]['content_sha256']:
                    raise ReviewError('Retained prediction changed.')
            return
        packages = [p for p in self.root.iterdir() if HASH.fullmatch(p.name)]
        required = len(raw)+sum(f['bytes'] for f in (m['files'][k] for k in FILES))
        used = sum(p.stat().st_size for d in packages for p in d.rglob('*') if p.is_file())
        if len(packages) >= 20 or used+required > 2*1024**3 or shutil.disk_usage(self.root).free-required < self.floor_bytes:
            raise ReviewError('Review storage limit reached. No existing records were removed.', 507)
        with tempfile.TemporaryDirectory(prefix='.pending-', dir=self.root) as staging:
            staged = Path(staging)/identity
            package = staged/'package'
            package.mkdir(parents=True)
            read = self.reader(source)
            write_new(package/'manifest.json', raw)
            for key, name in FILES.items():
                ref = m['files'][key]
                data = read(name, ref['bytes'])
                if len(data) != ref['bytes'] or digest(data) != ref['content_sha256']:
                    raise ReviewError('Prediction changed before saving. Reload the result.')
                write_new(package/name, data)
            sync_dir(package)
            sync_dir(staged)
            os.rename(staged, destination)
            sync_dir(self.root)

    def append(self, source, body):
        if not isinstance(body, dict) or set(body) != {'request_id','manifest_sha256','expected_latest_id','reviewer','action','reason_codes','note'}:
            raise ReviewError('Invalid review request.', 400)
        try:
            if str(uuid.UUID(body['request_id'], version=4)) != body['request_id']: raise ValueError()
            if not HASH.fullmatch(body['manifest_sha256']): raise ValueError()
        except (TypeError, ValueError): raise ReviewError('Invalid request identity.', 400)
        if (body['action'] not in REASONS or not isinstance(body['reason_codes'], list)
                or not body['reason_codes'] or not all(isinstance(r, str) for r in body['reason_codes'])
                or not set(body['reason_codes']) <= REASONS[body['action']]
                or len(set(body['reason_codes'])) != len(body['reason_codes'])
                or not isinstance(body['note'], str) or len(body['note']) > 2000
                or ('other' in body['reason_codes'] and not body['note'].strip())):
            raise ReviewError('Choose compatible reasons; Other requires a note.', 400)
        request_hash = digest(encode(body))
        identity = body['manifest_sha256']
        with self.locked():
            history = self.history(identity)
            for record in history:
                if record['request_id'] == body['request_id']:
                    if record['request_sha256'] != request_hash: raise ReviewError('Retry identity was reused with different content.')
                    # Re-establish durability after an uncertain acknowledgment.
                    with (self.root/identity/record['receipt']['location'].split('/')[-1]).open('rb') as stream: os.fsync(stream.fileno())
                    sync_dir(self.root/identity)
                    return dict(event=record['event'], receipt=record['receipt'])
            latest = history[-1]['event']['review_event_id'] if history else None
            if body['expected_latest_id'] != latest: raise ReviewError('Another decision was saved. Reload history before revising.')
            if len(history) >= 1000: raise ReviewError('Review history limit reached.', 507)
            raw, m, current = self.manifest(source)
            if current != identity: raise ReviewError('Prediction changed. Reload before saving.')
            event = dict(schema_version='1.0.0', review_event_id='review:'+str(uuid.uuid4()), recorded_at=datetime.now(timezone.utc).isoformat(),
                         case_package_id='case-package:'+identity, prediction_id='prediction:'+identity,
                         reviewer=body['reviewer'], action=body['action'], revision=len(history)+1,
                         supersedes_review_event_id=latest, reason_codes=body['reason_codes'], note=body['note'],
                         client=dict(application='PROWL', application_version='native-review-v1', transport='fastapi'))
            VALIDATOR.validate(event)
            if not event['reviewer']['reviewer_id'].strip(): raise ReviewError('Reviewer name is required.', 400)
            self.retain(source, raw, m, identity)
            if shutil.disk_usage(self.root).free - 16384 < self.floor_bytes:
                raise ReviewError('Review storage floor reached. No existing records were removed.', 507)
            receipt = self.receipt(event, identity)
            record = dict(event=event, receipt=receipt, request_id=body['request_id'], request_sha256=request_hash)
            folder = self.root/identity
            # Atomic create without replacement; incomplete bytes never become a ledger member.
            temporary = folder/('.event-'+uuid.uuid4().hex)
            try:
                write_new(temporary, encode(record))
                os.link(temporary, folder/f"event-{event['revision']:06}.json")
                sync_dir(folder)
            finally:
                if temporary.exists(): temporary.unlink()
            return dict(event=event, receipt=receipt)

    def packages(self):
        with self.locked():
            result = []
            for folder in sorted(self.root.iterdir()):
                if not HASH.fullmatch(folder.name): continue
                _, m, identity = self.manifest('archive/'+folder.name)
                history = self.history(identity)
                if history:
                    result.append(dict(manifest_sha256=identity, case_id=m['case_id'], latest=history[-1]['event']))
            return result
