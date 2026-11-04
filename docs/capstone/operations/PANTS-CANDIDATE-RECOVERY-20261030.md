# Restore missing CT inputs and complete the candidate exports

**Closeout October31 06:22UTC: COMPLETE.** All533 predictions accounted for with
exact266fit/67tune/200calibration roles;178 newly exported,355 preserved. The
handoff verified every prediction/sidecar against independent backups, then
finished successfully. Final receipt backups match. Supervisor exit0/reaped,
10,645.204s,3,088,224,256BpeakRSS,1,042,284,544BGPUreserved. Aggregate attempts
30,548.689s remain within16h. No workers remain. ManifestSHA
`b5c989a158598e2aa3e3c6ecdaed5f0bf4b91803d0574b3250c5def473827aed`.
Hourly recovery monitor removed after completion; no scientific training launched.
Earlier progress entries below are historical. No recovery stage needs rerunning.

The fresh PanTS download completed on October30 at19:52UTC. This recovery uses
the same trained generator, patient roles, pancreas masks, geometry and prediction
algorithm as the interrupted October27 export. It does not train a new model or
test a scientific hypothesis.

355 of533 prediction archives were committed before loss of access toD:. The
remaining178 CTs require6,128,299,671 bytes and occur in four training archives.
Existing masks are onE:. Only these178 CTs are restored, with exact compressed
byte size and SHA-256 equality to their original recorded inputs. The test archive
is not read. Original failed evidence and all completed artifacts remain intact.

## Gates and order

1. Stream the four archives into a new178-case source directory. Fail on missing,
   duplicate, unsafe, wrong-size or wrong-hash members. Two-hour bound; no retry.
2. Verify the original3389 pins and all355 prediction/sidecar pairs against their
   independentC: backups. Check that unfinished cases have no uncommitted outputs.
3. Test the additive relocation provider and continuation. Retain original mask
   identity/alignment, protected roles, preprocessing and native geometry checks.
   Deny lesion labels and cases outside the178 remaining membership.
4. Prepare a separate receipt: check all178 CT hashes and CT/pancreas headers;
   fully read and preprocess the previously failingPanTS_00005914 on CPU and
   compare its geometry with the frozen qualified cache. Freeze new code, tests,
   restoration and prior audit evidence alongside all inherited pins.
5. Dispatch the new continuation once using its exact receipt hash and exclusive
   GPU lock. Keep the original aggregate16h export budget by subtracting the
   failed attempt's19,903.485s. Preserve12GiB ownedRSS,6GiBGPU,64GiB cache/export,
   40GiBC-backup limits and100GiB free-space floors. Restored source data is
   separately bounded at7GiB. No retry, exclusion or scientific training.
6. Verify newly advancing exports and independent backups. On normal completion,
   require a merged533-patient manifest, complete backups and reaped workers.
   Verifier design/qualification and scientific launch remain separate next steps.

## Evidence locations

- Restoration: `E:/PROWL/sources/pants/restored-candidate-ct-20261030`
- Prior audit: `E:/PROWL/readiness/verifier-export-recovery-20261030-a01`
- Continuation receipt: `E:/PROWL/readiness/verifier-candidate-continuation-20261030-a01`
- New predictions: `E:/PROWL/artifacts/verifier-candidates-20261030-a01`
- New independent backups: `C:/Users/quinn/PROWL-Backups/verifier-candidates-20261030-a01`

At this entry restoration and prior audit are running. No readiness receipt or
GPU continuation has been created. No MLflow training run or training hours are
added for this inference-only recovery.

Update01:56UTC: prior audit completed0 in372.515s, all355 independent backup
pairs verified.48CPU tests pass15.22s. The failed5914CT matches its originalSHA.
Local one-shot `handoff_candidate_recovery_20261030.py` is active (owned88958),
waiting for the existing restore process37484 to exit successfully. It bounds
CPU preparation at1800s/12GiB, checks readiness, dispatches one exact-hash
continuation and verifies the final merged533 backups. It inhibits idle sleep,
requiresAC and stops on failure without retry. No recurring task or AI polling.
Do not manually invoke a second preparation or launch. Preserve new producing
files while this handoff is live; inspect handoff.jsonl for its current state.
