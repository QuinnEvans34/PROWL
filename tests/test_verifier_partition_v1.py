import pytest
from src.training.verifier_partition_v1 import partition, stratum


def rows():
    return [dict(case_id=f'p{i}',positive=i%4!=0,lesion_volume_mm3=[0,100,5000,20000][i%4]) for i in range(40)]


def test_exact_disjoint_reproducible():
    a=partition(rows(),['dev'],(24,10,6),8)
    assert a==partition(list(reversed(rows())),['dev'],(24,10,6),8)
    assert [len(v) for v in a['roles'].values()]==[24,8,2,6]
    names=sum(a['roles'].values(),[])
    assert len(names)==len(set(names))==40 and 'dev' not in names


@pytest.mark.parametrize('kind',['duplicate','development','size','volume'])
def test_bad_inputs(kind):
    data=rows();dev=['dev'];sizes=(24,10,6)
    if kind=='duplicate':data[1]=data[0]
    if kind=='development':dev=['p0']
    if kind=='size':sizes=(24,10,5)
    if kind=='volume':data[0]['lesion_volume_mm3']=float('nan')
    with pytest.raises(ValueError):partition(data,dev,sizes,8)


def test_size_boundaries():
    assert [stratum(dict(positive=True,lesion_volume_mm3=n)) for n in [999,1000,10000,10001]]==['small','medium','medium','large']
