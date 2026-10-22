"""Small, explicit literature intent vocabulary; not a general language classifier.

Keep the original question for retrieval/display. Normalization is for matching only.
Ambiguity and negation are not repaired by deleting words or guessing a positive intent.
"""
import re
import unicodedata


def interpret_question(question):
    text = unicodedata.normalize('NFKC', question).casefold().replace('’', "'")
    for pattern, replacement in (
        (r'\bcomputed tomography\b', 'ct'),
        (r'\bmagnetic resonance(?: imaging)?\b', 'mri'),
        (r'\blongest dimension\b', 'diameter'),
        (r'\bvolumetric(?: measurement)?\b', 'volume'),
    ):
        text = re.sub(pattern, replacement, text)
    has = lambda pattern: re.search(pattern, text) is not None
    subject = 'pancreas' if has(r'\b(pancrea\w*|pdac|mfcp)\b') else 'unspecified'
    modalities = [m for m, p in [('CT', r'\bct\b'), ('MRI', r'\b(mri|mrcp)\b'),
        ('ultrasound', r'\b(ultrasound|eus|us)\b'), ('PET', r'\bpet\b')] if has(p)]
    task = ('contour_review' if has(r'\b(contours?|outlines?|outlining|segment\w*|delineat\w*|radiomics|dice|dsc)\b')
        else 'study_limitations' if has(r'\b(limitations?|weakness\w*|bias\w*|cautions?)\b')
        else 'measurement' if has(r'\b(size|volume|diameter|large|big)\b')
        else 'literature_explanation')
    return dict(subject=subject, task=task, modalities=modalities,
        context='current_scan' if has(r'\b(this|my|our|your|current)\s+(?:\w+\s+){0,2}(pancrea\w*|scan|lesion|tumou?r|patient|case)\b') else 'literature',
        negated=has(r"\b(no|not|never|without|except|exclude|instead)\b|\b(don't|doesn't|isn't|can't)\b"),
        matching_text=text)
