"""Public fixtures only: new exclusions cannot disappear behind old preflight."""
from copy import deepcopy
import pytest
from src.retrieval.public_exposure import load_prepared_exposure, V5_SOURCES, DIRECTORY
from src.retrieval.evaluation_delta import extend_exposure
from tests.retrieval.test_public_exposure import public_fixture, write, sealed
from tests.retrieval.test_public_exposure_v3 import current_fixture
from tests.retrieval.test_public_exposure_v4 import prepared


@pytest.fixture
def v5(prepared):
    root,parent=prepared; sources=[]
    for index,path in enumerate(V5_SOURCES):
        cases=[dict(id='example',question=f'Invented new public wording {index}?')]
        if index in (4,5):
            raw=dict(wordings=[cases[0]['question']]);cases[0]['id']='wording-1'
        else: raw={('questions' if index==0 else 'cases'):deepcopy(cases)}
        if index==6: raw['files']=[dict(path='/private/never/read',sha256='historical-only')]
        pin=write(root,path,raw)
        sources.append(dict(**pin,exposure='development_only',cases=cases))
    data=sealed(dict(version='prowl-public-exposure-v5',status='public_preparation_private_admission_pending',
        parent=write(root,DIRECTORY+'public-exposure-v4-preparation.json',parent),sources=sources,
        inventory=extend_exposure(parent['inventory'],sources),limitations=['Invented']))
    write(root,DIRECTORY+'public-exposure-v5.json',data)
    return root,data


def test_preserves_parent_origins_and_new_wordings(v5):
    root,data=v5
    assert load_prepared_exposure(root)==data
    assert data['inventory']['record_count']==55
    assert data['inventory']['distinct_wording_count']==45


@pytest.mark.parametrize('change',['source','wording','union','parent','status','scope','bytes'])
def test_resealed_missing_or_changed_exclusions_refused(v5,change):
    root,data=v5
    if change=='source':data['sources'].pop()
    if change=='wording':data['sources'][0]['cases']=[]
    if change=='union':data['inventory']['rows'].pop()
    if change=='parent':data['parent']['path']='/private/never/read'
    if change=='status':data['status']='ready'
    if change=='scope':data['sources'][0]['exposure']='held_out'
    if change=='bytes':write(root,V5_SOURCES[0],dict(questions=[]))
    write(root,DIRECTORY+'public-exposure-v5.json',sealed(data))
    with pytest.raises(ValueError):load_prepared_exposure(root)
