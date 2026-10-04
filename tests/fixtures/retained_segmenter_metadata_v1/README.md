# Portable retained diagnostic metadata

These fixtures contain project-generated numeric/control metadata from completed PanTS diagnostics.
They are **retained real diagnostic metadata, not synthetic data**. No imaging/mask arrays, cache
tensors, model weights, downloaded literature or private clinical text is included.

`manifest.json` records the original local source paths and byte hashes, and pins every fixture.
`contracts.json` contains only the fields needed by cache/authorization/comparison tests. The native
baseline and consumed CAP-EXP-013 request keep their exact original bytes because the production
metadata-only reader checks their historical hashes. `train.txt` keeps the exact 7,200-member
compatibility-control bytes required by the existing protected-identity guard. This membership
control does not qualify members, supply labels or authorize training.

`tests/retained_segmenter_metadata.py` loads these files directly and verifies their sizes/hashes.
It never falls back to local outputs. Test request objects in the qualified-real domain exercise
schema/authority refusal rules using this metadata; they do not load real arrays or execute jobs.
No launch or storage approval file is included. A consumed request is provenance, not new authority.

The ordinary suite can use these fixtures in an exported tree with local outputs unavailable.
Checks against the original local evidence are explicitly selected:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests/test_retained_segmenter_evidence.py -m local_evidence -q -p no:cacheprovider
```

Those checks fail if the retained evidence is absent or differs; they do not silently skip. Historical
D-335 source/test pins remain in the original sealed control snapshot. The portability repair creates
a new test-source state and does not rewrite the old run's source manifest or requalify its executor.
