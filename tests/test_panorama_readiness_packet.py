from scripts.diagnostics.build_panorama_readiness_packet import select_qc


def test_selection_covers_strata_anomalies_repeats_and_loss():
    rows=[];audit={};scanners={}
    for prefix in ('expert_pdac','optional_machine','not_generic'):
        for i in range(12):
            name=f'{prefix}_{i}'
            r=dict(study_id=name,subject_id=name,disposition=prefix)
            rows.append(r);audit[name]=dict(status='ct_content_pass_not_admitted');scanners[name]='scannerA'
    for i in range(3):
        name='anomaly'+str(i);rows.append(dict(study_id=name,subject_id=name,disposition='quarantined_manual_non_pdac'))
        audit[name]=dict(status='ct_content_pass_not_admitted')
    rows[11]['subject_id']=rows[10]['subject_id']='repeat'
    audit[rows[11]['study_id']]['status']='union_crop_technical_hold'
    selected=select_qc(rows,audit,scanners)
    names={s['row']['study_id'] for s in selected}
    assert all('anomaly'+str(i) in names for i in range(3))
    assert rows[11]['study_id'] in names
    assert any('repeat_family:repeat' in s['reasons'] for s in selected)
    for prefix in ('expert_pdac','optional_machine','not_generic'):
        assert sum(prefix in s['reasons'] for s in selected)==10
