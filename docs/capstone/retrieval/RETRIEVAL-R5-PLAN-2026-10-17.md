# R5 — reason before selecting source IDs

R4's retained head-size result selects only four diabetes abstract sections and contains no labeled
direct disease evidence. It already fails its mandatory disease criterion; the remaining fixed
20-case run is being completed to retain all outcomes. Several early outputs choose S1–S4 in order.
Do not infer a provider defect or relabel those selections as useful.

R5 changes one selector behavior: require a short explicit relevance rationale in the structured
output before choosing paper/section IDs. The rationale describes the information need and why the
selected evidence addresses it. It is internal navigation metadata, never a displayed answer or
source. No gold labels, reference answers or question-specific templates are added. Existing
Qwen3:30b, think=false, token/context limits, raw question, menus, canonical passage expansion,
scope boundary and two-call40second retrieval deadline remain fixed. This tests deliberate evidence
selection without adding unconstrained long reasoning or changing the corpus.

Pin new producing files before one20-case run, at most40selector calls,20minutes, no retries.
Same R4 package criteria and latency targets, plus engineering review of rationale/ID consistency.
R4 history/code/results remain preserved. If this fails, do not promote or change labels to make it
pass; use retained failures to determine whether a different approach is justified.

## Pre-run correction after R4 stopped

R4 completed15questions, then refused the16th section menu (>50,000characters), after its paper
selection.31selector calls total; no retries. The failed run remains incomplete, not a20-case result.
R5 additionally removes repeated paper titles from every section entry: a single paper-ID/title
registry carries the same information. Opening text and all sections remain; the50,000character
budget is unchanged. This formatting repair is a second changed factor, so rationale and formatting
contributions cannot be isolated. No R5 invocation occurred before this amendment.
