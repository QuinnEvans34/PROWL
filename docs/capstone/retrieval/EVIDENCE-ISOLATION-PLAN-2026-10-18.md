# Controlled evidence-to-answer experiment

Quinton approved this experiment after the V22 failure review: locate failures in evidence assembly,
generation and validation; keep Trello current and commit coherent checkpoints. This authorizes this
fixed diagnostic ahead of formal evaluation, not protected-set access or UI promotion. Earlier failed
candidates, source corpus, labels and acceptance gates remain unchanged.

## Questions and controls

Use unchanged exposed quality-01 (head size/disease), quality-02 (inflammatory versus tumor findings),
and quality-03 (published volume and limits), from answer-quality-plan-v1. No new question wording.
Three arms per question, one fixed prompt, pinned Qwen2.5:14b, temperature0/seed42/context16384:

1. `retrieved_flat`: one real request to the current dense source-only API, canonical top5 passages.
2. `curated_flat`: manually inspected canonical passages supplying the relevant findings and context.
3. `curated_linked`: identical passages, order, IDs and text to arm2, plus explicit within-paper
   finding/population/method/statistic/qualification references. Links contain no additional facts.

The curated inputs are engineering-selected diagnostic evidence, not an independent gold set. They
are not per-question prepared answers. Selection and role annotation use exposed development needs;
this deliberate intervention cannot establish generalization. Freeze selectors before generation.
Check passage hashes and offsets against canonical representations. Preserve full source text only
in ignored local artifacts; tracked config holds locators/hashes/relationships, not source payloads.
No expected answers, required-concept lists or evaluation judgments enter any model request.

Head passages: PMID32703312 ordinals4,7,9,37, preserving overlap and single-feature limitations.
Findings: same paper ordinals0,22,24,37,39,44, preserving MFCP/PDAC scope, MRCP duct evidence,
combination limits, PDAC-context signs and focal-AIP portal-venous CT context.
Volume: PMID25950180 ordinals2,27,29: population/count/MRI method, mean±SEM convention and results.
These were read against retained original text before selection. No numerical head threshold is
supplied. A claim that no threshold exists anywhere is not supported. Sample-specific caution is an
interpretive limit, not a new population estimate. Source review is one engineering review, not human
or independent acceptance.

## Measurement and attribution

One draft per arm, at most three paragraphs and three citations per paragraph. Save it BEFORE any
validator. Run existing mechanical checks and frozen V22 factual-support review separately; neither
can delete or revise a diagnostic draft. No completeness/readability model calls or revision loop.
Manual source review grades factual support, responsiveness/old required concepts and readability
separately. Count omissions separately from unsupported claims; a narrow supported answer is not
automatically complete. Record model false approvals/rejections and mechanical false failures against
that manual review, at claim level where possible. Same-model review is not independent verification.

Rotate arm order across questions as preregistered. No repeat/seed sweep or tuning after results.
Compare retrieved_flat versus curated_flat to locate evidence sufficiency effects. Compare flat versus
linked curated arms to test relationship annotation. These tiny paired observations are diagnostic,
not statistically established causal effects; ordering/context length can affect timings. The prompt
differs from V22, so V22 versus this experiment does not isolate one factor. No attribution of a speed
change exclusively to evidence links. Preserve exact input/output, model options, stage timing and pins.
Also inspect retained R8 evidence coverage without rerunning that ranker or generating another arm.

## Resource and failure bounds

Three source-only live searches, nine drafts and at most nine support reviews;18chat attempts maximum.
One empty-prompt cold readiness/load call (120seconds maximum), then a resident-model run; report the
load separately, never hide it in a warm-latency claim. Model may stay resident for the batch; one final
unload. Each chat60seconds, batch1200seconds,18GiB sampled owned process-tree RSS,104GiB internal and
408GiB external free floors,12MiB output cap. One owned isolated11435 server with the previously
verified external model store; no download, original11434 modifications or deletion. Supervisor reaps
both worker and server on exit. A transport failure stops the run rather than overlapping a potentially
still-running request. Exclusive preparation/run markers prevent replay; preserve partial failures.

No training, full selector, private questions, new corpus ingestion, automatic label acceptance,
human-hours credit or production service edits. Existing dense/v6.1 remains selected regardless of
diagnostic result. Success means a complete auditable diagnosis with a justified next decision, not
that all answers happen to pass. Plan/code/input checkpoint precedes generation; results/spec/handoff
and Trello update follow, with all failed artifacts preserved.
