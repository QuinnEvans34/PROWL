# On-demand prediction and shared native measurements

**State:** current model activated and one real prediction displayed; volume withheld for region-boundary contact.
See [activation results](ON-DEMAND-ACTIVATION-2026-10-20.md) for current services and evidence;
initial unconfigured-state details below are historical.
**Scope:** AI-05 development slice, selected by Quinton on October 20. No formal quality acceptance.

## User workflow

Open `/predict` (linked from `/saved`), choose an admitted development scan and run prediction.
The worker creates one native label mask. The viewer displays those exact hash-verified bytes;
the measurement panel counts labels from the same bytes and affine. Asking another measurement
question or rechecking a result does not rerun segmentation. Run again explicitly starts a new job.
Scan changes and cancellation remove the old result and discard late responses.

Session results use temporary transport files, with at most four jobs retained and no persistent
cache enabled. Releasing a result removes only that server-owned job directory. Server shutdown
cleans the session directory. An optional persistent cache remains future work; it is not required
to reuse the current result. Training need not serialize every evaluation prediction.

## Delivered implementation

- `scripts/serve_on_demand.py`: loopback-only `/scan-inference/cases`, job creation/status/cancel,
  release and allowlisted result files. Explicitly unconfigured without operator-supplied pins.
- `src/inference/on_demand.py`: one POSIX process group at a time; fixed local worker, immutable
  case/model/recipe/code identities, timeout/RSS/output limits, reaping before result publication,
  fresh per-job request identity and file hashes. Failed/cancelled work cannot expose result files.
- `scripts/run_on_demand_worker.py`: checks source, assistance, checkpoint and code hashes before
  and after worker execution. No client-supplied path, command, checkpoint or split is accepted.
- `src/inference/assisted_prediction.py` and `assisted_windows.py`: independent model-state loader,
  current native orientation, pancreas-defined region, physical tiles, probability blending,
  lower-label tie breaking and native reinsertion. No training Session, optimizer or training RNG
  restore; no lesion reference input. Only fully trained raw model tensors are strict-loaded.
- `assisted-prediction-view-v1`: separate assisted manifest/evidence contract. Autonomous v2 still
  rejects reference-assisted records. UI verifies source, mask, request, model, recipe, supplied
  pancreas identity, native geometry, reconstruction coverage and original file hashes.
- `OnDemandPredictionView`: starts/polls/cancels jobs and supplies the verified result to the
  existing native viewer/measurement panel. The shared shell's new route stays with its local
  integration branch; portable worker/components publish separately.

Pancreas extent uses output labels 1+2; total suspected-lesion volume uses output label 2. The
provided pancreas mask selects the region and is disclosed as assistance; it is never substituted
for the measured prediction. This union differs intentionally from the evaluator's class-1-only
pancreas metric. Both CT-edge and inference-region contact withhold volume, as before. Passing
geometry and boundary checks does not establish anatomical completeness or clinical accuracy.

## Source provenance and numerical scope

Quinton authorized the source handoff from **Plan capstone experiment workflow**. The source-only
ZIP was delivered through ten numbered chat-output chunks and locally verified:
86,767 bytes, SHA-256 `ff38a32f186c56a4b9da83872184818cccf6f914fe1827974d0925afde83fd62`.
All individual source-file hashes match its manifest. Full bundle remains private/ignored under
`outputs/prowl/on-demand-20261020/reference/`; historical training/cohort modules were not imported
into the app or republished. The pure numerical helpers were extracted from:

- `segmenter_native_windows_v1.py`: geometry/orientation, starts/tiles, extraction, blend weights.
- `segmenter_physical_windows_v1.py`: physical geometry, coordinate maps, window sampling,
  native destinations and probability reconstruction.

Their exact producing source hashes are recorded in `assisted_windows.py`. Region selection and
native reinsertion follow the received region evaluator; the image-only adapter omits its target
and training-provider dependencies. Normalization is float32 clip[-100,250], +100, /350. Windows
are 144³ with stride72, separate ceil-rounded base10mm and extra[81,43,71]mm source-plane margins.
Model is three-class SegResNet16/GroupNorm8; raw checkpoint tensor location is
`session.raw.model`. Float32 and disabled CUDA TF32 are preserved. CPU/MPS equivalence to the
original CUDA run is **not qualified** by these synthetic checks.

## Checks and observed limits

22 Python checks pass: job concurrency/cancellation/reaping, identity failures, timeout, private
HTTP routes/origin checks, native geometry/units, supplied-mask validity, physical reconstruction,
orientation/obliquity, normalization/padding/ties and strict model-state loading. The model-loader
test constructs synthetic CPU models, transfers generated state exactly, rejects wrong dtype/shape/
nonfinite tensors and forbids optimizer construction; no model forward or real checkpoint was used.
One cross-language test runs a synthetic worker through the real HTTP file transport and real JS
loader; all identities match and its eight labeled 1mm³ voxels measure **0.008mL**. This artificial
fixture is labeled explicitly and is not offered as a clinical scan or live model result.

57 affected UI/library checks pass, including assisted provenance contradictions, wrong-job
refusal, original autonomous/v1 compatibility, late POST cancellation, stale scan responses,
no saved-result substitution, native volume arithmetic and existing viewer lifecycle behavior.
Production build passes with the existing large-bundle warning. Two existing Torch deprecation
warnings occur in the synthetic model-loader test. No patient arrays, trained checkpoint bytes,
training runs, protected evaluation or actual current-model predictions were used in this block.

Limits: 32 million native voxels; 64MiB each compressed CT/mask; 128MiB each decoded image;
1MiB per JSON record; at most256 physical tiles. Supervisor samples process-group RSS and output
size every approximately100ms, with a maximum600s job. These are sampled limits, not guarantees
that transient allocations cannot overshoot. Production configuration defaults to8GiB RSS and
132MiB job output. Actual current-case fit/latency and prediction quality remain unassessed.

## Local operation and remaining activation

Unconfigured service is running on port8017, owned session97229, with Vite5180 proxying it.
Browser `/predict` correctly shows that no current worker is connected and disables Run. UI and
backend code are connected; this is **not a successful real-model demonstration**. Existing
literature API, database, Ollama, saved native package and remote training remain intact.

The current raw trained checkpoint is still on the Windows laptop. Handoff identifies retained
`execution/step-006000.pt` (56,576,803 bytes), but no payload hash or local copy was supplied.
We also need one explicitly exposed development CT and its aligned supplied pancreas mask on the
inference host. Do not silently substitute the older local model or select protected/demo test cases.

Once those inputs and an idle inference resource window are available:

1. Pin the immutable checkpoint digest and exposed case identity; inspect native header/resource
   fit before activation. Preserve source bytes, label/assistance roles and any rejected attempts.
2. Run `scripts/configure_on_demand.py --case-id ... --ct ... --pancreas ... --checkpoint ...
   --checkpoint-sha256 ... --device ... --output <private-new-json> --exposed-development` with
   `.venv-prowl/bin/python`. This hashes files and pins the inference code closure without loading
   the model or executing inference. Output is private and must not be committed.
3. Stop only the owned unconfigured8017 server and restart `scripts/serve_on_demand.py --config
   <private-json> --port8017`. No automatic server replacement, training interruption or launch is
   scheduled. The worker reads admitted inputs only when the user requests prediction.
4. Run one bounded case, inspect native outline/coverage, confirm the same prediction identity in
   viewer and measurement evidence, and record resource/latency/failure or pass evidence. Compare
   against the original numerical producer before any cross-device reproduction claim.

Individual lesion components/diameter, reference-reviewed accuracy, normal-reference eligibility
and formal RAG quality checkpoints remain open. AI-05 stays In Progress.
