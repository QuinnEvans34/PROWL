"""Read the exact 583-byte publisher plan using only OrderedDict/NumPy scalar globals."""
import collections
import hashlib
import io
import json
import pickle
from pathlib import Path
import numpy as np


class RestrictedPlan(pickle.Unpickler):
    def find_class(self,module,name):
        allowed={('collections','OrderedDict'):collections.OrderedDict,
                 ('numpy.core.multiarray','scalar'):np._core.multiarray.scalar,
                 ('numpy','dtype'):np.dtype}
        if (module,name) not in allowed:raise pickle.UnpicklingError('Unapproved plan global')
        return allowed[module,name]

    def persistent_load(self,*args):raise pickle.UnpicklingError('External references refused')


if __name__=='__main__':
    root=Path('/Volumes/PROWL-Data/PROWL/teachers/stunet-audit-20261106-source')
    raw=(root/'plan_files/plans.pkl').read_bytes()
    pin=json.loads(Path('docs/stunet_audit/source_manifest.json').read_text())['files']['plan_files/plans.pkl']['sha256']
    assert len(raw)==583 and hashlib.sha256(raw).hexdigest()==pin
    plan=RestrictedPlan(io.BytesIO(raw)).load()
    with Path('docs/stunet_audit/upstream_plan_summary.json').open('x') as f:
        json.dump(dict(source_sha256=pin,bytes=len(raw),allowed_globals=['collections.OrderedDict','numpy.core.multiarray.scalar','numpy.dtype'],plan=plan),f,indent=2,default=int);f.write('\n')
    print(json.dumps(plan,default=int))
