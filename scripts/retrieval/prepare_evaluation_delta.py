"""Prepare fixed public v5→v6 changes and post-v3 exposures; never read protected inputs.

Run from repository root. Outputs are new local review files, not acceptance events.
"""
import hashlib
import json
from pathlib import Path

from src.retrieval.development_review import validate_delta_review, validate_review
from src.retrieval.development_set import checked_json, validate_draft
from src.retrieval.direct_ingestion import digest
from src.retrieval.evaluation_delta import delta_cases, extend_exposure
from src.retrieval.public_exposure import current_public_preflight, load_current_exposure

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'outputs/prowl/evaluation-preparation-20261020'
CFG = 'configs/evidence/evaluation/'


def read(path):
    return json.loads((ROOT / path).read_text())


def pin(path):
    return dict(path=path, sha256=hashlib.sha256((ROOT / path).read_bytes()).hexdigest())


def build():
    if OUT.exists():
        raise ValueError('Preserve existing preparation; select a new version before rerunning')
    preflight = current_public_preflight(ROOT)
    before, after = [read(CFG + f'development-{v}-draft.json') for v in ('v5', 'v6')]
    old_answers = (ROOT / 'docs/capstone/retrieval/DEVELOPMENT-QUESTIONS-AND-ANSWERS-V5.md').read_text()
    prior_review = validate_delta_review(read(CFG+'development-v5-human-review.json'), before, old_answers,
        prior_suite=read(CFG+'development-v4-draft.json'),
        prior_record=read(CFG+'development-v4-human-review.json'),
        prior_answers=(ROOT/'docs/capstone/retrieval/DEVELOPMENT-QUESTIONS-AND-ANSWERS.md').read_text())
    assert prior_review['development_review_attested_complete']
    current_review = validate_review(read(CFG+'development-v6-human-review.json'), after,
        answers_sha256=pin('outputs/prowl/development-v6-review-20261017/all-questions.md')['sha256'])
    manifest_path = 'configs/evidence/corpus-disease-v1.json'
    manifest = read(manifest_path)
    bundles = [checked_json(s['bundle'], ROOT) for s in manifest['sources']]
    validation = validate_draft(after, manifest, bundles,
        [checked_json(b, ROOT) for b in manifest['batches']],
        manifest_sha256=pin(manifest_path)['sha256'],
        regression_sha256=pin(CFG+'development-v1.json')['sha256'],
        information_needs_sha256=pin('docs/capstone/retrieval/planning/INFORMATION-NEEDS-V3.md')['sha256'],
        information_needs_base_sha256=pin('docs/capstone/retrieval/planning/INFORMATION-NEEDS.md')['sha256'],
        information_needs_parent_sha256=pin('docs/capstone/retrieval/planning/INFORMATION-NEEDS-V2.md')['sha256'])
    delta = delta_cases(before['cases'], after['cases'])
    parent = load_current_exposure(ROOT)
    sources = []
    for path in ('configs/evidence/record-search-screen-v1.json', 'configs/evidence/week3-quality-matrix-v1.json'):
        data = read(path)
        if data.get('scope', data.get('exposure')) not in (
                'exposed_engineering_screen_not_independent_evaluation', 'development_only_not_independent'):
            raise ValueError('Unexpected exposure source scope')
        sources.append(dict(**pin(path), exposure='development_only',
                            cases=[dict(id=c['id'], question=c['question']) for c in data['cases']]))
    exposure = dict(version='prowl-public-exposure-v4-preparation', parent=pin(CFG+'public-exposure-v3.json'),
        sources=sources, inventory=extend_exposure(parent['inventory'], sources),
        status='preparation_not_private_admission',
        limitations=['Named public matrices only; not an exhaustive conversation/test/UI inventory.',
                    'Semantic intent overlap requires independent review; exact wording is insufficient.',
                    'Private CLI remains disabled; admission must bind this inventory and subsequent exposure.'])
    exposure['content_sha256'] = digest(exposure)
    cases = {c['id']: c for c in after['cases']}
    reps = {b['representation']['representation_id']: b for b in bundles}
    pages = ['# Changes needing review — proposed development v6', '',
        'Review examples and evidence only; these are not model answers. Your accepted v4/v5 work is preserved.', '',
        '## Decisions needed', '',
        '1. Accept/revise the two replacement questions, expected concepts, evidence and new general-disease need N1.6.',
        '2. Accept/revise the added source evidence/judgments and two unchanged evidence-gap decisions below.',
        '3. Confirm consistency of the changes with retained questions: disease subtype, modality, population, units and limits.', '',
        'The Week3 demo acceptance is separate. No private questions are requested. Opening this packet records no decision.', '',
        'Removed from this proposed set (kept in exposure history): ' + ', '.join(delta['removed_ids']) + '.', '',
        'Unchanged question/expected concepts are summarized below, not sent for repeated full review.', '']
    appendix = ['# Added or changed source judgments', '',
        'Only differences from accepted v5. Prior source judgments remain in the original record.', '']
    for row in delta['cases']:
        c = cases[row['id']]
        if row['new'] or row['changed_core_fields'] or row['added_or_changed_spans']:
            pages += [f"## {c['question']}", '', f"Case: {c['id']}", '',
                      '**Expected meaning**', '']
            pages += ['- ' + x['description'] for x in c['concepts']]
            pages += ['', '**Limit:** ' + c['expected']['boundary'], '']
            for span in row['added_or_changed_spans']:
                b = reps[span['representation_id']]; cit = b['citation']
                text = b['representation']['text'][span['start']:span['end']]
                pages += [f"**{span['grade']}** — [{cit['title']}]({cit['url']})", '',
                    f"{cit['attribution']} · [License]({cit['license_url']})", '',
                    '> ' + text.replace('\n', '\n> '), '']
        if row['removed_spans'] or row['removed_judgments']:
            pages += [f"Changed/removed prior evidence for {c['id']}: see delta.json; no silent inheritance.", '']
        if row['added_or_changed_judgments']:
            appendix += [f"## {c['id']}: {c['question']}", '']
            appendix += [f"- {j['work_id']} — **{j['grade']}**: {j['rationale']}" for j in row['added_or_changed_judgments']]
            appendix += ['']
    impact = read(CFG+'disease-source-impact-v1.json')
    pages += ['## Evidence gaps and consistency', '']
    for row in impact['gap_rechecks']:
        pages += [f"- **{row['case_id']}**: {row['agent_judgment']}"]
    unchanged = [r['id'] for r in delta['cases'] if not r['changed_core_fields']]
    pages += ['', f'{len(unchanged)} retained questions have unchanged core fields/expected concepts.',
        'Added evidence does not turn MRI means into CT norms, cancer-cohort signs into differential proof,',
        'or literature findings into observations of the current scan.', '',
        '[Review only added/changed source judgments](source-judgment-changes.md).', '',
        'All prior accepted prose and full evidence remain available in their original packets; this packet records no new acceptance.']
    receipt = dict(version='evaluation-preparation-20261020', prior_review=prior_review,
        current_review=current_review, public_preflight=preflight, validation=validation,
        inputs=[pin(CFG+f'development-{v}-draft.json') for v in ('v5','v6')] + [pin(manifest_path)],
        counts=dict(retained_core_unchanged=len(unchanged), new_cases=sum(r['new'] for r in delta['cases']),
                    added_or_changed_spans=sum(len(r['added_or_changed_spans']) for r in delta['cases']),
                    added_or_changed_judgments=sum(len(r['added_or_changed_judgments']) for r in delta['cases'])),
        private_content_read=False, ready_for_private_authoring=False, ready_for_tuning=False)
    OUT.mkdir(parents=True)
    for name, value in [('delta.json',delta), ('exposure-v4-preparation.json',exposure), ('receipt.json',receipt)]:
        (OUT/name).write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n')
    (OUT/'changes-to-review.md').write_text('\n'.join(pages)+'\n')
    (OUT/'source-judgment-changes.md').write_text('\n'.join(appendix)+'\n')
    print(json.dumps(dict(counts=receipt['counts'], exposure_records=exposure['inventory']['record_count'],
                         exposure_wordings=exposure['inventory']['distinct_wording_count'], output=str(OUT))))


if __name__ == '__main__':
    build()
