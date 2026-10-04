# CAP-EXP-003 result — lower LR passes the small learning indicator

The D-278100-update comparison completed under D-277 overnight autonomy. Only LR changed from
CAP-EXP-002 (0.003→0.0003); same balanced loss, data, scratch seed, horizon and all100 crop traces.
Source/environment remained unchanged during execution. Mechanics and independent recovery passed.
**The preset indicator passed, but the contours remain poor and substantially oversized.**

| Case | Balanced loss before→after | Original loss after | Dice after | Prediction/reference voxels |
|---|---|---:|---:|---:|
| 3 | 1.838895→1.168853 | 1.286924 | 0.115384 | 45,505 / 2,786 |
| 26 | 1.775748→1.166057 | 1.296233 | 0.104487 | 60,265 / 3,322 |
| Mean | 1.807322→1.167455 | 1.291578 | 0.109935 | — |

Mean Dice gain0.108959 exceeds0.10 and the balanced objective decreases by more than10%.
This is a minimal learning/wiring criterion, not a useful-contour or generalization gate. Compared
with CAP-EXP-002, Dice roughly doubled, while balanced terminal loss was almost unchanged. Absolute
loss alone therefore obscures an important difference. Final predictions remain16–18× target volume;
inspected overlays show broad regions around the references. No threshold or best-checkpoint change.

Run `localizer-smoke-3f38fe90-2665-4935-81b3-00568a3ee51e`.
Receipt `bc9131fd77383ed3e2ef5cdd095cfaf61637556ce0ce2451132b1657a83ab7f9`.
Request `2e04914fa5daf14d153a2a674ac58ad0d770a937191c888cfb91bda06fa6958a`.
Authorization `34ada1dcc0b1b607e400127e8d0c90eab13a969916303b011b13153cb08ce245`.
Terminal `216256793a5a3ed6214ddfc3c2d6341d0c232fcddcb54fc0762266a45d3c642d`.
Backup `bbb256f4775a52eb98ccce2a0840e78bab23af1e7b2c454c6787c4f400df41bd`.
Restore `08eb1521a9bb12dbff5812f0fdf4ee1391b28d68cce9535904c561af8f6ace29`.

Whole attempt257.74s; sampled RSS3,847,028,736 bytes; boundary MPS driver2,475,524,096 bytes, overlapping.
Restored probe difference0; original scratch digest verified; all100 crop traces match CAP-EXP-001.
No original result overwritten, useful model claim, wider cohort, validation/test access or retry.
1,087-test native code baseline.

Next bounded choice: keep the lower-LR balanced recipe and test300 fresh updates with cosine T_max300.
This is a duration plus matched-schedule-horizon comparison, not proof that raw update count alone
causes any difference. Keep existing600s update/1,200s total ceilings. One such run is the final
planned overnight compute action; inspect its result and leave a morning handoff rather than keep
searching recipes indefinitely.
