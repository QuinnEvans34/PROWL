# V19 — source-locked readable rendering regression

V18's corrected feedback makes the model include the study sample and MRI method (14comparison/
41diabetes participants), without supplying those facts in feedback. It removes undefined±. The
result remains too technical and combines structural imaging with an unnecessary triglyceride
protocol detail; that wording is not accepted as a final answer. V17's head statement is source-faithful
but retains unnecessary parenchyma/acronym wording. Preserve both exact drafts and prior failures.

Complete the previously identified V10 writer-boundary repair: the readability stage receives only
the current draft's claim TEXT, question and numeric claim IDs, never raw source passages, citations,
other retrieved content or expected answers. It may shorten/paraphrase, but may not introduce facts.
Code preserves each claim's original citation bindings; no model-selected rebinding or cross-claim
merge. A final check receives only the rewritten claim and its actual bound citations. All mechanical
checks remain. This closes an information boundary and separates readability from evidence discovery.

First two retained inputs: V17head and V18volume. At most one rewrite and one source-review call per
input (4calls total), pinned14B/temperature0/seed42/context16384,60s per input,18GiBownedRSS/4min,
no retries or new draft/retrieval. Exactly preserve provenance of the retained inputs; reported times
are rendering-regression times, not full request latency. Require useful plain wording, preserved
study scope and no unsupported displayed assertion before a separately planned full-path check.
No paper/model/context candidate expansion, gold text, user acceptance or clinical claim follows.
