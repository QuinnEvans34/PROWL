"""Strict parsing of ordinary prose with terminal canonical-source references."""
import re
from .natural_answer import validate_draft, validate_question_claims


def parse_prose(text,sources,question):
    if not isinstance(text,str) or len(text)>5000:raise ValueError('Invalid prose size')
    if text.strip()=='INSUFFICIENT':return dict(grounding='',claims=[])
    parts=re.split(r'\n\s*\n',text.strip())
    if not 1<=len(parts)<=3:raise ValueError('Invalid paragraph count')
    lookup={s['source']:s['text'] for s in sources};claims=[]
    for part in parts:
        match=re.fullmatch(r'(.+?)\s*\[(P[0-9]+(?:\s*,\s*P[0-9]+)*)\]\s*\.?',part,re.S)
        if not match:raise ValueError('Missing terminal source markers')
        prose=' '.join(match[1].split())
        if '[' in prose or ']' in prose:raise ValueError('Unbound embedded references')
        ids=re.findall(r'P[0-9]+',match[2])
        if len(ids)>3 or any(i not in lookup for i in ids):raise ValueError('Invalid source references')
        claims.append(dict(text=prose,citations=[dict(source=i,quote=lookup[i]) for i in ids]))
    if sum(len(c['text'].split()) for c in claims)>150:raise ValueError('Prose word budget exceeded')
    draft=validate_draft(dict(grounding='',claims=claims),sources,max_citations=3)
    return validate_question_claims(question,draft)
