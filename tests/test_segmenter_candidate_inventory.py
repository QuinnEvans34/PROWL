from copy import deepcopy
import pytest
from scripts.diagnostics.segmenter_candidate_inventory import propose,legacy_hints,safe_read
from src.data.manifest_records import digest


def row(code,role,stratum,positive=False,count=0,voxels=100):
    return dict(study_id=f'pants:study:PanTS_{code:08d}',protected_role=role,descriptive_stratum=stratum,
        localizer_state='qualified',source_voxels=voxels,legacy_hint=dict(has_lesion_hint=positive,lesion_voxel_count_hint=count))


def invented():
    return [row(3,'train','venous|thick_gt5mm',True,1055),row(26,'train','non-contrast|medium_le5mm',True,7244),
        row(6110,'train','arterial|thin_le2mm'),row(2973,'train','non-contrast|thick_gt5mm',True,124),
        row(10,'train','arterial|thin_le2mm',True,400),row(11,'train','venous|thin_le2mm',True,300),
        row(12,'train','venous|medium_le5mm',True,2000,96000000),row(13,'train','delay|thin_le2mm'),
        row(2514,'validation','venous|medium_le5mm',True,1880),row(5641,'validation','non-contrast|thin_le2mm',True,47190),
        row(2727,'validation','arterial|thin_le2mm'),row(14,'validation','delay|thin_le2mm')]


def test_proposal_deterministic_varied_and_preserves_hints_not_qualification():
    r=invented();p=propose(r)
    assert p==propose(list(reversed(r))) and len(p)==12
    assert sum(x['protected_role']=='train' for x in p)==8
    assert sum(x['legacy_hint']['has_lesion_hint'] is True for x in p)==8
    assert r==invented() and all('qualification' not in x for x in p)
    assert any(x['study_id'].endswith('00002973') for x in p)


@pytest.mark.parametrize('fault',['held_anchor','missing_positive','missing_delayed','changed_validation_count'])
def test_shortage_or_changed_selection_fails_without_refill(fault):
    r=invented()
    if fault=='held_anchor':r[0]['localizer_state']='held'
    if fault=='missing_positive':r=[x for x in r if not x['study_id'].endswith('00000012')]
    if fault=='missing_delayed':r=[x for x in r if not x['study_id'].endswith('00000014')]
    if fault=='changed_validation_count':r.append(row(15,'validation','venous|thin_le2mm',True,10))
    with pytest.raises(ValueError):propose(r)


def test_legacy_reports_paths_and_identifiers_not_exported():
    raw=b'case_id,has_lesion,lesion_voxel_count,structured report,ct_path,patient_id\nPanTS_00000001,False,0,SECRET,/old/source/path,PRIVATE\n'
    r=legacy_hints(raw)
    assert 'SECRET' not in str(r) and 'PRIVATE' not in str(r) and '/old' not in str(r)
    assert r['pants:study:PanTS_00000001']['assurance']=='legacy_unverified_not_target_status'


def test_changed_metadata_and_unsafe_paths_rejected(tmp_path):
    p=tmp_path/'metadata.json';p.write_bytes(b'original')
    assert safe_read(tmp_path,p.name,digest(b'original'))==b'original'
    p.write_bytes(b'changed')
    with pytest.raises(ValueError):safe_read(tmp_path,p.name,digest(b'original'))
    with pytest.raises(ValueError):safe_read(tmp_path,'../metadata.json','0'*64)
    p.unlink();p.symlink_to(tmp_path/'missing')
    with pytest.raises(ValueError):safe_read(tmp_path,p.name,'0'*64)
