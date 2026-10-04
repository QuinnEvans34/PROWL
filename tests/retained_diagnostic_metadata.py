"""Pinned numeric diagnostic metadata for portable guard tests; no execution grant."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).parent / 'fixtures' / 'retained_diagnostic_metadata_v1'


def metadata():
    manifest = json.loads((ROOT / 'manifest.json').read_bytes())
    assert manifest['origin'] == 'retained_real_diagnostic_metadata_not_synthetic'
    assert manifest['execution_authority'] is False
    assert manifest['original_arrays_included'] is False
    assert manifest['model_or_cache_payloads_included'] is False
    raw = (ROOT / 'contracts.json').read_bytes()
    row = manifest['files']['contracts.json']
    assert len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256']
    return json.loads(raw)
