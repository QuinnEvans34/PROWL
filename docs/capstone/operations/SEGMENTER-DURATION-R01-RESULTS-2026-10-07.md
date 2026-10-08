# R01 controlled real-data training — October 7, 2026

**R01 finished with a scientific quality stop at update 48.** Actual training completed 48
optimizer updates, eight per training member, and saved checkpoints 0 and 48. The first native
screen failed lesion coverage requirements. Its six exports/views, screen, summary and two
checkpoints were independently restored: 16 artifacts. Both workers exited/reaped, the helper
finished and the shared lock released. Nothing is running or pending within this attempt.

**The 192-versus-48 duration question remains unanswered.** Training did not reach 96/144/192;
report-only 2514 was not evaluated. Preserve this early stop as a failed quality outcome, without
model promotion, criterion changes or an automatic retry/resume/extension. The actual scientific
training path worked; no runtime exception or watchdog stop was reported.

| Training native metric | Retained D-335 at 48 | R01 at 48 |
|---|---:|---:|
| Pancreas macro Dice | 0.159877 | 0.181887 |
| Lesion macro Dice | 0.055142 | 0.058952 |
| Lesion macro recall | 0.833063 | 0.691498 |
| Mean lesion false-positive volume | 162.628931 mL | 111.866668 mL |

The lesion recall floor was 0.803063 (baseline minus 0.03, also above the 0.80 absolute floor).
R01 fell below it. Lesion/component recall losses also exceeded 0.10 in cases 3, 26 and 5821.
All six components still had positive hits; tiny-case 2973 recall stayed 1.0. Every interim
per-case lesion false-positive check and pancreas coverage check passed. Better overlap and
lower lesion excess volume did not satisfy the unchanged coverage gate. Independently computed
confusion-matrix metrics agree with the recorded assessment and scoring oracle.

All six generated contour sheets were visually reviewed. Predictions still extend well beyond
the reference contours, including disconnected foreground regions; selected slices in cases
26 and 5821 show incomplete lesion overlap. These selected display slices support inspection;
the full-volume native counts determine the coverage result. No clinical interpretation or
broad model-strength/generalization claim follows from this small provided-ROI cohort.

## Authority and start

Quinton explicitly answered: “Yes, I approve this: Do you approve R01 real-data training under
that packet?” He quoted the final launch question and asked whether training starts now. This
authorizes the [reviewed R01 scientific packet](SEGMENTER-DURATION-R01-LAUNCH-PACKET-2026-10-07.md).
Actual request-bound authority preserves the full supplied text; SHA256
`d93ec0e2b06f760651d557e224dffecb98f2e858373b10cc639a491282349c45`.
Request SHA256 `60f3cc516f4d5a6be3337080df5ab5643592f23bb91b2e550f6ac6402ad067a8`.

The unchanged helper0e6a17e8 was invoked once through native approval review. Fresh402source pins,
inference certificate/runtime/AC/MPS/idle ownership, independent registered APFS volumes/UUIDs,
free space, namespace absence and fixed budget admission passed. Current backup19,624,209,117 B;
internal free115,145,076,736 B, external free2,864,653,803,520 B. Shared accelerator lock is held
across this one producer and conditional cold. Native controls/absolute command were independently
reviewed before `DISPATCH_R01` was entered once. Storage authority SHA256
`a96930a3a075b41d433a9710aed3d7c6cf6f0ffac68d9fd821b8cf45f360d820`.

Producer dispatch consumption records epoch1791416934.1447182 (17:48:54MDT). Input validation
preceded actual updates; dispatch is distinct from the first completed model update. Owned helper
execsession12310 has finished. Do not poll it as live, replay a stage or take over an old PID.
Quinton's approval was used for this one attempt and does not authorize another invocation.

## Fixed scientific scope

Fresh scratch SegResNet seed42, fp32/MPS144³ provided-pancreas ROI, unchanged v5loss/AdamW0.0003/
weight decay1e-5/constant schedule/no jitter. PanTS3/26/2232/2973/5821/6238 remain training members;
2514 remains terminal192 report-only and selects nothing. Checkpoints0/48/96/144/192; all six
native screens48/96/144/192 with report-only2514 added at192. Compare terminal192 with retained
D-335 terminal48, without selecting an interim best or altering case roles/holds/difficult cases.

Unchanged DUR-01 coverage/component/tiny/false-foreground stops are active. Maximum192producer
updates/253forwards and conditional cold30forwards/zero real updates;50original pancreas/lesion
target logicalreads across12+12+12+14, zero original CT, accepted cache104,509,440 B separate.
Hard60-minute total/12GiB ownedRSS/MPSdriver/AC/100GiBfree; fixed26GiB whole backup/original
17,341,924,636 B baseline+8GiBnew across spentN02 and this one real attempt;2GiBchildren/4GiBphase/
64MiBcontrols. Preserve all existing and partial artifacts; no deletion/pruning or capacity increase.

I03 qualifies saved inference recovery only. Optimizer resume is unqualified, the original
bit-exact next-update failure remains retained, and small finite differences are not declared
harmless. No automatic retry/resume/extension/sweep/follow-on. This small provided-ROI cohort
does not establish broad model strength, negative specificity or an autonomous baseline.

## Evidence and exact current point

Local receipt `outputs/prowl/SEGMENTER-DURATION-REAL-R01-20261007/` contains native preflight,
independent control review, exact frozen controls/command and dispatch review. Registered controls
are under `segmenter-duration-20261007-r01-real-controls`; the journal/worker/result files are
written there by the scoped dispatcher. Authority review is separately retained under
`outputs/prowl/SEGMENTER-DURATION-REAL-APPROVAL-R01-20261007/`.

### Actual accounting and recovery

- Producer: **68 forwards/48 optimizer calls**; all six members eight updates each. Twelve
  original target logical reads at screen48; 1,173,533 B hashing plus 1,173,533 B decoding and
  253,698,624 B expanded. Zero original CT reads or third-party weight imports. The unused
  later-stage portion of the 50-read maximum does not authorize continuation of this spent job.
- Cold: `stopped_checkpoints_restored`,16 independent restores, **zero forwards/zero updates**,
  zero original targets/CT. It validates kept checkpoint/export/view/screen/summary payloads;
  it does not rerun predictions or prove full 192-step recovery. `full_duration_qualified=false`.
  I03 inference readiness remains separate; optimizer continuation is still unqualified.
- Producer supervised545.335811750 s, sampled owned RSS4,870,045,696 B,worker reaped.
  Cold35.344273042 s/RSS2,573,090,816 B,reaped. Helper654.297250625 s/aggregate sampled
  owned peak5,611,421,696 B; no watchdog error; shared lock released. Worker-side transaction
 362.236527 s excludes input/provider resolution; do not confuse it with total elapsed runtime.
- Whole backup20,031,773,929 B; R01 growth407,564,812 B; total rehearsal-plus-R01 growth
 2,689,849,293 B from original17,341,924,636 B baseline. All fixed ceilings remain satisfied.
  Fresh metadata inventory: primary203,582,876 B/82files; keepers203,641,744 B/129files;
  restores203,640,237 B/129files; controls282,831 B/13files. Internal free114,688,000,000 B,
  external free2,863,104,000,000 B; both above100 GiB. No deletion/pruning or new capacity.
- All402 producing pins still match. No production code, numerical recipe, policy, source
  membership/roles/holds, original array or historical failed result was changed during execution.

Both producer and cold requests are consumed; R01 is operationally retired. Its final transaction
SHA256 is `86237e5eccbdb6fe436abc36a3bb0810b116a17745b00079fba7fbbd53d7e461`;
cold result `df204634cdd38ddd45f5e91c1986aba8439fa09743becffbb36192d439b00e3c`.
Local `result-review.json`, `history-review.json`, `final-inventory.json` and
`protected-pins-final.json` retain independent arithmetic, metadata comparison and accounting.
Machine-specific controls/payloads remain private; no independent backup claim for local receipts.

### What the retained history establishes

A model-free comparison of kept JSON histories found **the exact same 48 member sequence and
image/target batch-hash sequence** as D-335. The first loss matches. At update2, losses differ by
4.76837158203125e-7; subsequent losses diverge. Architecture, loss, precision, seed, sampling,
learning rate, decay and jitter declarations match; the request changes the session schema and
maximum steps 48→192. No weights were opened and no extra model/optimizer/source-array calls
were made by this comparison. Device numerical variation, an execution difference and their
significance remain unproven causes. Do not attribute this result to additional training: both
observed screens are at48. Do not infer that the earlier small replay differences are harmless.

**Exact next starting point:** review this coverage/false-foreground tradeoff and whether the
prospective early-stop design answers a fresh-duration question, together with the retained
history divergence. Decide a new concrete scope before another model run or policy amendment.
There is no demonstrated coding defect requiring a new implementation packet at this checkpoint.
Do not change acceptance just to label R01 successful, reopen its payloads for an unapproved
diagnostic, retry it or launch an overnight sweep. Dataset expansion remains necessary for a
convincing broader model, and SuPreM stays parked pending source evidence. W01-28 can be Done
for this finished attempt with the failed quality outcome explicit; the overall training goal
and parent W01-12 remain incomplete. Human hours are separate from runtime; no public push.

Tracking readback verified: W01-28 is titled “R01 stopped at 48; recovery complete”, in Done
and marked complete. Its description retains the quality failure and historical launch record;
Done records completion of this attempt, not success of the 192-update comparison.
