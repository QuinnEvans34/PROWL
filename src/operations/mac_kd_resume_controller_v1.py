"""Pure admission/lineage rules for explicitly stopped Mac KD segments."""
from pathlib import Path
import json
from src.data.segmenter_teacher_cache_v1 import sha
from src.data.teacher_target_publication_v1 import read_bound
from src.operations.kd_continuation_v1 import inspect_checkpoint,remaining_budget
from src.operations.kd_gpu_qualification_v1 import check_pins


def completed(root,backup,arm):
    root,backup=Path(root),Path(backup)
    result=json.loads((root/arm/'result.json').read_text())
    resources=json.loads((root/arm/'resources.json').read_text())
    end=json.loads((root/arm/'complete.json').read_text())
    if (result.get('completed',True) is not True or result.get('completed_updates')!=24000 or resources.get('success') is not True
            or resources.get('workers_reaped') is not True or resources.get('exit_code')!=0
            or end.get('success') is not True or (root/arm/'tracking-warning.json').exists()):
        raise ValueError('Completed healthy predecessor required')
    journal=root/arm/'execution/history.jsonl'
    events=[json.loads(line) for line in journal.read_text().splitlines()]
    if not events or events[-1].get('event')!='completed' or events[-1].get('step')!=24000:
        raise ValueError('Completed predecessor journal required')
    paths=list((root/arm/'execution').glob('*'))
    for path in paths:
        if path.is_file() and sha(path)!=sha(backup/arm/path.name):
            raise ValueError('Completed predecessor backup differs')
    return {str(p):sha(p) for p in paths+[root/arm/'result.json',root/arm/'resources.json',root/arm/'complete.json'] if p.is_file()}


def plans(original,original_pin,parent,parent_pin,arm,checkpoint):
    """Caller must prove process cleanup and hold the exclusive GPU lock."""
    original,parent=Path(original).resolve(),Path(parent).resolve()
    scientific=read_bound(original/'ready.json',original_pin)
    if scientific['version']!='mac-matched-kd-launch-1' or arm not in scientific['order']:
        raise ValueError('Original matched recipe required')
    check_pins(scientific['pins'])
    prior=read_bound(parent/'ready.json',parent_pin)
    old_segments={a:[] for a in scientific['order']}
    if parent==original:
        if parent_pin!=original_pin:raise ValueError('Original receipt mismatch')
        parent_backup=Path(scientific['backup'])
    else:
        if (prior['version']!='mac-kd-continuation-launch-1' or prior['original']!=str(original)
                or prior['original_sha256']!=original_pin):raise ValueError('Wrong parent comparison')
        check_pins(prior['pins']);old_segments=prior['segments'];parent_backup=Path(prior['backup'])
    inherited_pins={str(parent/'ready.json'):parent_pin}
    for segments in old_segments.values():
        for row in segments:check_pins(row['pins'])
    if arm=='treatment':
        # The treatment cannot get ahead of a completed control, including across pauses.
        locations=[(parent,parent_backup),(original,Path(scientific['backup']))]
        if parent!=original:
            locations.extend((Path(s['root']),Path(s['backup'])) for s in old_segments['control'])
        for location,backup in locations:
            if (location/'control/complete.json').exists():
                inherited_pins.update(completed(location,backup,'control'));break
        else:raise ValueError('No completed control for treatment')
    segments={a:list(rows) for a,rows in old_segments.items()}
    context=None
    if (parent/arm).exists():
        process=json.loads((parent/arm/'process.json').read_text())
        dispatch=json.loads((parent/arm/'dispatch.json').read_text())
        if dispatch['receipt_sha256']!=parent_pin:raise ValueError('Parent dispatch differs')
        resources=json.loads((parent/arm/'resources.json').read_text())
        if (parent/arm/'complete.json').exists():raise ValueError('Arm already complete; do not replay')
        context=inspect_checkpoint(parent/arm/'execution',parent_backup/arm,checkpoint)
        files=[parent/arm/name for name in ('resources.json','process.json','dispatch.json')]
        files.append(parent/arm/'execution/history.jsonl')
        row=dict(root=str(parent),backup=str(parent_backup),run_id=dispatch['run_id'],
                 resources=resources,pins={str(p):sha(p) for p in files},checkpoint_step=context['step'])
        if any(s['root']==row['root'] for s in segments[arm]):raise ValueError('Duplicate parent charge')
        segments[arm].append(row)
    elif arm!='treatment':raise ValueError('Missing control parent')
    budget=(remaining_budget(scientific['limits']['seconds_per_arm'],[s['resources'] for s in segments[arm]])
            if segments[arm] else dict(remaining_seconds=scientific['limits']['seconds_per_arm'],charged_seconds=0,
                                      original_seconds=scientific['limits']['seconds_per_arm']))
    for rows in segments.values():
        for row in rows:inherited_pins.update(row['pins'])
    order=scientific['order'][scientific['order'].index(arm):]
    if arm=='control' and ((parent/'treatment').exists() or (original/'treatment').exists()):
        raise ValueError('Treatment already exists; refuse duplicate pair')
    return dict(scientific=scientific,segments=segments,context=context,order=order,
                budget=budget,parent_backup=str(parent_backup),inherited_pins=inherited_pins)
