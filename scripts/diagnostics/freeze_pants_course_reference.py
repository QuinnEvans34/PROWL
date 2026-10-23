"""Freeze qualified setup evidence and generate a checked launch receipt; no training."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))


def main():
    from src.training import experiment_config as E
    from scripts.train_full_segmenter import preflight,tree_bytes
    from src.operations.full_training_platform import require_ac
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--setup',type=Path,required=True)
    a=p.parse_args();base=a.setup
    setup=json.loads((base/'setup.json').read_text());config=Path(setup['configuration'])
    cfg=E.load_experiment(config);full=cfg['full_segmenter'];cfg['paths']['output_dir']=full['output_dir']
    check=preflight(cfg,inspect=True);assert check['ready'],check
    require_ac()
    assert not Path(full['output_dir']).exists()
    assert not (Path(full['backup_dir'])/cfg['_experiment']['name']).exists()
    producer=json.loads((base/'cuda-profile/producer.json').read_text())
    cold=json.loads((base/'cuda-profile/cold.json').read_text())
    native=json.loads((base/'native-qualification-a02/report.json').read_text())
    assert producer['optimizer_updates']==3 and cold['full_state_restore_exact'] and cold['next_state_close']
    assert len(native['cases'])==2 and native['test_reads']==native['optimizer_updates']==0
    for rel in ('cuda-profile/producer-resources.json','cuda-profile/cold-resources.json','native-qualification-a02/resources.json'):
        assert json.loads((base/rel).read_text())['workers_reaped']
    reserve=(base/'cuda-profile/saved.pt').stat().st_size*7+128*1024**2
    assert tree_bytes(full['backup_dir'])+reserve<=full['backup_cap_bytes']
    free={d:shutil.disk_usage(d).free for d in ('C:/','E:/')}
    assert min(free.values())>cfg['_experiment']['run']['min_free_bytes']+reserve
    files=list((ROOT/'src').rglob('*.py'))+list((ROOT/'scripts').rglob('*.py'))
    files += [config, E.resolve(cfg['_experiment']['base_config']),
              ROOT/'docs/capstone/operations/PANTS-COURSE-REFERENCE-LONG-RUN-20261011.json']
    files += [E.resolve(v) for v in cfg['_experiment']['cohort'].values()]
    files += [E.resolve(cfg['_experiment']['initialization']['source_review'])]
    files += list(base.rglob('*.json'))
    versions={n:importlib.metadata.version(n) for n in ('torch','monai','numpy','scipy','nibabel','PyYAML')}
    receipt=dict(status='ready_to_launch_not_started',title='PanTS-only long run: recover the course recipe before adding PANORAMA',
        experiment_id='CAP-EXP-016',configuration=str(config),configuration_sha256=E.sha256(config),
        python=sys.executable,python_version=sys.version,packages=versions,
        code_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        code_state='Includes uncommitted working-tree changes bound by hashes; commit alone is not producing identity',
        file_sha256={str(f):E.sha256(f) for f in files},counts=setup['counts'],preflight=check,
        changed_recipe_qualification=dict(producer_updates=3,cold_updates=1,development_forwards=2,
            exact_restore=True,next_state_max_absolute_difference=cold['max_absolute_difference']),
        native_evaluator=dict(real_development_cases=2,real_cases_positive_only=True,
            qualification_only=True,failed_attempt_preserved='native-qualification',
            repair='Use approved semantic binary decoder shared with preparation'),
        tests='60 distinct focused tests across course recipe/full session/resume/windows/geometry/config, plus 34 binary-label tests; one explicit MPS-native skip. Repeated checks not double-counted.',
        backup_reserve_bytes=reserve,free_bytes=free,
        training_started=False,cache_rebuilt=False,scheduled_checks=False,
        direct_training_command=[sys.executable,str(ROOT/'scripts/train_full_segmenter.py'),'--experiment',str(config)],
        evaluation_command_template='evaluate_pants_native.py --experiment CONFIG --checkpoint CHECKPOINT --sha256 SHA256 --output FRESH_OUTPUT',
        comparison_command_template='compare_pants_course_reference.py --early NATIVE_8000_REPORT --final NATIVE_24000_REPORT --output FRESH_JSON',
        limitations=['Provided-pancreas development only; source membership unverified',
                    'One seed; historical comparison not matched; point-estimate detection/false-alarm guardrails',
                    'Full 75-case native evaluation occurs at scientific endpoints; qualification read two positive references only'])
    dest=base/'ready.json'
    with dest.open('x') as f:json.dump(receipt,f,indent=2);f.write('\n')
    print(json.dumps(dict(status=receipt['status'],receipt=str(dest),sha256=E.sha256(dest),counts=receipt['counts']),indent=2))


if __name__=='__main__':main()
