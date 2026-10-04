"""Predeclared training-only engineering comparison; never a promotion or validation selector."""
from copy import deepcopy
from src.data.source_inventory_records import require
from src.training import segmenter_native_scoring_v1 as scoring
TRAIN=['pants:study:PanTS_'+f'{n:08d}' for n in (3,26,2232,2973,5821,6238)]
VALIDATION=['pants:study:PanTS_00002514']
POLICY=dict(kind='v5_training_only_engineering_screen_v1',primary_step=48,
    before_baseline_sha256='f4bfcaf0dd63ff066ce8456d66b978e738e8cca8322a6c74fcce23c89b090db2',
    prior_after_audit_sha256='9073e9d1a4aaf002888a670f5c7d7068ec8bd897f12014cf1405841b9f1e09c2',
    pancreas_macro_dice_strictly_above=0.08413627515978402,pancreas_tp_each_case_strictly_above=0,
    lesion_macro_dice_at_least=0.03088619116270695,lesion_macro_recall_at_least=0.8,
    all_training_components_hit=True,validation_selects_nothing=True,volume_bar=None,
    required_reports=['per_case_class_and_union_counts','precision','false_positive_mm3','predicted_reference_volume_ratio','all_components','tiny_2973','boundary_6238','separate_2514'],
    promotion_allowed=False,specificity_claim_allowed=False)

def policy():return deepcopy(POLICY)

def assess(rows):
    require([(r['study_id'],r['protected_role']) for r in rows]==[(n,'train') for n in TRAIN]+[(n,'validation') for n in VALIDATION],'Comparison membership or roles changed')
    for row in rows:
        require(row['metrics']==scoring.from_confusion(row['confusion_matrix']),'Comparison integer metric formulas differ')
        require(sum(c['native_voxels'] for c in row['components'])==row['metrics']['lesion']['target_voxels'] and sum(c['true_positive'] for c in row['components'])==row['metrics']['lesion']['true_positive'],'Comparison component accounting differs')
    a=scoring.aggregates(rows);train=a['train'];checks=dict(pancreas_macro_dice=train['macro']['pancreas_parenchyma']['dice']>POLICY['pancreas_macro_dice_strictly_above'],pancreas_overlap_each=all(r['metrics']['pancreas_parenchyma']['true_positive']>0 for r in rows[:6]),lesion_macro_dice=train['macro']['lesion']['dice']>=POLICY['lesion_macro_dice_at_least'],lesion_macro_recall=train['macro']['lesion']['recall']>=POLICY['lesion_macro_recall_at_least'],all_components_hit=all(c['true_positive']>0 for r in rows[:6] for c in r['components']))
    volumes=[]
    for r in rows:
        m=r['metrics']['lesion'];spacing=r['source_affine'];import numpy as np
        mm3=abs(float(np.linalg.det(np.asarray(spacing)[:3,:3])))
        volumes.append(dict(study_id=r['study_id'],protected_role=r['protected_role'],lesion_precision=m['true_positive']/m['predicted_voxels'] if m['predicted_voxels'] else 0.,lesion_false_positive_mm3=(m['predicted_voxels']-m['true_positive'])*mm3,lesion_predicted_reference_ratio=m['predicted_voxels']/m['target_voxels'] if m['target_voxels'] else None))
    return dict(policy=policy(),checks=checks,passed=all(checks.values()),aggregates=a,volume_reports=volumes,validation_used_for_selection=False,promotion_allowed=False)
