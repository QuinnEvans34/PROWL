"""Render retained quality responses as readable Markdown; performs no network/model work."""
import argparse
import json
from pathlib import Path


def render(directory):
    receipt = json.loads((directory/'receipt.json').read_text())
    if receipt['state'] != 'completed' or len(receipt['cases']) != 30:
        raise ValueError('A completed fixed batch is required')
    intro = ['# Week 3 questions and answers', '',
             'Exposed development check. These are actual retained responses, not promised answers.',
             'Source passages are in a separate file so the answers are easy to read.',
             'Engineering review does not replace independent evaluation or your walkthrough.', '']
    sources = {}
    sections = []
    for case in receipt['cases']:
        saved = json.loads((directory/(case['id']+'.json')).read_text())
        result = saved['response']
        lines = [f"## {case['id']}: {case['question']}", '',
                 f"Result: {case['generation']}. Time: {case['seconds']:.2f} seconds.", '']
        answer = result.get('answer')
        if answer:
            evidence = {e['rank']: e['record'] for e in result['evidence']}
            for claim in answer['claims']:
                references = []
                for citation in claim['citations']:
                    record = evidence[citation['rank']]
                    pid = record['passage']['passage_id']
                    key = pid.split(':')[1]
                    sources[key] = record
                    references.append(f"[Source {citation['rank']}](sources.md#source-{key})")
                lines.extend([claim['text'], '', ' · '.join(references), ''])
            lines.extend([answer['scope'], '', answer['limitation'], ''])
        else:
            lines.extend(['No composed answer was returned.', '',
                          f"Reason: `{result['record_selection']['reason']}`. "
                          'This question needs clarification or is outside the reviewed answer coverage.', ''])
        lines.extend(['Checks: '+', '.join(f"{k}={'pass' if v else 'fail'}" for k, v in case['checks'].items()), ''])
        (directory/(case['id']+'.md')).write_text('\n'.join(lines))
        sections.extend(lines)
    (directory/'all-questions.md').write_text('\n'.join(intro+sections))
    source_lines = ['# Retained source passages', '', 'Canonical corpus text, grouped once by passage identity.', '']
    for key, record in sources.items():
        cite, passage = record['citation'], record['passage']
        source_lines.extend([f'## Source {key}', '', f"[{cite['title']}]({cite['url']})", '',
            f"PMID {cite['pmid']}; {passage['section_id']}; retained passage {passage['ordinal']}; "
            f"characters {passage['start']}–{passage['end']}.", '', record['text'], '',
            f"{cite.get('attribution', '')} · [License]({cite['license_url']})", ''])
    (directory/'sources.md').write_text('\n'.join(source_lines))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    render(parser.parse_args().directory)
