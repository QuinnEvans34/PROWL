# R8 — explicit, auditable terminology normalization

R7 stopped at its first disease screen:7.097seconds, no labeled direct head-size evidence. Its
section ranking and complete-section expansion are retained, not promoted. Generic rankers repeatedly
interpret “size” as normal dimensions, while the question asks about disease associations.

One bounded next change: an explicit terminology normalizer for pancreatic literature search.
When a question contains both size/dimension wording and explicit disease/abnormality wording,
expand size to size changes (enlargement, swelling or atrophy). For a pancreatic topic, expand
inflammation to inflammation/pancreatitis. Preserve every original clause, anatomy/subregion,
negation and requested study; never inject a diagnosis, threshold, source ID or expected answer.
If expanded text would exceed500characters, use the original query. Log both strings. These are
general search-intent rules, not full-question matching or canned answers; test noncatalog wording
and ensure ordinary size questions do not become disease questions. They intentionally supersede
the earlier experiment's no-normalization choice, without changing its failed result.

Vocabulary is motivated by the retained source language: PMC8292294 describes inflammatory edema
with enlargement; PMC7376657 discusses mass-forming pancreatitis and imaging differentials; the
corpus also describes atrophy. Expansion widens candidate discovery; only original retrieved source
text may support an answer. No modified labels, corpus or question text reaches final answering.

Same R7 section/window/ranking/output budgets, five sections/max3perpaper. Screen both disease
questions first, then remaining18only if direct-evidence screens pass. Inflammatory comparative
evidence must be confirmed by source reading. Same≥18direct/≥16full-concept package targets,
median≤20s/max≤45s, and all regressions reported. No generative retrieval or answer calls.
