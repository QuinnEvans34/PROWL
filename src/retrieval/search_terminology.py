"""Auditable broadening of pancreatic search terms, never answers or clinical assertions."""
import re


def normalize_search_terms(question):
    if not isinstance(question,str) or not 1<=len(question.strip())<=500:
        raise ValueError('Invalid question')
    if not re.search(r'\bpancrea\w*\b',question,re.I):return question
    expanded=re.sub(r'\binflammation\b','inflammation (pancreatitis)',question,flags=re.I)
    if re.search(r'\b(diseases?|conditions?|abnormal\w*|patholog\w*|indicate\w*)\b',question,re.I):
        expanded=re.sub(r'\b(size|dimensions?)\b',r'\1 changes (enlargement, swelling or atrophy)',expanded,flags=re.I)
    return expanded if len(expanded)<=500 else question
