import pytest
from src.retrieval.qualified_answer import study_guards


def test_one_feedback_reports_both_errors_and_general_context_requirement():
    claim=dict(text='The average pancreas volume is 80±4 cm³.',citations=[dict(quote='One study reported 80±4 cm³ as mean±SEM.')])
    with pytest.raises(ValueError) as error:study_guards(claim)
    assert 'specific study' in str(error.value)
    assert 'statistical meaning' in str(error.value)
    assert 'sample size, measurement method' in str(error.value)


def test_sem_cannot_be_relabelled_as_standard_deviation():
    with pytest.raises(ValueError):
        study_guards(dict(text='One study reported 80±4 cm³ (mean ± standard deviation).',citations=[dict(quote='Mean±SEM was 80±4 cm³.')]))
