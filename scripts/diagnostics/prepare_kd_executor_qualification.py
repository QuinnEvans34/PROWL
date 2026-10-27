"""Prepare a bound qualification request from full admission; never launch a worker."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.data.manifest_records import canonical, digest
from src.data.teacher_target_publication_v1 import read_bound
from src.data.segmenter_teacher_cache_v1 import sha, TeacherTargetStore
from src.data.pants_errata_kd_inputs_v1 import THROUGHPUT


def prepare(admitted, output, *, admission_sha256, control_design, kd_design):
    admitted = Path(admitted).resolve(strict=True)
    destination = Path(output).absolute()
    output = destination.parent.resolve(strict=True) / destination.name
    if output == admitted or admitted in output.parents or output in admitted.parents:
        raise ValueError('Preparation must be separate from admitted targets')
    if output.exists():
        raise FileExistsError(output)
    receipt = read_bound(admitted/'admission.json', admission_sha256)
    if receipt.get('version') != 'full-teacher-admission-1' or receipt.get('members') != 1333:
        raise ValueError('Full admission receipt required')
    control_path = admitted/'provider-control.json'
    control = read_bound(control_path, receipt['provider_sha256'])
    if (len(control['train']) != 1333 or len(control['validation']) != 70
            or len(set(control['train'])) != 1333
            or len(set(control['validation'])) != 70
            or set(control['train']) & set(control['validation'])):
        raise ValueError('Exact disjoint full cohort required')
    if control.get('throughput') != THROUGHPUT or not control.get('label_revision'):
        raise ValueError('Corrected on-demand provider required')
    source_root = Path(receipt['producer_root'])
    producer = {name: read_bound(source_root/name, pin)
                for name, pin in receipt['source_record_hashes'].items()}
    if set(producer) != {'request.json', 'result.json', 'resources.json'}:
        raise ValueError('Terminal producer bindings required')
    request, result, resources = [producer[name] for name in ('request.json','result.json','resources.json')]
    if (request['train'] != control['train'] or result.get('complete') is not True
            or result.get('success') is not True or resources.get('success') is not True
            or resources.get('workers_reaped') is not True
            or type(resources.get('exit_code')) is not int or resources['exit_code'] != 0):
        raise ValueError('Completed reaped producer required')
    teacher = request['teacher']
    common = dict(teacher_sha256=teacher['weights']['sha256'],
                  teacher_config_sha256=digest(canonical(teacher['config'])),
                  teacher_mapping_sha256=digest(canonical(teacher['labels'])),
                  preprocessing_sha256=digest(canonical(request['preprocessing_policy'])),
                  control_sha256=receipt['provider_sha256'])
    if json.loads((admitted/'common-identity.json').read_text()) != common:
        raise ValueError('Teacher identity differs from completed producer')
    store = TeacherTargetStore(admitted, receipt['manifest_sha256'], control=control,
                               common_identity=common)
    if store.manifest.get('qualification_only') is not False:
        raise ValueError('Partial qualification manifest rejected')
    for kind in ('request', 'result', 'resources'):
        if store.manifest.get(f'producer_{kind}_sha256') != digest(canonical(producer[kind+'.json'])):
            raise ValueError('Manifest producer binding mismatch')
    designs = [json.loads(Path(path).read_text()) for path in (control_design, kd_design)]
    if [d['distillation']['max_weight'] for d in designs] != [0, .1]:
        raise ValueError('Expected paired KD weights')
    left = deepcopy(designs[0]); left['distillation']['max_weight'] = .1
    if left != designs[1]:
        raise ValueError('Unmatched scientific design')
    for d in designs:
        if d['membership'] != dict(train=control['bindings']['train_file'],
                                   development=control['bindings']['dev_file']):
            raise ValueError('Design split bindings differ from provider')
        if d['backend'] != 'mps' or d['precision'] != 'float32':
            raise ValueError('Expected MPS float32 design')
        cfg = d['student_configuration']
        if cfg['session']['max_steps'] != 24000 or cfg['session']['lr_horizon_steps'] != 24000:
            raise ValueError('Original 24k design required')
        if any(cfg[key] != control[key] for key in ('region_policy', 'training_view_policy')):
            raise ValueError('Provider geometry or sampling differs')
    # Explicit operational binding, never overwrite historical design files.
    operational = deepcopy(designs)
    for d in operational:
        d['student_configuration']['throughput_policy'] = THROUGHPUT['version']
        d['provider_sha256'] = receipt['provider_sha256']
        d['target_manifest_sha256'] = receipt['manifest_sha256']
    files = [Path(__file__).resolve(), Path(control_design).resolve(), Path(kd_design).resolve(),
             admitted/'admission.json', control_path, admitted/'common-identity.json', admitted/'manifest.json']
    for folder in ('src/data', 'src/training', 'src/operations'):
        files.extend(sorted((ROOT/folder).glob('*.py')))
    payload = dict(version='full-provider-kd-qualification-preparation-1',
        status='PREPARED_NOT_GPU_QUALIFIED', scientific_ready=False,
        admitted_targets=str(admitted), teacher=teacher,
        preprocessing_policy=request['preprocessing_policy'], operational_designs=operational,
        pins={str(p): sha(p) for p in files},
        required_checks=['exclusive GPU, AC, storage and supervised resource admission',
                         'actual full-provider zero-KD equivalence and positive-KD updates',
                         'native positive and empty development evaluation with component evidence',
                         'independent checkpoint backup and fresh-process next-update restore',
                         'measured storage/runtime and matched scientific launch receipts'])
    output.mkdir(parents=False)
    with (output/'preparation.json').open('xb') as stream:
        stream.write(canonical(payload))
    return payload


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--admitted', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--admission-sha256', required=True)
    args = parser.parse_args(argv)
    designs = ROOT/'configs/experiments/mac-kd-comparison-20261023'
    prepare(args.admitted, args.output, admission_sha256=args.admission_sha256,
            control_design=designs/'control.json', kd_design=designs/'treatment.json')
    print(json.dumps(dict(status='PREPARED_NOT_GPU_QUALIFIED',
                         path=str(args.output/'preparation.json'))))


if __name__ == '__main__':
    main()
