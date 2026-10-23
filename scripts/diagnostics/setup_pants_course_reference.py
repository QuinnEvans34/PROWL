"""Prepare metadata/configuration only; never launches training or decodes CTs."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys
import yaml

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))


def main():
    from src.training import experiment_config as E
    from scripts.train_full_segmenter import preflight
    from src.data.segmenter_prepared_inputs_v1 import PreparedInputs
    from src.training.segmenter_full_session_v1 import DICE_FOCAL
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    spec=yaml.safe_load(a.source.read_text())
    spec['name']='pants_course_reference_dicefocal_24k_20261011'
    full=spec['recipe']['full_segmenter']
    full['output_dir']='E:/PROWL/artifacts/'+spec['name']
    full['session'].update(loss_id=DICE_FOCAL,warmup_steps=500,lr_horizon_steps=24000)
    spec['run'].update(max_updates=24000,validate_every=2000,checkpoint_every=500,
                       log_every=25,max_seconds=86400,retain_steps=[8000,24000])
    a.output.mkdir(parents=True,exist_ok=False)
    path=a.output/'experiment.yaml'
    path.write_text(yaml.safe_dump(spec,sort_keys=False))
    cfg=E.load_experiment(path);cfg['paths']['output_dir']=full['output_dir']
    report=preflight(cfg,inspect=True)
    if not report['ready']:raise ValueError(report)
    provider=PreparedInputs(cfg,full['geometry'])
    review=json.loads(Path(spec['cohort']['review']).read_text())
    counts={role:dict(Counter(review['target_states'][n] for n in provider.control[role])) for role in ('train','validation')}
    assert counts=={'train':{'positive':671,'reference_empty':662},'validation':{'positive':38,'reference_empty':37}},counts
    files=[a.source,path,*[E.resolve(v) for v in spec['cohort'].values()],
           ROOT/'docs/capstone/operations/PANTS-COURSE-REFERENCE-LONG-RUN-20261011.json']
    files+=list((ROOT/'src').rglob('*.py'))+list((ROOT/'scripts').rglob('*.py'))
    receipt=dict(status='metadata_preflight_passed_qualification_pending',training_started=False,
        counts=counts,preflight=report,configuration=str(path),source_sha256={str(f):E.sha256(f) for f in files},
        reused_cache=str(provider.root),cache_rebuilt=False,source_CT_payload_reads=0,
        spec_comparison='historical_context_not_matched_course_reproduction',
        qualification_command=['scripts/diagnostics/profile_lenovo_real_segmenter.py','--experiment',str(path),
            '--output',str(a.output/'cuda-profile'),'--backup','C:/Users/quinn/PROWL-Backups/pants-course-qualification-20261011',
            '--validation-limit','2'])
    (a.output/'setup.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('source_sha256','preflight')},indent=2))


if __name__=='__main__':main()
