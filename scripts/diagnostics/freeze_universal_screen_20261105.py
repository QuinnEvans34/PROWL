"""Freeze one inference-only request after CPU checks; does not issue a permit."""
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics.run_universal_screen_20261105 import PREP,MODEL,OUT,BACKUP,write,gate
from src.inference.universal_model_loading_20261105 import digest


def main():
    if (PREP/'request.json').exists() or OUT.exists() or BACKUP.exists():raise FileExistsError('Freeze/dispatch already exists')
    gate()
    spec=subprocess.check_output(['git','show','837533e:docs/capstone/operations/UNIVERSAL-SWIN-OVERNIGHT-20261105.md'])
    (PREP/'specification.md').write_bytes(spec)
    admitted=json.loads((PREP/'input-admission.json').read_text())
    if not admitted['development_admitted'] or admitted['eligible_train']:raise ValueError('Wrong inference-only admission')
    if 'Ran 18 tests' not in (PREP/'tests-final-v2.log').read_text() or 'OK' not in (PREP/'tests-final-v2.log').read_text():raise ValueError('CPU tests not complete')
    pins={}; dependencies=set()
    for kind in ('worker','supervisor'):
        env=json.loads((PREP/(kind+'-environment.json')).read_text())
        for path,pin in env['imported_and_mapped_file_pins'].items():
            if digest(path)!=pin:raise ValueError('Audited dependency changed: '+path)
            pins[path]=pin
            if not Path(path).is_relative_to(ROOT) or 'site-packages' in path:dependencies.add(path)
    for folder in ('src','scripts'):
        for path in (ROOT/folder).rglob('*.py'):pins[str(path.resolve())]=digest(path)
    for path in (ROOT/'tests').glob('test_universal*20261105.py'):pins[str(path.resolve())]=digest(path)
    for path in (MODEL/'source').rglob('*'):
        if path.is_file() and '__pycache__' not in str(path):pins[str(path.resolve())]=digest(path)
    for name in ('source-receipt.json','acquisition.json'):pins[str((MODEL/name).resolve())]=digest(MODEL/name)
    for name in ('specification.md','input-plan.json','input-admission.json','worker-environment.json','supervisor-environment.json','tests-final-v2.log'):
        pins[str((PREP/name).resolve())]=digest(PREP/name)
    inputs=[r for r in admitted['cases'] if r['role']=='development']
    observations={p:[Path(p).stat().st_size,Path(p).stat().st_mtime_ns] for p in pins}
    r={'schema':'prowl.universal-four-positive-screen.v1','status':'CPU_READY_REQUIRES_MAC_COMPLETION_PERMIT_AND_CUDA_PILOT',
       'cases':[c['case_id'] for c in inputs],'inputs':inputs,'training_admission':'NOT_ADMITTED','optimizer_updates':0,
       'training_rejections':[{k:c[k] for k in ('case_id','role','narrow_prior_role','failures')} for c in admitted['cases'] if c['role']=='train'],
       'specification_sha256':digest(PREP/'specification.md'),'source_revision':'43c12399cc98a40f447342a8dc2cecae5edae84c',
       'weights_revision':'76f0304ff9387c1baccbbc1d9eac78c5c5ccfeed','weight_sha256':digest(MODEL/'checkpoint.pth'),
       'output':str(OUT),'backup':str(BACKUP),'case_seconds':3600,'charged_preparation_seconds':3600,
       'preparation_accounting':'Conservative one-hour charge covers acquisition, CPU audit/header/tests and setup compute; no cap reset.',
       'limits':{'total_seconds_including_preparation':21600,'pilot_total_seconds':600,'owned_rss_bytes':12*1024**3,
                 'cuda_allocated_and_reserved_bytes':6*1024**3,'minimum_free_each_volume':100*1024**3,
                 'new_output_bytes':8*1024**3,'new_backup_bytes':8*1024**3,'aggregate_backup_bytes':64*1024**3},
       'representation':{'orientation':'RAS','spacing_mm':[1.5]*3,'hu_window':[-175,250],'scaled_range':[0,1],
                         'foreground':'CT scaled intensity > 0; no reference inputs','window':[96]*3,'overlap':.5,
                         'blending':'Gaussian logits; two selected channels accumulated on CPU','channel_indices':[10,27],
                         'native_restoration':'sigmoid followed by world-affine linear probability interpolation, grid-constant zero outside crop',
                         'decision':'strict >0.5; lesion precedence in combined codes; raw pancreas saved separately',
                         'implementation':'current MONAI1.6 preprocessing; not claimed identical to upstream MONAI0.9 hard-mask inverse',
                         'TTA':False,'postprocessing':False},
       'claims':{'external_exposure':'unknown','scope':'four exposed-development positive cases; descriptive only',
                 'independent_generalization':False,'empty_alarm_rate':'NOT_MEASURED','hypothesis_verdict':'NOT_TESTED'},
       'pins':pins,'pin_observations':observations,'environment_dependency_paths':sorted(dependencies),
       'integrity_policy':'Full byte verification before dispatch; subsequent unchanged dependency size/mtime guards; code hashes each stage; input hashes in separate admission/CT-inference/reference-scoring stages.'}
    write(PREP/'request.json',r)
    print(json.dumps({'request_sha256':digest(PREP/'request.json'),'specification_sha256':r['specification_sha256'],'pins':len(pins),'cases':r['cases']}))


if __name__=='__main__':main()
