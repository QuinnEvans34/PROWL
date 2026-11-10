"""Read existing qualification, bind new addresses and exact final parent; no CT reads."""
import json,sys,time,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.data.stunet_inputs_20261106 import sha
from src.data.stunet_longer_inputs_20261110 import Inputs
from src.training.stunet_longer_session_20261110 import PARENT_SHA
from scripts.training.supervise_stunet_longer_20261110 import size
from src.operations.stunet_continuation_storage_20261108 import check_storage

def write(path,value):
    with Path(path).open('x') as f:json.dump(value,f,indent=2)

def main():
    import torch
    torch.set_num_threads(2);started=time.monotonic()
    root=Path('E:/PROWL/readiness/stunet-longer-qualification-20261110-a01');root.mkdir(exist_ok=False)
    previous=Path('E:/PROWL/readiness/stunet-corrected-scientific-launch-20261108-a02/ready.json')
    old=json.loads(previous.read_text());pins=dict(old['pins'])
    for path,digest in pins.items():
        if sha(path)!=digest:raise ValueError('Historical pin changed: '+path)
    previous_config=json.loads(Path(old['inputs']).read_text())
    inputs=root/'inputs.json'
    write(inputs,dict(previous_inputs=old['inputs'],previous_inputs_sha256=sha(old['inputs']),plan=previous_config['plan'],plan_sha256=sha(previous_config['plan'])))
    provider=Inputs(inputs);schedule=provider.plan['schedule'];members=provider.plan['members']
    assert len(provider.train)==1333 and len(provider.dev)==70 and not provider.train&provider.dev
    assert [r['global_address'] for r in schedule]==list(range(24000,36000))
    coverage={(r['case_id'],tuple(r['origin'])) for r in schedule if r['kind']=='coverage'}
    assert coverage=={(n,tuple(o)) for n,m in members.items() for o in m['cover']}
    assert sum(r['kind']=='context' for r in schedule)==3000
    parent=Path('E:/PROWL/artifacts/pants_stunet_corrected_continuation_12k_20261108_launch02/execution/checkpoint-24000.pt')
    back=Path('C:/Users/quinn/PROWL-Backups/pants_stunet_corrected_continuation_12k_20261108_launch02/checkpoint-24000.pt')
    assert sha(parent)==sha(back)==PARENT_SHA
    state=torch.load(parent,map_location='cpu',weights_only=True)
    assert state['version']=='stunet-continuation-session-1' and state['step']==24000
    assert sum(state['exposure'].values())==24000 and set(state['exposure'])==provider.train
    assert state['identity']['input_sha256']==sha(old['inputs']) and state['identity']['nonpromotable'] is False
    identity=state['identity'];del state
    check_storage();reserve=8*parent.stat().st_size+128*1024**2
    current=size('C:/Users/quinn/PROWL-Backups')
    assert current+reserve<88*1024**3 and shutil.disk_usage('C:/').free-reserve>100*1024**3
    report=dict(status='PASS',historical_pins=len(pins),train=1333,development=70,positive=664,coverage_slots=len(coverage),new_addresses=[24000,35999],ct_reads=0,parent_checkpoint_sha256=PARENT_SHA,backup_current_bytes=current,projected_backup_bytes=current+reserve,projected_c_free=shutil.disk_usage('C:/').free-reserve,seconds=time.monotonic()-started)
    write(root/'cpu-review.json',report)
    extra=list(ROOT.glob('src/data/stunet_longer*20261110.py'))+list(ROOT.glob('src/training/stunet_longer*20261110.py'))+list(ROOT.glob('scripts/training/*stunet_longer*20261110.py'))+list(ROOT.glob('tests/test_stunet_longer*20261110.py'))+[Path(__file__),previous,inputs,root/'cpu-review.json',parent,back]
    for path in extra:pins[str(path)]=sha(path)
    r={k:old[k] for k in ('source','python','native_qualification','cold_atol','cold_rtol','rss_bytes','cuda_bytes')}
    r.update(inputs=str(inputs),parent_checkpoint=str(parent),parent_backup=str(back),parent_checkpoint_sha256=PARENT_SHA,parent_identity=identity,seconds=1800,pins=pins,stage_root=str(root/'producer'),qualification_backup='C:/Users/quinn/PROWL-Backups/stunet-longer-qualification-20261110-a01',supervisor_base_python=str(ROOT/'.venv-prowl-windows/Scripts/python.exe'))
    write(root/'producer-request.json',r)
    print(json.dumps(dict(report=report,request=str(root/'producer-request.json'),sha256=sha(root/'producer-request.json'))),flush=True)
if __name__=='__main__':main()
