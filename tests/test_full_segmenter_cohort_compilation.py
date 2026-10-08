import json
from pathlib import Path

import pytest

from scripts.compile_full_segmenter_cohort import compile_cohort
from src.training import experiment_config as E


def test_completed_content_selects_roles_and_records_exclusions(tmp_path,monkeypatch):
    audit=tmp_path/'audit';audit.mkdir();cache=tmp_path/'cache';cache.mkdir()
    cohort={}
    for key,text in [('train_ids','t good'),('development_ids','v'),('original_train_ids','t good'),
                     ('original_development_ids','v'),('test_ids','heldout'),('manifest','candidate manifest')]:
        path=tmp_path/key;path.write_text(text);cohort[key]=str(path)
    cohort['review']=None
    cfg={'_experiment':{'cohort':cohort},'full_segmenter':{'geometry':{'fixture':'geometry'}}}
    monkeypatch.setattr(E,'load_experiment',lambda _:cfg)
    source=dict(domain='candidate_audit_only',train=['t','good'],validation=['v'],
        geometry=cfg['full_segmenter']['geometry'],manifest_sha256=E.sha256(cohort['manifest']),
        target_states={'t':'reference_empty','good':'positive','v':'positive'})
    raw=json.dumps(source).encode();(audit/'input-control.json').write_bytes(raw);(cache/'control.json').write_bytes(raw)
    for name in ('good','v'):
        (cache/(name+'.json')).write_text(json.dumps(dict(case_id=name,control_sha256=E.sha256(cache/'control.json'),
            fidelity={'mechanical_survival_pass':True},cache_sha256='a'*64)))
    records=[dict(case_id='t',role='train',status='technical_failure',error='empty pancreas'),
             dict(case_id='good',role='train',status='technical_pass'),dict(case_id='v',role='validation',status='technical_pass')]
    (audit/'cases.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
    (audit/'summary.json').write_text(json.dumps(dict(completed=True,optimizer_updates=0,model_forwards=0,
        cohort_accepted=False,cache=str(cache),passed=2,failed=1)))
    (audit/'resources.json').write_text(json.dumps({'workers_reaped':True}))
    result=compile_cohort('fixture',audit,tmp_path/'out')
    assert result['train_cases']==result['development_cases']==result['excluded']==1
    review=json.loads((tmp_path/'out/cohort-review.json').read_text())
    assert review['exclusions'][0]['case_id']=='t' and review['target_states']=={'good':'positive','v':'positive'}
    assert (tmp_path/'out/train.txt').read_text()=='good\n'
    (audit/'resources.json').write_text(json.dumps({'workers_reaped':False}))
    with pytest.raises(ValueError,match='Completed'):compile_cohort('fixture',audit,tmp_path/'bad')
