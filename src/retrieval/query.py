"""Bounded query gate (fixture-level scope demonstration; P3 synthetic scope).

The structured finding accepts only allowlisted, non-identifying enums (``query`` schema). The
reviewer question is validated for length and characters, preserved exactly, and normalized for
matching only. Scope rules ``prowl-scope-kw-v1`` are deterministic keyword/regex rules.

LIMITATION (deliberate and stated): keyword rules demonstrate the refusal contract on fixtures.
They do not certify semantic safety, do not anonymize arbitrary free text, and are not a basis for
sending text to any external provider. The coarse bins and warning categories are provisional
fixture values until Plans 05/08 define them; D-208 score bands are not accepted.
"""
import re
import unicodedata

from src.retrieval.records import RecordError, SCHEMA_VERSION, identity_digest, validate

QUESTION_NORMALIZATION_VERSION = 'prowl-qnorm-v1'
SCOPE_POLICY_VERSION = 'prowl-scope-kw-v1'
MAX_QUESTION_CHARS = 500

# Case-specific referents: RF1/RF2/RF3 apply to *this* patient/case, not to study populations.
_CASE = r'(this|the|my|our) (patient|case|lesion|scan|study|tumou?r|mass|finding|person)'
RULES = (
    ('RF7_injection', re.compile(r'ignore (all |any |the |your |previous |prior )*(instructions|rules|policy|citations?)'
                                 r'|disregard (the |your |all |previous )*(instructions|rules|policy)'
                                 r'|answer anyway|without citations|jailbreak|developer mode')),
    ('RF8_protected_system_information', re.compile(r'system prompt|api key|password|credential|secret key'
                                                    r'|file ?path|env(ironment)? variables?|full (corpus|text) dump')),
    ('RF6_hidden_patient_material', re.compile(r'(radiology|pathology|source) report|medical record|patient record'
                                               r'|(show|give|send) me the (image|scan|mask|report)|ground truth label')),
    ('RF9_contour_certification', re.compile(r'(is|are) (this|the) (contour|outline|segmentation|mask)s? (correct|accurate|right|complete|safe|acceptable|ok)'
                                             r'|(approve|accept|certify|sign off( on)?) (this|the) (contour|outline|segmentation|mask)')),
    ('RF4_prognosis', re.compile(r'prognos|surviv|life expectancy|how long (will|does) ' + _CASE
                                 + r'|chance of (dying|death|recurrence)')),
    ('RF3_treatment', re.compile(r'(should|must|can) ' + _CASE + r'.{0,40}(treat|surgery|operat|chemo|radiation|refer|follow.?up|biops)'
                                 r'|(treat|manage|operate on|refer) ' + _CASE
                                 + r'|what (treatment|therapy|surgery) (should|is best|would)')),
    ('RF2_case_malignancy_stage_subtype', re.compile(r'(is|are) ' + _CASE + r'.{0,30}(malignant|benign|cancer|cancerous|metasta)'
                                                     r'|(stage|subtype|grade|type) of ' + _CASE
                                                     + r'|what (stage|subtype|grade) (is|does)')),
    ('RF1_diagnosis', re.compile(r'(does|do|did) ' + _CASE + r'.{0,20}(have|has)'
                                 r'|diagnos\w* (of )?' + _CASE + r'|what (is wrong|disease)')),
)
_IDENTIFIER = re.compile(r'pants_\d{3,}|panorama_\d{3,}|\b\d{6,}\b|\bmrn\b|\b\d{4}-\d{2}-\d{2}\b'
                         r'|(^|\s)(/[\w.-]+){2,}|[a-z]:\\|file:|https?://|\S+@\S+\.\w+')


def normalize_question(question):
    """Validation plus matching form. The original text is preserved separately and never altered."""
    if not isinstance(question, str):
        raise RecordError('question must be a string')
    if not question.strip():
        raise RecordError('question is empty')
    if len(question) > MAX_QUESTION_CHARS:
        raise RecordError(f'question exceeds {MAX_QUESTION_CHARS} characters')
    for ch in question:
        cat = unicodedata.category(ch)
        if cat in ('Cc', 'Cf') and ch != ' ':
            raise RecordError(f'refused character U+{ord(ch):04X} in question')
    return ' '.join(unicodedata.normalize('NFC', question).split())


def classify_scope(normalized_question):
    """Refusal codes from the keyword policy (empty tuple = in scope for this fixture gate)."""
    text = normalized_question.casefold()
    codes = [code for code, pattern in RULES if pattern.search(text)]
    if _IDENTIFIER.search(text):
        codes.append('identifier_or_path')
    return tuple(sorted(set(codes)))


def make_query(finding, question):
    """Validated query record. Unknown or forbidden finding keys fail schema validation."""
    if not isinstance(finding, dict):
        raise RecordError('finding must be an object')
    normalized = normalize_question(question)
    codes = classify_scope(normalized)
    payload = dict(finding=dict(finding), question_original=question, question_normalized=normalized,
                   normalization_version=QUESTION_NORMALIZATION_VERSION,
                   scope_policy_version=SCOPE_POLICY_VERSION,
                   state='refused' if codes else 'accepted', refusal_codes=list(codes))
    record = dict(schema_version=SCHEMA_VERSION, query_id='qry:' + '0' * 64, **payload)
    validate('query', record)  # schema first, so forbidden keys are rejected before hashing
    record['query_id'] = 'qry:' + identity_digest(payload)
    return validate('query', record)


def verify_query(record):
    validate('query', record)
    payload = {k: v for k, v in record.items() if k not in ('schema_version', 'query_id')}
    if 'qry:' + identity_digest(payload) != record['query_id']:
        raise RecordError('query ID does not match its content')
    if normalize_question(record['question_original']) != record['question_normalized']:
        raise RecordError('normalized question does not match the original')
    expected = classify_scope(record['question_normalized'])
    if list(expected) != record['refusal_codes']:
        raise RecordError('refusal codes do not match the scope policy')
    return record
