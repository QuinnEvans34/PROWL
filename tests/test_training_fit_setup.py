from copy import deepcopy
import pytest
from scripts.diagnostics.setup_training_fit import select_cases
from scripts.diagnostics.run_training_fit import validate


def control():
    return dict(train=[str(i) for i in range(120)],validation=['dev'],
        target_states={str(i):'positive' if i<60 else 'reference_empty' for i in range(120)})


def test_selection_reproducible_balanced_and_order_independent():
    a=control();b=deepcopy(a);b['train'].reverse()
    x=select_cases(a,b)
    assert x==select_cases(b,a) and len(x)==len(set(x))==100
    assert sum(a['target_states'][n]=='positive' for n in x)==50
    assert 'dev' not in x


@pytest.mark.parametrize('change',['overlap','membership','state','short'])
def test_invalid_membership_refused(change):
    a=control();b=deepcopy(a)
    if change=='overlap':b['validation']=['0']
    if change=='membership':b['train'].pop()
    if change=='state':b['target_states']['0']='reference_empty'
    if change=='short':a['train']=a['train'][:10];b=deepcopy(a)
    with pytest.raises(ValueError):select_cases(a,b)


def test_duplicate_requested_cases_refused_before_file_reads():
    with pytest.raises(ValueError):validate(dict(version='training-fit-1',models=[{},{}],cases=['x']*100))
