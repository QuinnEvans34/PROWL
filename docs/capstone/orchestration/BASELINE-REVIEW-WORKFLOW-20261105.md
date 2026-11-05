# Saved autonomous baseline workflow integration

The completed autonomous70 metadata export now enters the existing registered CPU
workflow: **admission → error analysis → reviewer handoff**. This adds the missing
saved-result connection; it does not wrap or rerun inference/scoring, qualify GPU
recovery, or complete the whole G3 production graph.

The owning adapter reuses `autonomous_baseline_review_v1` to verify the exact
export/request/ready hashes,70ordered dispositions,63scores/seven declared failures,
component/voxel arithmetic, scope and producer-reported integrity evidence. The
handoff retains the failure denominator, exposure, unknown-unit limitations and
UNQUALIFIED probability equivalence. It attaches no image payload or human decision.
Mac checks the transferred metadata, not Windows artifact bytes or model quality.

Each reuse validator rereads the pinned source before accepting an old artifact.
Changed source bytes refuse reuse; a new explicit source pin changes all affected
derivations. Changed output bytes refuse reuse without regenerating silently.
An injected analysis failure preserves the original failed attempt; explicit resume
reuses valid admission and completes only the pending descendants. The registry,
resolved configuration, lifecycle events and immutable run manifests use the
existing runner; no scheduler, shell stage, automatic retry or new framework.

Actual retained export SHA256
3944ea76135d9f756a22abea7931af43423a7050a928d79db79a8b10fbe78cc6
passed a mutation-free plan, three-stage run and three-stage reuse. Records:
`outputs/prowl/autonomous-baseline-workflow-20261105-02`.
Run8462f6d9-b579-4da5-aed7-93c6aa46ee91 completed3/3;
resume9c6c7004-a532-45d5-a781-e538d0752716 reused3/3 with the same source bytes.
The exact metadata was also retained outside /tmp at
`outputs/prowl/autonomous-baseline-source-20261105.json`; explicit relocation
resume5ab97dac-3493-42e2-9352-d8e8414e4493 again reused3/3 with the unchanged pin.
The first read-only CLI attempt lacked the isolated jsonschema dependency and
dispatched no stage; its failure is retained separately under the01directory.

```sh
PATH=/Users/quintonevans/.nvm/versions/node/v24.21.0/bin:$PATH \
PYTHONPATH=.:/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023/test-dependencies \
  .venv312/bin/python scripts/diagnostics/run_autonomous_baseline_workflow.py plan \
  --root /absolute/existing/dedicated-workflow-output \
  --source /absolute/retained/autonomous70-closeout.json \
  --export-sha256 3944ea76135d9f756a22abea7931af43423a7050a928d79db79a8b10fbe78cc6 \
  --request-sha256 ed67a10ab6cd59a0cbf91ff42bb4cb8152882d06eafdaa879fbbb9e8a91a7d2e \
  --ready-sha256 19e6f8b1e981145281c35bfcbb7293dbe9ea99b5d07c2e1cea7447e65d1d2845
```

Use `run` once, then `resume --resume-of UUID` explicitly. `inspect`/`status`
require only `--root` and `--run-id UUID`. The production CLI retains the existing
50GB output-volume reserve; zero-floor fixtures are synthetic tests only.

Broader workflow regression exposed an optional jsonschema format dependency:
invalid timestamps could be accepted when its date-time checker was absent.
Run-manifest validation now checks timezone-bearing RFC3339 timestamps using the
standard library, including invalid calendar dates and missing timezone rejection.
The verified Node24runtime is selected explicitly for literature contract tests.
Legacy three-workflow registry snapshots remain valid; the new workflow is an
optional additional registry kind, with exact stages/inputs/dependencies.

Remaining G3 work is actual expensive-stage integration/recovery and the complete
live imaging/reviewer/literature walkthrough. Existing63+7development evidence and
this CPU handoff do not establish independent held-out acceptance.
