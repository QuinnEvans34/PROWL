"""Exercise proposed monitor configuration in memory; never change the live UI."""
import importlib
import json
from pathlib import Path
import sys
import urllib.request
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.diagnostics import setup_fast_varied as setup
from src.training.experiment_config import sha256


def main():
    monitor=Path('C:/Users/quinn/PROWL-Monitor');handoff=setup.read(setup.SETUP/'dashboard-handoff.json')
    for name,pin in handoff['existing_pins'].items():
        if sha256(name)!=pin:raise ValueError('Live dashboard configuration changed')
    sys.path.insert(0,str(monitor))
    experiments=importlib.import_module('experiments');original=experiments.dashboard()
    setup.write(setup.SETUP/'dashboard-experiments.json',handoff['experiments'])
    setup.write(setup.SETUP/'dashboard-active.json',handoff['active_run'])
    experiments.REGISTRY=setup.SETUP/'dashboard-experiments.json'
    proposed=experiments.dashboard()
    server=importlib.import_module('server');server.ACTIVE=setup.SETUP/'dashboard-active.json'
    status=server.current_status()
    if not original['totals_complete'] or not proposed['totals_complete']:raise ValueError('Unavailable existing experiment')
    if proposed['total_seconds']!=original['total_seconds'] or proposed['total_steps']!=original['total_steps']:
        raise ValueError('Preparation changed scientific totals')
    if len({r['id'] for r in proposed['runs']})!=len(proposed['runs']):raise ValueError('Duplicated historical run')
    if status['status']!='preparing':raise ValueError('Prelaunch falsely shown running')
    with urllib.request.urlopen('http://127.0.0.1:8765/api/experiments',timeout=30) as response:
        live=json.load(response);api_status=response.status
    setup.write(setup.SETUP/'dashboard-check.json',dict(passed=True,live_api_status=api_status,
        live_totals_complete=live['totals_complete'],retained_runs=len(proposed['runs']),
        scientific_seconds_unchanged=proposed['total_seconds'],scientific_steps_unchanged=proposed['total_steps'],
        prelaunch_status=status['status'],new_run_not_counted=True,live_configuration_unchanged=True,
        configuration_sha256=sha256(setup.SETUP/'dashboard-handoff.json')))
    print('Proposed dashboard preserves all scientific totals and history; localhost API healthy; live config unchanged')


if __name__=='__main__':main()
