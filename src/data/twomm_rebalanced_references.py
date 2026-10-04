"""Separate233-label child-run scope and40-label zero-update import qualification."""
from src.data.twomm_training_references import StagedReferences,VolumeReboundReferences,qualified_items,scope
from src.data.source_inventory_records import require
from src.training.twomm_rebalanced_training import validate_controls


class ParentReferences(StagedReferences):
    def completed(self,*,through_step=None):
        expected=self._plan['evaluations']
        if through_step is not None:
            require(self._plan['schema_version']=='twomm-training-plan-5' and through_step in self._plan['checkpoint_steps'],'Wrong child reference boundary')
            expected=[s for s in expected if s['step']<=through_step]
        require(self.next_stage==len(expected),'Incomplete child reference cadence')
        for b in self.budgets:self._complete(b)
        return dict(files=sum(b.files for b in self.budgets),compressed_bytes=sum(b.compressed for b in self.budgets),expanded_bytes=sum(b.expanded for b in self.budgets),ct_files=0)


def open_references(repo,i,c,*,tick=lambda:None):
    b,p,_=validate_controls(i,c);require(i['purpose']=='qualified-twomm-training','Real child reference scope required')
    expected=scope(b,p);require(expected['files']==(40 if p['execution_mode']=='zero_update_parent_check' else 233) and expected['ct_files']==0,'Child stage scope differs')
    items,root,check=qualified_items(repo,b,tick=tick)
    return ParentReferences(items,root,check,p,reader=VolumeReboundReferences)
