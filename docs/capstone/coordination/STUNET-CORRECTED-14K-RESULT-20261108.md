# Corrected STU-Net: first complete70-case validation

Global14000 /2000new updates; raw native evaluation completed in93.14minutes. All70IDs/reference counts match parent, zero reconstruction gaps, report/independent backup hashes match. Training continues unchanged.

| Metric | Parent12k | Corrected14k |
| --- | --- | --- |
| Positive macro Dice | 0.371633 | 0.353488 |
| Positive macro recall | 0.541016 | 0.505244 |
| Pooled voxel recall | 0.527570 | 0.513336 |
| Positive case hits /36 | 35 | 32 |
| Reference component hits /45 | 41 | 37 |
| Empty-case alarms /34 | 27 | 30 |
| False-positive volume mL | 382.515 | 491.703 |
| Small-case macro recall (5 cases) | 0.464489 | 0.333254 |

This first result is worse on Dice, case detection and empty alarms than parent12k. It is an interim result after only2000new updates, not a final hypothesis verdict or proof of the cause. Keep the frozen run and selection unchanged.

JSON contains exact per-case raw counts, source/reference bindings, size strata, macro and pooled recall definitions and parent comparison. Scalar counts cannot locate FP components; predicted components on positive cases are not automatically false components. No5mm postprocessing was applied. Future models must bind the standing5mm policy with paired raw/filtered qualification and raw fallback; no retrospective rewrite here.

Raw report SHA256 `044dcd30400f8896a144b18921b3d40d4df135986f6635c7ca2a4c98b76aa3ee`. Export JSON SHA256 `07ceb2b660036fb3222523cdf6cbcad8294186fc023919805575a77fc49e9a40`. No model/CT/mask reads or new inference.
