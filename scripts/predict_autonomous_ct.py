#!/usr/bin/env python3
"""One CT-only diagnostic from pinned inference weights; no reference/scoring options."""
import argparse
import json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.data.source_inventory_records import require
from src.inference.cascade_models_v1 import load_weights
from src.inference.autonomous_cascade_v1 import run_case


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--request',required=True)
    args=parser.parse_args();r=json.loads(Path(args.request).read_text())
    require(set(r)=={'ct_path','ct_sha256','case_id','output_dir','models','localizer_recipe',
                     'patch_size','tensor_shape','device'},'Exact CT-only request fields required')
    require(set(r['models'])=={'localizer','segmenter'},'Two model roles required')
    models={}
    for role,item in r['models'].items():
        require(set(item)=={'path','sha256'},'Only pinned weights may reach loader')
        models[role],_=load_weights(item['path'],expected_sha256=item['sha256'],role=role)
    # Fail closed on all other data-file reads during inference. Installed library/code reads
    # remain allowed. This is an audit tripwire, not an OS sandbox against malicious model code.
    ct=Path(r['ct_path']).resolve();out=Path(r['output_dir']).resolve();reads=[]
    def audit(event,values):
        if event!='open' or not isinstance(values[0],(str,bytes)):return
        p=Path(values[0]).resolve()
        if p==ct:reads.append(str(p));return
        if p.is_relative_to(out):return
        if p.is_relative_to(Path(sys.prefix).resolve()) or p.is_relative_to(ROOT/'src'):
            return
        if str(p) in ('/dev/null','/dev/urandom'):return
        raise PermissionError(f'CT-only inference blocked unexpected file access: {p}')
    sys.addaudithook(audit)
    result=run_case(ct,out,case_id=r['case_id'],expected_ct_sha256=r['ct_sha256'],
        **models,localizer_sha256=r['models']['localizer']['sha256'],
        segmenter_sha256=r['models']['segmenter']['sha256'],localizer_recipe=r['localizer_recipe'],
        patch_size=tuple(r['patch_size']),tensor_shape=tuple(r['tensor_shape']),device=r['device'])
    (out/'input-access.json').write_text(json.dumps(dict(allowed_data_input=str(ct),observed_ct_opens=len(reads),
        reference_paths_allowed=False,scope='Python audit hook after verified weight loading'),indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],case_id=r['case_id'],output_dir=str(out))))


if __name__=='__main__':main()
