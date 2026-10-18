"""Render retained diagnostic drafts and their exact citations as local Markdown."""
import json
from pathlib import Path
from src.retrieval.evidence_experiment import corpus_records

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'outputs/prowl/evidence-isolation-v1-20261018'


def main():
    config = json.loads((ROOT/'configs/evidence/evidence-isolation-v1.json').read_text())
    result = json.loads((ROOT/'configs/evidence/evidence-isolation-v1-results.json').read_text())
    run = json.loads((OUT/'receipt.json').read_text())
    canonical = {s['source']: s for s in corpus_records(ROOT, config['manifest']).values()}
    audits = {(e['id'],e['arm']): e for e in result['entries']}
    outcomes = {(e['id'],e['arm']): e for e in run['outcomes']}
    labels = dict(retrieved_flat='Current search passages', curated_flat='Checked passages',
                  curated_linked='Same checked passages with study links')
    lines = ['# Controlled experiment: actual answers', '',
        '**Experimental drafts, not approved medical answers. Nothing here was promoted to the UI.**', '',
        'All nine drafts completed. None met the original completeness requirements. These are actual',
        'model outputs, preserved before validation. Read the audit below each answer; citations link',
        'to exact original passages in the separate evidence file. Uncertain support is kept separate',
        'from definite errors. This is one engineering review, not independent acceptance.', '']
    evidence = ['# Original passages used in the controlled experiment', '',
        'Local evidence only. Passage text and attribution come from the unchanged canonical corpus.', '']
    for case in config['cases']:
        cid=case['id']; inputs={a:json.loads((OUT/(cid+'-'+a+'-input.json')).read_text()) for a in config['arms']}
        lines += ['## '+inputs['curated_flat']['question'], '']
        union={s['source']:s for value in inputs.values() for s in value['sources']}
        for arm in config['arms']:
            value=outcomes[(cid,arm)]; audit=audits[(cid,arm)]
            lines += ['### '+labels[arm], '', f"Draft: {value['draft_seconds']:.2f}s · Draft + review: {value['seconds']:.2f}s", '']
            for i,claim in enumerate(value['draft']['claims'],1):
                refs=' '.join(f"[{ref['source']}](evidence.md#{cid}-{ref['source'].lower()})" for ref in claim['citations'])
                lines += [claim['text']+' '+refs, '']
            lines += ['**Review:** '+audit['completeness_reason'], '']
            for claim in audit['claims']:
                lines += [f"- Paragraph {claim['claim']} — **{claim['manual_support']}**: {claim['reason']}"]
            lines += ['', 'Factual reviewer: '+', '.join(f"paragraph {c['claim']} {c['model_support']}" for c in audit['claims'])+'.',
                '', 'Mechanical checks: '+('; '.join(i['reason'] for i in audit['mechanical_issues']) or 'No issues detected.') , '']
        evidence += ['## '+inputs['curated_flat']['question'], '']
        for sid,s in sorted(union.items(),key=lambda pair:int(pair[0][1:])):
            record=canonical[sid]['record']; citation=record['citation']; p=record['passage']
            evidence += [f'### {cid}-{sid.lower()}', '', f"**{sid}: [{s['title']}]({citation['url']})**", '',
                'Authors: '+', '.join(citation['authors'])+'.', '',
                f"Section `{p['section_id']}` · passage ordinal {p['ordinal']} · `{p['passage_id']}`", '',
                '> '+s['text'], '', citation['attribution']+' · '+citation['license_url'], '']
    for name,content in [('all-answers.md',lines),('evidence.md',evidence)]:
        with (OUT/name).open('x') as f: f.write('\n'.join(content)+'\n')
    print(OUT/'all-answers.md')


if __name__=='__main__': main()
