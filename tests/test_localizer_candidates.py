import pytest
from src.data.localizer_candidates import select_candidates,stratum


def example():
    rows=[{'case_id':str(i),'ct phase':'Venous' if i%2 else '', 'spacing':'1,1,7' if i%3 else 'unknown',
           'model_dice':i/10,'tumor?':'unused'} for i in range(12)]
    roles={str(i):'train' if i<6 else 'validation' if i<11 else 'test' for i in range(12)}
    return rows,roles


def test_order_independent_disjoint_and_ignores_model_scores():
    rows,roles=example();a=select_candidates(rows,roles,counts={'train':4,'validation':3},retained_train=['0'])
    for r in rows:r['model_dice']=999;r['tumor?']='changed'
    b=select_candidates(rows[::-1],roles,counts={'train':4,'validation':3},retained_train=['0'])
    assert a==b and not a['qualification_or_target_permission_granted']
    train={r['study_id'] for r in a['candidates']['train']};val={r['study_id'] for r in a['candidates']['validation']}
    assert 'pants:study:0' in train and not train&val and 'pants:study:11' not in train|val
    assert all(r['status']=='candidate_not_qualified' for group in a['candidates'].values() for r in group)


def test_missing_metadata_is_a_stratum_not_exclusion():
    assert stratum({'ct phase':'','spacing':'bad'})=='missing|missing'
    rows,roles=example();r=select_candidates(rows,roles,counts={'train':6,'validation':5})
    assert len(r['candidates']['train'])==6


@pytest.mark.parametrize('problem',['duplicate','missing','wrong_retained_role','shortage'])
def test_refuse_identity_and_role_shortcuts(problem):
    rows,roles=example();retain=[];counts={'train':4,'validation':3}
    if problem=='duplicate':rows.append(rows[0])
    if problem=='missing':rows.pop()
    if problem=='wrong_retained_role':retain=['6']
    if problem=='shortage':counts['validation']=6
    with pytest.raises(ValueError):select_candidates(rows,roles,counts=counts,retained_train=retain)


def test_bounded_header_reader_no_array_decoding():
    import io,gzip
    import nibabel as nib
    from scripts.diagnostics.localizer_candidate_headers import header_only,LimitedReader
    header=nib.Nifti1Header();header.set_data_shape((10,11,12));header.set_xyzt_units('mm')
    raw=header.binaryblock + b'\0'*100000
    result=header_only(io.BytesIO(gzip.compress(raw)))
    assert result['shape']==[10,11,12] and result['units'][0]=='mm'
    assert result['compressed_bytes_read']<=65536 and result['voxel_count']==1320
    with pytest.raises(ValueError,match='cap'):LimitedReader(io.BytesIO(raw)).read(65537)
    with pytest.raises(ValueError,match='Truncated'):header_only(io.BytesIO(gzip.compress(b'short')))
