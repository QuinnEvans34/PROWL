from copy import deepcopy
import pytest

from src.data.audit_assessment_link import link_audits, link_coverage_reference, parse
from src.data.manifest_records import canonical, digest
from retained_segmenter_metadata import fixture_path

pytestmark = pytest.mark.unit
# Exact compatibility-control bytes; this does not qualify any member for training.
TRAIN = fixture_path('train.txt').read_bytes()


def fixture():
    target = dict(study='PanTS_00000003', structure='pancreas',
                  ct='PanTSMini_ImageTr_00000001_00001000/PanTS_00000003/ct.nii.gz',
                  mask='PanTSMini_Label/PanTS_00000003/segmentations/pancreas.nii.gz')
    pair = dict(audit_version='voxel-audit-v1.1', grid=dict(compatible=True),
                unit_interpretation=None)
    for role, sha in [('ct', 'a'*64), ('mask', 'b'*64)]:
        pair[role] = dict(role=role, status='measured', stop=None,
            file=dict(root_alias='followup_source', uri=target[role], content_sha256=sha),
            header=dict(voxels=2, shape=[1, 1, 2]), spatial_units='unknown',
            scaling=dict(slope=1, inter=0, active=False),
            voxels=dict(count=2, finite=2, nonfinite=dict(nan=0,posinf=0,neginf=0),
                        stored_nonfinite=0, scaled_overflow_voxels=0,
                        float64_precision_loss_risk=False, stored_min=0, stored_max=1,
                        values_basis='stored'))
    pair['mask']['mask'] = dict(distinct_values=[0,1], value_counts=[[0,1],[1,1]],
                               distinct_values_truncated=False, nonzero_voxels=1, empty=False)
    return target, pair


def package(target, pair):
    selection = dict(train_sha256=digest(TRAIN), pairs=[target])
    artifacts = {'selection.json': canonical(selection), 'pair-00.json': canonical(pair)}
    receipt = dict(status='complete', files={k:digest(v) for k,v in artifacts.items()},
                   source_hashes={pair[r]['file']['uri']:pair[r]['file']['content_sha256']
                                  for r in ('ct','mask')},
                   summaries=[dict(study=target['study'], structure=target['structure'],
                                   mask=deepcopy(pair['mask']['mask']))])
    raw = canonical(receipt)
    return dict(receipt_bytes=raw, expected_receipt_sha256=digest(raw), artifacts=artifacts,
                train_bytes=TRAIN)


def test_valid_is_repeatable_nonpromoting_and_preserves_input():
    args = package(*fixture()); before=deepcopy(args)
    result = link_audits(**args)
    assert args == before
    assert result == link_audits(**args)
    row = result[0]
    assert row['semantic_value_counts'] == [[0,1],[1,1]]
    assert row['complete_stored_value_set'] is None
    assert row['allowed_uses'] == []
    assert all(x['disposition']=='unresolved' for x in row['purpose_assessments'])


@pytest.mark.parametrize('fault', ['artifact', 'receipt', 'missing', 'train'])
def test_byte_identity_faults(fault):
    args = package(*fixture())
    if fault=='artifact': args['artifacts']['pair-00.json'] += b' '
    if fault=='receipt': args['receipt_bytes'] += b' '
    if fault=='missing': del args['artifacts']['pair-00.json']
    if fault=='train': args['train_bytes'] += b'\n'
    with pytest.raises(ValueError): link_audits(**args)


@pytest.mark.parametrize('fault', ['stopped','count','truncated','foreground','role',
    'grid','study','structure','units','nonfinite','duplicate_values','partial_counts'])
def test_internally_rehashed_invalid_evidence_rejected(fault):
    target,pair=fixture(); mask=pair['mask']
    if fault=='stopped': mask['status']='stopped'
    if fault=='count': mask['voxels']['count']=3
    if fault=='truncated': mask['mask']['distinct_values_truncated']=True
    if fault=='foreground': mask['mask']['nonzero_voxels']=0
    if fault=='role': mask['role']='ct'
    if fault=='grid': pair['grid']['compatible']=False
    if fault=='study': mask['file']['uri']=mask['file']['uri'].replace('00000003','00000078')
    if fault=='structure': target['structure']='pancreatic_lesion'
    if fault=='units': pair['unit_interpretation']=dict(study_id='wrong',ct_sha256='a'*64,mask_sha256='b'*64)
    if fault=='nonfinite': mask['voxels']['nonfinite']['nan']=1
    if fault=='duplicate_values': mask['mask']['distinct_values']=[0,0]
    if fault=='partial_counts': mask['mask']['value_counts']=[[0,1],[1,2]]
    with pytest.raises(ValueError): link_audits(**package(target,pair))


def test_lesion_cannot_receive_pancreas_assessment():
    target,pair=fixture()
    target['structure']='pancreatic_lesion'
    target['mask']=target['mask'].replace('pancreas.nii','pancreatic_lesion.nii')
    pair['mask']['file']['uri']=target['mask']
    assert 'purpose_assessments' not in link_audits(**package(target,pair))[0]


@pytest.mark.parametrize('fault', [None, 'target', 'ct', 'image', 'hash'])
def test_coverage_reference_is_verified_but_does_not_promote(fault):
    row = link_audits(**package(*fixture()))[0]
    row['study_id'] = 'pants:study:PanTS_00000078'
    row['ct_source']['bytes'] = 123
    bone = b'synthetic image bytes'
    evidence = dict(source=dict(file=deepcopy(row['ct_source'])),
                    views={'bone.png':dict(sha256=digest(bone))})
    if fault=='ct': evidence['source']['file']['content_sha256']='f'*64
    raw=canonical(evidence)
    args=dict(evidence_bytes=raw,expected_sha256=digest(raw),bone_bytes=bone,review_bytes=b'review')
    if fault=='target': row['structure']='pancreatic_lesion'
    if fault=='image': args['bone_bytes']=b'changed'
    if fault=='hash': args['expected_sha256']='f'*64
    if fault:
        with pytest.raises(ValueError): link_coverage_reference(row,**args)
    else:
        before=deepcopy(row)
        result=link_coverage_reference(row,**args)
        assert before==row
        assert result['purpose_assessments']==row['purpose_assessments']
        assert result['allowed_uses']==[]
        assert result['coverage_review_reference']['status']=='provisional_review_not_adjudication'


@pytest.mark.parametrize('raw', [b'{"a":1,"a":2}', b'{"a":NaN}'])
def test_ambiguous_json_rejected(raw):
    with pytest.raises(ValueError): parse(raw)
