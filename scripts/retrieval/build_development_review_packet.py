"""Render the public v4 development review as local Markdown pages; no review decisions.

Run as a module from the repository root. Exact source excerpts stay under ignored outputs/.
This fixed-input renderer never accepts protected questions or modifies evaluation labels.
"""
import argparse
import hashlib
import html
import json
from pathlib import Path
import re

from src.retrieval.development_set import checked_json, validate_draft
from src.retrieval.development_review import validate_review

ROOT = Path(__file__).resolve().parents[2]
GRADES = {'direct': 'Direct support', 'partial_context': 'Background context',
          'contradicting_or_limiting': 'Limit or conflicting evidence',
          'not_relevant': 'Does not answer this question', 'uncertain': 'Uncertain'}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(output):
    output = output.resolve()
    if not output.is_relative_to((ROOT / 'outputs/prowl').resolve()) or output.exists():
        raise ValueError('Use a new directory under repository outputs/prowl')
    suite_path = ROOT / 'configs/evidence/evaluation/development-v4-draft.json'
    answers_path = ROOT / 'docs/capstone/retrieval/DEVELOPMENT-QUESTIONS-AND-ANSWERS.md'
    review_path = ROOT / 'configs/evidence/evaluation/development-v4-human-review.json'
    manifest_path = ROOT / 'configs/evidence/corpus-coverage-v1.json'
    suite = json.loads(suite_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    bundles = [checked_json(s['bundle'], ROOT) for s in manifest['sources']]
    report = validate_draft(suite, manifest, bundles,
        [checked_json(b, ROOT) for b in manifest['batches']],
        manifest_sha256=sha(manifest_path),
        regression_sha256=sha(ROOT / 'configs/evidence/evaluation/development-v1.json'),
        information_needs_sha256=sha(ROOT / 'docs/capstone/retrieval/planning/INFORMATION-NEEDS-V2.md'),
        information_needs_base_sha256=sha(ROOT / 'docs/capstone/retrieval/planning/INFORMATION-NEEDS.md'))
    review_report = validate_review(json.loads(review_path.read_text()), suite,
                                    answers_sha256=sha(answers_path))
    sections = re.findall(r'^### (\d+)\. (.*?)\n(.*?)(?=^### |^## |\Z)',
                          answers_path.read_text(), re.M | re.S)
    if ([int(n) for n, _, _ in sections] != list(range(1, 31))
            or [q for _, q, _ in sections] != [c['question'] for c in suite['cases']]):
        raise ValueError('Readable questions do not match the draft')
    by_rep = {b['representation']['representation_id']: b for b in bundles}
    by_work = {b['work']['work_id']: b for b in bundles}
    # Build all pages before creating output; fail rather than leave an incomplete review packet.
    pages = {}
    index = ['# Development evidence review — one question at a time', '',
        'These are evaluation references, not live model outputs or searchable RAG evidence.', '',
        f'[Read all 30 questions and their evidence in one document]({output / "all-questions.md"})', '',
        'Start with question 1. Each page combines the expected answer, required facts, exact source',
        'excerpts, limitations and source judgments. No decision is recorded by opening a page.', '',
        'Reply by question number with **accept**, **revise**, or **unsure**. Distinguish wording/answer',
        'feedback from evidence-label review. Uncertainty is useful feedback; do not guess.', '',
        'Changed questions: **1, 3, 5, 7, 9, 10, 12, 16, 17, 19**. All thirty need the final review.', '']
    for (number, question, body), case in zip(sections, suite['cases']):
        match = re.search(r'\*\*Expected (?:answer|response)\*\*\s*\n(.*?)(?=\n\*\*(?:Source|Sources|Basis):)', body, re.S)
        if match is None:
            raise ValueError('Expected answer block missing')
        filename = f'question-{int(number):02}.md'
        index.append(f'- [{number}. {question}]({output / filename})')
        lines = [f'# {number}. {question}', '', f'[All questions]({output / "README.md"})', '',
            '**Review example — not a generated answer.**', '', '## Expected answer', '',
            match.group(1).strip(), '', '## What the evidence must establish', '']
        lines += [f'- {c["description"]} (`{c["id"]}`)' for c in case['concepts']]
        if not case['concepts']:
            lines.append(f'Expected behavior: **{case["expected"]["status"]}** — {case["expected"]["reason"]}.')
        lines += ['', f'**Boundary:** {case["expected"]["boundary"]}', '', '## Exact source evidence', '']
        for n, span in enumerate(case['labels']['spans'], 1):
            bundle = by_rep[span['representation_id']]
            citation = bundle['citation']
            quote = bundle['representation']['text'][span['start']:span['end']]
            authors = citation['authors'][0] + (' et al.' if len(citation['authors']) > 1 else '')
            lines += [f'### Evidence {n} — {GRADES[span["grade"]]}', '',
                f'[{citation["title"]}]({citation["url"]})', '',
                f'{authors} ({citation["year"]}). {citation["attribution"]} '
                f'[License]({citation["license_url"]}).', '',
                '> ' + html.escape(quote).replace('\n', '\n> '), '',
                f'Concepts: {", ".join(span["concept_ids"]) or "context/limitation only"}. '
                f'Normalized offsets: [{span["start"]}, {span["end"]}).', '']
        if not case['labels']['spans']:
            lines += ['No gold spans: this case requires refusal or acknowledgement of missing evidence.',
                'This is not proof that the topic is absent from all medical literature.', '',
                f'[Scope policy]({ROOT / "docs/capstone/retrieval/AI-EXPERT-CONTRACT-V1.md"}) · '
                f'[Corpus coverage]({ROOT / "docs/capstone/retrieval/CORPUS-FREEZE-2026-10-17.md"})', '']
        lines += ['## Source judgments to review', '']
        for judgment in case['source_judgments']:
            citation = by_work[judgment['work_id']]['citation']
            lines.append(f'- [{citation["pmcid"]}]({citation["url"]}) — **{GRADES[judgment["grade"]]}**: {judgment["rationale"]}')
        if not case['source_judgments']:
            lines.append('No positive source judgments are assigned to an unsupported/refused case.')
        lines += ['', '## Your decision', '',
            f'- Wording and expected answer: **{ "pending" if case["id"] in review_report["pending"]["wording_and_answer"] else "accepted in record" }**',
            f'- Evidence labels: **{ "pending" if case["id"] in review_report["pending"]["evidence_labels"] else "accepted in record" }**',
            '- Check required facts, study/organ identity, limitations and alternate source support.',
            '- Reply accept/revise/unsure with any concern. This page does not submit decisions.', '',
            f'Case `{case["id"]}` · version {case["version"]} · content SHA `{case["content_sha256"]}`.',
            f'Draft SHA `{suite["content_sha256"]}`. Source excerpts are local CC BY 4.0 material; keep off Git.', '']
        pages[filename] = '\n'.join(lines)
    pages['all-questions.md'] = ('# Complete development evidence review\n\n'
        'All thirty questions, expected answers and evidence in one reading pass. '
        'Review examples, not live model outputs. Opening this file does not record decisions.\n\n'
        + '\n\n---\n\n'.join(pages.values()))
    pages['README.md'] = '\n'.join(index) + '\n'
    output.mkdir(parents=True, exist_ok=False)
    for name, content in pages.items():
        (output / name).write_text(content)
    receipt = dict(development_content_sha256=suite['content_sha256'],
        answers_sha256=sha(answers_path), review_sha256=sha(review_path),
        renderer_sha256=sha(Path(__file__)), question_count=30,
        span_count=sum(len(c['labels']['spans']) for c in suite['cases']),
        validation_state=report['state'], ready_for_tuning=False,
        files={name: sha(output / name) for name in pages})
    (output / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    return output / 'README.md'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    print(build(parser.parse_args().output))
