"""Summarize fixed-cohort offline scores without hiding failed cases."""
from collections import Counter


def summarize(rows, expected_ids):
    if len(expected_ids) != len(set(expected_ids)) or [r['case_id'] for r in rows] != list(expected_ids):
        raise ValueError('Results must account for every fixed case exactly once, in order')
    complete = [r for r in rows if r['scoring_status'] == 'complete']
    positive = [r for r in complete if r['score']['lesion_reference_state'] == 'positive']
    empty = [r for r in complete if r['score']['lesion_reference_state'] == 'reference_empty']
    if len(positive) + len(empty) != len(complete):
        raise ValueError('Unknown lesion reference state')

    def mean(group, metric, key):
        values = [r['score']['metrics'][metric][key] for r in group
                  if r['score']['metrics'][metric][key] is not None]
        return dict(value=sum(values)/len(values) if values else None, n=len(values))

    return dict(fixed_cases=len(rows), scored_cases=len(complete),
        failed_or_unscored_cases=len(rows)-len(complete),
        inference_status_counts=dict(Counter(r['inference_status'] for r in rows)),
        positive_cases_scored=len(positive), reference_empty_cases_scored=len(empty),
        positive_lesion_macro_dice=mean(positive, 'lesion', 'dice'),
        positive_lesion_macro_recall=mean(positive, 'lesion', 'recall'),
        union_macro_dice=mean(complete, 'pancreas_lesion_union', 'dice'),
        empty_reference_mean_predicted_lesion_ml=mean(empty, 'lesion', 'false_positive_ml'),
        metric_population='Scored cases only; failed cases retained separately, never silently dropped',
        empty_reference_policy='Annotation empty, not verified healthy')
