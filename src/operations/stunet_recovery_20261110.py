"""User-approved disk-floor amendment and strict interrupted-validation reuse."""
import json,ctypes,shutil
from pathlib import Path
from scripts.training.supervise_stunet_longer_20261110 import size
CHECKPOINT_SHA='25aea4b9d4fc0eeb89b27fe46f2443d4c8b9e157ef0e1380f4a37e13568830c3'
def check_storage():
    ids=[]
    for drive,expected in [('C:/','9ed7859f-4768-4f11-9788-792a793f0ee4'),('E:/','424d39a3-ac76-4f41-aa1c-8b9f5ce0b829')]:
        buf=ctypes.create_unicode_buffer(256)
        if not ctypes.windll.kernel32.GetVolumeNameForVolumeMountPointW(drive.replace('/','\\'),buf,256):raise OSError('Volume missing')
        if expected not in buf.value.lower():raise ValueError('Volume identity changed')
        ids.append(buf.value)
        if shutil.disk_usage(drive).free<50*1024**3:raise RuntimeError('50GiB free-space floor')
    if ids[0]==ids[1]:raise ValueError('Independent volumes required')
    if size('C:/Users/quinn/PROWL-Backups')>88*1024**3:raise RuntimeError('88GiB backup cap')
    if size('E:/PROWL/cache')>32*1024**3:raise RuntimeError('32GiB cache cap')
def reusable_cases(rows,development,profile):
    updates=[r for r in rows if r['event']=='update']
    if [r['step'] for r in updates]!=list(range(24001,26001)):raise ValueError('Unexpected failed update history')
    checks=[r for r in rows if r['event']=='checkpoint']
    if len(checks)!=1 or checks[0]['step']!=26000 or checks[0]['sha256']!=CHECKPOINT_SHA:raise ValueError('Checkpoint binding')
    if any(r['event'] in ('native_completed','completed','training_completed') for r in rows):raise ValueError('Already completed')
    starts=[r for r in rows if r['event']=='native_started']
    if len(starts)!=1 or starts[0]['step']!=26000:raise ValueError('Validation binding')
    saved=[r for r in rows if r['event']=='native_case']
    names=sorted(development)
    if len(saved)!=14 or [r['case_id'] for r in saved]!=names[:14]:raise ValueError('Expected exact saved prefix14')
    for r in saved:
        if r['step']!=26000 or r['variant']!='raw' or r['gaps']!=0 or r['tiles']!=profile[r['case_id']]['tiles']:raise ValueError('Invalid saved native row')
    return [{k:r[k] for k in ('case_id','tiles','gaps','scope','metrics')} for r in saved]
