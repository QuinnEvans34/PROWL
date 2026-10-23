from scripts.diagnostics.review_region_results_timing import compare,timing

def cases(score,alarms=0):
    rows=[]
    for i in range(70):
        positive=i<36;prediction=1 if positive or i-36<alarms else 0
        rows.append(dict(case_id=str(i),metrics=dict(reference_positive=positive,reference_components=int(positive),
            size_band='small' if positive else 'empty',target_volume_mm3=float(positive),
            case_detected=positive,false_alarm_any=not positive and prediction>0,detected_components=int(positive),
            predicted_volume_mm3=float(prediction),lesion=dict(dice=score if positive else 0.,target_voxels=int(positive),
                predicted_voxels=prediction,true_positive=int(positive)),pancreas=dict(dice=.8,target_voxels=10))))
    return rows

def test_zero_difference_fails_to_reject_and_cannot_meet_practical_gain():
    result=compare(cases(.4),cases(.4))
    assert result['delta']==0 and result['ci95']==[0,0]
    assert result['null']=='fail_to_reject' and result['practical']=='reject'

def test_positive_dice_does_not_override_alarm_guard():
    result=compare(cases(.4),cases(.5,alarms=5))
    assert result['null']=='reject' and result['practical']=='reject'
    assert not result['guards']['empty_alarm']

def test_native_timing_and_update_boundary_are_separate():
    rows=[dict(event='update',step=499,member_id='a',elapsed_seconds=1),
          dict(event='update',step=500,member_id='b',elapsed_seconds=3),
          dict(event='native_started',step=500,elapsed_seconds=4),
          dict(event='native_completed',step=500,elapsed_seconds=14),
          dict(event='update',step=501,member_id='a',elapsed_seconds=16),
          dict(event='completed',elapsed_seconds=17)]
    result=timing(rows)
    assert result['native_during_training_hours']==10/3600
    assert result['outside_recorded_validation_hours']==7/3600
    assert result['regular_update_interval_seconds']['mean']==2
