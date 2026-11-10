from scripts.diagnostics.close_stunet_margin_20261110 import render


def test_report_separates_highest_dice_from_guard_qualified_selection():
    def metrics(dice):
        return dict(positive_macro_dice=dice, positive_macro_recall=.5,
            small_case_macro_recall=.2, detected_cases=34, detected_components=38,
            empty_alarm_cases=27, false_positive_mL=221.)
    result = dict(policies={'raw':metrics(.41), 'bias0_near5_min0':metrics(.43),
                            'unsafe-max':metrics(.60)},
        selected_exploratory_policy='bias0_near5_min0', best_dice_ignoring_guards='unsafe-max',
        guards={'bias0_near5_min0':dict(passes=True), 'unsafe-max':dict(passes=False)},
        checkpoint_sha256='a'*64, request_sha256='b'*64, seconds=8000.)
    text = render(result, dict(status='VERIFIED_COMPLETE'))
    assert 'Highest Dice ignoring safeguards: **unsafe-max** (0.600000); guard status: False' in text
    assert 'Guard-qualified exploratory selection: **bias0_near5_min0**, Dice **0.430000**' in text
    assert 'versus standing 5 mm: +0.000000' in text
    assert 'No policy deployed' in text
    assert 'zero training updates' in text
    assert 'no independent or leakage-free performance claim' in text
