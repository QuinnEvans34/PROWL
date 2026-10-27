"""Explicitly reviewed process-monitor continuation; never admits arbitrary failures."""
import json
import math
from pathlib import Path
from src.data.segmenter_teacher_cache_v1 import sha


def remaining_after_monitor_stop(previous, review_path):
    previous=Path(previous)
    review=json.loads(Path(review_path).read_text())
    for field,name in [('request_sha256','request.json'),('resources_sha256','resources.json'),('worker_log_sha256','worker.log')]:
        if review[field]!=sha(previous/name):raise ValueError('Monitor-stop evidence changed')
    if review.get('stopped') is not True or review.get('reason')!='process sample timeout' or review.get('pause_receipt') is not False:
        raise ValueError('Explicit Monitor-stop review required')
    resources=json.loads((previous/'resources.json').read_text())
    if (resources.get('workers_reaped') is not True or resources.get('success') is not False
        or resources.get('exit_code') != -15
        or resources.get('error') != "TimeoutExpired(['/bin/ps', '-axo', 'pid=,ppid=,rss='], 5)"):
        raise ValueError('Not the reviewed reaped process-sampling failure')
    seconds=resources.get('seconds')
    if type(seconds) not in (int,float) or not math.isfinite(seconds) or seconds<0:raise ValueError('Invalid elapsed time')
    request=json.loads((previous/'request.json').read_text())
    remaining=request['limits']['seconds']-math.ceil(seconds)
    if remaining<=0:raise ValueError('Original budget exhausted')
    return remaining
