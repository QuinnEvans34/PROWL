# Reserved-patient prediction archive — approved inference stage

Launch verified October27: ownedexec60178, supervisor33052/worker12088
(wrappers66924/16836). RequestSHA
edd8824e401aad8e5d8aefbf228f876931f3e792caaa457a7b28b32ca38b6a31;3389pins.
Seven completed patient records verified:all6reused andfirstnew00000023,29.5s;
00000026started. All7archive/sidecar E/C hashes andrequestbackupmatch.
The full stage is still running, not a completed533archive. Do not redispatch.

User explicitly approved the October26 budget proposal on October27. This
authorizes one prediction-generation stage, not verifier scientific training.
No original cap is silently edited: the larger limits apply only to this new
versioned export supervisor and receipt. Older frozen configurations remain intact.

## Scope and limits

Exactly533reserved patients:266fit,67tune,200calibration. Reuse the six verified
pilot archives in place; generate527new predictions. No lesion-label reads,
development/test inputs, optimizer updates, threshold tuning or checkpoint
selection. Candidate components derive from the frozen hard multiclass output;
pancreas-provided regions and original floating-point probability export retained.

- Wall limit16hours; combined ownedRSS12GiB; GPU allocator/reserved limit6GiB.
- Combined existingcache+pilot+export+setup allowance64GiB onE:.
- Combined existing+new independent backup allowance40GiB onC:.
- Minimum100GiBfree onboth drives, including reservations before new archives.
- AC and exclusive GPU lock; Windows job supervision/reaping; no retry/resume.
- No background AI schedule, training-hour inflation or new MLflow training run.

## Implementation and tests

Additive scripts/diagnostics/export_verifier_candidates_20261027.py and
src/operations/verifier_candidate_archive_v1.py. Existing pilot, generator,
probability exporter and source loader remain unchanged.
48CPUtests pass48.57s, including original candidate/provider tests, role refusal,
capacity reservations, independent-device refusal, exactbackup, preserved partial
on copy corruption, missing/duplicate identity, reuse without inference, refusal
of existing dispatch/output, and mocksupervisor success/failure/resource limits.
Evidence tests.xml in the new setup directory. This is engineering evidence,
not a segmentation score or verifier efficacy result.

Prepare checks inherited producer hashes, actual fixedterminalcheckpoint identity,
completed generator review, pilot outcome, actual visual review, all six archives
and source/environment bindings. Request is frozen before one-shot dispatch.
Never alter its producing files afterward. The supervisor uses no label method;
fit-only pilot labels are stripped from the reused records in the new archive.

## Locations and continuation

Setup: E:/PROWL/readiness/verifier-candidate-export-20261027-a01.
Output: E:/PROWL/artifacts/verifier-candidates-20261027-a01.
Backup: C:/Users/quinn/PROWL-Backups/verifier-candidates-20261027-a01.

Commands are --prepare once, then --run-sha256 with exact request.json hash once.
Inspect all existing files/processes before either. Neither is a resume command.
Follow the same owned process if a stage already started; failed stages require
a user decision. Do not rerun the six-case pilot or original dataset audit.

progress.jsonl records case_started and case_completed. Completion is appended
only after the archive and its sanitized sidecar both have verified C: backups.
Reused E:archives remain at the pilot paths recorded in each sidecar. New E:archives
reside under the output directory. No duplicate E:copies of the six pilot archives.
Each archive is losslessly round-tripped, sha-bound and tied to source geometry,
CT/pancreas identities, generator receipt and role. Label arrays never enter it.

manifest.json COMPLETE_PREDICTIONS_ONLY accounts for all533patients, including
zero-candidate cases. It and the final journal are independently backed up.
Final completion additionally requires setup/resources.json success/exit0/reaped,
matching archive/sidecar/manifest backups and no pin changes. Progress alone is
not a full-stage pass. Initial launch verification must observe all six reuses,
at least one newly inferred patient and matching independent backups.

After successful complete-stage review: fit-only candidate sizing and truth-
component sidecars, representation/network design, training/restore qualification,
new verifier scientific receipt and explicit launch review remain required.
The67tuning and200calibration labels remain protected until their planned stages;
70development cases must not guide those choices. H0 remains untested.
