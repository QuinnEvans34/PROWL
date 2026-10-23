"""Verify the frozen setup; --launch is an explicit separate training action."""
import argparse
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))


def main():
    from src.training.experiment_config import sha256
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--receipt',type=Path,required=True);p.add_argument('--sha256',required=True)
    p.add_argument('--launch',action='store_true');a=p.parse_args()
    if sha256(a.receipt)!=a.sha256:raise ValueError('Frozen receipt changed')
    r=json.loads(a.receipt.read_text())
    if r['status']!='ready_to_launch_not_started':raise ValueError('Setup not ready')
    for path,pin in r['file_sha256'].items():
        if sha256(path)!=pin:raise ValueError('Frozen input changed: '+path)
    for name,version in r['packages'].items():
        if importlib.metadata.version(name)!=version:raise ValueError('Environment changed: '+name)
    if sys.version!=r['python_version'] or Path(sys.executable).resolve()!=Path(r['python']).resolve():
        raise ValueError('Python runtime changed')
    command=r['direct_training_command']
    if not a.launch:command=command+['--preflight','--inspect-input-paths']
    subprocess.run(command,cwd=ROOT,check=True)


if __name__=='__main__':main()
