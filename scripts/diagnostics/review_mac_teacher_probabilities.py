"""Review one completed training-case diagnostic cache; no CT/model access."""
import json
from pathlib import Path
import hashlib
import numpy as np
import nibabel as nib
from scipy import ndimage
from src.data.segmenter_native_windows_v1 import orient
from src.data.segmenter_content_v1 import target_content

BASE=Path('/Volumes/PROWL-Data/PROWL/artifacts/distillation-mac-20261023')
CASE='PanTS_00002720'
output=BASE/'first-case-probability-review-01.json'
if output.exists():raise ValueError('Preserve existing review')
meta=json.loads((BASE/f'metadata-received-01/native-region/members/{CASE}.json').read_text())
row=next(r for r in json.loads((BASE/'pilot-local-bindings-01.json').read_text())['pilot'] if r['case_id']==CASE)
slices=tuple(slice(l,h) for l,h in zip(meta['region_low'],meta['region_high']))
mask_pins={}
for role in ('pancreas','lesion'):
    p=Path(row['files'][role]['path'])
    with p.open('rb') as f:pin=hashlib.file_digest(f,'sha256').hexdigest()
    if pin!=row['files'][role]['sha256']:raise ValueError('Source changed')
    obj=nib.load(p);proxy=obj.dataobj
    mask,_=target_content(proxy.get_unscaled(),dict(slope=float(proxy.slope),intercept=float(proxy.inter)))
    mask=orient(mask,meta['parent_geometry'])[slices]
    if role=='pancreas':target=mask.astype(np.uint8)
    else:target[mask!=0]=2
    mask_pins[role]=pin
probability=BASE/f'patient-pilot-01/{CASE}-probability.npz'
with np.load(probability,allow_pickle=False) as z:
    raw=z['probability'];assert raw.dtype==np.uint16 and raw.shape==target.shape
    q=raw.astype(np.float32)/65535
assert int((target==2).sum())==meta['lesion_voxels']
parts,count=ndimage.label(target==2,structure=np.ones((3,3,3)))
components=[]
for i in range(1,count+1):
    values=q[parts==i]
    components.append(dict(component=i,voxels=len(values),detected=bool((values>.5).any()),
        eligible_positive_voxels=int((values>.5+0.5/65535).sum()),suppressed_at_point1=int((values<=.1).sum())))
record=dict(case_id=CASE,quantized_diagnostic_only=True,
    probability_sha256=hashlib.sha256(probability.read_bytes()).hexdigest(),source_mask_sha256=mask_pins,
    strata={str(k):dict(voxels=int((target==k).sum()),high_at_point9=int((q[target==k]>=.9).sum()),
                       low_at_point1=int((q[target==k]<=.1).sum())) for k in (0,1,2)},
    components=components,decoded_CT_reads=0,model_runs=0,quality_accepted=False,
    quantization_note='Within half a uint16 step of decision boundaries, classifications are approximate; not a calibrated probability assessment.')
with output.open('x') as f:json.dump(record,f,indent=2)
print(json.dumps(record,indent=2))
