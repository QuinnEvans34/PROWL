"""Changed-sampler pilot only; no repeat cohort/source/duplicate audit."""
import json
import time
import numpy as np
from scripts.train_varied_region import SETUP,provider,read,write,check,resource_check
from src.data.segmenter_pancreas_region_v1 import bank,window_origin
from src.data.segmenter_varied_region_v1 import components,choose,coverage_slots
from src.data.segmenter_physical_windows_v1 import sample_window


def run():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    check(read(SETUP/'setup.json'));resource_check();p=provider()
    root=SETUP/'pilot';root.mkdir(exist_ok=False)
    selected=read(SETUP/'pilot-selection.json')['cases'];results=[];started=time.monotonic()
    for number,name in enumerate(selected,1):
        resource_check();began=time.monotonic()
        # Exactly one source CT load, then the SAME production from_case function.
        case=p.load(name,role='train',operation='optimizer');record,cover=bank(case)
        parts,positive=components(case['target'],record);total=p.planned_counts[name]
        slots=coverage_slots(total,len(cover));actual_covers=[];jitter_origins=[];traces=[];views=[]
        for visit in range(total):
            step=4*visit
            # Sampling seed is tied to the supplied update/visit; no mutable RNG.
            image,target,transform,trace=p.from_case(case,step=step,focused_visit=visit,seed=42)
            expected_origin,expected=choose(record,cover,parts,step=step,focused_visit=visit,total=total,seed=42,name=name)
            if trace['origin']!=list(expected_origin) or trace['kind']!=expected['kind']:raise ValueError('Production sampler mismatch')
            repeat=choose(record,cover,parts,step=step,focused_visit=visit,total=total,seed=42,name=name)
            if repeat!=(expected_origin,expected):raise ValueError('Nondeterministic view')
            expected_target,_=sample_window(case['target'],record,expected_origin,order=0)
            if not np.array_equal(expected_target,target) or not np.isfinite(image).all():raise ValueError('Actual target/image failure')
            if trace['kind']=='reserved_cover':actual_covers.append(tuple(trace['origin']))
            else:
                if not (target==2 if positive else target>0).any():raise ValueError('Missing focused annotation')
                jitter_origins.append(tuple(trace['origin']))
                if len(views)<2:
                    # Retain only the two illustrated windows, not a dense case cache.
                    views.append((image[0].copy(),target.copy(),trace))
                if trace['whole_component_fits']:
                    part=parts[trace['component_index']]
                    if not all(o<=l and h<=o+144 for o,l,h in zip(trace['origin'],part['low'],part['high'])):
                        raise ValueError('Whole component clipping')
            traces.append(trace)
        if actual_covers!=list(map(tuple,cover)):raise ValueError('Lost reserved coverage window')
        # Existing full1403 bank proof is reused; these bank windows are byte-identical.
        possible=any(n>144 for n in record['shape'])
        if possible and len(jitter_origins)>1 and len(set(jitter_origins))<2:
            raise ValueError('No view variation; investigate geometry, do not invent a pass')
        context_origin,kind=window_origin(record,cover,step=3,focused_visit=1,seed=42,name=name)
        x,y,transform,trace=p.from_case(case,step=3,focused_visit=1,seed=42)
        if trace['origin']!=list(context_origin) or trace['kind']!=kind:raise ValueError('Context origin changed')
        expected_x,_=sample_window(case['image'],record,context_origin,order=1)
        if not np.array_equal(x[0],expected_x):raise ValueError('Context image changed')
        if len(views)!=2:raise ValueError('Insufficient jitter pilot views')
        fig,axes=plt.subplots(2,3,figsize=(11,7))
        for row,(image,label,view) in enumerate(views):
            anchor=[a-o for a,o in zip(view['anchor'],view['origin'])]
            for d in range(3):
                lab=np.take(label,anchor[d],axis=d).T
                axes[row,d].imshow(np.take(image,anchor[d],axis=d).T,cmap='gray',vmin=0,vmax=1,origin='lower')
                for support,color in [(lab>0,'cyan'),(lab==2,'red')]:
                    if support.any() and not support.all():axes[row,d].contour(support,levels=[.5],colors=[color],linewidths=.7)
                axes[row,d].set_title(f'Jitter view {row+1}, axis {d}');axes[row,d].axis('off')
        fig.suptitle(f'Private training pilot {number}/12: lesion red, foreground cyan; annotated anchor planes')
        fig.tight_layout();figure=f'case-{number:02d}.png';fig.savefig(root/figure,dpi=100);plt.close(fig)
        result=dict(case_id=name,positive=positive,figure=figure,passed=True,
            reserved_windows=len(cover),scheduled_focus_visits=total,jitter_views=len(jitter_origins),
            distinct_jitter_origins=len(set(jitter_origins)),components=len(parts),context_identical=True,
            complete_original_bank_preserved=True,all_jitter_anchors_retained=True,traces=traces,
            seconds=time.monotonic()-began)
        results.append(result)
        with (root/'progress.jsonl').open('ab') as stream:
            from src.data.manifest_records import canonical
            stream.write(canonical(dict(completed=number,total=12,seconds=time.monotonic()-started)));stream.flush()
        print(json.dumps(dict(completed=number,seconds=result['seconds'])),flush=True)
    write(root/'result.json',dict(passed=True,cases=results,ct_reads=12,test_reads=0,
        source_audit_replayed=False,cohort_coverage_audit_replayed=False,seconds=time.monotonic()-started))
