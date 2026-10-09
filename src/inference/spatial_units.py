"""Explicit CT-side unit decisions; never infer physical units from label masks."""

def resolve_mm(header_units, ct_sha256, review=None):
    if header_units == 'mm' and review is None:
        return dict(header_units='mm', interpreted_units='mm', basis='CT header')
    if header_units != 'unknown':
        raise ValueError('Unsupported CT units or unnecessary units override')
    fields = {'ct_sha256', 'interpreted_units', 'evidence', 'reviewer', 'basis'}
    if (not isinstance(review, dict) or set(review) != fields
            or review['ct_sha256'] != ct_sha256 or review['interpreted_units'] != 'mm'
            or review['basis'] not in ('ct_acquisition_metadata', 'source_dataset_documentation')
            or not all(isinstance(review[k], str) and review[k].strip() for k in ('evidence', 'reviewer'))):
        raise ValueError('Unknown CT units require a CT-hash-bound source review; no automatic mm assumption')
    return dict(header_units='unknown', interpreted_units='mm', review=dict(review),
                basis='Explicit source review; evidence content must be independently reviewed')
