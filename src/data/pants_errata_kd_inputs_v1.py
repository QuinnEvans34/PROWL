"""Corrected on-demand inputs with a pinned native-grid view for offline KD.

Both paired arms use this provider. No prefetch or fast-cache equivalence claim.
"""
from copy import deepcopy
import json
from pathlib import Path
from src.data.pants_errata_inputs_v1 import ErrataInputs
from src.data.pants_errata_v1 import EXPECTED
from src.data.segmenter_fast_varied_v1 import source_info
from src.data.manifest_records import canonical,digest
from src.training.experiment_config import sha256

THROUGHPUT=dict(version='errata-kd-on-demand-1',prefetch=False,ct='original_full_decode_per_visit',labels='original_with_explicit_errata_overlay')

class ErrataKDInputs(ErrataInputs):
    def __init__(self,*,native_metadata_root,native_metadata_pins,**kwargs):
        super().__init__(**kwargs)
        self.native_metadata_root=Path(native_metadata_root)
        self.native_metadata_pins=deepcopy(native_metadata_pins)
        if set(self.native_metadata_pins)!=set(self.control['train']):raise ValueError('Exact training native metadata membership required')
        self.control=deepcopy(self.control)
        self.control['kd_native_metadata']=dict(root=str(self.native_metadata_root),pins=self.native_metadata_pins)
        self.control['throughput']=deepcopy(THROUGHPUT)
        self.pin=digest(canonical(self.control))
    def plan_next(self,request):
        if request is not None:self.check_role(request[0],'train','optimizer')
        # Deliberately no asynchronous reads.
    def cache_member(self,name):
        meta,pin,_=source_info(self,name,'train','optimizer')
        if name in EXPECTED:
            _,small=self.corrected_target(name)
            if small['metadata_sha256']!=pin or small['original_source_sha256']!=meta['source_sha256']:raise ValueError('Errata origin mismatch')
        else:
            path=self.native_metadata_root/(name+'.json')
            if sha256(path)!=self.native_metadata_pins[name]:raise ValueError('Native metadata changed')
            small=json.loads(path.read_text())
            if small['metadata_sha256']!=pin or small['source_sha256']!=meta['source_sha256']:raise ValueError('Native source identity mismatch')
        return None,small
