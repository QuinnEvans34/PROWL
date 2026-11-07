"""Train-only128 coverage plan from already-qualified lossless target cache.

No CT or test reads. New sampling plan, not reuse of a truncated24k schedule.
"""
import argparse,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from src.data.segmenter_physical_windows_v1 import coverage_bank


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def check_cover(target,record,cover,window=128):
    support=target>0
    for axis,factor in enumerate(record['factors']):
        points=np.flatnonzero(support.any(axis=tuple(i for i in range(3) if i!=axis)))
        low=int(points[0])*factor;high=(int(points[-1])+1)*factor
        intervals=sorted(set((o[axis],min(o[axis]+window,record['shape'][axis])) for o in cover))
        reached=low
        for a,b in intervals:
            if b<=reached:continue
            if a>reached:raise ValueError('Coverage gap')
            reached=b
        if reached<high:raise ValueError('Truncated annotated field')
    # coverage_bank is a Cartesian product of these axis intervals.
    if len(cover)!=np.prod([len(set(o[a] for o in cover)) for a in range(3)]):raise ValueError('Incomplete Cartesian bank')


def main():
    p=argparse.ArgumentParser();p.add_argument('--cache',required=True);p.add_argument('--train',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    out=Path(a.output);out.mkdir(exist_ok=False);began=time.monotonic();cache=Path(a.cache)
    manifest=json.loads((cache/'manifest.json').read_text());names=Path(a.train).read_text().splitlines()
    if len(names)!=1333 or set(names)!=set(manifest['members']) or not manifest['complete']:raise ValueError('Cohort/cache identity')
    members={}
    for n in names:
        member=manifest['members'][n];mp=cache/(n+'.json');ap=cache/(n+'.npz')
        if sha(mp)!=member['metadata_sha256'] or sha(ap)!=member['target_sha256']:raise ValueError('Cache changed: '+n)
        m=json.loads(mp.read_text())
        with np.load(ap,allow_pickle=False) as f:
            if f.files!=['target']:raise ValueError('Target payload')
            t=f['target']
        if t.dtype!=np.uint8 or t.shape!=tuple(m['record']['native_shape']) or not np.isin(t,[0,1,2]).all():raise ValueError('Target geometry/values')
        if int((t==2).sum())!=m['lesion_voxels']:raise ValueError('Lesion count changed')
        cover=coverage_bank(t>0,m['record'],window=128);check_cover(t,m['record'],cover)
        members[n]={'cover':cover,'positive':m['positive'],'record':m['record'],'source_sha256':m['source_sha256'],'cache':member,'lesion_voxels':m['lesion_voxels']}
        if len(members)%100==0:print(json.dumps({'cases':len(members),'seconds':time.monotonic()-began}),flush=True)
    total=sum(len(x['cover']) for x in members.values())
    if total>9000:raise ValueError('12k schedule cannot cover all annotated fields within9000focus updates')
    # One seeded case order per bank round avoids exhausting one patient at once.
    rng=np.random.Generator(np.random.PCG64(42));coverage=[]
    for cycle in range(max(len(x['cover']) for x in members.values())):
        for i in rng.permutation(len(names)):
            n=names[int(i)]
            if cycle<len(members[n]['cover']):coverage.append({'case_id':n,'kind':'coverage','origin':members[n]['cover'][cycle]})
    focus=list(coverage)
    while len(focus)<9000:
        for i in rng.permutation(len(names)):
            if len(focus)==9000:break
            focus.append({'case_id':names[int(i)],'kind':'component_jitter'})
    context=[]
    while len(context)<3000:
        for i in rng.permutation(len(names)):
            if len(context)==3000:break
            context.append({'case_id':names[int(i)],'kind':'context'})
    schedule=[];fi=ci=0
    for step in range(12000):
        if step%4==3:schedule.append(context[ci]);ci+=1
        else:schedule.append(focus[fi]);fi+=1
    result=dict(version='stunet128-coverage-first-1',members=members,schedule=schedule,
                cases=1333,coverage_windows=total,focused_updates=9000,context_updates=3000,
                complete_annotated_field_coverage=True,seconds=time.monotonic()-began,
                cache_manifest_sha256=sha(cache/'manifest.json'),train_sha256=sha(a.train),
                source_sha256=sha(__file__),scientific_updates=0,
                policy='Seeded coverage rounds first in focus slots, then component jitter; independent seeded context permutations. Nonuniform per-case visit counts explicitly traced.')
    with (out/'plan.json').open('x') as f:json.dump(result,f)
    print(json.dumps({k:v for k,v in result.items() if k not in ('members','schedule')}),flush=True)


if __name__=='__main__':main()
