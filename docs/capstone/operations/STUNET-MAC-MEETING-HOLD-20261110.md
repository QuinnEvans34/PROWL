# Mac experiment held; live expert restored — November 10

At the user's request, remaining Mac experiment work is held for their return home. No successor or automatic restart is armed. Lenovo training was not changed.

The primary terminal-24k inference-policy study had already completed all 70 cases and 54 settings. Its verified closeout and independently replayed backups are recorded in [the results](../evaluation/STUNET-24K-MARGIN-RESUMED-RESULTS-20261110.md) and commit `b81ee4d`. MLflow `5ece75b524484d8c94391228acfabebd` is FINISHED. Raw Dice is 0.411971; standing 5 mm Dice is 0.428578; the guard-qualified exploratory seed/grow candidate reaches 0.432626. No policy was deployed.

## Secondary CPU stage

The six-setting voxel-clipping follow-up started before this request and stopped safely after its two largest pilot cases. Its projection of 2,060.35 remaining seconds exceeded the 1,142.33 seconds available under its separate 20-minute cap. This was a runtime qualification failure, not a completed six-setting comparison. No retry or cap increase was made.

Evidence remains at `/Volumes/PROWL-Data/PROWL/artifacts/stunet-margin-mac-20261110/screen-02/voxel-clip-01/`, including `qualification.json`, `worker-failure.json` and `resources.json`. The supervisor recorded 59.16 seconds, peak owned RSS 2,092,728,320 bytes, all workers reaped and no survivors. Preserve both pilot records. A later additive CPU-only continuation needs a revised bounded time decision; the original active allowance and deadline must not silently reset. It needs no repeated model inference.

Removed the stopped `com.prowl.stunet-voxel-clip-20261110-02` registration and completed `com.prowl.stunet-margin-closeout-20261110-04` helper. The primary GPU registration was already removed by its verified closeout. At 13:49 Mountain, no experiment worker or matching launchd registration remained.

## Meeting readiness

Prepared the existing local expert through the UI's `/local-expert/prepare` endpoint. Status reports database, search, Ollama and model ready, no competing GPU owner, and no answer blocker. The intended live-answer service is PID 20776, start November 10 13:47:21, port 8016; process identity was checked. Existing battery authorization still applies to interactive answers only.

A live request through `http://127.0.0.1:5180/literature-search/answer` asked “Why can pancreas boundaries be hard to outline on CT?” and returned `generation=completed`, `status=summarized`, with bound citations. Measured end-to-end HTTP time was 3.709394 seconds; service retrieval was 0.454 seconds and total service time 3.053 seconds. This verifies availability and latency for one question, not comprehensive answer quality. The prompt, pinned model and retrieval configuration were unchanged. The live expert remains available for the user's own meeting checks.
