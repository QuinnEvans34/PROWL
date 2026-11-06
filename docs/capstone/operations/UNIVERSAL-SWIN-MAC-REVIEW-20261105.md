# Larger-model screen: Mac review

The requested experiment finished before bedtime. The official Universal Swin
UNETR checkpoint was downloaded and verified on both machines, then screened on
Lenovo after complete KD closeout. It has62,595,315parameters, about4.4times the
student. This was pretrained inference only; no fine-tuning occurred.

| Positive development case | Universal lesion Dice | Prior autonomous baseline |
| --- | ---: | ---: |
|2028|0.826177|0.464840|
|1347|0.388500|0.476145|
|2514|0.764949|0.083505|
|8743|0.863391|0.815458|
|Mean on these four cases|**0.710754**|**0.459987**|

Three cases improved and one worsened. The descriptive mean difference is
+0.250767on this fixed subset. This is not a comparison with the full70-case KD
average and does not isolate model size: initialization, training data and input
processing differ. External training overlap remains unknown. All four reference
lesion components had some overlap; four predicted components had none. Case1347
remains weak, with recall0.395536and precision0.381709.

The result justifies a broader, separately planned evaluation. It does not establish
independent generalization, negative-case specificity, transfer-training performance
or clinical acceptance. No confidence interval or hypothesis verdict was issued.
All12proposed training cases retained their missing-unit admission failures, and
no negative case passed the new strict unit rule. Those limitations were preserved.

## Verification and saved outputs

Lenovo published the [complete report](UNIVERSAL-SWIN-RESULTS-20261105.md) and
[sanitized result](UNIVERSAL-SWIN-RESULTS-20261105.json) in f7ece22. Mac reviewed
the loader, geometry, supervisor, freeze logic and tests without merging code.
CPU checks passed:35on Mac and18on Lenovo. The CUDA pilot reserved at most
4,915,724,288bytes, below6GiB; independent checkpoint reload matched exactly.
Ten stage workers exited0/reaped;5,442producing pins and45independent backup pairs
were verified on Lenovo. MLflow051c194b2e54428aba6b9420129e18b6 is FINISHED.
Evaluation took365.032seconds and contributes **zero training hours**.

Mac independently checked12named CT/reference source hashes against its retained
files, matched prior autonomous scores and KD reference voxel counts, and checked
Dice/precision/recall/mean arithmetic. The adjacent Mac-review JSON records scope.
These are metadata/source-byte checks; Mac has not yet read the new predictions.

Saved native predictions remain on Lenovo with independentC backups. A small
prediction-only private packet was requested; the remote connection became
unavailable after successful result publication. Mac delivery is pending
reconnection, not failed inference or a lost result. No private code, CT, annotation,
weight or mask is committed to Git.

## Tomorrow

1. Inspect the saved masks, especially1347and the improvement on2514; verify native
   geometry/reference bindings before interpreting spatial errors.
2. Investigate pretraining overlap and plan a broader balanced development test,
   including negative cases with defensible unit/geometry admission.
3. Resolve training-reference unit provenance without changing original files or
   weakening gates. Then specify a short adaptation with untouched pretrained
   outputs as its baseline before considering long training.
4. Review the [full KD result](MAC-KD-COMPLETION-20261105.md): its selected gain was
   small and component misses/false positives remain important. Neither model is
   promoted on average Dice alone. No additional experiment was launched.
