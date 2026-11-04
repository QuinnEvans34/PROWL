"""Restricted optimizer view over an unchanged, previously qualified cache.

Preserves the complete parent admission checks, then binds a new identity and
denies all reserved/development loads. Not a final candidate-evaluation provider.
"""
from copy import deepcopy
from src.data.segmenter_fast_varied_v1 import FastVariedInputs
from src.data.manifest_records import canonical,digest


class GeneratorInputs(FastVariedInputs):
    def __init__(self, *, partitions, partition_sha256, focused_counts,
                 expected_parent_pin, **kwargs):
        # Verify the original complete manifest using the original complete roles.
        # Do not weaken that constructor to admit a mismatched subset manifest.
        kwargs['prefetch']=False
        super().__init__(**kwargs)
        try:
            if self.pin!=expected_parent_pin:raise ValueError('Parent cache control changed')
            roles=partitions['roles'];names=roles['generator_train']
            assigned=sum(roles.values(),[])
            if len(assigned)!=len(set(assigned)) or set(assigned)!=set(self.control['train']):
                raise ValueError('Partition must account for entire admitted training role')
            if set(partitions['development'])!=set(self.control['validation']):
                raise ValueError('Protected development membership changed')
            if not names or set(focused_counts)!=set(names) or any(type(n)!=int or n<1 for n in focused_counts.values()):
                raise ValueError('Restricted schedule membership')
            if len(partition_sha256)!=64:raise ValueError('Partition identity required')
            parent_control=deepcopy(self.control)
            self.allowed=frozenset(names)
            self.control=deepcopy(parent_control)
            self.control.update(version='restricted-generator-inputs-1',train=list(names),
                planned_focused_counts=deepcopy(focused_counts),
                restricted_generator=dict(parent_control_sha256=expected_parent_pin,
                    partitions_sha256=partition_sha256,scope='design-informed exploratory',
                    selection='fixed_terminal_no_heldout_selection',evaluation_enabled=False))
            self.pin=digest(canonical(self.control))
            self.planned_counts=deepcopy(focused_counts)
            self.rows={n:self.rows[n] for n in names}
            self.observations={n:self.observations[n] for n in names}
            self.cache_manifest=deepcopy(self.cache_manifest)
            self.cache_manifest['members']={n:self.cache_manifest['members'][n] for n in names}
            self.component_cache={}
        except BaseException:
            self.close();raise

    def check_role(self,name,role,operation):
        if role!='train' or operation not in ('optimizer','audit') or name not in self.allowed:
            raise ValueError('Generator cannot access reserved or development patients')

    def cache_member(self,name):
        self.check_role(name,'train','optimizer')
        return super().cache_member(name)

    def plan_next(self,request):
        if request is not None:
            name,step,visit,seed=request
            self.check_role(name,'train','optimizer')
            if type(step)!=int or type(visit)!=int or min(step,visit)<0:
                raise ValueError('Invalid lookahead counters')
        super().plan_next(request)

    def enable_prefetch(self):
        from concurrent.futures import ThreadPoolExecutor
        if self._closed or self._executor is not None:raise ValueError('Invalid worker lifecycle')
        self._executor=ThreadPoolExecutor(max_workers=1,thread_name_prefix='prowl-generator-input')
