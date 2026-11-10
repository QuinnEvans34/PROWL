import copy,json
from types import SimpleNamespace
import pytest
from src.operations.stunet_recovery_20261110 import reusable_cases,CHECKPOINT_SHA,check_storage
from scripts.training.supervise_stunet_recovery_20261110 import verify

def fixture():
    names=[f'case-{i:02d}' for i in range(70)];profile={n:{'tiles':1} for n in names}
    rows=[dict(event='update',step=s) for s in range(24001,26001)]+[dict(event='checkpoint',step=26000,sha256=CHECKPOINT_SHA),dict(event='native_started',step=26000)]
    rows += [dict(event='native_case',case_id=n,step=26000,variant='raw',tiles=1,gaps=0,scope='provided',metrics={}) for n in names[:14]]
    rows.append(dict(event='native_progress',step=26000,completed_cases=14,tiles_done=15))
    return rows,names,profile

def test_reuse_only_complete_prefix_not_partial_tiles():
    rows,names,profile=fixture();saved=reusable_cases(rows,names,profile)
    assert len(saved)==14 and [r['case_id'] for r in saved]==names[:14]
    assert 'event' not in saved[0] and 'step' not in saved[0]

@pytest.mark.parametrize('kind',['duplicate','wrong_step','wrong_hash','gap','missing_update','completed','tile_count'])
def test_reuse_rejects_unbound_or_incomplete(kind):
    rows,names,profile=fixture()
    if kind=='duplicate':rows[-2]['case_id']=names[0]
    if kind=='wrong_step':rows[-2]['step']=24000
    if kind=='wrong_hash':rows[2000]['sha256']='bad'
    if kind=='gap':rows[-2]['gaps']=1
    if kind=='missing_update':rows.pop(0)
    if kind=='completed':rows.append(dict(event='completed'))
    if kind=='tile_count':rows[-2]['tiles']=2
    with pytest.raises(ValueError):reusable_cases(rows,names,profile)

def test_fifty_gib_storage_floor_and_caps(monkeypatch):
    import src.operations.stunet_recovery_20261110 as m
    def volume(drive,buf,n):
        buf.value='9ed7859f-4768-4f11-9788-792a793f0ee4' if drive.startswith('C') else '424d39a3-ac76-4f41-aa1c-8b9f5ce0b829';return 1
    monkeypatch.setattr(m.ctypes.windll.kernel32,'GetVolumeNameForVolumeMountPointW',volume)
    monkeypatch.setattr(m,'size',lambda p:0);monkeypatch.setattr(m.shutil,'disk_usage',lambda p:SimpleNamespace(free=50*1024**3))
    check_storage()
    monkeypatch.setattr(m.shutil,'disk_usage',lambda p:SimpleNamespace(free=50*1024**3-1))
    with pytest.raises(RuntimeError,match='50GiB'):check_storage()

def test_original_wall_budget_not_reset(tmp_path):
    failure=tmp_path/'failure.json';failure.write_text(json.dumps(dict(success=False,workers_reaped=True,error="RuntimeError('100GiB free-space floor')",seconds=13159.5)))
    qual=tmp_path/'qual.json';qual.write_text(json.dumps(dict(success=True,workers_reaped=True,seconds=20)))
    result=tmp_path/'result.json';result.write_text(json.dumps(dict(status='PASS',scientific_updates=0)))
    r=dict(pins={},failed_resources=str(failure),restore_resources=str(qual),restore_result=str(result),approval='User approves 50GiB floor and continuation from26k',rss_bytes=12*1024**3,cuda_bytes=6*1024**3,seconds=144000-13159.5-20)
    verify(r,'science');r['seconds']=144000
    with pytest.raises(ValueError,match='Cumulative'):verify(r,'science')
