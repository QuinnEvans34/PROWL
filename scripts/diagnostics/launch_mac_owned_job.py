"""One-shot launchd ownership, independent of the initiating terminal/chat.

No timer, KeepAlive, login installation, or automatic retries. Plist stays in the
artifact directory; explicit bootstrap is the only launch trigger.
"""
import argparse,json,os,plistlib,re,subprocess
from pathlib import Path

def definition(label,argv,cwd,out,env):
    if not re.fullmatch(r'com\.prowl\.[a-z0-9.-]+',label):raise ValueError('Scoped label required')
    if not argv or not Path(argv[0]).is_absolute() or not Path(argv[0]).is_file():raise ValueError('Absolute executable required')
    if not Path(cwd).is_dir() or not Path(out).is_dir():raise ValueError('Existing paths required')
    return dict(Label=label,ProgramArguments=argv,WorkingDirectory=str(cwd),EnvironmentVariables=env,
        RunAtLoad=True,KeepAlive=False,ProcessType='Background',ExitTimeOut=15,
        StandardOutPath=str(Path(out)/'launchd.stdout.log'),StandardErrorPath=str(Path(out)/'launchd.stderr.log'))

def start(label,argv,cwd,out,env):
    domain=f'gui/{os.getuid()}';target=domain+'/'+label
    if subprocess.run(['launchctl','print',target],capture_output=True).returncode==0:raise ValueError('Job already registered')
    registration=Path.home()/'Library/Application Support/PROWL/owned-jobs'
    registration.mkdir(parents=True,exist_ok=True)
    logs=registration/label;logs.mkdir(exist_ok=False)
    p=registration/(label+'.plist');record=definition(label,argv,Path.home(),logs,env)
    with p.open('xb') as f:plistlib.dump(record,f)
    with (Path(out)/'job.plist').open('xb') as f:plistlib.dump(record,f)
    subprocess.run(['launchctl','bootstrap',domain,str(p)],check=True)
    with (Path(out)/'dispatch.json').open('x') as f:json.dump(dict(label=label,target=target,automatic_restart=False,recurring=False),f)
    print(target)

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--label',required=True);a.add_argument('--out',type=Path,required=True);a.add_argument('command',nargs=argparse.REMAINDER);v=a.parse_args()
    env={k:os.environ[k] for k in ['HOME','PATH','PYTHONPATH','PYTORCH_ENABLE_MPS_FALLBACK','OMP_NUM_THREADS'] if k in os.environ}
    start(v.label,v.command,Path.cwd(),v.out,env)
