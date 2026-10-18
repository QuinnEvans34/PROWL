"""Append canonical abstract and study-method passages for retrieved papers."""
import re


def with_source_context(hits,bundles,records):
    works={h['record']['passage']['work_id'] for h in hits}
    context=set()
    for b in bundles:
        rep=b['representation']
        if rep['work_id'] not in works:continue
        for section in rep['sections']:
            if (section['section_id'].startswith('abstract') or re.search(
                r'\b(subjects|participants|patient selection|study population|statistical analysis|data analysis)\b',
                section['title'],re.I)):
                context.add((rep['work_id'],section['section_id']))
    result=list(hits);seen={h['record']['passage']['passage_id'] for h in result}
    for r in sorted(records,key=lambda r:(r['passage']['work_id'],r['passage']['ordinal'])):
        p=r['passage']
        if (p['work_id'],p['section_id']) in context and p['passage_id'] not in seen:
            seen.add(p['passage_id']);result.append(dict(record=r,score=0.0))
    if len(result)>50 or sum(len(h['record']['text'])+len(h['record']['citation']['title']) for h in result)>30000:
        raise ValueError('Study context exceeds evidence budget')
    return result
