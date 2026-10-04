# Codex review of Claude's P3 foundation

September 28, 2026. **Changes requested; P3 contract review is not accepted yet.**
Quinton supplied the handback and requested native tests and contract review. This review
leaves Claude's implementation, schemas, tests, planning files and handback unchanged.
No P4b start, dependency installation, live literature acquisition or database work occurred.

## What passed

All 30 file hashes listed in CLAUDE-FOUNDATION-HANDOFF-2026-09-28.md matched the
reviewed files. Both packet commands ran in the native Mac environment:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests/retrieval -q -p no:cacheprovider
# 120 passed in 0.59s
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests -q -p no:cacheprovider
# 751 passed, 2 existing torch.jit deprecation warnings in 5.07s
```

The separation between official and proposed metrics, synthetic token counters, and
fixture-only query classification is explicit. These tests establish implementation behavior,
not retrieval quality or a production semantic safety gate. Claude reports fault-injection
work in the handback; Codex did not independently repeat that whole mutation campaign.

## Required corrections

### R1 — P1: Recompute revision and rights identities when loading records

`src/retrieval/records.py:208` and `:219` schema-check revisions and rights without
recomputing their content-derived identities. Changing display_snippet from true to false
while keeping rights_id is accepted and produces the same corpus_id. Changing a revision's
content_sha256 while retaining revision_id is also accepted. Persisted records can therefore
claim an old identity after their content or permissions change.

Add reusable identity verifiers and invoke them at replay/assembly boundaries, not only in
constructors. Regress each rights permission and revision content mutation. Enforce the
packet's duplicate-logical-record rule as well: `_index_unique` currently silently collapses
identical duplicates; repeated revisions through distinct source events are a separate case.

### R2 — P1: Bind evaluation to the actual question and verified passage records

`src/retrieval/metrics.py:145` looks up a ranking by dictionary key but never checks its
question_id against the label set. A ranking for q:wrong supplied under q:one is scored.
Passing the same label set twice counts it as two answerable questions and can reweight
means. Passage dictionaries are indexed without verifying exact slices/identities, and
accepted-query verification is optional in verify_ranking and absent from evaluate.

Reject duplicate question identities, bind question/query/configuration/corpus explicitly,
and validate the passage/representation records against the manifest before scoring. Add
regressions for wrong-question lookup keys, duplicate labels, changed passage content and
refused/mismatched query records through the actual evaluation entry point.

### R3 — P1: Validate delivered passage geometry and counted text before giving credit

`src/retrieval/context.py:74` trusts supplied passage offsets and optional caller-provided
text. With the existing context fixture, change only the first passage's end offset to the
end of the representation: delivered-span recall rises from 1/3 to 1 without changing its
passage ID or token count. The extra evidence was never actually delivered.

Verify every representation/passage identity and exact slice before packing or scoring.
For text counters, derive text from that verified slice or require exact equality. Bind the
integration path to its validated ranking/corpus/question and enforce display permission
independently of indexing permission. Keep fixture counts and proposed metrics explicitly
synthetic/provisional. Add the forged-offset regression and an altered-counted-text case.

### R4 — P2: Protect and validate the original-to-normalized offset map

`src/retrieval/passages.py:152` omits paragraph offset_map from representation identity;
`:161` does not validate its semantic mapping. Replacing a map with [[0,1,9000,9001]] is
accepted with the original representation ID. Source-coordinate provenance can change
undetected even though normalized-text geometry still looks valid.

Define and verify mapping coverage, order and bounds against retained original paragraph
information, and bind that information/map to an appropriate immutable identity. Test
Unicode/whitespace mappings plus gaps, overlaps and out-of-bounds original coordinates.
A schema-valid four-integer array alone cannot establish a correct mapping.

### R5 — P2: Verify the claimed eligible-pool exhaustion

`src/retrieval/metrics.py:83` accepts a caller's eligible_pool_size but does not persist it;
`:102` checks only that a shortfall reason exists. Returning one of five eligible corpus
members with eligible_pool_size=1 passes verification. This violates the packet's depth-50
or complete-smaller-pool requirement and can change reported metrics.

Bind a verifiable eligible inventory/count to the corpus and any supported filter policy,
then require min(50, eligible count) results. For P3's unfiltered fixtures, corpus membership
is sufficient. Reject bool/noninteger sizes and test false exhaustion, valid small pools and
50-result depth. Do not invent production filtering to fix this synthetic contract.

## Handback to Claude

Address R1–R5 within the existing P3 foundation scope, add regressions at the public entry
points, rerun both packet commands where available, update design/handback/hash evidence,
and return for Codex native review. Preserve the frozen needs and existing decisions.
P4b remains behind successful contract review and separate dependency approval. This review
is a correction request, not a new phase dispatch or adoption of proposed metrics.

## Reproduction

Save the following block to a temporary Python file and run from the repository root with:
`env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. .venv-prowl/bin/python /path/to/probes.py`.
It uses only invented test fixtures and in-memory mutations. On the reviewed handback it
prints true for the first three checks, 1 for the wrong-question count, 2 for duplicate
questions, 1 for the false-exhaustion count, and [0.3333333333333333, 1.0] for forged recall.
After fixes, these inputs should fail validation; convert them to assertion-based regressions.

```python
from copy import deepcopy
import runpy,json
from src.retrieval.records import build_corpus
from src.retrieval.passages import verify_representation
from src.retrieval.metrics import evaluate,verify_ranking
from src.retrieval.labels import make_label_set
from src.retrieval.context import delivered_evidence,FixtureCounts
r=runpy.run_path('tests/retrieval/test_records.py')
m=runpy.run_path('tests/retrieval/test_metrics.py')
c=runpy.run_path('tests/retrieval/test_context.py')
results={}
x=r['chain']();original=build_corpus(**x)
x['rights'][0]['permissions']['display_snippet']=False
results['changed_rights_with_stale_id_same_corpus']=build_corpus(**x)['corpus_id']==original['corpus_id']
x=r['chain']();x['revisions'][0]['content_sha256']='f'*64
results['changed_revision_hash_accepted']=bool(build_corpus(**x))
x=r['chain']();rep=x['representations'][0];old=rep['representation_id'];rep['paragraphs'][0]['offset_map']=[[0,1,9000,9001]]
results['broken_offset_map_accepted_unchanged_id']=verify_representation(rep)['representation_id']==old
manifest,ps,reps=m['corpus']();q=make_label_set(question_id='q:one',label_version='lv1',answerable=True,required_concepts=['c:one'],spans=[m['span'](reps[0],0,6)])
rank=m['ranking'](manifest,'q:wrong',[p['passage_id'] for p in ps])
kwargs=dict(label_sets=[q],rankings={'q:one':rank},corpus_manifest=manifest,passages=ps,representations=reps,configuration_id='cfg:syn-a',label_version='lv1')
results['wrong_question_ranking_accepted']=evaluate(**kwargs)['official']['n_answerable']
results['duplicate_question_count']=evaluate(**dict(kwargs,label_sets=[q,q]))['official']['n_answerable']
short=m['ranking'](manifest,'q:one',[ps[0]['passage_id']])
results['one_of_five_claiming_pool_exhausted_accepted']=verify_ranking(short,manifest)['result_count']
rep,(a,b,c0),labels=c['setup']()
base=delivered_evidence(question_label_set=labels,ranked_passages=[a],representations=[rep],counter=FixtureCounts({a['passage_id']:1}))
a=deepcopy(a);a['end']=len(rep['text'])
forged=delivered_evidence(question_label_set=labels,ranked_passages=[a],representations=[rep],counter=FixtureCounts({a['passage_id']:1}))
results['forged_passage_context_recall']=[base['delivered_span_recall'],forged['delivered_span_recall']]
print(json.dumps(results,indent=2))
```
