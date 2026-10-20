# Saved model candidate comparison

**Decision:** Do not prefer raw step8000 over step6000 for a new local measurement run.
The predeclared recall condition fails. AI-05 remains open; no checkpoint, runtime or guard changed.

Quinton authorized the evidence-only request to *Plan capstone experiment workflow*. Before inspecting
quality, that owner selected step8000 as the highest fully completed raw native report from
`pants_pancreas_region_24k_20261019`. The inventory contained2k/4k/6k/8k reports. There was no subsequent
candidate substitution, EMA comparison, new inference or training change. This is a development
selection decision, not a training-stop recommendation or independent benchmark.

## Matched results

Both reports contain the same70 cases:36 positive references and34 annotation-empty references,
with identical target counts, native voxel volumes and reconstruction metadata. No missing outcomes.
Volumes below convert saved mm³ to mL; pancreas is the producer's separate pancreas class, not a
claim of complete organ volume. Empty annotations do not establish healthy scans.

| Measure | Raw6000 | Raw8000 |
| --- | ---: | ---: |
| Positive lesion recall, mean | 44.88% | 25.74% |
| Positive lesion recall, median | 38.36% | 17.22% |
| Positive cases with any lesion overlap | 33/36 | 28/36 |
| Mean positive lesion Dice | 0.2175 | 0.2397 |
| Empty references with any predicted lesion | 34/34 | 32/34 |
| Total false-positive lesion volume, empty references | 333.395mL | 82.986mL |
| Mean false-positive volume, empty references | 9.806mL | 2.441mL |
| Mean absolute lesion volume error, positive references | 9.985mL | 4.163mL |
| Mean absolute pancreas volume error, all70 | 55.062mL | 46.990mL |

Less overprediction improves several aggregate metrics, but the recall decrease fails the
[declared selection rule](MODEL-AND-PANORAMA-HANDOFF-2026-10-20.md). Mean recall also decreases in
every positive size group: small5cases42.51→26.69%, medium24cases51.99→28.34%, large7cases22.20→16.13%.
Large-lesion mean absolute volume error worsens8.152→9.555mL despite the better pooled average.

The fixed subset remains unchanged. Lesion recalls for29/84/927 are91.69→53.32%,99.66→98.59%,
and5.91→15.72%. Empty-reference FP volumes for139/514/698 fall6.021→4.137mL,10.600→2.050mL,
and6.874→1.546mL. Case139 has producer metrics but remains excluded from the prior Mac run by its
size limit; this report does not erase that exclusion or imply a new Mac prediction.

## Coverage and provenance limits

The reports do not retain native predicted boundary contact, surface/diameter errors or adequate
whole-organ coverage judgments. Zero reconstruction gaps only describe the tiled inference region.
Case698's previously observed CT-boundary contact stays unresolved. Source-provided pancreas
assistance and reused development data remain explicit; this is not autonomous segmentation.

Baseline checkpoint SHA: `ac50b534eb5e5334bfb29626743ed626a1d16363d8ac1c3374165140318f397f`.
Candidate path is `execution/step-008000.pt`; **its checkpoint digest was not retained in consulted
metadata**. The owner verified uninterrupted raw-run lineage and journal/report agreement, without
opening weights. No claim of a hash-bound candidate checkpoint or CUDA/MPS voxelwise equivalence.

Baseline report SHA: `c70d3fd952efbbec3dffb1dd7fb6428f243927761c6b21cdd921ec4a22b0398f`.
Candidate report SHA: `7cdec25c143feca7154f7a41fc122d02f1db79896bd52f15e4d072c33dc868f9`.
Received receipt SHA: `bd6520f106b509c84fb2997f24cff599be6f15f60b9e65f497ae91900e91ac05`.

The original137,189 bytes were transferred through16 numbered base64 chunks and verified on Mac.
`scripts/diagnostics/reconcile_model_panorama_handoff_20261020.py` independently recomputes summary,
stratum and subset arithmetic, verifies70-case membership, count/Dice consistency and matched
reconstruction. It reads only the hash-bound saved receipts; no arrays, models or protected tests.
Original evidence and `local-reconciliation.json` remain in
`outputs/prowl/model-panorama-handoff-20261020/`; the portable aggregate is recorded under
`configs/evidence/evaluation/model-panorama-reconciliation-20261020.json`.

## Next decision

This requested comparison is complete with a rejected candidate. Do not lower the recall rule or
run another local checkpoint merely because Dice improved. A future comparison must name a new
completed candidate before inspecting its outcomes, retain the same multidimensional measures and
resolve checkpoint identity/coverage before promotion. No additional owner message or run is
required to close this evidence checkpoint. Reliable measurement acceptance itself remains open.
