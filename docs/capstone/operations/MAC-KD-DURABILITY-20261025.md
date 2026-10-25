# Mac KD continuation and durable ownership — October25

The October23 supervisor disappeared; guardian-failure.json records cleanup, not
successful completion. The initiating cause is unproven. The execution design
allowed the chat-owned supervisor to determine the worker lifetime.

## Repair and evidence

One-shot macOS launchd owns the supervisor directly (PPID1). No KeepAlive,
recurring schedule, login installation or automatic retry. The job registration
and bootstrap logs live under `~/Library/Application Support/PROWL/owned-jobs`;
scientific artifacts remain external. Working directory is the user's home;
absolute executable/script paths preserve the existing environment.

Synthetic probe01 external plist bootstrap failed before a worker started.
Probe02 internal plist with external bootstrap logs/working directory exited78.
Probe03 internal plist/logs and home working directory passed:20 ticks after the
initiating command returned,21.34seconds,15,319,040B peak owned RSS,exit0/reaped;
launchd exit0 and supervisor parent1 verified. This establishes initiating-process
independence, not an observed future chat termination or reboot/logout persistence.
Original failures and their artifacts are retained. No security permissions changed.

## Active teacher preparation

Label `com.prowl.rsuper-targets-20261025-02` owns continuation
`rsuper-full-targets-02`. Initial verified supervisor49082, worker49254;
process.json is authoritative. Same fixed teacher and geometry. Verify/reuse
completed case6311 from attempt01 and12 saved pilot predictions; preserve all
original files. Completed second case1053 at217.09supervised seconds, proving
new inference/reconstruction beyond reused output. No student scientific updates.

Remaining wall budget345000seconds charges600seconds for the interrupted attempt
against the original96hours. Existing memory/storage/GPU/AC limits remain.
Keep AC and external drive connected; no promise of lid-closed/logout/reboot survival.
No automated scientific training chain is armed. Do not duplicate the job.

Status: `launchctl print gui/501/com.prowl.rsuper-targets-20261025-02`.
Read progress.jsonl/tiles.jsonl and eventual resources.json/result.json from the
external artifact directory. A registered job alone is not evidence of progress.

## Full training path work

Additive corrected-label KD provider binds native metadata only for1333 training
members. Development retains unchanged native evaluation without teacher targets.
Both planned arms use explicit on-demand/no-prefetch identity; no fast-loader
runtime equivalence claim. New recovery adapter preserves that identity.
Four CPU tests covered corrected inputs and exact synthetic next-update restore;
seven combined component/recovery/ownership tests pass. Synthetic models do not
qualify actual full-recipe MPS execution.

Full-provider metadata/sampling audit attempt01 mistakenly expected teacher native
metadata for development; it failed before CT/model reads. Exact original source
snapshots are retained and verified against its request pins. Corrected attempt02
checks train-only native metadata,18kfocused/6kcontext updates,664positive training
cases,1333train/70dev separation. Completion must be read from its result/resources.

Teacher-free native evaluation now emits all26-connected reference components,
volumes, hits and source/geometry hashes; sidecars bind exact native report bytes.
Tests distinguish small components from whole-patient size, anisotropic volumes,
empty negatives,26-connectivity and report tampering. Real evaluator integration
and actual full-provider MPS recovery remain necessary before either24k arm.

The ongoing teacher stage is still roughly a multi-day prerequisite. This repair
does not turn partial target generation into completed training or waive quality,
checkpoint, native-evaluation or paired-comparison requirements.

## Verified full-provider outcome

Attempt02 PASS:1333train,664positive,70development;18,000focused+6,000context
updates. All coverage-bank slots fit the full24k schedule.146.07seconds,
1,433,944,064B peak owned RSS,exit0/reaped; zero CT voxel reads or optimizer updates.
Provider SHA256900619faa0a5905fca165bebca0c9afd56f9df635cdd7141c4f95a31204a0053.
All6 provider request pins and1674 active target request pins matched final check.
Target continuation has2 completed cases and is processing1012 (third member).
Inactive synthetic launchd registrations removed; artifact evidence preserved;
active target registration untouched. Remaining actual-MPS full-provider/executor/
native-evaluator recovery and final paired launch cannot be claimed from CPU tests.

## Native executor evidence integration

Added segmenter_kd_evidence_executor_v1 as a wrapper around the existing region
executor, leaving its update cadence and selection loop unchanged. Every scheduled,
selected and terminal native report now produces a hash-bound component sidecar
before calling the required backup hook for both artifacts. Missing component
evidence or a backup failure prevents native/completed events and preserves the
pre-validation checkpoint and failed journal. No automatic retry or resume.
18 focused CPU tests passed in4.21seconds, including durable report/sidecar copies,
backup failure, missing evidence, synthetic recovery and existing selection tests.
This is integration test evidence, not actual MPS executor qualification.
The launchd target job continued across chat turns:4cases complete, fifth processing
at inspection. Scientific training remains unlaunched; target generation owns MPS.

## Target admission and executor recovery rehearsal

Added generated-target admission checking exact producer/provider train order,
train/development separation, source CT identity, corrected native grid, complete
reconstruction, payload SHA/size/type/shape, and successful reaped full generation.
Partial qualification manifests cannot be admitted by the full training store.
CPU rehearsal rsuper-target-admission-20261025-01 passed on6 completed targets;
all7 corrected labels retain the same teacher CT/native geometry.9.34seconds,
1,472,888,832B peak RSS,exit0/reaped,zeroCTvoxelreads/zeroGPUupdates. All17 rehearsal
pins and1674 active generation pins still match. No full training manifest published.

Actual executor integration with an invented CPU network exposed a real JSON
journal failure: teacher provenance contains a NumPy float32 quantization bound.
The additive executor wrapper now converts NumPy scalars to exact Python scalar
values for reporting only. Model state/calculations and original producer modules
are unchanged; arrays/unsupported objects/nonfinite values still fail serialization.
The8-update synthetic executor run restores its backed-up step4 checkpoint through
ErrataKDSession and reaches exactly the same final state after4more updates.
30 focused tests PASS in2.79seconds. Earlier test failures (NumPy JSON conversion)
and first CLI import failure (missing dependency path, before any request/output)
are recorded here; no failed GPU stage or scientific attempt was retried.
Generation continued to6 complete with3188 processing. Actual full-provider MPS
executor/native inference/recovery remains unqualified; no successor auto-launch.
