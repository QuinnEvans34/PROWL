"""Explicit local metadata checks; no source arrays or execution authority."""
import json
from pathlib import Path
import pytest
from retained_diagnostic_metadata import metadata
from scripts.diagnostics import localizer_candidate_headers_v2 as headers
from scripts.diagnostics import localizer_candidate_content_v2 as pilot
from scripts.diagnostics import localizer_candidate_content_v3 as continuation
from scripts.diagnostics import segmenter_native_scoring as native
from scripts.diagnostics import segmenter_content_continuation as segmenter
from scripts.diagnostics import twomm_parented_launch as parent
from scripts.diagnostics import twomm_training_tail_launch as tail
from src.data.manifest_records import digest

pytestmark = pytest.mark.local_evidence


def test_candidate_metadata_and_selections_match_verified_local_evidence():
    saved = metadata()
    assert headers.controls() == saved['header_job']
    assert json.loads((headers.SELECTION/'selection.json').read_bytes()) == saved['header_selection']
    assert json.loads((pilot.HEADERS/'result.json').read_bytes())['cases'] == saved['header_cases']
    assert pilot.checked_selection() == saved['selections']['batch-01']
    for batch in continuation.ACTIVE:
        assert continuation.checked_selection(batch) == saved['selections'][batch]


def test_native_input_metadata_matches_verified_local_evidence():
    assert list(native.inputs()) == metadata()['native_scoring_inputs']


def test_localizer_binding_and_pinned_ancestry_match_local_evidence():
    saved = metadata()
    assert json.loads(parent.BINDING.read_bytes()) == saved['binding']
    assert parent.parent_reference() == saved['parent_reference']
    assert tail.prefix_reference() == saved['prefix_reference']
    # Verify the sealed probe record without opening a tensor/probe payload.
    probe = saved['parent_probe']
    raw = (Path(probe['path']).parent/'receipt.json').read_bytes()
    assert digest(raw) == saved['parent_reference']['prefix_reference']['execution_receipt_sha256']
    assert json.loads(raw)['files']['probe.pt']['sha256'] == probe['sha256']


def test_segmenter_continuation_matches_pinned_local_proposal():
    raw = segmenter.source.safe_local(segmenter.CONTINUATION,segmenter.CONTINUATION_PIN)
    assert json.loads(raw) == metadata()['continuation']
