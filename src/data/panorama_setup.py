"""PANORAMA setup-stage semantics. Catalog records are never training admission.

Implements the approved metadata/voxel mapping without promoting machine masks,
assigning evaluation roles, clearing duplicate candidates, or changing source files.
"""
import re

import numpy as np


def classify(study_id, subject_id, diagnosis, level, annotation_method):
    if not re.fullmatch(r'\d{6}_\d{5}', study_id):
        raise ValueError('Invalid publisher study ID')
    if not isinstance(subject_id, str) or not subject_id.strip():
        raise ValueError('Missing publisher subject identity')
    if diagnosis not in ('PDAC', 'non-PDAC'):
        raise ValueError('Unknown diagnosis, not a negative')
    if annotation_method not in ('human_manual', 'machine_generated'):
        raise ValueError('Unknown annotation provenance')
    imported = level in ('MSD_dataset', 'NIH_dataset')
    anomaly = not imported and diagnosis == 'non-PDAC' and annotation_method == 'human_manual'
    if imported:
        disposition = 'excluded_declared_import'
    elif anomaly:
        disposition = 'quarantined_manual_non_pdac'
    elif diagnosis == 'non-PDAC':
        disposition = 'not_generic_lesion_supervision'
    elif annotation_method == 'human_manual':
        disposition = 'expert_pdac_candidate_pending_qc_and_duplicates'
    else:
        disposition = 'optional_machine_pdac_candidate_not_primary'
    return dict(study_id='panorama:study:'+study_id, subject_id='panorama:subject:'+subject_id,
                publisher_study_id=study_id, pdac='positive' if diagnosis == 'PDAC' else 'negative',
                pancreatic_lesion='positive' if diagnosis == 'PDAC' else 'unknown',
                reference_standard=level, lesion_method=annotation_method,
                pancreas_method='machine_generated', disposition=disposition,
                allowed_uses=[], protected_role='unassigned', training_ready=False)


def map_labels(raw, *, diagnosis):
    """Return separate masks and crop support; never make a training batch.

    The crop support includes lesion, unlike the existing PanTS pancreas-only
    geometry. Callers must not relabel this support as pancreas ground truth.
    """
    raw = np.asarray(raw)
    if raw.ndim != 3 or raw.dtype.kind not in 'iuf' or not np.isin(raw, range(7)).all():
        raise ValueError('Expected 3D mask with exact publisher values 0..6')
    if diagnosis not in ('PDAC', 'non-PDAC'):
        raise ValueError('Unknown diagnosis')
    pancreas, lesion = (raw == 4).astype(np.uint8), (raw == 1).astype(np.uint8)
    if not pancreas.any():
        raise ValueError('Empty pancreas requires review')
    if bool(lesion.any()) != (diagnosis == 'PDAC'):
        raise ValueError('Outcome/mask conflict requires review')
    return dict(pancreas=pancreas, lesion=lesion,
                crop_support=np.maximum(pancreas, lesion),
                target=np.where(lesion, 2, pancreas).astype(np.uint8))
