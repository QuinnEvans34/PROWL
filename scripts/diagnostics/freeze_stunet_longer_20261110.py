"""Freeze the next single stage only after successful, reaped qualification."""
import argparse,json,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.training.supervise_stunet_longer_20261110 import sha,size,check_storage
from scripts.training.train_stunet_longer_20261110 import write,backup
Q=Path('E:/PROWL/readiness/stunet-longer-qualification-20261110-a01')
def add(r,path):r['pins'][str(path)]=sha(path)
def main():
    import psutil
    p=argparse.ArgumentParser();p.add_argument('--stage',choices=['cold','science'],required=True);a=p.parse_args()
    r=json.loads((Q/'producer-request.json').read_text())
    stages=['producer'] if a.stage=='cold' else ['producer','cold']
    for stage in stages:
        d=Q/stage;result=json.loads((d/'worker/result.json').read_text());resources=json.loads((d/'resources.json').read_text())
        assert result['status']=='PASS' and result['scientific_updates']==0 and resources['success'] and resources['workers_reaped']
        owner=json.loads((d/'owner.json').read_text())
        for pid in [owner['worker'],owner['supervisor']]:
            if psutil.pid_exists(pid):raise RuntimeError('Prior stage process still present')
        for path in [d/'resources.json',d/'worker/result.json',d/'owner.json']:add(r,path)
    producer=json.loads((Q/'producer/worker/result.json').read_text())
    for label in ('step4','step5'):
        row=producer[label]
        assert sha(row['path'])==sha(row['backup'])==row['sha256']
        for path in (row['path'],row['backup']):add(r,path)
    r['producer']=str(Q/'producer/worker');add(r,Path(__file__));add(r,Q/'cpu-tests.xml')
    check_storage()
    if a.stage=='cold':
        r['stage_root']=str(Q/'cold');dest=Q/'cold-request.json'
    else:
        root=Path('E:/PROWL/readiness/stunet-longer-scientific-launch-20261110-a01');root.mkdir(exist_ok=False)
        r.update(seconds=144000,stage_root=str(root/'run'),run_id='pants_stunet_longer_continuation_12k_20261110',title='Continue STU-Net from 24k to 36k with fresh views',artifact='E:/PROWL/artifacts/pants_stunet_longer_continuation_12k_20261110_launch01',scientific_backup='C:/Users/quinn/PROWL-Backups/pants_stunet_longer_continuation_12k_20261110_launch01',approval='Continue approved same PanTS patients for another 12k')
        for stage in stages:
            r[stage+'_resources']=str(Q/stage/'resources.json');r[stage+'_result']=str(Q/stage/'worker/result.json')
        for path in [Q/'producer-request.json',Q/'cold-request.json',ROOT/'docs/capstone/operations/STUNET-LONGER-LAUNCH-20261110.md',ROOT/'docs/capstone/operations/STUNET-LONGER-36K-PROPOSAL-20261109.md']:add(r,path)
        reserve=6*698166891+64*1024**2
        assert size('C:/Users/quinn/PROWL-Backups')+reserve<88*1024**3 and shutil.disk_usage('C:/').free-reserve>100*1024**3
        write(root/'readiness-review.json',dict(status='PASS_READY_FOR_ONE_USER_APPROVED_LAUNCH',phase_updates=12000,global_start=24000,global_end=36000,qualification_scientific_updates=0,parent_reference_sha256=r['parent_checkpoint_sha256'],projected_c_backups=size('C:/Users/quinn/PROWL-Backups')+reserve,projected_c_free=shutil.disk_usage('C:/').free-reserve))
        add(r,root/'readiness-review.json');dest=root/'ready.json'
    write(dest,r)
    b=Path('C:/Users/quinn/PROWL-Backups/stunet-longer-readiness-20261110-a01')
    backup(dest,b/dest.name)
    if a.stage=='science':
        backup(dest.parent/'readiness-review.json',b/'readiness-review.json')
        for stage in stages:
            for path in [Q/stage/'resources.json',Q/stage/'worker/result.json',Q/stage/'worker/history.jsonl']:backup(path,b/stage/path.name)
        for path in [Q/'inputs.json',Q/'cpu-review.json',Q/'cpu-tests.xml']:backup(path,b/path.name)
    print(json.dumps(dict(request=str(dest),sha256=sha(dest),pins=len(r['pins']))),flush=True)
if __name__=='__main__':main()
