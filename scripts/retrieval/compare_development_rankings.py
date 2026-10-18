#!/usr/bin/env python3
"""One fixed, read-only, exposed-development comparison; no protected input option.

See RETRIEVAL-DEVELOPMENT-COMPARISON-2026-10-17.md. New output directory is mandatory;
existing evidence is never overwritten. This does not promote a retriever into the live UI.
"""
import argparse
import json
import time
from pathlib import Path

from retrieval.direct_corpus import read_config, connect, encoder, limits
from src.retrieval.corpus_inventory import database_inventory
from src.retrieval.development_ranking import rank_candidates
from src.retrieval.development_set import checked_json, validate_draft
from src.retrieval.direct_ingestion import search
from src.retrieval.labels import gold_passages, gold_works
from src.retrieval.metrics import collapse_to_sources, recall_at_k, reciprocal_rank, span_hit_recall
from src.retrieval.records import sha256_hex

ROOT = Path(__file__).resolve().parents[2]
PLAN = 'docs/capstone/retrieval/RETRIEVAL-DEVELOPMENT-COMPARISON-2026-10-17.md'
DRAFT = 'configs/evidence/evaluation/development-v6-draft.json'


def pin(path):
    return dict(path=path, sha256=sha256_hex((ROOT/path).read_bytes()))


def write(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def score(ranking, case, records, representations):
    ids = [r['passage_id'] for r in ranking]
    if len(set(ids)) != len(ids) or any(pid not in records for pid in ids):
        raise ValueError('Invalid ranking membership')
    passages = {pid: r['passage'] for pid, r in records.items()}
    works = {pid: p['work_id'] for pid, p in passages.items()}
    gp = gold_passages(list(passages.values()), case['labels'])
    gw = gold_works(case['labels'], representations)
    source_ids = collapse_to_sources(ids, works)
    metrics = dict(depth=len(ids), unique_sources=len(source_ids),
        source_mrr=reciprocal_rank(source_ids, gw), passage_mrr=reciprocal_rank(ids, gp),
        top5_direct_hits=len(set(ids[:5]) & gp),
        top5_source_coverage=len({works[p] for p in ids[:5]} & gw)/len(gw),
        diagnostic_span_hit_at_5=span_hit_recall(ids, passages,
            [s for s in case['labels']['spans'] if s['grade']=='direct'], 5))
    for k in (1, 3, 5, 10):
        metrics[f'source_recall_at_{k}'] = recall_at_k(source_ids, gw, k)
        metrics[f'passage_recall_at_{k}'] = recall_at_k(ids, gp, k)
    return metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT/'outputs/prowl'):
        raise ValueError('Output must be a new local development directory')
    output.mkdir(parents=True, exist_ok=False)
    producing = [PLAN, DRAFT, 'configs/evidence/development-search-v1.json',
        'configs/evidence/corpus-disease-v1.json', 'src/retrieval/development_ranking.py',
        'scripts/retrieval/compare_development_rankings.py', 'src/retrieval/direct_ingestion.py',
        'src/retrieval/development_set.py', 'src/retrieval/metrics.py', 'src/retrieval/labels.py']
    receipt = dict(state='started', scope='exposed_development_not_formal_selection',
        pins=[pin(p) for p in producing], rankings=[], metrics=[], model_generation_calls=0)
    write(output/'receipt.json', receipt)
    start = time.monotonic()
    try:
        spec = json.loads((ROOT/'configs/evidence/development-search-v1.json').read_text())
        manifest = checked_json(spec['manifest'], ROOT)
        batches = [checked_json(p, ROOT) for p in manifest['batches']]
        bundles = [checked_json(s['bundle'], ROOT) for s in manifest['sources']]
        suite = json.loads((ROOT/DRAFT).read_text())
        receipt['validation'] = validate_draft(suite, manifest, bundles, batches,
            manifest_sha256=spec['manifest']['sha256'],
            regression_sha256=pin('configs/evidence/evaluation/development-v1.json')['sha256'],
            information_needs_sha256=pin('docs/capstone/retrieval/planning/INFORMATION-NEEDS-V3.md')['sha256'],
            information_needs_base_sha256=pin('docs/capstone/retrieval/planning/INFORMATION-NEEDS.md')['sha256'],
            information_needs_parent_sha256=pin('docs/capstone/retrieval/planning/INFORMATION-NEEDS-V2.md')['sha256'])
        cases = [c for c in suite['cases'] if c['expected']['status']=='answered']
        receipt['excluded_status_counts'] = {k: sum(c['expected']['status']==k for c in suite['cases'])
                                            for k in ('refused', 'insufficient_evidence')}
        records = {i['record']['passage']['passage_id']: i['record'] for b in batches for i in b['items']}
        config = read_config(ROOT/'infra/retrieval/.env.ingestion.json'); limits(config)
        model = encoder(config)
        if model.id != spec['encoder_id']:
            raise ValueError('Encoder differs from baseline')
        with connect(config) as db:
            with db.transaction():
                db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
                db.execute("SET LOCAL statement_timeout='30s'")
                if db.execute('SELECT pg_database_size(current_database())').fetchone()[0] > 8*1024**3:
                    raise ValueError('Database size cap exceeded')
                if database_inventory(db, spec['collection']) != manifest['inventory']:
                    raise ValueError('Database corpus differs from frozen inventory')
                receipt['database_identity_verified'] = True
                for index, case in enumerate(cases):
                    limits(config)
                    begin = time.monotonic()
                    ranks = rank_candidates(db, spec['collection'], model, case['question'])
                    entry = dict(id=case['id'], question=case['question'], rankings=ranks,
                                 seconds=time.monotonic()-begin)
                    receipt['rankings'].append(entry)
                    write(output/'receipt.json', receipt)
                    if index == 0:
                        reference = search(db, spec['collection'], model, case['question'], 5)
                        if [(h['record']['passage']['passage_id'], h['score']) for h in reference] != [
                                (h['passage_id'], h['score']) for h in ranks['dense'][:5]]:
                            raise ValueError('Dense baseline parity failed')
                        receipt['dense_top5_parity'] = True
                    print(f"Ranked {index+1}/{len(cases)} {case['id']}", flush=True)
        # All retrieval is complete before relevance scoring. No label field went to SQL/encoder.
        reps = [b['representation'] for b in bundles]
        by_case = {c['id']: c for c in cases}
        for entry in receipt['rankings']:
            receipt['metrics'].append(dict(id=entry['id'], candidates={name:
                score(ranks, by_case[entry['id']], records, reps) for name, ranks in entry['rankings'].items()}))
        receipt['means'] = {name: {key: sum(row['candidates'][name][key] for row in receipt['metrics'])/len(cases)
            for key in receipt['metrics'][0]['candidates'][name]} for name in ('dense','lexical','hybrid')}
        base = receipt['means']['dense']
        disease = [r for r in receipt['metrics'] if r['id'] in ('q:dev6-31','q:dev6-32')]
        receipt['candidate_checks'] = {}
        for name in ('lexical', 'hybrid'):
            m = receipt['means'][name]
            checks = dict(source_recall_improves=m['source_recall_at_5'] > base['source_recall_at_5'],
                source_mrr_nonregression=m['source_mrr'] >= base['source_mrr'],
                passage_recall_nonregression=m['passage_recall_at_5'] >= base['passage_recall_at_5'],
                both_disease_top5_improve=len(disease)==2 and all(
                    r['candidates'][name]['top5_direct_hits'] > r['candidates']['dense']['top5_direct_hits'] for r in disease))
            receipt['candidate_checks'][name] = dict(checks, qualifies=all(checks.values()))
        qualified = [n for n, c in receipt['candidate_checks'].items() if c['qualifies']]
        receipt['preview_candidate'] = max(qualified, key=lambda n: (receipt['means'][n]['source_recall_at_5'],
            receipt['means'][n]['source_mrr'], -('dense','lexical','hybrid').index(n))) if qualified else None
        receipt['state'] = 'completed'
    except Exception as exc:
        receipt.update(state='failed', failure_type=type(exc).__name__)
        raise
    finally:
        receipt['seconds'] = time.monotonic()-start
        write(output/'receipt.json', receipt)
    print(json.dumps(dict(state=receipt['state'], means=receipt['means'],
                         candidate_checks=receipt['candidate_checks']), indent=2))


if __name__ == '__main__':
    main()
