"""Portable, pinned project-generated numeric metadata; never an execution grant."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).parent / 'fixtures' / 'retained_segmenter_metadata_v1'


def fixture_path(name):
    manifest = json.loads((ROOT / 'manifest.json').read_bytes())
    assert manifest['origin'] == 'retained_real_diagnostic_metadata_not_synthetic'
    assert manifest['execution_authority'] is False
    assert manifest['original_arrays_included'] is False
    assert manifest['model_or_cache_payloads_included'] is False
    row = manifest['files'][name]
    path = ROOT / name
    raw = path.read_bytes()
    assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
    return path


def metadata():
    return json.loads(fixture_path('contracts.json').read_bytes())
