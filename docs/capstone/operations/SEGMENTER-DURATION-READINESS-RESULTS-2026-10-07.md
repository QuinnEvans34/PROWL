# Duration readiness handback — October 7

**Later diagnosis handback:** [DUR-05/D01/D02](SEGMENTER-DURATION-RECOVERY-AUDIT-RESULTS-2026-10-07.md)
finished after Quinton selected the bounded diagnosis sequence. Fresh D02 measured weight max
3.7253e-9 and optimizer max4.3656e-9, exact progress/CPU/MPS RNG; bit-exact continuation still
fails. Reporting is repaired/40new checks pass. No scientific readiness or launch claimed.
[DUR-06 inference-only readiness and real-data preparation](SEGMENTER-DURATION-REAL-DATA-PREPARATION-2026-10-07.md)
is the concrete unapproved next decision. The original N02 failure and proposal wording below
remain retained historical evidence, not new dispatch or replay authority.

## N02 finished: producer complete, independent next-update recovery failed

**The full 192-update invented producer completed. Native qualification remains incomplete because
cold recovery failed at the step-48-to-49 state comparison. Nothing from this attempt is running.**
Quinton's DUR-04 approval was applied, its 70 changed/new model-free checks passed, and the repair
was locally preserved at `8ae2748e3c1c9e0467b76c1b079f6a3e023b9342`. Its conditional N02 request
was prepared, separately reviewed, then dispatched once per stage. Both stages are disk-consumed;
N02 is operationally retired. No retry, reset, automatic extension or scientific job follows.

### What finished and what failed

- Producer: 192 invented 144³/MPS updates; each of the six training members received 32 updates.
  Checkpoints at 0/48/96/144/192, four native screens, and all 25 exports plus 25 views completed.
  The persisted counter is 253 forwards/192 optimizer calls. Producer watchdog elapsed
  1,202.456363 seconds, sampled owned RSS peak 4,495,294,464 bytes, 15,492 samples; worker reaped.
- Cold: consumed failure after 72.057609 supervised seconds, sampled owned RSS peak
  4,823,351,296 bytes, 928 samples; worker reaped. Exact worker error:
  `Independent full next-update recovery differs`, at launcher line 237. Its combined assertion
  covers model, optimizer, progress, CPU RNG and MPS RNG; it short-circuits and does not persist
  which component failed or its numerical difference. Do not infer corruption, a serialization
  defect or MPS nondeterminism from this message alone.
- The pinned control path reaching that assertion establishes that probability checks at steps
  0 and 48 met the unchanged 1e-6 requirement and all six step-48 native exports matched exactly.
  All four screens, images, probes, expected full step-49 state, two checkpoints and six
  export/view pairs were restored: 22 completed restore receipts. The remaining checkpoints
  and 19 exports were not cold-qualified. Probability differences were not retained numerically.
- Cold ran one invented replay update before the assertion. Nine forwards/one optimizer call
  follow from the pinned source path, **not a persisted cold counter**; aggregate calls inferred
  across the attempt are 262 forwards/193 updates. The outer helper's failure JSON retains its
  initial zero call placeholders and must not be cited as zero model work. That raw record is
  preserved unchanged; `failure-audit.json` records the distinction.
- Primary Python payload reads were blocked by the installed recovery guard; cold restored from
  the independent internal keeper. Full next-update matching and all-25 export recovery remain
  unqualified. No `SEGMENTER-DURATION-NATIVE-READINESS.json` or successful cold result was written.

All work used invented inputs and invented native targets: zero original/cache/CT/third-party
weight payloads. The positive-only policy template remains separate from D-335 and actual native
reference counts. Positive `reference_drift` and negative `components` policy failures were
retained at the engineering screens. The producer's terminal decision is `terminal_insufficient`;
this rehearsal supplies no scientific model-quality acceptance.

### Resources, preservation and tracking

The helper completed in 1,334.311343 seconds with sampled aggregate owned RSS peak 5,456,035,840
bytes and 10,406 samples. No watchdog stop occurred. It exited; both worker records report reaping,
and the helper's final record reports the shared MPS lock released. A read-only native PID check
confirmed helper PID 78471 absent. The original 60-minute/12-GiB ceilings were preserved.

Backup baseline was 17,341,924,636 bytes; final metadata inventory is 19,624,209,117 bytes, growth
2,282,284,481 bytes. N02 keepers are 1,611,507,905 bytes, partial restores 670,373,414 bytes and
controls 403,162 bytes. These sum to the measured growth and fit the approved child/phase/control
and whole-backup ceilings. Internal free space was 115,507,200,000 bytes and external free space
2,863,104,000,000 bytes at the final observation, above the 100-GiB floor. Existing evidence was
preserved; no pruning, capacity increase or other-lane capability rebinding occurred. The 26-GiB
budget remains approved/applied, but another rehearsal is outside the spent one-rehearsal scope.

All 397 producing source pins and the historical experiment tail remain unchanged after the job.
No completed test, producer or recovery stage was rerun. The post-run metadata helper initially
looked for uppercase `EXPERIMENTS.md`, found none and stopped; its corrected review used the
existing `docs/experiments.md`. No model or payload operation occurred in either review.

Local receipt `outputs/prowl/SEGMENTER-DURATION-NATIVE-N02-20261007/` preserves the frozen manifest,
independent control review, producer result, raw helper failure/resources, copied cold worker log,
consumption/failure records, supplemental failure audit and post-run pin review. Actual keeper
and partial restore artifacts remain in their approved N02 namespace. These local metadata
receipts alone are not independent recovery acceptance. W01-28 is **To-Do/incomplete**, titled
`Blocked: native recovery step-49 state mismatch`; its updated description and list were read back.
Human active hours remain unconfirmed; unattended runtime is excluded. No public push occurred.

### DUR-05 proposal: diagnose the exact recovery mismatch before another model job

This is a concrete **unapproved** follow-up. Its closed producing allowlist is:

1. New `src/training/segmenter_duration_recovery_audit_v1.py`: bounded component comparisons for
   model, optimizer, progress, CPU RNG and MPS RNG. Report all component predicates, at most 16
   differing field paths, shapes/dtypes/devices, mismatch counts and finite maximum absolute
   differences where applicable. Persist metadata only; no weights, arrays or full optimizer
   values in the report. The conjunction remains exactly as strict as the existing requirement;
   a numerical tolerance cannot turn failure into acceptance.
2. Amend only the cold comparison/failure-reporting region of
   `scripts/diagnostics/segmenter_duration_launch.py`: write a bounded atomic audit before the
   existing refusal and retain partial counters, checkpoint probability differences, native
   export counts and reached phase on failure. Keep primary denial, one-use request consumption,
   numerical recipe, sampler, source/hash guards and every time/resource/quality limit unchanged.
3. New `tests/test_segmenter_duration_recovery_audit.py`: invented small tensor and fake-session
   checks for each component failure, simultaneous failures, nonfinite/structural substitutions,
   bounded output and recorded failure counters. Zero model forwards/optimizer calls; run only
   the new tests under a 90-second/2-GiB ceiling. No old test replay or 144³ generation.
4. New `docs/capstone/imaging/SEGMENTER-DURATION-RECOVERY-AUDIT-CONTRACT-V1.md`: record the exact
   scope and limits before code; snapshot the launcher, preserve the 397-entry ledger and record
   the one approved hash transition plus new producing pins. Routine handback/tracking updates
   and a meaningful reviewed local commit are included. No session/executor/numerical change.

This packet authorizes no N02 payload inspection, replay, native run, writer or scientific launch.
After diagnostics are qualified, any use of retained invented states or new recovery job requires
its own reviewed request, source binding and remaining storage allocation. It must not reuse the
spent N02 authority. **Exact next starting point:** Quinton's decision on this four-file, model-free
DUR-05 packet. Full native recovery and a separately frozen scientific request still precede
actual-data training. SuPreM's missing publisher evidence remains a separate unresolved route.

## Historical DUR-04 handback: N02 running at that checkpoint

Quinton answered “Yes, approve” to the exact dispatcher amendment and continuation into the
already-approved conditional N02. Only dispatcher `verify_code` and changed/new readiness tests
were amended; the source-path contract was added. Two source snapshots and396ledger preserved.
New397ledger verifies394prior unchanged paths/two approved amended hashes/one new contract.
70changed/new model-free checks passed;59unchanged tests deselected. Pytest1.31s, supervised
1.715557s,365,084,672B sampled owned peak/24samples, workers reaped; zero forwards/optimizer/
actual arrays. Exact28script success/hash substitution, full397closure and launcher readiness
plus unsafe-path/file refusals qualify. All other dispatcher functions and producing files fixed.

N02 fresh preflight passed independent registered APFS UUID/writability/device/free guards,
AC/MPS/idle-owner check and held shared MPS lock. External device16777242/free2,866,266,128,384B;
internal device16777231/free118,011,367,424B. Backup baseline17,341,924,636B. Source closure397
verified. Native invented inputs/target geometry/controls prepared in4.62s under the5minute limit.
The frozen controls were separately reviewed before dispatch: request
`575603717131190f97ea7496e4ef0d4c0311ae5f9be0599658dad1c0671fd70b`.
Producer dispatched once; native cold recovery follows only a complete192producer. Shared lock
stays held through both. No original/cache/CT/third-party weight payloads; no scientific job.

Policy template is explicitly invented positive-only control, separate from D-335 or actual native
counts; invented-train-4 is negative and any inapplicable/poor-quality DUR-01 result stays recorded.
Engineering completion cannot establish model quality. Original192+1updates/253+31forwards/60min/
12GiB and26GiB whole/8GiBgrowth/100GiB floor/2GiBchild/4GiBphase/64MiBcontrols stay fixed.
Local N02 receipt `outputs/prowl/SEGMENTER-DURATION-NATIVE-N02-20261007/` contains preflight, frozen
manifest, independent control review and dispatch start. Active controls are in the exact registered
internal backup scope `segmenter-duration-20261007-n02-rehearsal-controls`; primary/keeper/restore
areas use that same approved namespace. No other lane was rebound. Preserve any consumed failure;
no retry/reset. N01 remains retired. Human hours unconfirmed; all unattended runtime excluded.

**Current restart:** monitor this one N02 session and retain its producer/cold outcome. Do not
dispatch another job or repeat completed checks. The earlier DUR-04 proposal/approval-pending
paragraphs below are historical; scientific launch remains a separate exact request after native
qualification.

**Readiness repair finished; native rehearsal has not started.** Quinton answered “I approve” to
the exact DUR-03 repair/conditional N02 question. The four-new/two-amended-file implementation
is complete. All60new model-free checks passed; no old suite or consumed attempt was replayed.
N01 remains operationally retired. N02 is unprepared/unconsumed and conditional on a separate
source-path guard repair described below. No native or scientific model calls occurred.

## Changes and evidence

- New `src/operations/segmenter_duration_readiness_v1.py` checks only the six approved historical
  hash transitions, consistent origin states, complete unchanged numerical closure and current
  byte identities. It independently pins the successful Oct3export manifest/log, portability
  result, exact storage amendment/old schema and relevant committed metadata dependencies.
- New `tests/test_segmenter_duration_readiness.py` checks acceptance, each old/current substitution,
  missing/unlisted sources, inconsistent CPU/native origin, every provenance hash/dependency,
  failed receipt states, real launcher runtime/fallback/readiness separation, unsafe file reads
  and the unchanged dispatcher refusal. Tests deny session construction and identity/model work.
- New `docs/capstone/imaging/SEGMENTER-DURATION-READINESS-CONTRACT-V1.md` records the closed scope.
  The launcher replaces only its historical equality assertion; the executor adds only the new
  module/test/contract to required closure. Two original files were byte-snapshotted before edits.
- The new396-entry producing ledger preserves313prior paths byte-for-byte, records two approved
  amended hashes, adds68unchanged historical paths and13other producing entries. Those13are the
  three new producing files and ten previously missing pinned portable metadata dependencies.
  All396current bytes match. Historical315ledger and all129CPU/native origin pins remain intact.
  Experiment-log tail remains `8c9246f1c74ef8c01b8265d3a537bd373d9a98e3338d215d9d74e7202bffb7dd`.

A001qualifies60checks in2.02s pytest time,2.491359s supervised elapsed,367,951,872B sampled owned
peak RSS,35samples; workers reaped. Two pre-existing Torch deprecation warnings. Zero model
forwards/optimizer calls/original/cache/target arrays, including preparation. Limits90s/2GiB.
The initial closure helper used system Python and failed on missing `jsonschema` before writing
closure evidence; changing only that helper to the configured `.venv-prowl` completed it. The
failure is retained; no install or test rerun occurred.

Local receipt: `outputs/prowl/SEGMENTER-DURATION-DUR03-20261007/`. It retains snapshots, approval
context, A001log/resources, provenance pins, closure reconciliation,396pins and dispatcher blocker.
These same-disk records are not an independent backup. No external areas/writers/actual controls
were prepared; no unchanged drive/AC/resource probe was repeated.26GiB budget remains settled.

## Next concrete amendment — DUR-04 proposal, not implemented

The new launcher check passes, but the existing dispatcher `verify_code` accepts only source roots
`src`, `tests`, `docs`, `requirements`, `configs`. The required396-entry closure contains28pinned
`scripts/diagnostics/*.py` paths, including `segmenter_duration_launch.py` itself. It therefore
refuses `Code pin cannot point to data/weights` before dispatch. The new negative integration
check demonstrates this existing defect. Removing script pins or routing around the verifier
would weaken source closure, so neither occurred. This is software integration evidence, not a
training result or a fresh N02 attempt.

Approve only this bounded follow-up:

1. Amend `src/operations/segmenter_duration_dispatch_v1.py` at `verify_code`: admit only the exact
   28script names listed in the retained `dispatcher-blocker.json`, each a `.py` file with its
   independently frozen request SHA256. Keep relative/non-traversing path, regular/single-link/
   non-symlink/read-budget guards and all other roots/suffix rules. No arbitrary scripts prefix.
   The fixed worker/CLI, authority, consumption, resource watchdog and process ownership stay fixed.
2. Amend `tests/test_segmenter_duration_readiness.py`: replace the demonstrated-blocker assertion
   with full396-entry verification success and add exact28script, unexpected-script, traversal,
   absolute-path, payload-suffix and hash-substitution checks. Run only changed/new node IDs,
   ≤90s/2GiB/zero model calls. Preserve the60check evidence and prior source snapshots; do not
   rerun the unchanged161DUR-02 suite or other unchanged checks.
3. Create `docs/capstone/imaging/SEGMENTER-DURATION-SOURCE-PATH-CONTRACT-V1.md`; update this handback
   and routine pointers/Trello/automation. Snapshot two amended sources, record exact before/after
   hashes and qualify the full actual source-verification/readiness chain without arrays/models.

The exact28names are the `scripts` list in the preserved396-entry verification record and blocker;
no more may be inferred. Other numerical sources, targets, storage, backup and dispatcher functions
are outside this amendment. After qualified DUR-04, continue the **already approved conditional**
fresh N02 preparation and one native rehearsal under the unchanged144³/MPS/192+1/253+31/60min/
12GiB limits. Approval of DUR-04 is needed because the dispatcher is outside DUR-03's six-file
allowlist; the original native approval does not authorize altering that pinned guard.

Stop on any further refusal and preserve it. Full native/cold success precedes a separately frozen
scientific request. No SuPreM use, data acquisition, capacity increase, deletion, retrieval/N4 work,
public push or scientific launch. Human active hours remain unconfirmed; runtime is excluded.

**Exact restart:** obtain DUR-04 amendment approval; repair and qualify `verify_code` on the entire
396-entry closure before generating144³inputs or preparing N02 requests/areas. N02 itself has not
failed, retired or consumed a request. Preserve every historical acceptance and failure.
