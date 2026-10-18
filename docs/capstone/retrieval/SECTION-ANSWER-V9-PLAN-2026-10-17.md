# V9 — qualified plain-language answers with study context

V6.2 source replay completed10cases but failed:3summaries,2provider/validation failures,1correct gap,
4correct scope blocks. Displayed head-size claims overstate an author-experience incidence estimate
and narrow a whole-pancreas age statement to the head. Findings answer gives unrequested study
performance figures without their full context. Same-model review did not catch those problems.
No deployment. Exact traces and original candidate metadata retained; that JSON inherited an8192
top-level context field, while the plan/code/provider traces used16384. Correct the declarative field
before integration; do not disguise the original mismatch.

V9 retains R8 rankings but appends canonical abstract sections and source-method context headings
(subjects/participants/patient selection/study population/statistical analysis/data analysis) for
the papers actually selected. This is general source context, never labels or question-specific
answers. Deduplicate existing passage IDs. Same50passage/30,000character ceiling; fail on overflow.
Full source metadata may improve qualifiers but adds irrelevant text; report actual context cost.

One new answer policy: original question, exact source quotes, pinned Qwen3:30b, temperature0/seed42,
16384context, same60second deadline and at most2calls. Shorter plain-English instructions explicitly
exclude unrequested disease-incidence/performance percentages, distinguish whole-organ versus
subregion findings, and preserve author estimates/population/statistics. Allow up to3citations per
paragraph so population, numerical result and statistical definition can be cited together. Retain
mechanical guards and add two: percentages require a question asking for rates/performance, and
a named pancreatic subregion in a claim must occur in that claim's actual cited passages. These
lexical checks are conservative backstops, not semantic proof or independent review.

First replay the same10exposed quality cases using retained canonical evidence plus this general
source context. No retrieval replay or altered labels. At most12generationcalls/15minutes, no
retries. Require useful supported disease answers, correctly scoped volume/range explanation,
readable function answer, correct gap and4scope blocks, zero unsupported displayed claims, and no
provider failures before preview promotion. Independently read the source support as engineering
review; unchanged required-concept gaps must still be reported. A failure stays a failure and
requires a separately documented next decision. Formal human/held-out acceptance remains open.
