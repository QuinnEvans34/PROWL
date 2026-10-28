"""Read-only training-cohort header audit; no inference or source modifications."""
import csv,json,sys,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
import SimpleITK as sitk
import numpy as np
from src.data.teacher_header_geometry_v1 import checked_header_grid
from src.data.segmenter_teacher_geometry_v2 import metadata_grid,plan
from scripts.diagnostics.qualify_distillation_mac import BASE

def main():
    output=Path(sys.argv[1]);output.mkdir(exist_ok=False)
    req=json.loads((BASE/'rsuper-full-targets-08/request.json').read_text())
    rows={r['case_id']:r for r in csv.DictReader((BASE/'rsuper-training-sources-01/manifest.csv').open())}
    prior=BASE/'teacher-header-audit-20261028-01/cases.jsonl'
    report=[json.loads(line) for line in prior.read_text().splitlines()]
    assert [r['case_id'] for r in report]==req['train'][:len(report)]
    (output/'cases.jsonl').write_text(prior.read_text())
    reused=len(report);started=time.monotonic()
    for name in req['train'][reused:]:
        meta=json.loads((BASE/f'metadata-received-01/native-region/members/{name}.json').read_text())
        try:
            reader=sitk.ImageFileReader();reader.SetFileName(rows[name]['ct_path']);reader.ReadImageInformation()
            g=checked_header_grid(reader,meta);old=metadata_grid(meta['parent_geometry'])
            plan(g['shape'],max_voxels=req['limits']['max_voxels'],max_tiles=req['limits']['max_case_tiles'])
            result=dict(case_id=name,passed=True,expected=g,old_shape=old['shape'],changed_shape=g['shape']!=old['shape'],affine_difference=float(np.max(np.abs(np.array(g['affine'])-old['affine']))))
        except Exception as e:result=dict(case_id=name,passed=False,error=repr(e))
        report.append(result)
        with (output/'cases.jsonl').open('a') as f:f.write(json.dumps(result)+'\n')
    pins={str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in [prior,Path(__file__),ROOT/'src/data/teacher_header_geometry_v1.py',ROOT/'tests/test_teacher_header_geometry_v1.py',BASE/'rsuper-full-targets-08/request.json']}
    summary=dict(success=all(r['passed'] for r in report),total=len(report),failures=[r for r in report if not r['passed']],changed=[r['case_id'] for r in report if r.get('changed_shape')],seconds=time.monotonic()-started,pins=pins)
    (output/'result.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary),flush=True)
if __name__=='__main__':main()
