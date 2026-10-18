from copy import deepcopy
import pytest
from src.retrieval.conservative_render import preservation_issues
from src.retrieval import conservative_answer as module
from tests.retrieval.test_readable_answer import EVIDENCE


def test_rewrite_cannot_drop_study_population_count_or_method_value():
    original='In a study of 12 participants using MRI at 3.0T, the mean was 80 cm³.'
    assert preservation_issues(original,'Using MRI, the mean was 80 cm³.')
    assert not preservation_issues(original,'A study using MRI at 3.0T measured an average of 80 cm³ in 12 participants.')


def test_rewrite_cannot_broaden_named_disease_comparison():
    assert preservation_issues('Chronic pancreatitis versus pancreatic ductal adenocarcinoma.','Inflammation versus a tumor.')


def test_only_absence_draft_is_withheld_without_displaying_absence_assertion(monkeypatch):
    monkeypatch.setattr(module,'chat',lambda *a,**k:dict(claims=[dict(text='The sources do not specify this policy.',citations=[dict(source='P1')])]))
    result=module.generate_conservative('What is the policy?',deepcopy(EVIDENCE),lambda *a:dict(models=[dict(name=module.MODEL,digest=module.MODEL_SHA)]))
    assert result['status']=='insufficient' and result['claims']==[]
    assert result['validation']=='no_supported_claims'


def test_absence_detection_does_not_match_positive_information():
    assert not module.source_absence('The study reports a policy that excludes ducts.')
