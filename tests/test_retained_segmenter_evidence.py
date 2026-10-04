"""Opt-in checks against local originals; missing evidence fails rather than skips."""
import json
from pathlib import Path
import pytest
from retained_segmenter_metadata import ROOT,fixture_path,metadata
from scripts.diagnostics import segmenter_cache_qualification as q

pytestmark = pytest.mark.local_evidence
REPO = Path(__file__).parents[1]


def test_exact_compatibility_membership_matches_local_original():
    assert fixture_path('train.txt').read_bytes() == (REPO/'outputs/splits/train.txt').read_bytes()


def test_exact_native_baseline_and_consumed_request_match_local_originals():
    manifest=json.loads((ROOT/'manifest.json').read_bytes())
    for key,name in [('baseline','accepted-native-baseline.json'),('request','CAP-EXP-013-PREPARED-20261003/request.json')]:
        assert fixture_path(name).read_bytes() == (REPO/manifest['sources'][key]['path']).read_bytes()


def test_retained_inventory_is_exact_no_source_arrays(monkeypatch):
    monkeypatch.setattr(q.loader,'resolve_registered',lambda:pytest.fail('Unexpected registered storage read'))
    monkeypatch.setattr(q.source,'source_stream',lambda *a:pytest.fail('Unexpected source array'))
    binding,scope=q.inputs();saved=metadata()
    assert binding==saved['cache_binding'] and scope==saved['cache_scope']
    assert len(binding['entries'])==7 and q.cache.checked_binding(binding,q.content_hash(binding))==104509440
    assert sum(x['compressed_bytes'] for x in scope['files'])==145701969
    assert sum(x['expanded_bytes'] for x in scope['files'])==544986944
    assert [e['descriptor']['protected_role'] for e in binding['entries']]==['train']*6+['validation']
    assert all(e['fidelity']['outside_pancreas_voxels']>=0 for e in binding['entries'])


def test_verified_local_refresh_matches_committed_evidence():
    saved=metadata()
    original=json.loads((q.ROOT/'SEGMENTER-GEOMETRY-SCOPE-attempt02-20261001/result.json').read_bytes())['files']
    proof=q.source.verify_package(q.METADATA,q.METADATA_PIN)
    assert original==saved['refresh_rows'] and proof==saved['refresh_evidence']
    assert q.refreshed_rows(original,proof)==q.refreshed_rows(saved['refresh_rows'],saved['refresh_evidence'])
