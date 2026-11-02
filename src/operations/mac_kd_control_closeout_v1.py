"""Audit completed optimization after the one known cleanup-only failure.

Does not reinterpret the historical orchestration outcome or rewrite its receipts.
Caller must additionally establish current process absence and exclusive ownership.
"""
import json
from pathlib import Path
from src.data.segmenter_teacher_cache_v1 import sha


def inspect(root, backup, validation):
    root, backup = Path(root), Path(backup)
    arm=root/'control'
    result=json.loads((arm/'result.json').read_text())
    resources=json.loads((arm/'resources.json').read_text())
    if (result.get('completed') is not True or result.get('status')!='completed'
            or result.get('completed_updates')!=24000):
        raise ValueError('Completed control optimization required')
    if (resources.get('exit_code')!=0 or resources.get('success') is not False
            or resources.get('workers_reaped') is not False
            or resources.get('error')!="ValueError('Owned worker descendant was not reaped')"):
        raise ValueError('Only the recorded cleanup-only failure is eligible')
    if (arm/'tracking-warning.json').exists() or (root/'treatment').exists():
        raise ValueError('Tracking failure or existing treatment')
    execution=arm/'execution'
    events=[json.loads(line) for line in (execution/'history.jsonl').read_text().splitlines()]
    if not events or events[-1].get('event')!='completed' or events[-1].get('step')!=24000:
        raise ValueError('Terminal control journal required')
    for name,step in [('native-terminal.json',24000),('native-selected.json',result['selected_step'])]:
        report=json.loads((execution/name).read_text())
        if (report['step']!=step or [row['case_id'] for row in report['cases']]!=list(validation)
                or report['scope']!='native_provided_pancreas_region_development'
                or any(row['reconstruction']['gap_voxels']!=0 for row in report['cases'])):
            raise ValueError('Complete gap-free matched native validation required')
    paths=list(execution.glob('*'))+[arm/'result.json']
    pins={}
    for path in paths:
        if not path.is_file():continue
        peer=backup/'control'/path.name
        digest=sha(path)
        if digest!=sha(peer):raise ValueError('Control independent backup differs: '+path.name)
        pins[str(path)]=digest;pins[str(peer)]=digest
    for name in ('resources.json','process.json','dispatch.json'):
        path=arm/name;pins[str(path)]=sha(path)
    return dict(version='reviewed-control-closeout-1',optimization_complete=True,
                historical_supervision_success=False,resources=resources,result=result,pins=pins)
