"""Finalize EMA receipt using the reviewed cache root, not its allocation parent.

The setup helper's first freeze attempt stopped on the allocation-root control path.
Preserve that qualified helper and all its pins; this finalizer corrects only receipt
collection. No model, data, profile, or experiment configuration changes are made.
"""
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET
import yaml
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.setup_pants_ema_72k import SETUP,NAME,configuration
from scripts.train_full_segmenter import preflight,tree_bytes
from src.training import experiment_config as E
from src.data.source_inventory_records import require
from src.data.manifest_records import canonical

def main():
    setup=json.loads((SETUP/'setup.json').read_text());filepins=dict(setup['file_sha256'])
    for path,sha in filepins.items():require(E.sha256(path)==sha,'Qualified code changed: '+path)
    suites=list(ET.parse(SETUP/'tests.xml').getroot().iter('testsuite'))
    require(suites and sum(int(s.get('tests','0')) for s in suites)>=53 and all(int(s.get('failures','0'))==int(s.get('errors','0'))==0 for s in suites),'Tests failed')
    for stage in ('producer','cold'):
        require(json.loads((SETUP/'cuda-profile'/f'{stage}-resources.json').read_text()).get('workers_reaped') is True,'Worker not reaped')
    cold=json.loads((SETUP/'cuda-profile/cold.json').read_text());require(cold['full_state_restore_exact'] and cold['next_state_close'],'Recovery failed')
    cfg=configuration();full=cfg['full_segmenter'];report=preflight(cfg,inspect=True);require(report['ready'],str(report))
    reserve=12*(SETUP/'cuda-profile/saved.pt').stat().st_size+256*1024**2
    require(tree_bytes(full['backup_dir'])+reserve<full['backup_cap_bytes'],'Backup allocation')
    require(tree_bytes(full['cache_dir'])<=full['cache_max_bytes'],'Cache allocation')
    for path in (Path('C:/'),Path('E:/')):require(shutil.disk_usage(path).free>100*1024**3+reserve,'Storage reserve')
    require(not (Path(full['backup_dir'])/NAME).exists(),'Backup already exists')
    review=json.loads(Path(cfg['_experiment']['cohort']['review']).read_text())
    cache_control=Path(review['prepared_cache']['root'])/'control.json'
    require(E.sha256(cache_control)==review['prepared_cache']['control_sha256'],'Cache binding changed')
    paths=[Path(__file__).resolve(),SETUP/'experiment.yaml',SETUP/'setup.json',SETUP/'tests.xml',cache_control,
        E.resolve(yaml.safe_load((SETUP/'experiment.yaml').read_text())['base_config']),Path(cfg['_experiment']['initialization']['source_review'])]
    paths+=list((SETUP/'cuda-profile').glob('*.json'))+[Path(v) for v in cfg['_experiment']['cohort'].values()]
    for path in paths:filepins[str(path)]=E.sha256(path)
    receipt=dict(configuration=str(SETUP/'experiment.yaml'),title='PanTS only: longer 72k schedule with ordinary and EMA weights',
        ema=dict(alpha=.99,start_step=500),control_sha256=setup['control_sha256'],file_sha256=filepins,
        preflight=report,backup_reserved_bytes=reserve,receipt_collection_correction='Use prepared_cache.root/control.json; original helper retained unchanged',
        authority='User explicitly approved this single PanTS-only run; no automatic PANORAMA follow-up')
    with (SETUP/'ready.json').open('xb') as stream:stream.write(canonical(receipt))
    print(E.sha256(SETUP/'ready.json'),flush=True)

if __name__=='__main__':main()
