"""Separate report-supervised release; reuse unchanged fixed Mac pilot executor."""
import json
import os
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.qualify_distillation_mac import BASE,write,storage_preflight
from scripts.diagnostics.bind_mac_distillation_metadata import sha
from src.operations.full_training_platform import require_ac,training_guard
REV='eab1a7e9f421740bf8f3f834d1f69d17cbe3a8aa'
SHA='38535f10430265e431ca3ffa7fe3ff15efed5bccb65ba909b6e3ce18af11e459'
SIZE=606931502
BUNDLE=BASE/'teacher-rsuper-merlin'
CONVERT=BASE/'rsuper-merlin-convert-01'
PILOT=BASE/'rsuper-merlin-pilot-01'


def acquire():
    from scripts.diagnostics import acquire_distillation_teacher as a
    storage_preflight();BUNDLE.mkdir(exist_ok=False)
    a.STORAGE_ROOT=Path('/Volumes/PROWL-Data')
    original=json.loads((BASE/'teacher/acquisition.json').read_text())
    for row in original['files']:assert sha(Path(row['path']))==row['sha256']
    files=[]
    for remote,local,maximum,pin in [
        ('merlin_pancreas_pants_release/fold_0_latest.pth','merlin_pancreas_pants_release/fold_0_latest.pth',SIZE,SHA),
        ('README.md','README.md',131072,None),('labels_pants.yaml','labels_pants.yaml',131072,None),
        ('merlin_pancreas_pants_release/config.txt','pants_pancreas_release/config.txt',131072,None)]:
        files.append(a.fetch(f'https://huggingface.co/AbdomenAtlas/R-SuperPanTSMerlin/resolve/{REV}/{remote}',
            BUNDLE/'release'/local,maximum=maximum,sha256=pin))
    # Byte-identical source/dependencies, isolated bundle. Config destination is
    # an explicit runtime layout alias; contents and release URL remain unchanged.
    for folder in ['source','dependencies']:
        shutil.copytree(BASE/'teacher'/folder,BUNDLE/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for p in sorted((BUNDLE/folder).rglob('*')):
            if p.is_file():
                original_path=BASE/'teacher'/folder/p.relative_to(BUNDLE/folder)
                assert sha(p)==sha(original_path)
                files.append(dict(path=str(p),sha256=sha(p),copied_from=str(original_path)))
    write(BUNDLE/'acquisition.json',dict(success=True,hf_revision=REV,code_revision=original['code_revision'],
        files=files,config_layout_alias='pants_pancreas_release/config.txt contains unchanged R-SuperPanTSMerlin config',
        license_note='Candidate card lacks explicit model license; no redistribution',model_execution=False))


def convert_worker():
    from scripts.diagnostics import convert_distillation_teacher as c
    c.BASE=BUNDLE;c.OUT=CONVERT;c.CHECKPOINT=BUNDLE/'release/merlin_pancreas_pants_release/fold_0_latest.pth';c.SHA=SHA
    c.worker()


def pilot_worker():
    from scripts.diagnostics import pilot_distillation_mac_v2 as p
    p.OUT=PILOT
    p.worker()


def main(stage):
    from src.operations.mac_pilot_supervision_v1 import run
    storage_preflight();require_ac()
    if stage=='acquire':acquire();return
    if stage=='convert':
        CONVERT.mkdir(exist_ok=False)
        write(CONVERT/'request.json',dict(checkpoint_sha256=SHA,seconds=180,rss_bytes=4*1024**3,
              producer_sha256=sha(Path(__file__))))
        ok=run([sys.executable,__file__,'convert-worker'],CONVERT,seconds=180,rss_bytes=4*1024**3,
            env={**os.environ,'PROWL_TEACHER_CONVERT':'1','OMP_NUM_THREADS':'1'})
    elif stage=='pilot':
        from src.training.teacher_medformer_v1 import bundle_identity
        from scripts.diagnostics.pilot_distillation_mac_v2 import LIMITS
        old=json.loads((BASE/'patient-pilot-02/request.json').read_text())
        for p,h in old['pins'].items():assert sha(Path(p))==h,p
        request=dict(old,teacher=bundle_identity(BUNDLE,CONVERT/'conversion.json'),
            scope='R-SuperPanTSMerlin matched fixed12 exploratory pilot; original labels retained for paired rescore')
        request['pins']=dict(old['pins'])
        for p in [Path(__file__).resolve(),ROOT/'scripts/diagnostics/pilot_distillation_mac_v2.py']:
            request['pins'][str(p)]=sha(p)
        PILOT.mkdir(exist_ok=False);write(PILOT/'request.json',request)
        def tick():
            if sum(p.stat().st_size for p in PILOT.iterdir() if p.is_file())>LIMITS['output_bytes']:raise ValueError('Output budget')
        with training_guard(ROOT/'outputs/prowl/.mps-profile.lock'):
            ok=run(['caffeinate','-i',sys.executable,__file__,'pilot-worker'],PILOT,seconds=LIMITS['seconds'],rss_bytes=LIMITS['rss_bytes'],tick=tick,
                env={**os.environ,'PROWL_MAC_TEACHER_PILOT':'1','PYTORCH_ENABLE_MPS_FALLBACK':'0','OMP_NUM_THREADS':'2'})
    else:raise ValueError(stage)
    if not ok:raise SystemExit(1)


if __name__=='__main__':
    stage=sys.argv[1]
    if stage=='convert-worker':convert_worker()
    elif stage=='pilot-worker':pilot_worker()
    else:main(stage)
