"""Opt-in reviewed literature fact records. No free-text routing or production integration.

Hashes preserve a reviewed interpretation; they do not prove that interpretation true.
Source checks establish identity/locations and limited literal correspondence, not entailment.
"""
from copy import deepcopy
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re

POLICY = 'reviewed-volume-facts-v1'
FIELDS = {'object', 'extent', 'quantity', 'unit', 'population', 'sample_size', 'method',
          'statistic', 'mean', 'uncertainty', 'uncertainty_kind', 'matching'}
LIMITS = ['selected_study_group', 'not_universal_average', 'not_ct_reference', 'not_patient_normality']
POPULATIONS = {
    'normal_glucose_tolerance_comparison': 'people with normal glucose tolerance in the comparison group',
    'well_controlled_type2_metformin': 'people with well-controlled type 2 diabetes taking only metformin',
}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def record_digest(record, spans):
    refs = {ref for field in record['fields'].values() for ref in field['evidence']}
    return digest(dict(record=record, spans={ref: spans[ref] for ref in sorted(refs)}))


def _literal(value, text):
    # A sentence-ending period is punctuation, not a decimal continuation.
    suffix = r'(?!\w|\.\d)' if re.fullmatch(r'\d+(?:\.\d+)?', str(value)) else r'(?!\w)'
    return re.search(r'(?<![\w.])'+re.escape(str(value))+suffix, text, re.I) is not None


class FactCatalog:
    """A detached snapshot of records admitted by a separately versioned review inventory."""

    def __init__(self, catalog, review, canonical):
        if set(catalog) != {'version', 'manifest', 'spans', 'records'} or catalog['version'] != POLICY:
            raise ValueError('Unsupported fact catalog')
        if review['catalog_version'] != POLICY or review['status'] != 'engineering_reviewed':
            raise ValueError('Missing engineering source review')
        if review['manifest'] != catalog['manifest']:
            raise ValueError('Review/corpus mismatch')
        self._records = {}; self._evidence = {}; self._citations = {}
        by_id = {s['passage_id']: s for s in canonical.values()}
        for sid, span in catalog['spans'].items():
            if set(span) != {'passage_id', 'work_id', 'ordinal', 'start', 'end', 'text_sha256'}:
                raise ValueError('Invalid span fields')
            source = by_id[span['passage_id']]; p = source['record']['passage']
            start, end = span['start'], span['end']
            if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(source['text'])
                    or span['work_id'] != p['work_id'] or span['ordinal'] != p['ordinal']):
                raise ValueError('Invalid canonical location')
            quote = source['text'][start:end]
            if hashlib.sha256(quote.encode()).hexdigest() != span['text_sha256']:
                raise ValueError('Source span changed')
            self._evidence[sid] = dict(span=deepcopy(span), quote=quote)
            self._citations[span['passage_id']] = dict(passage_id=span['passage_id'],
                work_id=p['work_id'], section_id=p['section_id'], ordinal=p['ordinal'],
                quote=source['text'], citation=deepcopy(source['record']['citation']))
        if set(review['records']) != {r['id'] for r in catalog['records']}:
            raise ValueError('Review membership differs')
        for record in catalog['records']:
            self._validate(record, catalog['spans'], review)
            if record['id'] in self._records: raise ValueError('Duplicate record')
            self._records[record['id']] = deepcopy(record)

    def _validate(self, record, spans, review):
        if set(record) != {'id', 'work_id', 'fields', 'limitations', 'retrieval_anchors'}:
            raise ValueError('Invalid record fields')
        if set(record['fields']) != FIELDS or record['limitations'] != LIMITS:
            raise ValueError('Required qualifications absent')
        if record_digest(record, spans) != review['records'][record['id']]:
            raise ValueError('Record/interpretation differs from reviewed version')
        fields = record['fields']
        for name, field in fields.items():
            if set(field) != {'value', 'evidence'} or not field['evidence']:
                raise ValueError('Unbound field')
            if any(spans[ref]['work_id'] != record['work_id'] for ref in field['evidence']):
                raise ValueError('Cross-paper field')
        values = {k: f['value'] for k, f in fields.items()}
        fixed = dict(object='pancreas', extent='whole_organ', quantity='volume', unit='cm3',
                     method='MRI', statistic='mean', uncertainty_kind='SEM', matching=['age', 'weight', 'sex'])
        if any(values[k] != v for k, v in fixed.items()) or values['population'] not in POPULATIONS:
            raise ValueError('Unsupported measured object/method/statistic')
        if type(values['sample_size']) is not int or values['sample_size'] < 1:
            raise ValueError('Invalid sample count')
        for key in ('mean', 'uncertainty'):
            try: number = Decimal(values[key])
            except (InvalidOperation, TypeError): raise ValueError('Invalid numerical result')
            if not isinstance(values[key], str) or not number.is_finite() or number <= 0:
                raise ValueError('Invalid numerical result')
        # Limited field-specific correspondence. Association of a group's values with its label
        # still depends on the pinned engineering review, not a numeric-token heuristic.
        patterns = dict(object='pancreas', extent='total pancreas volume', quantity='volume', unit='cm3',
            method='magnetic resonance imaging', statistic='mean', uncertainty_kind='SEM',
            population=('normal glucose tolerance' if values['population']=='normal_glucose_tolerance_comparison'
                        else 'well-controlled type 2 diabetes'))
        for name, field in fields.items():
            quotes = ' '.join(self._evidence[ref]['quote'] for ref in field['evidence'])
            if name in patterns and patterns[name].casefold() not in quotes.casefold():
                raise ValueError('Field descriptor absent from its evidence')
            if name in ('mean', 'uncertainty', 'sample_size') and not _literal(values[name], quotes):
                raise ValueError('Numerical field absent from its evidence')
            if name == 'matching' and not all(_literal(v, quotes) for v in values[name]):
                raise ValueError('Matching factors absent from evidence')
            if name == 'population' and values[name]=='well_controlled_type2_metformin' and 'taking only metformin' not in quotes:
                raise ValueError('Treatment qualifier absent from evidence')
        mean_passages = {spans[s]['passage_id'] for s in fields['mean']['evidence']}
        if not record['retrieval_anchors'] or not set(record['retrieval_anchors']) <= mean_passages:
            raise ValueError('Retrieval anchor must locate the result')

    def select(self, hit_records, intent):
        """Trusted structured intent only; callers must separately qualify natural-language routing."""
        if set(intent) != {'object', 'extent', 'quantity', 'population', 'method', 'uncertainty_kind', 'use'}:
            raise ValueError('Invalid structured intent')
        if intent['use'] != 'literature_example':
            return dict(status='unsupported_use', record_ids=[])
        ids = set()
        for hit in hit_records:
            p = hit['passage']; pid = p['passage_id']
            if pid in self._citations:
                canonical = self._citations[pid]
                if (hit['text'] != canonical['quote'] or p['work_id'] != canonical['work_id']
                        or hit['citation'] != canonical['citation']):
                    raise ValueError('Retrieved record differs from canonical evidence')
            ids.add(pid)
        selected = []
        for rid, record in self._records.items():
            v = {k: f['value'] for k, f in record['fields'].items()}
            if not ids.intersection(record['retrieval_anchors']): continue
            if all(intent[k] == v[k] for k in ('object', 'extent', 'quantity', 'population', 'method', 'uncertainty_kind')):
                selected.append(rid)
        return dict(status='selected' if selected else 'no_eligible_record', record_ids=sorted(selected))

    def render(self, record_id):
        record = self._records[record_id]; f = record['fields']; v = {k: x['value'] for k,x in f.items()}
        statements = []
        def add(text, fields, kind='source_fact'):
            spans = sorted({ref for key in fields for ref in f[key]['evidence']})
            passages = sorted({self._evidence[s]['span']['passage_id'] for s in spans})
            statements.append(dict(text=text, kind=kind, fields=fields, span_ids=spans, citations=passages))
        add(f"One MRI study reported a mean whole-pancreas volume of {v['mean']} cm³ in "
            f"{v['sample_size']} {POPULATIONS[v['population']] }.",
            ['object','extent','quantity','unit','population','sample_size','method','statistic','mean'])
        add(f"The reported ±{v['uncertainty']} cm³ is the standard error of the mean (SEM): "
            "uncertainty in the estimated group mean, rather than a range of individual sizes.",
            ['uncertainty','uncertainty_kind','unit'], kind='source_fact_with_statistical_glossary')
        add('The study groups were matched for age, weight and sex.', ['matching'])
        add('Treat this as a result from a selected study group, not a universal average or a CT reference range. '
            'It cannot determine whether an individual scan is normal or abnormal.',
            ['population','sample_size','method'], kind='interpretation_limit')
        used = {pid for s in statements for pid in s['citations']}
        used_spans = {sid for s in statements for sid in s['span_ids']}
        return dict(policy=POLICY, record_id=record_id, work_id=record['work_id'],
            review='engineering_reviewed_independent_review_pending', statements=statements,
            limitations=deepcopy(record['limitations']),
            citations=[deepcopy(self._citations[p]) for p in sorted(used)],
            evidence={sid: deepcopy(self._evidence[sid]) for sid in sorted(used_spans)},
            factual_coverage=sorted({k for s in statements for k in s['fields']}))

    def verify_answer(self, answer, *, record_id):
        # No later model/editor rewrite can retain a valid envelope while dropping qualifications.
        if answer != self.render(record_id): raise ValueError('Answer differs from qualified assembly')
        return True
