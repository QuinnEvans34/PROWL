# Prepared request: retained step6000 producer comparison

**Status:** Quinton explicitly authorized “Great. I give permission. Carry on.” on October20.
The metadata-only response is received and independently compared: all three cases agree in both
classes. See [results](MEASUREMENT-PRODUCER-COMPARISON-RESULTS-2026-10-20.md). No inference/training requested.
**Recipient:** Plan capstone experiment workflow on Quinns-Laptop.

## Request text

Please perform a metadata/report-only comparison for the existing raw step6000 evaluation of
`pants_pancreas_region_24k_20261019`. Do not load weights, CTs, annotation arrays, probabilities or
prediction payloads; do not launch inference or alter training. No newer/best/EMA checkpoint
substitution. If the requested report/fields are unavailable, report that explicitly.

The Mac's fixed checkpoint SHA-256 is
`ac50b534eb5e5334bfb29626743ed626a1d16363d8ac1c3374165140318f397f`.
Current development-list SHA is
`6b69605f49de0dd20346bee9db7fea4842c050cea4cf8d85268775deabc301bf`.
The previously handed-off native6000 report hash was
`c70d3fd952efbbec3dffb1dd7fb6428f243927761c6b21cdd921ec4a22b0398f`.
Please verify report identity and its checkpoint/variant/step/development/source bindings from
retained metadata, then return the existing rows for PanTS_00000927, PanTS_00000514 and
PanTS_00000698. Include exact per-class target/prediction/TP counts if stored; otherwise exact
saved metrics with definitions. Include retained orientation/ROI/window/reconstruction/device and
producing source identities where available. No metric recomputation from arrays.

The independent Mac raw-mask lesion counts (not component-selected) are:
-927: target11,301, prediction1,487, TP668, FP819, FN10,633; Dice0.1044729433844229.
-514: target0, prediction2,223, TP0, FP2,223, FN0.
-698: target0, prediction11,123, TP0, FP11,123, FN0.

Our source audit verified all36 received source members,11 exact helper AST matches and3
artificial preprocessing/restoration comparisons (7 windows). Original source decoder matches
all three local references exactly, including927's explicit encoding repair; source ROIs match
retained jobs. These checks do not establish CUDA/MPS output parity. The report comparison should
help determine whether the low recall/false positives already occurred in the original producer
before choosing a new model or calibration experiment. Return compact JSON/text through this chat;
no transfer listener or public data publication is requested.
