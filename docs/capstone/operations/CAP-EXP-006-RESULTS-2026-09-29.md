# CAP-EXP-006 results — sustained learning exposes validation coverage loss

D-287 authorized one sustained experiment. **Completed2,400 updates and stopped**, exactly150
updates per each of16 training members, zero validation optimizer members. All35 artifacts were
independently backed up and restored; final fixed-probe difference0. No pending run, automatic
resume, extension or permission to repeat the consumed request.

## Outcome and decision

The experiment materially improved mean Dice and reduced excess foreground, but **failed both
predeclared coverage safeguards**. Record it as a tradeoff, not an accepted localizer improvement.
The final checkpoint is a retained research artifact, not promoted for autonomous ROI use.

| Metric | CAP-EXP-005 final | CAP-EXP-006 final |
|---|---:|---:|
| Train mean Dice |0.1262|0.7481|
| Development-validation mean Dice |0.1512|0.4529|
| Train mean mask recall |0.9867|0.9697|
| Development-validation mean mask recall |0.9490|0.4606|
| Train median predicted/reference volume |13.08|1.50|
| Validation median predicted/reference volume |12.56|1.09|
| Train provisional ROI screen |13/16|16/16|
| Validation provisional ROI screen |9/11|2/11|
| Strict fit screen |0/27|1/27 (training case3188)|

Primary final validation Dice gain **+0.30168** exceeds the+0.05 practical bar, but mean validation
recall falls **0.48847**, beyond the permitted0.02 drop. Seven validation boxes newly fall below
99.5% reference coverage:1004,2942,3104,5747,7265,7484,7839. Three validation boxes exceed25% scan
volume:7482,7687,7839. Case7839 fails both, giving9/11 total ROI failures. All27 masks are nonempty.
All11 validation Dice values improve versus CAP-EXP-005; the coverage failure is nevertheless real.

Near-unity total volume is not evidence of good alignment or complete coverage: missed pancreas
can coexist with false foreground elsewhere. The ROI screen uses the same all-component argmax
mask box and10mm requested margin as before. No threshold or margin was tuned after seeing results.
No lesion containment, source-wide complete-organ coverage, expert acceptance or clinical claim.

## Learning curve

| Updates | Role | Mean Dice | Mean balanced loss | Mean recall | Median volume ratio | ROI pass | Strict fit pass |
|---:|---|---:|---:|---:|---:|---:|---:|
|0|Train|0.0006|1.8103|0.0120|30.95|0/16|0/16|
|0|Validation|0.0009|1.8077|0.0133|28.38|0/11|0/11|
|288|Train|0.1540|1.0650|0.9783|10.40|14/16|0/16|
|288|Validation|0.1644|1.1410|0.8945|10.34|8/11|0/11|
|800|Train|0.2832|0.8705|0.9890|5.40|11/16|0/16|
|800|Validation|0.2772|1.0984|0.8113|5.65|7/11|0/11|
|1600|Train|0.6743|0.4614|0.9477|1.55|15/16|0/16|
|1600|Validation|0.4705|1.7775|0.5282|1.24|3/11|0/11|
|2400|Train|0.7481|0.3584|0.9697|1.50|16/16|1/16|
|2400|Validation|0.4529|2.2517|0.4606|1.09|2/11|0/11|

Between1600 and2400, training Dice rises0.6743→0.7481 while validation Dice falls0.4705→0.4529;
validation recall falls0.5282→0.4606 and balanced loss rises1.7775→2.2517. This is consistent with a
small-cohort generalization gap and late overfitting; this single run cannot uniquely identify its
cause, prove convergence or establish an ideal horizon. Step1600 is not retrospectively selected
or promoted as the winner. The frozen endpoint remains2400.

The duration question is now informative: insufficient training contributed to poor training fit,
but more training on these16 members does not by itself yield a high-recall validation localizer.
CAP-EXP-006 also changes cosine horizon288→2400; it is not identical learning-rate history.

## Visual and difficult-case review

All27 exported three-plane processed-grid overlays were reviewed in three contact sheets; enlarged
views of validation3104,7484,7687 confirm visible missed reference regions and, for7687, distant
foreground. Training predictions generally overlap the displayed reference more closely. This is
limited engineering review of selected planes, not every source slice or radiologist acceptance.

Partial/boundary training cases3717/4965 remain, with final Dice0.551/0.439 and volume ratios2.48/3.56.
Noisy8037/8443 remain, with Dice0.861/0.888. Case6350 is still held. No member was removed, replaced,
reclassified or made eligible based on model results. Original membership and issue history remain.
Validation lacks arterial/thin-slice coverage; biological patient identity remains the previously
recorded study-as-subject limitation. Publisher-test inputs were not used.

## Execution and recovery

- Same frozen16/11, exactly54 qualified source files, unchanged model/loss/preprocessing/sampler.
- Fresh frozen seed42 initialization, native MPS fp32/fallback disabled,2400 updates/150 per member.
- Full27-case evaluation at0/288/800/1600/2400; checkpoints0/400/800/1200/1600/2000/2400.
- Every checkpoint independently backed up before further updates; each evaluation persisted.
- All27 final source-grid binary NIfTI/PNG/transform/metric packages validated.
- Update phase2062.75s (34.38min), including intermediate evaluation/checkpoint backup overhead.
- Total2444.27s (**40.74min**), including source loading, exports, backup and independent recovery.
- PeakRSS8,871,067,648bytes (**8.26GiB**), under16GiB; time/storage limits unchanged.
- All35 artifacts restored in a fresh process with primary Python reads blocked; step2400,
  fixed prediction probe difference0. No physical-unplug test or bitwise MPS continuation claim.
- **1,180 native tests pass**,2 pre-existing upstream warnings. Code stayed frozen during execution.

Post-run review revalidated job-receipt members and terminal references, all checkpoints/exports,
exact update counts and optimizer/validation separation. Review-script plotting attempted to use
matplotlib, which is absent from both environments; no dependency was installed or training rerun.
The learning curve is retained above and as exact JSON. All27 overlays and three contact sheets
were produced using existing image tooling. This reporting issue did not affect run artifacts.

## Next recommendation — not another launch

1. Perform a bounded, read-only coverage-failure audit using retained predictions/transform records
   and, if necessary, newly specified checkpoint inference. Separate missed pancreatic extent from
   distant components and processed/source-grid effects; report per-case failure modes. Do not
   casually lower thresholds until a development-only policy comparison is explicitly designed.
2. Prepare a larger, more representative frozen training cohort through the existing purpose-specific
   qualification path; preserve difficult cases and original protected ancestry. Choose candidates
   by predeclared metadata/coverage, not by discarding cases the current model finds hard. Current11
   remain development diagnostics, not a final untouched test set. Address documented validation
   coverage gaps through qualified new candidates, not substitution of held6350 without evidence.
3. Freeze the next controlled experiment after that review. Data breadth and generalization deserve
   priority over simply extending2400 on this same tiny cohort. Sampling/augmentation and a
   high-recall ROI operating policy are candidate interventions, not adopted changes. Keep model,
   loss, data changes and policy changes separable when making causal claims.

Do not connect this failed-coverage checkpoint to a production cascade or claim stage2 readiness.
No further training, retrieval changes, source changes, Git commit or push occurred in this task.

## Retained evidence

Design: [CAP-EXP-006 launch plan](CAP-EXP-006-LAUNCH-PLAN-2026-09-29.md).
Implementation: [sustained executor handback](SUSTAINED-EXECUTOR-HANDBACK-2026-09-29.md).
Request `expanded-launch-request-bb413397-e1a1-463d-8aba-1edf0887129c`;
SHA `024fb5b495d78a4ad4686846ec113c3ecc9d8c023cd298a189cafc3c304cf01e`.
Approval SHA `d041179d7e7573803348ad393989ce91cc5c82f48bc8050cfb31412e459b695e`.
Run `outputs/prowl/expanded-execution-943d4c6d-29b8-4d85-a2e5-fce579116f59`;
job receipt `900c05364910507ba4f927733f1bf3225a900c85fabc4a99a6bcba306c0c9567`.
Derived review `outputs/prowl/cap-exp-006-review-20260929`: summary, full trajectory, paired
comparison, decision check, update counts,27 PNG/record pairs, contact sheets and hash receipt.

## Final per-case results

| Case | Role | Dice | Mask recall | Volume ratio | Box reference coverage | Scan fraction | ROI screen |
|---|---|---:|---:|---:|---:|---:|---|
|PanTS_00000003|Train|0.7718|0.9749|1.53|100.00%|4.57%|Pass|
|PanTS_00000026|Train|0.7674|0.9741|1.54|100.00%|3.61%|Pass|
|PanTS_00002973|Train|0.6974|0.9656|1.77|100.00%|5.47%|Pass|
|PanTS_00003188|Train|0.7887|0.9850|1.50|100.00%|4.09%|Pass|
|PanTS_00003191|Train|0.7941|0.9677|1.44|100.00%|4.60%|Pass|
|PanTS_00003239|Train|0.7752|0.9616|1.48|100.00%|4.05%|Pass|
|PanTS_00003668|Train|0.7709|0.9623|1.50|100.00%|5.56%|Pass|
|PanTS_00003717|Train|0.5506|0.9586|2.48|100.00%|5.50%|Pass|
|PanTS_00004226|Train|0.7706|0.9689|1.51|100.00%|6.14%|Pass|
|PanTS_00004965|Train|0.4387|1.0000|3.56|100.00%|0.31%|Pass|
|PanTS_00005286|Train|0.7972|0.9713|1.44|100.00%|11.85%|Pass|
|PanTS_00005593|Train|0.8140|0.9693|1.38|100.00%|3.77%|Pass|
|PanTS_00006886|Train|0.6427|0.9700|2.02|100.00%|22.88%|Pass|
|PanTS_00007295|Train|0.8417|0.9512|1.26|100.00%|5.27%|Pass|
|PanTS_00008037|Train|0.8611|0.9578|1.22|100.00%|2.73%|Pass|
|PanTS_00008443|Train|0.8877|0.9768|1.20|100.00%|5.58%|Pass|
|PanTS_00001004|Validation|0.6736|0.5687|0.69|85.40%|3.19%|Fail|
|PanTS_00002942|Validation|0.6285|0.5888|0.87|89.78%|6.01%|Fail|
|PanTS_00003104|Validation|0.2983|0.2573|0.72|76.90%|2.96%|Fail|
|PanTS_00004995|Validation|0.4662|0.5643|1.42|100.00%|5.24%|Pass|
|PanTS_00005747|Validation|0.4507|0.3513|0.56|65.87%|2.15%|Fail|
|PanTS_00007265|Validation|0.3705|0.3871|1.09|98.15%|5.66%|Fail|
|PanTS_00007482|Validation|0.4157|0.4443|1.14|100.00%|33.33%|Fail|
|PanTS_00007484|Validation|0.3534|0.3384|0.91|54.56%|1.64%|Fail|
|PanTS_00007687|Validation|0.3396|0.4848|1.86|100.00%|34.00%|Fail|
|PanTS_00007839|Validation|0.3513|0.4129|1.35|95.89%|41.72%|Fail|
|PanTS_00008855|Validation|0.6336|0.6685|1.11|99.77%|3.26%|Pass|
