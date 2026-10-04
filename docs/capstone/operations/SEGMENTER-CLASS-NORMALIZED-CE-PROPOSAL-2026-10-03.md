# Next proposal — class-normalized CE qualification

D-330's `[1,64,256]` candidate fails the original synthetic lesion learning bars after480updates; exact restart agrees. No MPS or real request follows. Keep both v3/v4 implementations and all failed evidence. The next factor to investigate is **CE's dependence on target class volume**, rather than another fixed global weight chosen from a few saved logits.

## Evidence and inference

The real training audit's provisional64pancreas weight raised its weighted CE denominator share to41.9–56.5%. In the preserved invented sparse fixture, the same recipe assigns93.0% to pancreas and1.09% to lesion, versus17.25%/12.91% under v3. The new candidate learns pancreas Dice0.955–0.968, but three positive fixtures have lesion Dice/recall0 and the outside-pancreas fixture has0.471/0.333. All targets/counts and original bars stay fixed. This supports investigating allocation across class sizes; it does not establish causal proof or predict real CT learning.

## One explicit candidate to consider

For each case, calculate the mean voxel CE separately within each **present true class** among0/1/2, then give those present-class means equal weight. Average case losses across the batch; add the unchanged present-foreground Dice term. Proposed ID `per_case_present_class_mean_ce_present_foreground_dice_v5`. No fixed `[1,64,256]` or `[1,1,256]` multipliers in this candidate: the single named factor is the CE class-allocation/reduction policy.

Precisely, for case i with K_i present classes and count n_ik:

`CE_i = sum_present_k [sum_(y=k) -log_softmax(z)_k / n_ik] / K_i`.

`CE = mean_i CE_i`.

The CE output-logit gradient at a voxel of true class y is `(p - one_hot(y)) / (B * K_i * n_iy)`.

Preserve Dice mean over each case's present foreground classes1/2, epsilon1e-5, batch mean. Absent foreground Dice stays excluded, all-background Dice is zero. Absent true classes are excluded from the class-mean denominator, but their probabilities still compete in softmax and are penalized by CE on present classes. Empty input, nonfinite numerics, invalid codes, unsafe dtype/task and division-by-zero must be refused. No target clipping, foreground filtering or lesion-centered sampling.

Equal class allocation prevents a larger pancreas count from diluting the small lesion's nominal CE share. It may overemphasize a tiny/noisy target or produce too much foreground; successful mechanics alone does not establish the operating policy. Retain explicit negative and false-positive screens and difficult cases.

## Bounded next work

1. Separate versioned objective/task/codec and small invented independent scalar/analytic-gradient oracles, including batch cases with different present classes, all-background/only-lesion, overlap precedence, tiny/boundary/multiple lesions and negative penalties. Preserve all accepted v3/v4 producers and wrong-loss resume refusal.
2. Freeze new seed42/24³/AdamW0.003/480update CPU class-cue qualification, two paths with actual30-update interruption plus450restart. Original D-322 learning bars unchanged; same five fixtures and sampler;≤180s/2GiB pertrajectory,256MiB output. No real inputs, automatic retry or duration extension. Use v3's retained qualifying480 result and v4's retained failure as comparison evidence without rerunning consumed requests.
3. Only if the learning gate passes, separately prepare native144³/four-update/resource/native-grid/checkpoint recovery under fresh storage and request identities. Then consider a fresh same6/1/48update real comparison, changing only the CE allocation policy with all other settings fixed. Fresh14target scope, terminal primary, explicit training comparison screens and Quinton's separate exact launch approval remain required.

This is the next recommended investigation, not an accepted loss, frozen request, new optimization job or real-launch authorization. Do not silently soften tests, select a checkpoint using2514, infer specificity/generalization, remove tiny/boundary cases or promote a model. A first small synthetic failure is useful evidence, not a reason to run longer automatically.
