"""Opt-in qualitative literature facts; deterministic assembly, no question routing.

Review hashes bind curated semantics, not clinical truth. No extraction or diagnostic model.
The deployed synthesis contract is intentionally not changed by this offline prototype.
"""
from copy import deepcopy
import hashlib

from src.retrieval.fact_records import digest

POLICY = 'reviewed-disease-facts-v1'
RELATIONS = {
    'occasionally_shows': 'occasionally shows',
    'predominant_site_for': 'is a predominant site for',
    'can_mimic': 'can resemble',
    'cannot_reliably_distinguish': 'cannot reliably distinguish',
    'depends_on': 'depends on',
    'favors': 'favors',
    'best_seen': 'is best seen with',
    'likely_shows': 'is likely to show',
    'more_likely_in': 'is more likely in',
    'usually_shows': 'usually shows',
}
PROFILES = {
    (('MFCP', 'PDAC'), 'focal_head_mass'): {'finding', 'overlap', 'single_feature_limit', 'combination_limit'},
    (('MFCP', 'PDAC'), 'imaging_differentiation'): {'finding', 'method', 'overlap', 'single_feature_limit', 'combination_limit'},
    (('focal_AIP', 'PDAC'), 'imaging_differentiation'): {'finding', 'overlap'},
}
APPLICATION_LIMIT = ('These are literature comparisons, not findings from your scan. '
                     'They do not establish an individual diagnosis or a numerical pancreas-head size threshold.')


def record_digest(record, spans):
    refs = {sid for fact in record['facts'] for sid in fact['evidence']}
    return digest(dict(record=record, spans={sid: spans[sid] for sid in sorted(refs)}))


class DiseaseFactCatalog:
    """Require source identity, reviewed relationships, and complete comparison qualifiers."""

    def __init__(self, catalog, review, canonical):
        if set(catalog) != {'version', 'manifest', 'spans', 'records'} or catalog['version'] != POLICY:
            raise ValueError('Unsupported disease catalog')
        if (review['catalog_version'] != POLICY or review['status'] != 'engineering_reviewed'
                or review['manifest'] != catalog['manifest']):
            raise ValueError('Review/corpus mismatch')
        self._records = {}; self._evidence = {}; self._citations = {}
        by_id = {s['passage_id']: s for s in canonical.values()}
        self._hit_hashes = {pid: digest(s['record']) for pid, s in by_id.items()}
        for sid, span in catalog['spans'].items():
            if set(span) != {'passage_id', 'work_id', 'ordinal', 'start', 'end', 'text_sha256'}:
                raise ValueError('Invalid source span')
            source = by_id[span['passage_id']]; p = source['record']['passage']
            start, end = span['start'], span['end']
            if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(source['text'])
                    or span['work_id'] != p['work_id'] or span['ordinal'] != p['ordinal']):
                raise ValueError('Invalid source location')
            quote = source['text'][start:end]
            if hashlib.sha256(quote.encode()).hexdigest() != span['text_sha256']:
                raise ValueError('Source span changed')
            self._evidence[sid] = dict(span=deepcopy(span), quote=quote)
            self._citations[span['passage_id']] = dict(passage_id=span['passage_id'], work_id=p['work_id'],
                ordinal=p['ordinal'], section_id=p['section_id'], quote=source['text'],
                citation=deepcopy(source['record']['citation']))
        if set(review['records']) != {r['id'] for r in catalog['records']}:
            raise ValueError('Review membership differs')
        for record in catalog['records']:
            self._validate(record, catalog['spans'], review)
            if record['id'] in self._records: raise ValueError('Duplicate record')
            self._records[record['id']] = deepcopy(record)

    def _validate(self, r, spans, review):
        if set(r) != {'id', 'work_id', 'organ', 'comparison', 'topic', 'facts', 'retrieval_anchors'}:
            raise ValueError('Invalid record shape')
        profile = (tuple(r['comparison']), r['topic'])
        if r['organ'] != 'pancreas' or profile not in PROFILES:
            raise ValueError('Unsupported comparison scope')
        if record_digest(r, spans) != review['records'][r['id']]:
            raise ValueError('Unreviewed interpretation')
        if {f['role'] for f in r['facts']} != PROFILES[profile]:
            raise ValueError('Required qualifications absent')
        for f in r['facts']:
            if set(f) != {'role', 'subject', 'relation', 'object', 'method', 'phase', 'evidence'}:
                raise ValueError('Invalid fact shape')
            if (f['relation'] not in RELATIONS or not f['evidence']
                    or any(not isinstance(f[k], str) or not f[k].strip() for k in ('subject', 'object'))):
                raise ValueError('Invalid source relation')
            if any(spans[s]['work_id'] != r['work_id'] for s in f['evidence']):
                raise ValueError('Cross-paper relationship')
            if (f['method'] not in (None, 'CT', 'MRCP', 'CT or MRI')
                    or f['phase'] not in (None, 'portal-venous')
                    or f['phase'] is not None and f['method'] != 'CT'):
                raise ValueError('Invalid modality/phase binding')
            role_relation = {'overlap': 'can_mimic', 'single_feature_limit': 'cannot_reliably_distinguish',
                             'combination_limit': 'depends_on', 'method': 'best_seen'}
            if f['role'] in role_relation and f['relation'] != role_relation[f['role']]:
                raise ValueError('Invalid qualification relationship')
        if profile == (('MFCP', 'PDAC'), 'imaging_differentiation'):
            if not any(f['role'] == 'method' and f['method'] == 'MRCP' for f in r['facts']):
                raise ValueError('MRCP qualifier absent')
        if r['comparison'] == ['focal_AIP', 'PDAC']:
            if not any(f['role'] == 'finding' and f['method'] == 'CT'
                       and f['phase'] == 'portal-venous' for f in r['facts']):
                raise ValueError('Focal AIP CT phase absent')
        evidence_ids = {spans[s]['passage_id'] for f in r['facts']
                        if f['role'] in ('finding', 'method') for s in f['evidence']}
        if not r['retrieval_anchors'] or not set(r['retrieval_anchors']) <= evidence_ids:
            raise ValueError('Anchor must locate a finding or method')

    def select(self, hit_records, intent):
        if set(intent) != {'organ', 'comparison', 'topic', 'use'}:
            raise ValueError('Invalid structured intent')
        if intent['use'] != 'literature_comparison':
            return dict(status='unsupported_use', record_ids=[])
        ids = set()
        for hit in hit_records:
            pid = hit['passage']['passage_id']
            if self._hit_hashes.get(pid) != digest(hit):
                raise ValueError('Noncanonical retrieved record')
            ids.add(pid)
        selected = sorted(rid for rid, r in self._records.items()
            if all(intent[k] == r[k] for k in ('organ', 'comparison', 'topic'))
            and ids.intersection(r['retrieval_anchors']))
        return dict(status='selected' if selected else 'no_eligible_record', record_ids=selected)

    def render(self, record_id):
        r = self._records[record_id]; statements = []
        for f in r['facts']:
            text = f"{f['subject']} {RELATIONS[f['relation']]} {f['object']}"
            if f['phase']: text += f" on {f['phase']} phase {f['method']}"
            elif f['method'] and f['role'] != 'method': text += f" on {f['method']}"
            text = text[0].upper() + text[1:]
            refs = sorted(set(f['evidence']))
            statements.append(dict(text=text+'.', kind='source_fact', role=f['role'], span_ids=refs,
                citations=sorted({self._evidence[s]['span']['passage_id'] for s in refs})))
        statements.append(dict(text=APPLICATION_LIMIT, kind='application_limit', role='scope_limit',
                               span_ids=[], citations=[]))
        used = {s for statement in statements for s in statement['span_ids']}
        pids = {p for statement in statements for p in statement['citations']}
        return dict(policy=POLICY, record_id=record_id, comparison=deepcopy(r['comparison']),
            topic=r['topic'], review='engineering_reviewed_independent_review_pending',
            statements=statements, evidence={s: deepcopy(self._evidence[s]) for s in sorted(used)},
            citations=[deepcopy(self._citations[p]) for p in sorted(pids)])

    def verify_answer(self, answer, *, record_id):
        if answer != self.render(record_id): raise ValueError('Answer differs from qualified assembly')
        return True
