"""Bounded paired exposed-packet comparison; preparation never calls a model."""
import argparse
from copy import deepcopy
import json
from pathlib import Path
import statistics
import sys
import time
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.retrieval.check_single_summary_candidate import prepare
from src.retrieval import general_extract as baseline, single_pass_summary as candidate
from src.retrieval.natural_answer import api
from src.data.segmenter_teacher_cache_v1 import sha

LIMIT_SECONDS=1800
DURATIONS=('total_duration','load_duration','prompt_eval_duration','eval_duration')


def identities():
    return {name:dict(policy=module.POLICY,model=module.MODEL,model_sha256=module.MODEL_SHA,
             prompt_sha256=module.fingerprint() if name=='baseline' else module.FINGERPRINT,
             source_sha256=sha(module.__file__),shared_chat_sha256=sha(ROOT/'src/retrieval/natural_answer.py'),
             request_seconds=90 if name=='baseline' else 60)
            for name,module in [('baseline',baseline),('candidate',candidate)]}


def prepared(output,source=None):
    manifest=prepare(output,source)
    manifest.update(comparison=identities(),max_logical_requests=20,total_seconds=LIMIT_SECONDS,
                    timing_scope='saved-evidence generation; excludes retrieval and UI',order='alternate arm order by packet')
    (output/'inputs.json').write_text(json.dumps(manifest,indent=2))
    report(output,manifest,[])
    return manifest


def report(output,manifest,results):
    lines=['# Paired answer review','',manifest['timing_scope'],
           'Exposed regression questions. Quality decisions pending; no automatic promotion.','',
           '| Question | Arm | Temperature | Seconds | Calls | Outcome |',
           '| --- | --- | --- | ---: | ---: | --- |']
    for r in results:
        lines.append(f"| {r['name']} | {r['arm']} | {r['temperature']} | {r['seconds']:.2f} | {len(r['calls'])} | {'Failed' if 'failure' in r else r['answer']['coverage']} |")
    for packet in manifest['packets']:
        lines+=['',f"## {packet['question']}",'']
        for r in (x for x in results if x['name']==packet['name']):
            lines += [f"### {r['arm']} / {r['temperature']}",'']
            if 'failure' in r:lines+=[r['failure']]
            else:
                for claim in r['answer']['claims']:
                    lines += [claim['text'],'']
                    for c in claim['citations']:lines += [f"[{c['rank']}] {c['quote']}",'']
                lines += [r['answer'].get('limitation','')]
            lines += ['Support: Pending; completeness: Pending; qualifications: Pending; readability: Pending; citations: Pending; refusal: Pending.','']
        for e in packet['evidence']:lines += [f"Source [{e['rank']}] {e['record']['citation']['title']}",e['record']['text'],'']
    # No timing acceptance if an arm failed or lacks a matched warm observation.
    paired=[]
    for p in manifest['packets']:
        rows={r['arm']:r for r in results if r['name']==p['name'] and r['temperature']=='warm'}
        if set(rows)=={'baseline','candidate'} and all('failure' not in r for r in rows.values()):
            paired.append((rows['baseline']['seconds'],rows['candidate']['seconds']))
    summary=dict(complete_warm_pairs=len(paired),quality_review='Pending',promoted=False)
    if len(paired)==len(manifest['packets']):
        a,b=map(statistics.median,zip(*paired))
        summary.update(baseline_median_seconds=a,candidate_median_seconds=b,
                       timing_target_met=b<=a*.8 and all(y-x<=5 for x,y in paired))
    (output/'timing-summary.json').write_text(json.dumps(summary,indent=2))
    (output/'paired-review.md').write_text('\n'.join(lines))


def evaluate(output,manifest,transport=api,clock=time.monotonic,generators=None):
    if manifest['comparison']!=identities():raise ValueError('Frozen comparison changed')
    marker=output/'comparison-started.json'
    with marker.open('x') as stream:json.dump(dict(max_seconds=LIMIT_SECONDS,automatic_retry=False),stream)
    generators=generators or dict(baseline=baseline.generate,candidate=candidate.generate)
    deadline=clock()+LIMIT_SECONDS;results=[]
    def save():
        (output/'results.json').write_text(json.dumps(results,indent=2));report(output,manifest,results)
    for index,packet in enumerate(manifest['packets']):
        arms=('baseline','candidate') if index%2==0 else ('candidate','baseline')
        for arm in arms:
            model=manifest['comparison'][arm]['model'];pin=manifest['comparison'][arm]['model_sha256']
            # Verify cold state rather than inferring it from a short delay.
            try:
                if clock()>=deadline:raise TimeoutError('Total comparison budget exhausted')
                transport('generate',dict(model=model,keep_alive=0),deadline=min(deadline,clock()+30))
                loaded=transport('ps',deadline=min(deadline,clock()+30))
                if any(x.get('name')==model or x.get('model')==model or x.get('digest')==pin for x in loaded['models']):
                    raise ValueError('Cold model unload not verified')
            except Exception as error:
                (output/'setup-failure.json').write_text(json.dumps(dict(name=packet['name'],arm=arm,failure=repr(error))))
                save();return results
            cold_ok=False
            for temperature in ('cold','warm'):
                start=clock();calls=[]
                r=dict(name=packet['name'],arm=arm,temperature=temperature,cold_unload_verified=True,
                       promoted=False,input_sha256=packet['source_sha256'])
                try:
                    if start>=deadline:raise TimeoutError('Total comparison budget exhausted')
                    if temperature=='warm':
                        loaded=transport('ps',deadline=min(deadline,start+30))
                        if not cold_ok or not any(x.get('digest')==pin for x in loaded['models']):
                            raise ValueError('Warm state not verified; no warm generation attempted')
                    request_deadline=min(deadline,start+manifest['comparison'][arm]['request_seconds'])
                    def call(path,payload=None):
                        if clock()>=request_deadline:raise TimeoutError('Request budget exhausted')
                        trace=None
                        if path=='chat':
                            trace=dict(request=deepcopy(payload));calls.append(trace)
                        try:response=transport(path,payload,deadline=request_deadline)
                        except Exception as error:
                            if trace is not None:trace['failure']=repr(error)
                            raise
                        if trace is not None:
                            trace['response']=response
                            trace['seconds']={key:(response[key]/1e9 if isinstance(response.get(key),(int,float)) else None) for key in DURATIONS}
                            trace['prompt_tokens']=response.get('prompt_eval_count');trace['output_tokens']=response.get('eval_count')
                        return response
                    r['answer']=generators[arm](packet['question'],deepcopy(packet['evidence']),call)
                    if clock()>request_deadline:raise TimeoutError('Request budget exceeded')
                    cold_ok=True
                except Exception as error:r['failure']=repr(error)
                r.update(seconds=clock()-start,calls=calls);results.append(r);save()
                if clock()>=deadline:return results
    return results


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--prepare-only',action='store_true');a=p.parse_args()
    if a.prepare_only:prepared(a.output);return
    from src.operations.full_training_platform import training_guard
    with training_guard(ROOT/'outputs/prowl/.mps-profile.lock'):
        manifest=prepared(a.output)
        try:evaluate(a.output,manifest)
        finally:
            # Only this pinned comparison model; no unrelated model unloading.
            api('generate',dict(model=candidate.MODEL,keep_alive=0),deadline=time.monotonic()+30)
            loaded=api('ps',deadline=time.monotonic()+30)
            if any(x.get('digest')==candidate.MODEL_SHA or x.get('name')==candidate.MODEL for x in loaded['models']):
                raise ValueError('Comparison cleanup not verified; do not resume training')
            (a.output/'model-cleanup.json').write_text(json.dumps(dict(unloaded=True,model=candidate.MODEL,model_sha256=candidate.MODEL_SHA)))

if __name__=='__main__':main()
