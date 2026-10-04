from pathlib import Path
import json
import pytest
from src.data.source_metadata_inventory import MetadataInventory

pytestmark=pytest.mark.unit


@pytest.fixture(autouse=True)
def bounded_process_memory(monkeypatch):
    # Unit fixtures must not inherit the process-lifetime peak of earlier model tests.
    # The explicit memory_budget case still rejects this 64 MiB observation against 1 byte.
    import sys
    from types import SimpleNamespace
    import src.data.source_metadata_inventory as module
    rss=64*1024**2 if sys.platform=='darwin' else 64*1024
    monkeypatch.setattr(module.resource,'getrusage',lambda _:SimpleNamespace(ru_maxrss=rss))



def fixture(tmp_path):
    root=tmp_path.resolve();roles={'PanTS_00000001':'train','PanTS_00000002':'validation','PanTS_00009001':'test'}
    for sid in list(roles)[:2]:
        (root/'shard'/sid).mkdir(parents=True)
        (root/'shard'/sid/'ct.nii.gz').write_bytes(b'not an image')
        (root/'labels'/sid/'segmentations').mkdir(parents=True)
        for n in ['pancreas','other']:(root/'labels'/sid/'segmentations'/f'{n}.nii.gz').write_bytes(b'not a mask')
    (root/'labels'/'PanTS_00009001').mkdir()
    return root,{'shard':list(roles)[:2]},roles


def run(root,shards,roles,**kwargs):
    return MetadataInventory(root,check_mount=lambda:None,**kwargs).run(shards,'labels',roles)


def test_metadata_only_keeps_roles_and_never_opens_payloads(tmp_path,monkeypatch):
    root,shards,roles=fixture(tmp_path)
    (root/'labels'/'PanTS_00009001'/'forbidden').symlink_to('/no/such/file')
    monkeypatch.setattr(Path,'open',lambda *a,**k: (_ for _ in ()).throw(AssertionError('payload opened')))
    data,summary=run(root,shards,roles);rows=[json.loads(x) for x in data.splitlines()]
    assert len(rows)==4 and summary['present']==4 and summary['content_hashes_computed']==0
    assert {r['protected_role'] for r in rows}=={'train','validation'}
    assert summary['publisher_test_payloads_inspected']==0 and summary['outside_purpose_structure_counts']=={'other.nii.gz':2}


def test_missing_file_recorded_without_filtering(tmp_path):
    root,shards,roles=fixture(tmp_path);(root/'shard'/'PanTS_00000001'/'ct.nii.gz').unlink()
    data,s=run(root,shards,roles)
    assert s['missing']==1 and s['file_count']==4 and b'"state":"missing"' in data


@pytest.mark.parametrize('fault',['link','unknown_case','extra_ct','wrong_type','duplicate_scope','unsafe','entry_budget','time_budget','output_budget','memory_budget'])
def test_stops_on_unsafe_or_unbounded_inventory(tmp_path,fault):
    root,shards,roles=fixture(tmp_path);kw={}
    if fault=='link':(root/'shard'/'PanTS_00000001'/'link').symlink_to(root)
    if fault=='unknown_case':(root/'shard'/'extra').mkdir()
    if fault=='extra_ct':(root/'shard'/'PanTS_00000001'/'extra').write_bytes(b'')
    if fault=='wrong_type':
        p=root/'shard'/'PanTS_00000001'/'ct.nii.gz';p.unlink();p.mkdir()
    if fault=='duplicate_scope':shards['shard'].append(shards['shard'][0])
    if fault=='unsafe':shards={'../shard':shards['shard']}
    if fault=='entry_budget':kw['max_entries']=1
    if fault=='time_budget':kw['seconds']=0
    if fault=='output_budget':kw['max_output']=1
    if fault=='memory_budget':kw['max_memory']=1
    with pytest.raises((ValueError,TimeoutError,MemoryError)):run(root,shards,roles,**kw)


def test_mount_failure_stops_before_scan(tmp_path):
    root,shards,roles=fixture(tmp_path)
    def fail():raise ValueError('mount changed')
    with pytest.raises(ValueError,match='mount changed'):MetadataInventory(root,check_mount=fail)
