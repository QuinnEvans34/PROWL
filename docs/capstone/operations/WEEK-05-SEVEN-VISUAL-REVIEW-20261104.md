# Seven-case native visual error review

All26new contact sheets were actually opened and inspected using image tools: five missed reference components,20zero-overlap false-positive components and one partially overlapping component with extensive spillover. This is representative saved-output review on exposed development, not clinical diagnosis, annotation adjudication, independent generalization or hypothesis acceptance. Probability equivalence remains UNQUALIFIED under the approved exception. No model, scoring, threshold, unit or training changes occurred.

## Findings

| Case | Observed pattern |
| --- | --- |
|4681|Small missed yellow annotation near pancreatic contours despite pancreas localization. Three reviewed false-positive components are remote posterior soft-tissue islands near the spine, with extra predicted-pancreas labeling.|
|8769|Missed reference sits at pancreatic contour edge. One FP is within pancreatic contours; two are far superior in thoracic soft tissue.|
|6755|Missed reference near pancreatic contours; another reference lesion has overlap and spillover. FP targets include a pancreatic-contour focus, a remote thoracic island and a small posterior island. Strong image grain/streaking limits interpretation.|
|2889|Missed reference and FP patterns closely resemble6755. Their distinct case files/native geometry are bound, but visual resemblance means independent anatomy should not be assumed from IDs alone. No shared-identity determination, audit or exclusion was performed.|
|2235|Missed yellow annotation visibly anterior to reference/predicted pancreas-parenchyma contours. One FP is at a pancreatic contour end; two tiny FPs lie on the first acquired slice remotely. Coarse native through-plane sampling limits orthogonal detail.|
|8711|Two isolated FP foci lie within pancreatic contours. The amended component4 occupies much of the pancreatic region:3378overlap/20503predicted voxels, with17125extra voxels. Green overlap is inferior, magenta extension extensive, and some yellow outline remains missed.|
|6880|Reference-empty case has a large crescent/patch at pancreatic contours and two smaller pancreatic-region foci. This is not solely remote-organ confusion. Empty reference does not establish verified health.|

These observations distinguish four error patterns: remote extra pancreas/lesion labeling, within-pancreas extra lesion labeling, missed lesion annotations despite nearby pancreas localization, and extensive overlabeling attached to a partially overlapping lesion prediction. A hypothesis about better localization addresses only the first pattern; strict pancreas-parenchyma masking could remove annotation such as2235's target. The review does not establish the best intervention, tune a threshold or authorize a new experiment.

All completed cohort scores previously showed full annotation field coverage in the expanded evaluation region. These views are consistent with that coverage; they do not prove detail preservation through model resampling. Small targets, heterogeneous CT contrast, coarse sampling and training/optimization remain possible contributors, not demonstrated causes.

## Comparison with prior four-case review

The prior November3 review already showed4681/6755misses in both autonomous and provided-region arms, and remote/boundary FP predictions in909/2028. Fresh autonomous sheets reproduce the4681/6755miss pattern using the bound saved outputs, now with CT-only enlargements and distinct predicted-pancreas contours. This review extends the evidence to within-pancreas errors,8711's partially overlapping spillover and2235's annotation outside the parenchyma contour. The provided-region arms were not rerendered or rescored; comparison uses the existing report. No statistical or causal contrast between these selected examples is claimed.

## Display and evidence

Private images: `E:/PROWL/readiness/week05-seven-visual-review-20261104-a01`.
Independent backups: matching directory under `C:/Users/quinn/PROWL-Backups`.
Original plan1b81693 SHA256 `10d9674f0476d6d854a478bd9406c30a2ea154a854976d66378fb4701224dd8e`; amendment61eb806 SHA256 `1463a206dfbf549804d4877cb82e996549ab0ba56990f6e7d7a946749349d979` replaces8711's trivial1voxel target with component4before rendering. No target was changed based on rendered appearance.

Before each case load, CT/reference/prediction/result/score/access hashes were checked against frozen records. Native shapes and affines match within original1e-5absolute tolerance. CT units are mm; unknown reference-unit assumptions are retained exactly. Lossless RAS permutation/flips only; non-axis-aligned geometry is rejected, not silently deobliqued. Source and image hashes plus native/RAS affine geometry are in the [full recovered metadata JSON](WEEK-05-SEVEN-VISUAL-REVIEW-FULL-METADATA-20261104.json). No medical pixels or arrays are committed.

Each sheet shows three orthogonal planes and three rows: context overlay, enlarged CT alone, enlarged overlay. Fixed HU[-100,250], physical aspect ratio,20mm zoom margin and maximum selected-component area with lowest-index tie breaking. Yellow=reference lesion, magenta=predicted lesion, green=overlap, blue=reference pancreas, cyan=predicted pancreas, orange=evaluation ROI. Captions show zero-based RAS slice indices, original native target XYZ and RAS world coordinates.

## Runtime, failure preservation and limits

Seven synthetic geometry/display tests passed8.32s. Rendering produced all26PNGs within296.406s, peak owned RSS1183797248bytes, one CPU thread, no GPU. The worker then exited1 during final JSON serialization of a NumPy int64 zoom coordinate. It was reaped; failure log/resources and partial manifest are preserved. This was not a timeout, resource excess or source identity/geometry failure. Original rendering files remain pinned and were not patched or rerun.

A separate metadata-only recovery parsed the fully written seven-case field from the partial manifest, reconciled26expected filenames with logs/PNGs and actual inspection notes, rechecked33original output/backup pairs and producing-code pins, and wrote a separate recovered manifest plus independent backup. Two recovery/serialization regression tests passed1.21s. An additive native-number converter is tested for future use; it was not used to rerun real images. No source arrays were reloaded for recovery. The original bounded worker remains truthfully FAILED even though all saved sheets were inspectable and the review was completed.

The original full-precision per-image plane JSON records were not completed. A separately authorized bounded recovery reconstructed them using the same frozen selection/orientation/crop functions on exact-hash masks and native geometry, without CT voxel reads or rendering. All78slice indices independently read from inspected PNG captions match the recovered records. Recovery succeeded47.593s/657227776Bpeak/exit0/reaped; cumulative charged time373.999s includes296.406sfailedrender and30sconservative allowance for first metadata salvage, below1200s. Three metadata regression tests passed0.98s, including actual renderer-to-manifest JSON roundtrip reproducing and correcting the NumPy scalar boundary. Original failed records/pins remain unchanged. Two2235first-slice tiny FP targets are visible axially but the orange ROI edge obscures their orthogonal overlay pixels. This is a display limitation, not evidence those predictions are absent. CT-only orthogonal context remains visible. No extra sheets were silently rendered to hide it.

First salvaged metadata SHA256 `8f42842e38816d5f732140145fa9fb39953c9833531a4d56fe47af2b398553e8` remains preserved. Final full-metadata JSON SHA256 (UTF-8/LF): `6769a04712874b737f79922c11b3de1fdfc5ea79fdcda92b0695eb09473ab0c0`. Final provenance explicitly distinguishes the first no-array salvage from later mask-only reconstruction; no CT voxels were reread for either recovery.
26PNGs total15159327bytes. Every sheet has a factual observation and SHA256 in that report. No quality acceptance, clinical conclusion, duplicate exclusion or new experiment follows automatically.

## Private handoff and cleanup

Original35review/failure files and four full-plane recovery files matched independent backups before final publication; final review sidecars were independently copied and verified. Worker process checks found no remaining render/recovery owners and GPU was idle. No original producer or saved prediction/score changed.

Packet: E:/PROWL/readiness/week05-seven-gallery-transfer-20261104-a01/seven-native-review-v2.tar,15370240bytes,32regular root-relative members,expanded15304498bytes. SHA256 `a2fcfb586d881e0b0373ff69b6d3ac3c50ceec920f1f895e3b7a980731cbc444`. Strict prowl-review-transfer-v1 member/size/hash readback passed. Contains26PNGs, finalreview, plan, amendment and resource receipts; no source arrays, model weights or secrets. Earlier packet/version1 remains retained and superseded for provenance. Sender is bounded600s/1GiB; receive code stays in private chat/log only, never Git. Receipt of the packet by Mac is not claimed until confirmed.
