"""Reuse pinned complete-region metadata; no source masks or CTs reread."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.training.experiment_config import sha256
from src.operations.verifier_candidate_archive_v1 import write_json
BASE=Path('E:/PROWL/readiness/verifier-training-20261031-a01')
original=Path('E:/PROWL/readiness/verifier-candidate-export-20261027-a01/request.json')
assert sha256(original)=='edd8824e401aad8e5d8aefbf228f876931f3e792caaa457a7b28b32ca38b6a31'
pins={str(Path(k).resolve()).lower():v for k,v in json.loads(original.read_text())['pins'].items()}
review=Path('E:/PROWL/readiness/verifier-fit-design-20261031-a01/review.json')
design=json.loads((BASE/'design-v3.json').read_text());assert sha256(review)==design['fit_review_sha256']
archive=Path('E:/PROWL/artifacts/verifier-candidates-20261030-a01/manifest.json')
assert sha256(archive)=='b5c989a158598e2aa3e3c6ecdaed5f0bf4b91803d0574b3250c5def473827aed'
records={r['case_id']:r for r in json.loads(archive.read_text())['cases']};rows=[]
for r in json.loads(review.read_text())['cases']:
 n=r['case_id'];p=Path('E:/PROWL/cache/varied-targets-20261022-a01')/(n+'.json')
 assert sha256(p)==pins[str(p.resolve()).lower()]
 m=json.loads(p.read_text());geometry=records[n]['geometry']
 assert all(m[k]==geometry[k] for k in ('geometry','parent_geometry','region_low','region_high'))
 assert m['lesion_voxels']==r['annotated_voxels'],n
 rows.append(dict(case_id=n,source_annotated_voxels=r['annotated_voxels'],qualified_region_lesion_voxels=m['lesion_voxels'],metadata_path=str(p),metadata_sha256=sha256(p)))
assert len(rows)==266
write_json(BASE/'fit-coverage-reuse.json',dict(passed=True,method='frozen region metadata lesion count equals independently reviewed full-source annotation count; identical prediction-region geometry',cases=rows,review_sha256=sha256(review),archive_sha256=sha256(archive),script_sha256=sha256(__file__),source_voxel_reads=0))
print('266 fitting cases: complete inherited annotated field corroborated without voxel re-audit')
