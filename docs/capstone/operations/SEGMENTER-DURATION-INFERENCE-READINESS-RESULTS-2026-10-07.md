# DUR-06 inference-only readiness handback — October 7, 2026

**Engineering delivered; focused I01 failed in its helper preflight. No inference certificate or
scientific launch.** Quinton explicitly approved DUR-06: “Yes, I approve of DUR-06.” The four-file
[closed contract](../imaging/SEGMENTER-DURATION-INFERENCE-READINESS-CONTRACT-V1.md) was implemented.
The one accepted native invocation stopped before checkpoint payloads, models or storage preflight.
This is an avoidable helper binding defect, not evidence that checkpoint recovery failed.

## Implemented and qualified

- Executor `validate_request()` admits separately named inference-only readiness with explicit
  `training_resume_qualified=false`; no restart, extension or real recovery updates.
- Launcher `validate_readiness()` authenticates the distinct certificate, historical producer,
  exact source lineage, runtime, unit and cold result, all five checkpoint probes and 25 exact
  native masks/views. Original full-readiness branch and `cold()` exact-replay assertion stay fixed.
- New fake-metadata test module and contract complete the four producing paths. 62 new model-free
  tests passed; pytest 1.39 seconds, supervised 1.804800625 seconds/373,932,032 bytes sampled owned RSS,
  25 samples, exit 0, workers reaped. Zero model/optimizer/array calls; no full-suite claim or replay.
- 402 current source/test/contract pins match: 398 prior paths unchanged, two amended functions,
  two new paths. Source-region review proves numerical code and everything outside the named
  readiness regions are unchanged. Historical experiment record is byte-identical to HEAD.

## I01 exact outcome

Frozen request SHA256 `c9a4596736a6ca5c1d2d958bf74d781158632da317384c1aa3d57b81964b145a`;
helper SHA256 `96fe58c61dde095a52207e1ca88c9b2996c1fc7dde01681cc1dfd328c2d30445`.
One native invocation was independently reviewed and accepted. It exited 1 after 1.370969042 seconds;
374,718,464 bytes sampled owned RSS, 19 samples, workers reaped, no watchdog stop.

At helper line 46, `pinned(**r['frozen_manifest'])` passed the literal metadata key `sha256` to a
function whose second parameter was named `pin`. Python refused with:

`TypeError: pinned() got an unexpected keyword argument 'sha256'`

The failure report's persisted counters are zero forwards, zero optimizer calls and zero retained
payload-member bytes. No checkpoint/probability/export/view read or check occurred. The failure
was before registry/storage/AC/idle/lock admission and before the consumption marker. I01 is
**operationally retired, not falsely marked disk-consumed**. The exclusive request/failure namespace
and logs remain; never rerun/reset it. No readiness certificate was created. No actual source,
cache, CT, third-party payload, external writer, backup copy, capacity change or training job.

The pre-dispatch inventory remains a projection, not completed read evidence: 62 retained invented
artifacts/1,554,717,069 payload-member bytes, largest 209,986,197 bytes. Original N02 producer proof
remains 192 updates/253 forwards; bit-exact continuation still failed. N02/D01/D02 remain retired.

## Corrected replacement prepared as an inactive proposal

The private helper draft names its hash-reader parameter `sha256`. Ten distinct failure-specific
invented-metadata checks reproduce the original error, verify positional and all six keyword
bindings, and refuse wrong hashes/oversized metadata. Successful check run 0.006514375 seconds,
33,996,800 bytes process RSS; zero models, arrays, checkpoint payloads or job dispatch. Two failed
regression-harness starts are retained: system Python lacked jsonschema; the first native harness
had an overbroad static detector that matched dictionary update(). The final harness distinguishes
session/optimizer calls. These are not extra successful test counts or scientific attempts.

**Proposed next approval: “Approve corrected I02”.** Concrete closed replacement:

1. Snapshot current 402 pins and three amended paths. In launcher `validate_readiness()` change
   only the receipt base, result directory and exact attempt literals to fresh DUR06-I02/I02.
   Keep its other predicates and every other function, especially `cold()`, unchanged.
2. Update the invented test fixture's attempt and add exact I02-result-path/I01-denial checks;
   qualify 64 changed/new model-free cases within 90 seconds/2 GiB. Amend the existing inference
   contract to record this replacement. 399 other producing paths stay exact; no old tests replayed.
3. Independently freeze/review **one** `DUR_INFERENCE_20261007_I02`, with new local unit/lineage
   receipts and output namespace; preserve all I01 controls, logs and failures. Corrected helper
   draft SHA256 `b5cdabd0d34c67199a5bb26e71674dc62098bd97db398d6db15fcf2daeb1eb26`.
   The tested hash-reader function is byte-identical; the draft requires the proposed 64-case result.
4. Fresh internal-volume/free/cap/AC/MPS/idle/shared-lock admission, then the same retained-invented
   62-artifact inventory: 30 forwards/zero updates, 600 seconds/12 GiB, 2 GiB reads/8 MiB local outputs,
   100 GiB free. No full producer repeat, new backup phase, cap increase or external writer.
5. On full success and worker/resource/source review, create only the distinct inference-only
   certificate. On failure preserve and stop. Real-data source/storage/request preparation and
   the scientific launch decision remain separate; optimizer resume stays unqualified.

This replacement is **unapproved/unprepared/unexecuted**. All three exact patch drafts and the
corrected helper are in the ignored DUR06 receipt; no I02 production changes or actual controls
have been applied. The next task is this concrete decision, not another full training subsystem.

## Preservation and restart

Ignored local evidence: `outputs/prowl/SEGMENTER-DURATION-DUR06-20261007/` and
`outputs/prowl/SEGMENTER-DURATION-INFERENCE-I01-20261007/`. Source snapshots, 400/402 ledgers,
unit qualification/resources, frozen request/helper/inventory, worker log/failure audit and
inactive replacement drafts are retained. Local Git preservation covers portable implementation,
tests, contract, this handback and routine pointers only; no private evidence or public push.

W01-28 remains incomplete/To-Do, explicitly blocked on fresh I02 approval. Parent W01-12 remains
incomplete. Trello readback and exact local commit receipt are recorded locally after preservation.
Hours are unchanged: Monday 4, Tuesday 5–6 estimated, Wednesday 09:00 open human clock; finish/pauses/
net participation await Quinton. Unattended work adds no credited time.

Exact restart: read this result and the inactive replacement patches, obtain the I02 decision,
then apply only that three-path amendment and qualify it before preparing any actual request.
