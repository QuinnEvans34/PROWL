# D-301 — versioned session and independent recovery passed

Implemented a separate 144³ readiness session and checkpoint codec without changing older consumers.
The identity binds cache completion, input/source/environment hashes, config and processed-grid
sampling policy. Real sessions reject optimizer updates. Synthetic updates accept no external image:
they create their fixture internally. Cache inference checks the persisted identity and removes extra
patch padding before returning a processed-grid prediction.

Checkpoint decoding uses weights-only CPU deserialization, a new state version and exact inventories.
It rejects nonfinite or wrong-shape/dtype model tensors, optimizer-policy/history changes, scheduler
position drift, changed controls, wrong identity and nonzero real-readiness steps. Synthetic optimizer
state is restored into a fresh session, then moved to MPS when requested.

## Verification

1,406 native tests passed (18 new; two existing upstream warnings). Scoped tests cover rejection paths,
cache identity changes, unpadding, real-update denial and deterministic nonzero continuation with a
small test model. Native rehearsal uses the actual production SegResNet and full144³ sampler/network.
Full test output: `/tmp/prowl_d301_tests.log`. Scoped `git diff --check` passes.

Native MPS, fallback0, float32, workers0, threads2:

- Two generated-fixture updates; step2 checkpoint saved to the registered external artifact root and
  independently backed up on the internal device. Producer performs one further synthetic update.
- Fresh recovery process prohibits primary-drive reads, resolves the independent backup into a new
  restore artifact, and repeats prediction and the next update. Exactly four synthetic optimizer
  calls total (producer3, restored1); zero real cases or real updates.
- Prediction maximum difference: **0**. Next crop trace exact; next loss difference: **0**.
  Maximum next-weight difference: **7.450580596923828e-9**, below the1e-6 limit.
- Producer13.094s total, peak RSS1,103,609,856bytes (1.028GiB).
  Recovery6.425s total, peak RSS996,999,168bytes (0.929GiB).
  Maximum sampled MPS driver5,177,671,680bytes (4.822GiB). Driver samples are stage-end observations,
  not an allocator peak. Independent memory, power, time, output and free-space guards stayed within limits.
- Prediction did not change model weights. All local receipt members rehashed independently after
  completion. No active job remains; no automatic repetition or training request is pending.

## Retained evidence

Producer: `outputs/prowl/twomm-session-e40e21a0-334e-4b1c-879f-f8a827236c05`.
Receipt: `b03055add52d0dd01dbb9c93c7d11b26d3bd3f5ee39e1dbcd81bf61233941a24`.

Recovery: same directory name with `-recovery` suffix.
Receipt: `2906ab5aee17f75eb6bbcfbb59fd13d4ea5a19d1f35dc3cbb11bbf8d26cb0935`.

New restore artifact: `restore:6051405f-4d3b-48a3-8922-b86a31c7211e`;
completion `540c4249323b33b546d0df218217dc160d12b7ab1b6e94cbd75a1687a6469e0d`.
Primary and backup references are retained in `references.json`; full source/environment controls are
inside each checkpoint. No primary-unplug claim: primary reads were blocked by the recovery process.
The rehearsal proves recovery from a completed boundary, not survival of an actual mid-kernel OS kill.

## Next

Implement/test and freeze the [real-cache pilot packet](TWOMM-INFERENCE-PROFILE-PACKET-2026-09-30.md),
then run8 edge cases and, after review, the remaining145. D-300 cached inputs remain unchanged.
Real full-volume inference, source-grid exports, actual-cache-bound recovery and native-reference
measurement access remain before launch. This step did not assess model learning or generalization.
