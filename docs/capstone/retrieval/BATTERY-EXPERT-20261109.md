# Local AI expert on battery — November 9

Quinton explicitly authorizes loading and using the local AI expert without AC
for presentations. This replaces the earlier same-day source-only battery
fallback. The change applies to interactive literature inference, not training,
teacher generation, segmentation experiments or their admission rules.

The expert had reused `training_guard`, which bundled exclusive accelerator
ownership with training's AC requirement. A separate `expert_gpu_guard` now takes
the same nonblocking accelerator lock without the AC condition. Preparation and
the local UI proxy also stop treating battery power as an answer blocker. The
status still reports power, so the UI can say “Running on battery.”

Existing model identity, bounded prompt/output/deadline, request serialization,
storage admission, Docker memory budget, local-origin restrictions and exclusive
accelerator ownership remain. No scientific launcher, training guard, model,
prompt, weights, context budget or resource limit was changed. Another GPU owner
still selects CPU source-only search and blocks model requests.

## Actual qualification on the unplugged Mac

- Started with no model allocated and the previous owned CPU source service.
  Clicking **Prepare AI expert** loaded the pinned `qwen3:8b` and replaced only
  that verified source service with the answer service. Power was battery.
- Research answered the existing boundary question with a generated paragraph
  and citation buttons. Readiness displayed model ready and running on battery.
- A second exposed question, “Does the pancreas produce insulin?”, completed
  through the UI proxy in **3.62 seconds**, with `generation=completed`, the pinned
  model digest and bound citations. This is one smoke timing, not a latency or
  answer-quality benchmark. Known semantic/source-support quality work remains.
- Status before and after the second request showed `ac_power=false`, model
  loaded, no competing GPU job and no answer blocker. System memory pressure
  reported53% free after model loading. Private response/ownership/power evidence
  is retained under `outputs/prowl/expert-battery-live-20261109/`.
- 20Python and73UI checks passed. These cover battery preparation/upgrade,
  inference lock exclusivity and release, **continued training AC refusal**,
  source-only model-route refusal, ready-on-battery messaging, keyboard submission
  and source fallback when another job owns the GPU. Production build passed
  with the existing large-viewer-chunk advisory.

No training or successor experiment was launched. The existing Lenovo run and
its producing files remain untouched. The model/search services are left ready
for Quinton; normal model keep-alive behavior is unchanged.

## Presentation steps

Charge beforehand, open Research, and click **Prepare AI expert** before starting
the demonstration. Check for “The local model is loaded and ready for questions.”
The same action works on AC and battery; no hidden switch or command is needed.
Ask the question normally and open a citation. The existing internal literature
database works without the external drive; opening a publisher's full website
still requires network access. Retained CT/Training screenshots and **Find
sources** remain useful fallbacks if an unrelated service is unavailable.
