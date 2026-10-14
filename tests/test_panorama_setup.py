import numpy as np
import pytest

from src.data.panorama_setup import classify, map_labels


def record(**kwargs):
    args = dict(study_id='100001_00001', subject_id='100001', diagnosis='PDAC',
                level='histopathology', annotation_method='human_manual')
    args.update(kwargs)
    return classify(**args)


def test_non_pdac_not_generic_negative():
    r = record(diagnosis='non-PDAC', annotation_method='machine_generated')
    assert r['pdac'] == 'negative' and r['pancreatic_lesion'] == 'unknown'
    assert not r['allowed_uses'] and not r['training_ready']


@pytest.mark.parametrize('level', ['MSD_dataset', 'NIH_dataset'])
def test_import_excluded_first(level):
    assert record(level=level, diagnosis='non-PDAC')['disposition'] == 'excluded_declared_import'


def test_manual_pancreas_stays_machine():
    r = record()
    assert r['lesion_method'] == 'human_manual' and r['pancreas_method'] == 'machine_generated'
    assert r['protected_role'] == 'unassigned'


def test_automatic_not_primary_and_anomaly_held():
    assert record(annotation_method='machine_generated')['disposition'].startswith('optional_machine')
    assert record(diagnosis='non-PDAC')['disposition'].startswith('quarantined')


def test_repeated_subject_not_split_by_study():
    assert record()['subject_id'] == record(study_id='100001_00002')['subject_id']


def test_mapping_and_crop_include_lesion_outside_pancreas():
    raw = np.arange(7, dtype=np.uint8).reshape(7, 1, 1)
    mapped = map_labels(raw, diagnosis='PDAC')
    assert mapped['target'].ravel().tolist() == [0,2,0,0,1,0,0]
    assert mapped['crop_support'].ravel().tolist() == [0,1,0,0,1,0,0]
    assert mapped['pancreas'][1,0,0] == 0


@pytest.mark.parametrize('raw,diagnosis', [
    (np.array([4,7], dtype=np.uint8), 'PDAC'),
    (np.array([4], dtype=np.uint8), 'PDAC'),
    (np.array([4,1], dtype=np.uint8), 'non-PDAC'),
    (np.array([1], dtype=np.uint8), 'PDAC'),
    (np.array([4.,1.5]), 'PDAC'),
    (np.array([4.,float('nan')]), 'PDAC'),
])
def test_bad_masks_fail_closed(raw, diagnosis):
    with pytest.raises(ValueError):
        map_labels(raw.reshape(-1,1,1), diagnosis=diagnosis)


@pytest.mark.parametrize('changes', [dict(diagnosis=''), dict(subject_id=''),
    dict(study_id='../escape'), dict(annotation_method='unknown')])
def test_bad_metadata(changes):
    with pytest.raises(ValueError):
        record(**changes)


def test_exact_float_storage_is_not_fractional_labels():
    mapped=map_labels(np.array([4.,1.],dtype=np.float64).reshape(2,1,1),diagnosis='PDAC')
    assert mapped['target'].dtype==np.uint8
    assert mapped['target'].ravel().tolist()==[1,2]
