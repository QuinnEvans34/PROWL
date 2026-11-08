"""Phase-relative phone cards; keep global ancestry explicit and hours untouched."""
import copy
import experiments_legacy_20261108 as parent


def adjust_continuation(result,start):
    if not start:return result
    r=copy.deepcopy(result)
    r['ancestry_start']=start;r['global_steps']=max(start,r['steps'])
    r['global_target_steps']=r['target_steps']
    r['steps']=max(0,r['steps']-start);r['target_steps']-=start
    if r['target_steps']<=0:raise ValueError('Invalid continuation interval')
    if r['next_validation'] is not None:r['next_validation']=max(2000,r['next_validation']-start)
    seen=set()
    def adjust(row):
        if id(row) not in seen and 'step' in row:
            seen.add(id(row));row['global_step']=row['step'];row['step']-=start
    for key in ('latest','best','ema_latest','ema_best'):
        if r.get(key):adjust(r[key])
    for key in ('history','native'):
        for row in r[key]:
            adjust(row)
    return r


_experiment=parent.experiment
def experiment(entry,allowed,comparison,now):
    return adjust_continuation(_experiment(entry,allowed,comparison,now),entry.get('start_update',0))


parent.experiment=experiment
dashboard=parent.dashboard
