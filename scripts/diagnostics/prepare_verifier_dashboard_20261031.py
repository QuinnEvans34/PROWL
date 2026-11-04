"""Stage phone display changes only; never switch or restart the live dashboard."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics import build_verifier_views_20261031 as build
from src.training.experiment_config import sha256
from src.operations.verifier_candidate_archive_v1 import write_json
MONITOR=Path('C:/Users/quinn/PROWL-Monitor')

def patches(py,html):
    def replace(text,old,new):
        if text.count(old)!=1:raise ValueError('Monitor source shape changed')
        return text.replace(old,new)
    py=replace(py,'native_history=[], progress=None)','native_history=[], verifier_history=[], progress=None)')
    py=replace(py,"            elif event == 'training_completed':", "            elif event == 'verifier_tune':\n                result['verifier_history'].append({k:row[k] for k in ('step','epoch','patient_balanced_bce','candidate_patients')})\n            elif event == 'training_completed':")
    py=replace(py,"generator_only=metric_scope=='generator_no_development_selection'","generator_only=metric_scope in ('generator_no_development_selection','verifier_candidate_classification')")
    py=replace(py,"metric_scope=metric_scope,progress=data['progress'],","metric_scope=metric_scope,progress=data['progress'], verifier_history=data['verifier_history'], tuning_cases=entry.get('tuning_cases',0),")
    card="""if(r.metric_scope==='verifier_candidate_classification')return `<article class="${r.status==='running'?'active':''}" data-run="${esc(r.id)}"><div class="top"><div><h2>${esc(r.title)}</h2><p class="sub">${num(r.train_cases)} fitting scans · ${num(r.tuning_cases)} tuning scans</p></div><span class="badge">${esc(r.status)}</span></div><div class="stats"><div><span class="number">${duration(r.seconds)}</span><span class="label">Logged training time</span></div><div><span class="number">${dice(r.loss)}</span><span class="label">Training loss</span></div><div><span class="number">${dice(r.verifier_history?.at(-1)?.patient_balanced_bce)}</span><span class="label">Latest tuning BCE · lower is better</span></div></div><progress max="${r.target_steps}" value="${r.steps}" aria-label="Training progress"></progress><p class="small">${num(r.steps)} / ${num(r.target_steps)} updates · Last recorded activity ${num(r.age_seconds)}s ago<br>Candidate classification. Development Dice and false-alarm comparisons follow frozen-model calibration.</p></article>`;
"""
    html=replace(html,"if(r.metric_scope==='generator_no_development_selection')",card+"if(r.metric_scope==='generator_no_development_selection')")
    return py,html

def main():
    out=build.BASE/'dashboard'
    if out.exists():raise ValueError('Dashboard staging already exists')
    py,html=patches((MONITOR/'experiments.py').read_text(),(MONITOR/'index.html').read_text())
    compile(py,'staged_experiments.py','exec');out.mkdir()
    (out/'experiments.py').write_text(py);(out/'index.html').write_text(html)
    write_json(out/'handoff.json',dict(status='STAGED_NOT_APPLIED',before={str(MONITOR/f):sha256(MONITOR/f) for f in ('experiments.py','index.html','experiments.json','active-run.json')},
        after={str(out/f):sha256(out/f) for f in ('experiments.py','index.html')},instruction='After explicit scientific launch, apply staged files only after beforehash checks and backups, preserve existing pending generator in history, add verifier entry with tuning_cases67; keep existing private access. Verify actual API updates, loss, tuning BCE and journal-derived hours.'))

if __name__=='__main__':main()
