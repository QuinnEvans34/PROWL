# Autonomous development quality plan — October 17, 2026

Quinton requests autonomous improvement until engineering has confidence in the system. This extends
the local development sequencing amendment to retrieval and answer integration; it does not supply
human label acceptance or independent evaluation. Baseline b1ee0ba, corpus disease-v1, dense search,
answer policy v6.1 remain available. No training, full selector, private content or inferred hours.

## Confidence target

For this development checkpoint, require materially improved passage coverage across all20 exposed
answerable v6 questions, useful disease-question answers grounded in actual comparative evidence,
readable answer/source navigation, tested refusals/citation integrity, and bounded local latency.
Measure and record gaps; never equate safe empty answers with useful answers or same-model review
with independent verification. Formal acceptance remains gated on Step5/6/7 and human review.

## Experiment R2, fixed before execution

The previous top50 pools omit the comparative inflammatory passages. Instead of a question-specific
expansion dictionary, score all1,179 existing canonical passages using one generic cross-encoder.
Model: `cross-encoder/ms-marco-MiniLM-L6-v2`, publisher revision
`233902d25c440f23af6f7d6e94d2946bac0bee0a`, Apache2.0 per
[publisher card](https://huggingface.co/cross-encoder/ms-marco-MiniLM-L6-v2).
Use existing Transformers/PyTorch, local-only safetensors, no remote executable code or new packages.
Download only config/tokenizer/weights/card, maximum110MiB, verify publisher weight SHA and pin all
files. Keep weights ignored/local; existing104GiB internal/408GiB external free-space floors apply.

One configuration: raw question + unchanged passage text, CPU float32,4threads, batch32, maximum512
tokens with no silent truncation, eval/inference mode. All corpus members eligible; logits descending,
passage-ID tie-break. Top50 for metrics, top5 for current answer interface. No labels/reference
answers/source boosts/rewrite injected into ranking. Bound per-question ranking30seconds, full run
15minutes, model input count1,179. Preserve error/partial receipts; no automatic retries or sweeps.

Run all20 exposed answerable questions once, reuse previous dense rankings as pinned baseline.
Use the same source/passages metrics and per-question diagnostics; labels remain provisional. For
development promotion require ≥16/20 questions with a labeled direct top5 passage, higher passage
recall@5, source MRR at least baseline, direct top5 hits for both disease questions, and actual
comparative inflammatory evidence in the findings question (not merely cancer-cohort signs).
Report all regressions. Median warm retrieval should be ≤10seconds, maximum≤30seconds on this host;
this is a local target, not a general hardware guarantee. Do not weaken criteria after results.

If qualified, integrate a versioned search configuration retaining canonical bindings and scope
guards. Then run the existing10-case answer-quality batch using the unchanged v6.1 prompt first;
retain raw traces, classify support/completeness/readability independently by reading sources. At
most20generationcalls,60seconds/question,no automatic retry. Record a separate plan before any
answer-policy/context adjustment justified by those results. Later general paraphrase/adversarial
checks are exposed development cases, never a substitute for independent held-out questions.

If R2 fails, diagnose the retained ranks and write a new bounded plan before another changed factor.
No unrecorded model sweep or immediate promotion. DB interruption history stays an explicit risk;
use read-only canonical inventory admission and preserve failures. Source text stays local/ignored.
