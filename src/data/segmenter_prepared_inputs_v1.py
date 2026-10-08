"""Admit reviewed members of a completed content cache without repeating preprocessing."""
import csv
import json
from pathlib import Path

import numpy as np

from src.data.manifest_records import canonical,digest
from src.data.source_inventory_records import require
from src.data import segmenter_training_inputs_v1 as boundary
from src.data.segmenter_full_inputs_v1 import Inputs
from src.training.experiment_config import resolve,ids,sha256


class PreparedInputs:
    def __init__(self,cfg,recipe):
        cohort=cfg['_experiment']['cohort']
        review=json.loads(resolve(cohort['review']).read_text())
        require(review.get('decision')=='accepted' and review.get('evidence'), 'Reviewed cohort required')
        train=ids(resolve(cohort['train_ids']));dev=ids(resolve(cohort['development_ids']));names=set(train+dev)
        require(len(names)==len(train+dev), 'Overlapping input roles')
        prepared=review['prepared_cache'];root=Path(prepared['root'])
        require(root.is_absolute() and sha256(root/'control.json')==prepared['control_sha256'], 'Prepared cache control changed')
        source=json.loads((root/'control.json').read_text())
        require(source['domain']=='candidate_audit_only' and source['geometry']==recipe and
            set(train)<=set(source['train']) and set(dev)<=set(source['validation']), 'Cache recipe/roles differ')
        self.members=prepared['members'];states=review['target_states']
        require(set(self.members)==set(states)==names, 'Complete reviewed cache membership required')
        for name,state in states.items():
            require(state==source['target_states'][name], 'Target semantics changed after preparation')
            require(state in ('positive','verified_negative') or (state=='reference_empty' and
                review.get('empty_reference_policy')=='annotation_background_not_verified_healthy'),
                'Explicit empty-reference interpretation required')
        with resolve(cohort['manifest']).open(newline='') as stream:self.rows={r['case_id']:r for r in csv.DictReader(stream)}
        self.root=root;self.source=source;self.recipe=recipe
        self.control=dict(version='segmenter-prepared-inputs-1',domain='reviewed_full_cohort',train=train,
            validation=dev,target_states=states,source_control_sha256=prepared['control_sha256'],
            manifest_sha256=sha256(resolve(cohort['manifest'])),review_sha256=sha256(resolve(cohort['review'])),
            members=self.members,geometry=recipe)
        self.pin=digest(canonical(self.control))

    def get(self,name,*,role,operation):
        require(role in ('train','validation') and operation in ('optimizer','evaluator') and
            name in self.control['train' if role=='train' else 'validation'] and
            (operation!='optimizer' or role=='train'), 'Protected input role violation')
        for kind,observation in self.source['observations'][name].items():
            require(Inputs.observe(Path(self.rows[name][kind+'_path']))==observation, 'Source changed since preparation')
        path=self.root/(name+'.npz');metadata=path.with_suffix('.json');pins=self.members[name]
        require(sha256(path)==pins['cache_sha256'] and sha256(metadata)==pins['metadata_sha256'], 'Prepared cache changed')
        meta=json.loads(metadata.read_text())
        require(meta['case_id']==name and meta['control_sha256']==self.control['source_control_sha256'] and
            meta['cache_sha256']==pins['cache_sha256'] and meta['transform']['recipe']==self.recipe and
            meta['fidelity']['mechanical_survival_pass'], 'Incomplete cache geometry/content evidence')
        with np.load(path,allow_pickle=False) as data:x,y=data['image'],data['target']
        return boundary.Batch(boundary._TOKEN,study_id=name,role=role,operation=operation,image=x,target=y,
                              control_sha256=self.pin)
