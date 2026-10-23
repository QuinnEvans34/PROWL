"""Recoverable final-journal backup closeout; no model or source changes."""
import json
from pathlib import Path
import shutil
import sqlite3
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.training.experiment_config import sha256
from src.operations.full_training_platform import durable_replace,require_ac


def main():
    require_ac()
    output=Path('E:/PROWL/readiness/region-throughput-20261022-a01/parent-closeout.json')
    if output.exists():raise ValueError('Closeout already recorded')
    setup=Path('E:/PROWL/readiness/pancreas-region-20261019-a01')
    for receipt in [setup/'ready.json',Path('E:/PROWL/readiness/varied-focus-20261022-a01/setup.json')]:
        for path,pin in json.loads(receipt.read_text())['pins'].items():
            if sha256(path)!=pin:raise ValueError('Frozen producing pin changed: '+path)
    if not json.loads((setup/'scientific-resources.json').read_text())['workers_reaped']:
        raise ValueError('Parent worker not reaped')
    con=sqlite3.connect('file:C:/Users/quinn/PROWL-Tracking/mlflow.db?mode=ro',uri=True)
    status=con.execute('SELECT status FROM runs WHERE run_uuid=?',('1edf56ad4b7b48a5a5baa0e729e46a5c',)).fetchone()
    con.close()
    if status!=('FINISHED',):raise ValueError('MLflow parent not FINISHED')
    source=Path('E:/PROWL/artifacts/pants_pancreas_region_24k_20261019/execution/history.jsonl')
    root=Path('C:/Users/quinn/PROWL-Backups/pants_pancreas_region_24k_20261019')
    destination=root/'history.jsonl';saved=root/'history-pre-closeout-20261022.jsonl'
    temporary=root/'history-closeout-20261022.partial'
    if saved.exists() or temporary.exists():raise ValueError('Closeout previously started; inspect, no retry')
    a,b=source.read_bytes(),destination.read_bytes()
    if not a.startswith(b):raise ValueError('Backup is not exact prefix')
    tail=[json.loads(line)['event'] for line in a[len(b):].splitlines()]
    if tail!=['native_completed','training_completed','completed']:raise ValueError('Unexpected missing tail')
    if source.stat().st_dev==destination.stat().st_dev:raise ValueError('Independent backup required')
    occupied=sum(p.stat().st_size for p in root.parent.rglob('*') if p.is_file())
    if occupied+len(a)+len(b)>27917287424:raise ValueError('Backup cap')
    if any(shutil.disk_usage(d).free<100*1024**3 for d in ('C:/','E:/')):raise ValueError('Disk floor')
    import os
    shutil.copyfile(destination,saved)
    if sha256(saved)!=sha256(destination):raise ValueError('Preserved prefix mismatch')
    with temporary.open('xb') as f:f.write(a);f.flush();os.fsync(f.fileno())
    if sha256(temporary)!=sha256(source):raise ValueError('New journal backup mismatch')
    durable_replace(temporary,destination)
    if sha256(destination)!=sha256(source):raise ValueError('Installed backup mismatch')
    with output.open('x') as f:json.dump(dict(source=str(source),backup=str(destination),
        preserved_prior_copy=str(saved),sha256=sha256(source),missing_events_added=tail,
        parent_mlflow='FINISHED',all_parent_successor_pins_match=True,source_unchanged=True),f,indent=2)
    print(output)


if __name__=='__main__':main()
