"""Replay case addresses only; no CT, optimizer, model or inference."""
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics import setup_fast_varied as setup
from src.training.segmenter_fast_varied_session_v1 import member_at
from src.training.segmenter_full_session_v1 import Session
from src.data.segmenter_varied_region_v1 import coverage_slots
from src.training.experiment_config import sha256


def main():
    import torch
    output=setup.SETUP/'full-schedule.json'
    if output.exists():raise ValueError('Schedule already checked')
    setup.check_pins();p=setup.varied.provider();reference=setup.read(setup.varied.SETUP/'schedule.json')
    rows={r['case_id']:r for r in map(json.loads,(setup.parent.COHORT/'cases.jsonl').read_text().splitlines())}
    raw=object.__new__(Session);raw.control=p.control;raw.config={'seed':42,'max_steps':24000};raw._epoch=None;raw._order=None
    focused=dict.fromkeys(p.control['train'],0);exposure=focused.copy();counts={'context':0,'reserved':0,'jitter':0}
    before=torch.get_rng_state().clone()
    for step in range(24000):
        raw.step=step;name=raw.next_member()
        if member_at(p.control['train'],step,42)!=name:raise ValueError('Lookahead patient permutation differs')
        exposure[name]+=1
        if step%4==3:counts['context']+=1
        else:
            slots=coverage_slots(reference['focused_counts'][name],rows[name]['cover_windows'])
            counts['reserved' if focused[name] in slots else 'jitter']+=1;focused[name]+=1
    if not torch.equal(before,torch.get_rng_state()):raise ValueError('Lookahead consumed model CPU RNG')
    if focused!=reference['focused_counts'] or exposure!=reference['exposure']:raise ValueError('Exposure changed')
    if counts!={'context':6000,'reserved':2518,'jitter':15482}:raise ValueError('Mix changed')
    setup.write(output,dict(passed=True,updates=24000,cases=1333,counts=counts,
        exact_patient_permutation=True,exact_exposure_and_counters=True,model_rng_unchanged=True,
        CT_reads=0,optimizer_updates=0,source_sha256=sha256(ROOT/'src/training/segmenter_fast_varied_session_v1.py')))
    print(json.dumps(counts))


if __name__=='__main__':main()
