# CAP-EXP-002 result — foreground recovered, extensive overprediction

D-277 overnight comparison completed100 updates. Same scratch digest and all100 crop traces as
CAP-EXP-001; only training factor changed was equal foreground/background CE weighting. Ten full-
volume evaluations/probes were observational. Mechanics, checkpoint publication, independent backup
and fresh-process restore passed. **Learning criterion failed**, despite substantial balanced-loss
reduction: final mean Dice0.054974, below the required0.10 improvement over0.000976.

| Case | Balanced loss before→after | Original loss after | Dice after | Prediction/reference voxels |
|---|---|---:|---:|---:|
| 3 | 1.838895→1.166986 | 1.209314 | 0.056223 | 96,319 / 2,786 |
| 26 | 1.775748→1.166903 | 1.220789 | 0.053725 | 119,079 / 3,322 |
| Mean | 1.807322→1.166945 | 1.215052 | 0.054974 | — |

Mean foreground probability inside/outside target was0.8663/0.1645 and0.8781/0.1764. The final
contact sheets were inspected: predicted foreground covers broad tissue regions surrounding the
reference, not a useful pancreas outline. Prediction volume is roughly35× reference. This supports
that class weighting changes foreground pressure, but does not establish a good loss recipe. The
original objective value cannot be compared directly to the new balanced objective; both are retained.

Mean Dice at25/50/75/100 was0.02579/0.04948/0.03343/0.05497. No intermediate checkpoint was selected
as a replacement outcome. No threshold tuning or extension occurred. Before metrics and initial
weights match the first experiment; all100 sampled traces match exactly. Source/environment were
rechecked unchanged after execution.

Run: `outputs/prowl/localizer-smoke-414075aa-761e-443f-bf5d-cab30d79843a`.
Receipt: `c4991d60f045ba24ca29b02ccf0e6915134ad323de49425cf49216ffb1a4e65a`.
Request: `51e7bf8afc41375284634532ae4c5e9ce26ee0c8aa83698ab3a8cf5cc5cb7287`.
Authorization: `5607d7766a385e3d7a57aca0a4b758dd2cd032e8fb99df4790b2f3b7ed557dbf`.
Terminal completion: `3806dd318ed0e769178bcc27ffd177e9cdd4b629f9a91d7c8d7027bf5ed0a574`.
Backup completion: `9aaad49221cd6855eac577a08226fb731535266e2fb62b46e14d68098e371853`.
Restore completion: `7ce10111c4d6b1ffc7e65e7a8c945d4dd8e14ab3a95c29aef2349a28f7766d2d`.

Whole attempt256.10s; sampled RSS3,638,673,408 bytes; boundary MPS driver2,475,524,096 bytes (overlap,
not additive). Restored fixed-probe difference0. All limits held.1,086-test native baseline.

Next, under Quinton's overnight authority, isolate a tenfold lower LR with the same balanced loss,
100-step horizon and all other settings. This tests step size, not class weighting again. A separate
CAP-EXP-003 plan and pinned request are required before its one fresh run. Do not infer that lower LR
will help from the oscillating Dice alone. No model is promoted as a trained localizer.
