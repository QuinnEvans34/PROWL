# R7 — deterministic section expansion after local relevance ranking

R6 stopped on its first question: source selection completed, section selection exceeded the
60second retrieval deadline. No completed evidence package; two selector attempts, no retry.
R5 improved direct evidence to15/20 but full concepts only10/20 and both disease cases missed.
Keep both rejected. The section representation helped, while generative routing remains unreliable.

R7 removes generative retrieval. Rank source-section windows with the already pinned MiniLM
cross-encoder. Window text includes canonical paper title and section heading; full normalized
section text is covered by1200character windows with200character overlap. If a question/window
pair exceeds512tokens, split the window further rather than truncate. Use maximum1600windows,
CPU4threads/batch32, per-question45seconds. Record real window count. No new weights or corpus.

Score each section by its highest window score. Select five distinct sections, at most three from
one paper, using score descending then stable source/section ID. Return all existing canonical
passages of selected sections, never the synthetic scoring windows. Cap50passages/30,000characters
including titles; refusal on overflow, no silent clipping. This larger context is explicitly a
different package from top5passages and R4's four sections. Compare coverage and text cost honestly.

Use the original question unchanged; no labels, reference answers or source-specific boosts enter
ranking. Screen the two disease questions first. Require direct labeled evidence and actual
inflammatory comparison; if either fails, stop and retain the screen rather than spend a full run.
If they pass, run the remaining18questions once. For integration require direct evidence≥18/20,
full concept coverage≥16/20, median≤20seconds/max≤45seconds, plus exact identity/canonical binding.
Source and passage metrics remain provisional exposed development. No answer generation in R7.
Before any larger-context answer test, write its explicit context/output/latency plan.
