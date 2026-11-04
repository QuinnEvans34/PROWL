import json,types
from pathlib import Path
from scripts.diagnostics.prepare_verifier_dashboard_20261031 import patches,MONITOR

def test_staged_parser_reads_actual_verifier_metrics(tmp_path):
    py,html=patches((MONITOR/'experiments.py').read_text(),(MONITOR/'index.html').read_text())
    module=types.ModuleType('staged');module.__file__=str(tmp_path/'experiments.py');exec(compile(py,module.__file__,'exec'),module.__dict__)
    path=tmp_path/'journal.jsonl'
    rows=[dict(event='update',step=5,elapsed_seconds=32.,loss=.6,learning_rate=.0003),dict(event='verifier_tune',step=5,epoch=1,patient_balanced_bce=.55,candidate_patients=3,elapsed_seconds=35.)]
    path.write_text(''.join(json.dumps(r)+'\n' for r in rows));d=module.journal(path,set())
    assert d['seconds']==35 and d['steps']==5 and d['verifier_history'][0]['patient_balanced_bce']==.55
    assert d['history']==[] and 'Latest tuning BCE' in html
