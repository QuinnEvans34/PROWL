"""Metadata-only binding, bounded CUDA qualification and a new immutable receipt."""
import argparse
from copy import deepcopy
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

import yaml

ROOT = Path(__file__).resolve().parents[2]; sys.path.insert(0, str(ROOT))
from src.training import experiment_config as E
from src.data.manifest_records import canonical
from src.data.source_inventory_records import require
from scripts.train_full_segmenter import preflight, session_config, tree_bytes

SETUP = Path('E:/PROWL/readiness/pants-augmentation-24k-20261017-a01')
BACKUP = Path('C:/Users/quinn/PROWL-Backups/pants-augmentation-qualification-20261017')
NAME = 'pants_only_augmented_views_24k_win_20261017'
SPEC = ROOT/'docs/capstone/operations/PANTS-AUGMENTED-VIEWS-24K-20261017.json'


def environment():
    import torch
    return dict(python=sys.version, executable=sys.executable,
                packages={k:importlib.metadata.version(k) for k in ('torch', 'monai', 'numpy', 'scipy', 'nibabel', 'PyYAML', 'mlflow')},
                cuda=torch.version.cuda, device=torch.cuda.get_device_name(0))


def pins():
    paths = list((ROOT/'src').rglob('*.py')) + list((ROOT/'scripts').rglob('*.py'))
    paths += [SPEC, SPEC.with_suffix('.md'), ROOT/'tests/test_segmenter_augmentation.py',
              ROOT/'tests/test_pants_augmentation_plan.py']
    return {str(p):E.sha256(p) for p in paths}


def configuration():
    cfg = E.load_experiment(SETUP/'experiment.yaml')
    cfg['paths']['output_dir'] = cfg['full_segmenter']['output_dir']
    return cfg


def pipeline(stage):
    with (SETUP/'pipeline.jsonl').open('ab') as stream:
        stream.write(canonical(dict(stage=stage, utc_ms=int(time.time()*1000)))+b'\n')
        stream.flush(); os.fsync(stream.fileno())


def verify_pins():
    setup = json.loads((SETUP/'setup.json').read_text())
    for path, sha in setup['file_sha256'].items(): require(E.sha256(path) == sha, 'Producing file changed: '+path)
    require(environment() == setup['environment'], 'Environment changed')
    return setup


def prepare():
    spec = json.loads(SPEC.read_text()); control = spec['control']; cohort = spec['cohort']
    parent = Path(control['configuration']); old_receipt = parent.parent/'ready.json'
    require(E.sha256(parent) == control['configuration_sha256'], 'Parent configuration changed')
    require(E.sha256(control['matched_native_reports']) == control['matched_native_reports_sha256'], 'Parent native reports changed')
    require(E.sha256(cohort['matched_development_file']) == cohort['matched_development_sha256'], 'Matched development changed')
    original = yaml.safe_load(parent.read_text()); candidate = deepcopy(original)
    old = json.loads(old_receipt.read_text()); env = environment()
    require(all(env['packages'][k] == v for k,v in old['packages'].items()) and env['python'] == old['python_version'],
            'Control numerical runtime differs')
    # Only these previously reviewed shared modules differ from the control receipt.
    allowed = {'src/data/localizer_preprocessing_v4.py', 'src/data/segmenter_geometry_v2.py',
               'src/data/segmenter_prepared_inputs_v1.py', 'src/training/experiment_config.py'}
    changed = {}
    for name, sha in old['file_sha256'].items():
        path = Path(name)
        if path.is_relative_to(ROOT/'src') or path.is_relative_to(ROOT/'scripts'):
            require(path.is_file(), 'Missing control source: '+name)
            if E.sha256(path) != sha:
                relative = path.relative_to(ROOT).as_posix()
                require(relative in allowed, 'Unreviewed control source difference: '+relative)
                changed[relative] = dict(parent_sha256=sha, current_sha256=E.sha256(path))
    original_review = Path(original['cohort']['review']); review = json.loads(original_review.read_text())
    require(review.get('domain') != 'exploratory_pants_panorama_20261012', 'Mixed provider forbidden')
    train = E.ids(Path(original['cohort']['train_ids'])); dev = E.ids(Path(cohort['matched_development_file']))
    excluded = set(E.ids(Path(original['cohort']['development_ids'])))-set(dev)
    require(len(train) == 1333 and len(dev) == 70 and excluded == set(cohort['excluded_development']), 'Frozen cohort mismatch')
    require(not excluded.intersection(train), 'Excluded development entered training')
    require(sum(review['target_states'][n] == 'positive' for n in train) == 671 and
            sum(review['target_states'][n] == 'positive' for n in dev) == 36, 'Target semantics/counts changed')
    init = original['initialization']; require(init['sha256'] == spec['fixed_recipe']['initialization_sha256'] and
            E.sha256(init['checkpoint']) == init['sha256'], 'Original initialization changed')
    SETUP.mkdir(parents=True, exist_ok=False); pipeline('bind')
    (SETUP/'development.txt').write_bytes(Path(cohort['matched_development_file']).read_bytes())
    selected = set(train+dev)
    review['target_states'] = {k:v for k,v in review['target_states'].items() if k in selected}
    review['prepared_cache']['members'] = {k:v for k,v in review['prepared_cache']['members'].items() if k in selected}
    review['input_sha256']['development_ids'] = E.sha256(SETUP/'development.txt')
    review['augmentation_amendment'] = dict(parent_review=str(original_review), parent_sha256=E.sha256(original_review),
        excluded_development=sorted(excluded), reason='Reuse settled matched70; unchanged cached inputs, train-only augmentation', specification=str(SPEC))
    (SETUP/'cohort-review.json').write_bytes(canonical(review))
    candidate['cohort'].update(development_ids=str(SETUP/'development.txt'), review=str(SETUP/'cohort-review.json'))
    candidate['name'] = NAME; candidate['recipe']['full_segmenter']['output_dir'] = 'E:/PROWL/artifacts/'+NAME
    candidate['run']['max_seconds'] = spec['resources']['max_seconds']
    require(candidate['recipe']['full_segmenter']['session'] == original['recipe']['full_segmenter']['session'], 'Numerical recipe changed')
    require(candidate['recipe']['full_segmenter']['geometry'] == original['recipe']['full_segmenter']['geometry'], 'Geometry changed')
    (SETUP/'experiment.yaml').write_text(yaml.safe_dump(candidate, sort_keys=False))
    cfg = configuration(); report = preflight(cfg, inspect=True); require(report['ready'], str(report))
    from src.data.segmenter_prepared_inputs_v1 import PreparedInputs
    provider = PreparedInputs(cfg, cfg['full_segmenter']['geometry'])
    require(not hasattr(provider, 'mixed') and provider.control['train'] == train, 'Unexpected sampler/mixed provider')
    control_input = json.loads(Path('E:/PROWL/artifacts/pants_course_reference_dicefocal_24k_20261011/input-control.json').read_text())
    require(control_input['train'] == provider.control['train'] and control_input['geometry'] == provider.control['geometry'], 'Control training changed')
    require(all(control_input['members'][n] == provider.control['members'][n] and
                control_input['target_states'][n] == provider.control['target_states'][n] for n in selected), 'Cache/member binding changed')
    audit = dict(control_ready_sha256=E.sha256(old_receipt), changed_control_files=changed,
        numerical_packages_identical=True, python_identical=True, ordered_training_identical=True,
        cache_member_hashes_identical=True, geometry_recipe_identical=True, initialization_identical=True,
        selected_control_native_sha256=control['matched_native_reports_sha256'],
        numerical_intervention='Versioned train-only flips/quarter-turns/intensity/noise',
        nonnumerical_changes=['matched70 subset of historical75; same control rescored on70',
            'local MLflow and UTC/augmentation trace journaling', '30h safety watchdog rather than24h; optimizer budget remains24k'],
        shared_code_review={'localizer':'Only permitted cap changes; no localizer invoked',
            'geometry':'Default16M cap and provided-ROI mapping unchanged; cached transforms retained; prior three-affine parity documented',
            'prepared_inputs':'Mixed branch added; PanTS branch unchanged and asserted selected',
            'experiment_config':'Mixed-role metadata branch only for mixed review; retain_steps validation; no numerical changes'},
        inference='Same argmax/restore_codes/native_metrics/target decoder as parent native evaluator',
        limitations=['Reused development cohort, exploratory conditional comparison, not external confirmation',
                    'SuPreM provenance and provided-pancreas ROI limitations unchanged'])
    (SETUP/'compatibility-audit.json').write_bytes(canonical(audit))
    filepins = pins()
    bound = [SETUP/'experiment.yaml', SETUP/'compatibility-audit.json', parent, old_receipt,
             Path(control['matched_native_reports']), provider.root/'control.json', E.resolve(candidate['base_config']),
             Path(init['checkpoint']), Path(init['source_review'])]
    bound += [Path(v) for v in candidate['cohort'].values()]
    for path in bound: filepins[str(path)] = E.sha256(path)
    (SETUP/'setup.json').write_bytes(canonical(dict(parent_configuration=str(parent), parent_sha256=E.sha256(parent),
        file_sha256=filepins, preflight=report, control_sha256=provider.pin, environment=env, scientific_training_launched=False)))
    print(json.dumps(report), flush=True)


def worker(cold):
    import torch
    from src.training.segmenter_full_session_v1 import Session, identity_for
    from src.training.segmenter_augmentation_v1 import AugmentedSession, augmentation_identity
    from src.training.segmenter_full_executor_v1 import atomic_checkpoint
    from src.training.segmenter_native_case_v1 import native_case
    from src.data.segmenter_prepared_inputs_v1 import PreparedInputs
    from src.operations.full_training_platform import durable_replace
    from scripts.diagnostics.profile_lenovo_real_segmenter import compare
    setup = verify_pins(); cfg = configuration(); output = SETUP/'cuda-profile'
    torch.set_num_threads(2); started = time.monotonic(); torch.cuda.reset_peak_memory_stats()
    provider = PreparedInputs(cfg, cfg['full_segmenter']['geometry'])
    require(provider.pin == setup['control_sha256'], 'Qualification control changed')
    config = dict(session_config(cfg), max_steps=4, warmup_steps=1, lr_horizon_steps=4)
    if cold:
        saved = torch.load(BACKUP/'saved.pt', map_location='cpu', weights_only=True)['session']
        expected = torch.load(output/'expected.pt', map_location='cpu', weights_only=True)['session']
        identity = dict(version='segmenter-augmented-session-1', raw=identity_for(config, provider.control, 'cuda', cfg['_experiment']['initialization']),
                        augmentation=augmentation_identity())
        session = AugmentedSession.restore(saved, identity); compare(session.state(), saved, exact=True)
        update = session.update(provider); maxima = []; compare(session.state(), expected, maxima=maxima)
        expected_update = json.loads((output/'producer.json').read_text())['updates'][-1]
        require(update['augmentation'] == expected_update['augmentation'] and update['batch_sha256'] == expected_update['batch_sha256'],
                'Cold augmentation view not exact')
        report = dict(full_state_restore_exact=True, next_state_close=True, augmented_batch_exact=True,
                      max_absolute_difference=max(maxima, default=0), rtol=1.3e-6, atol=1e-5, optimizer_updates=1, update=update)
    else:
        session = AugmentedSession(Session(config, provider.control, device='cuda', initialization=cfg['_experiment']['initialization']))
        updates = [session.update(provider) for _ in range(3)]
        atomic_checkpoint(output/'saved.pt', session, best_score=None, history_bytes=0)
        temp = BACKUP/'saved.partial'
        with (output/'saved.pt').open('rb') as src, temp.open('xb') as dest:
            shutil.copyfileobj(src, dest); dest.flush(); os.fsync(dest.fileno())
        require(E.sha256(temp) == E.sha256(output/'saved.pt'), 'Backup mismatch')
        durable_replace(temp, BACKUP/'saved.pt')
        updates.append(session.update(provider)); atomic_checkpoint(output/'expected.pt', session, best_score=None, history_bytes=0)
        names = [next(n for n in provider.control['validation'] if provider.control['target_states'][n] == state)
                 for state in ('positive', 'reference_empty')]
        evaluations = [native_case(session.raw, provider, n) for n in names]
        report = dict(optimizer_updates=4, updates=updates, native_evaluations=evaluations, backup_sha256=E.sha256(BACKUP/'saved.pt'))
    torch.cuda.synchronize()
    report.update(seconds=time.monotonic()-started, peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                  peak_reserved_bytes=torch.cuda.max_memory_reserved(), nonpromotable=True, control_sha256=provider.pin)
    (output/('cold.json' if cold else 'producer.json')).write_bytes(canonical(report))


def qualify():
    from src.operations.full_training_platform import training_guard, watch_windows, require_ac
    verify_pins(); output = SETUP/'cuda-profile'; output.mkdir(exist_ok=False); BACKUP.mkdir(exist_ok=False)
    require(output.stat().st_dev != BACKUP.stat().st_dev, 'Independent backup required')
    cfg = configuration(); full = cfg['full_segmenter']; last = [0.]
    def tick():
        if time.monotonic()-last[0] < 30: return
        require_ac()
        for path in (output, BACKUP): require(shutil.disk_usage(path).free >= 100*1024**3, 'Storage floor')
        require(tree_bytes(full['backup_dir'])+512*1024**2 <= full['backup_cap_bytes'], 'Diagnostic backup reserve')
        last[0] = time.monotonic()
    with training_guard(ROOT/'outputs/prowl/.cuda-training.lock'):
        for stage in ('producer', 'cold'):
            tick(); pipeline(stage)
            with (output/(stage+'.log')).open('x') as log:
                process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '--stage', stage], cwd=ROOT,
                                          stdout=log, stderr=subprocess.STDOUT)
                try: watch_windows(process, seconds=1800, rss_bytes=12*1024**3, tick=tick)
                finally: (output/(stage+'-resources.json')).write_bytes(canonical(getattr(process, 'duration_resources', {})))
            print(stage+' passed and worker reaped', flush=True)


def freeze():
    setup = verify_pins()
    suites = list(ET.parse(SETUP/'tests.xml').getroot().iter('testsuite'))
    require(suites and sum(int(s.get('tests','0')) for s in suites) >= 50 and
            all(int(s.get('failures','0')) == int(s.get('errors','0')) == 0 for s in suites), 'Insufficient/pending/failed tests')
    for stage in ('producer', 'cold'):
        require(json.loads((SETUP/'cuda-profile'/f'{stage}-resources.json').read_text()).get('workers_reaped') is True, 'Worker not reaped')
    producer = json.loads((SETUP/'cuda-profile/producer.json').read_text())
    cold = json.loads((SETUP/'cuda-profile/cold.json').read_text())
    require(producer['optimizer_updates'] == 4 and len(producer['native_evaluations']) == 2 and
            cold['optimizer_updates'] == 1 and cold['full_state_restore_exact'] and cold['next_state_close'] and cold['augmented_batch_exact'], 'Qualification incomplete')
    require(E.sha256(BACKUP/'saved.pt') == producer['backup_sha256'] == E.sha256(SETUP/'cuda-profile/saved.pt'), 'Backup changed')
    cfg = configuration(); full = cfg['full_segmenter']; report = preflight(cfg, inspect=True); require(report['ready'], str(report))
    reserve = 8*(SETUP/'cuda-profile/saved.pt').stat().st_size+256*1024**2
    require(tree_bytes(full['backup_dir'])+reserve < full['backup_cap_bytes'], 'Backup allocation')
    require(tree_bytes(full['cache_dir']) <= full['cache_max_bytes'], 'Cache allocation')
    for path in (Path('C:/'), Path('E:/')): require(shutil.disk_usage(path).free > 100*1024**3+reserve, 'Storage reserve')
    require(not Path(full['output_dir']).exists() and not (Path(full['backup_dir'])/NAME).exists(), 'Run already exists')
    review = json.loads(Path(cfg['_experiment']['cohort']['review']).read_text())
    filepins = dict(setup['file_sha256'])
    paths = [SETUP/'experiment.yaml', SETUP/'setup.json', SETUP/'tests.xml', SETUP/'compatibility-audit.json',
             Path(review['prepared_cache']['root'])/'control.json', E.resolve(yaml.safe_load((SETUP/'experiment.yaml').read_text())['base_config']),
             Path(cfg['_experiment']['initialization']['source_review']), Path(cfg['_experiment']['initialization']['checkpoint'])]
    paths += list((SETUP/'cuda-profile').glob('*.json')) + [Path(v) for v in cfg['_experiment']['cohort'].values()]
    spec = json.loads(SPEC.read_text())
    paths += [Path(spec['control']['configuration']), Path(spec['control']['matched_native_reports'])]
    for path in paths: filepins[str(path)] = E.sha256(path)
    from src.training.segmenter_augmentation_v1 import augmentation_identity
    receipt = dict(configuration=str(SETUP/'experiment.yaml'), title=spec['title'], experiment_id=spec['experiment_id'],
        augmentation=augmentation_identity(), control_sha256=setup['control_sha256'], environment=setup['environment'],
        file_sha256=filepins, preflight=report, backup_reserved_bytes=reserve,
        authority='User explicitly approved completing setup, updating the phone dashboard and launching this single qualified PanTS augmentation run')
    with (SETUP/'ready.json').open('xb') as stream: stream.write(canonical(receipt)); stream.flush(); os.fsync(stream.fileno())
    pipeline('ready'); print(E.sha256(SETUP/'ready.json'), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stage', choices=['prepare', 'qualify', 'producer', 'cold', 'freeze'], required=True)
    a = p.parse_args()
    try:
        if a.stage in ('producer', 'cold'): worker(a.stage == 'cold')
        else: globals()[a.stage]()
    except BaseException:
        if SETUP.exists(): pipeline('failed')
        raise
