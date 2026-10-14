"""Reviewed training-only PANORAMA extension of the unchanged prepared PanTS provider."""
from copy import deepcopy
import json
from pathlib import Path
import numpy as np

from src.data import segmenter_full_batch_v1 as boundary
from src.data.manifest_records import canonical, digest
from src.data.source_inventory_records import require, content_hash
from src.training.experiment_config import ids, resolve, sha256, load_experiment

DOMAIN = 'exploratory_pants_panorama_20261012'
EXCLUDED = {'PanTS_00000922', 'PanTS_00005105', 'PanTS_00005370', 'PanTS_00007299', 'PanTS_00007523'}


def extra_training(review):
    """Narrow explicit extension; never redefine the original protected split files."""
    if review.get('domain') != DOMAIN:
        return set()
    require(review.get('decision') == 'accepted' and review.get('policy') ==
            'declared_imports_excluded_five_dev_holds_exploratory', 'Mixed policy not accepted')
    require(set(review.get('excluded_development', [])) == EXCLUDED, 'Mixed development holds differ')
    members = review.get('panorama_cache', {}).get('members', {})
    require(bool(members) and all(n.startswith('panorama:study:') for n in members), 'Training-only namespaced additions required')
    return set(members)


class MixedInputs:
    def __init__(self, cfg, recipe):
        from src.data.segmenter_prepared_inputs_v1 import PreparedInputs
        cohort = cfg['_experiment']['cohort']
        review_path = resolve(cohort['review']); review = json.loads(review_path.read_text())
        extra = extra_training(review)
        require(bool(extra), 'Mixed additions absent')
        parent = review['pants_parent']
        for path, pin in parent['file_sha256'].items():
            require(sha256(path) == pin, 'Parent prepared metadata changed')
        parent_cfg = load_experiment(parent['experiment'])
        require(parent_cfg['full_segmenter']['geometry'] == recipe, 'PanTS geometry changed')
        self.pants = PreparedInputs(parent_cfg, recipe)
        require(self.pants.pin == parent['control_sha256'], 'Parent input identity changed')
        train, dev = ids(resolve(cohort['train_ids'])), ids(resolve(cohort['development_ids']))
        require(train == self.pants.control['train'] + sorted(extra), 'Mixed training membership/order differs')
        require(dev == [n for n in self.pants.control['validation'] if n not in EXCLUDED], 'Reduced development differs')
        require(not (EXCLUDED & set(train+dev)) and len(set(train+dev)) == len(train+dev), 'Mixed role collision')
        states = {n:self.pants.control['target_states'][n] for n in train+dev if n not in extra}
        states.update({n:'positive' for n in extra})
        require(review['target_states'] == states, 'Mixed target semantics changed')
        self.members = review['panorama_cache']['members']; self.metadata = {}
        for name, member in self.members.items():
            require(sha256(member['metadata']) == member['metadata_sha256'], 'PANORAMA metadata changed')
            meta = json.loads(Path(member['metadata']).read_text()); row = meta['source']
            require(meta['study_id'] == row['study_id'] == name and meta['subject_id'] == row['subject_id'] == member['subject_id'],
                'PANORAMA source identity differs')
            require(row['reference_standard'] not in ('MSD_dataset','NIH_dataset') and
                row['lesion_method']=='human_manual' and row['pdac']=='positive' and
                row['protected_role']=='unassigned' and not row['training_ready'] and
                row['disposition']=='expert_pdac_candidate_pending_qc_and_duplicates', 'Ineligible PANORAMA source')
            require(meta['mechanical_survival_pass'] and meta['tensor_lesion_voxels']>0 and meta['tensor_pancreas_voxels']>0,
                'PANORAMA component preservation not passed')
            expected = deepcopy(recipe); expected['roi_selection']='pancreas_lesion_union'
            require(meta['geometry']['transform']['recipe'] == expected and
                content_hash(meta['geometry']) == meta['geometry_sha256'] and
                meta['geometry']['transform']['roi_origin']=='provided_panorama_pancreas_lesion_union' and
                meta['mapping']=='panorama_union_1_to_lesion_4_to_pancreas', 'PANORAMA geometry/mapping changed')
            require(meta['cache'] == member['cache'] and meta['cache_sha256']==member['cache_sha256'], 'Cache binding differs')
            self.metadata[name]=meta
        self.control = dict(version='segmenter-mixed-inputs-1', domain=DOMAIN, train=train, validation=dev,
            target_states=states, geometry=recipe, pants_control=self.pants.control,
            excluded_development=sorted(EXCLUDED), panorama_members=self.members,
            sources={n:dict(source='PANORAMA',subject_id=m['subject_id']) for n,m in self.members.items()},
            manifest_sha256=sha256(resolve(cohort['manifest'])), review_sha256=sha256(review_path),
            policy=review['policy'])
        self.pin = digest(canonical(self.control))
        # Native evaluation remains PanTS-only, with the exact existing transform/reference path.
        self.root, self.rows, self.source = self.pants.root, self.pants.rows, self.pants.source

    def get(self, name, *, role, operation):
        require(role in ('train','validation') and operation in ('optimizer','evaluator') and
            name in self.control['train' if role=='train' else 'validation'] and
            (operation!='optimizer' or role=='train'), 'Protected mixed input role violation')
        if name in self.members:
            require(role=='train' and operation=='optimizer', 'PANORAMA is training-only')
            from scripts.diagnostics.audit_panorama_setup import observation
            member=self.members[name];meta=self.metadata[name]
            require(sha256(member['metadata'])==member['metadata_sha256'], 'PANORAMA metadata changed after binding')
            for kind, expected in meta['observations'].items():
                require(list(observation(meta['source'][kind]['path']))==expected, 'Consumed PANORAMA source changed')
            require(sha256(member['cache'])==member['cache_sha256'], 'PANORAMA cache changed')
            with np.load(member['cache'],allow_pickle=False) as data:
                x,y=data['image'],data['target']
        else:
            batch=self.pants.get(name,role=role,operation=operation)
            x,y=batch.checked(self.pants.pin,operation,name)
        return boundary.Batch(boundary._TOKEN,study_id=name,role=role,operation=operation,
            image=x,target=y,control_sha256=self.pin)
