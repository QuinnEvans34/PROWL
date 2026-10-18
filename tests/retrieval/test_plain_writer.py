import pytest
from src.retrieval.plain_writer import parse_prose
SOURCES=[dict(source='P1',text='The pancreas has a reported length range of 12 to 15 cm.')]


def test_plain_prose_binds_exact_original_quote():
    r=parse_prose('The reported length range is 12 to 15 cm. [P1]',SOURCES,'Pancreas size?')
    assert r['claims'][0]['citations'][0]['quote']==SOURCES[0]['text']


@pytest.mark.parametrize('text',['No markers.', 'Length 12 cm. [P2]','Length 12 cm. [P1, P1]', 'Length [9] is 12 cm. [P1]','Length 999 cm. [P1]','```json\n{}\n```'])
def test_ambiguous_or_unsupported_prose_is_rejected(text):
    with pytest.raises(ValueError):parse_prose(text,SOURCES,'Pancreas size?')


def test_only_exact_sentinel_is_insufficient():
    assert not parse_prose('INSUFFICIENT',SOURCES,'Pancreas?')['claims']
    with pytest.raises(ValueError):parse_prose('Insufficient evidence.',SOURCES,'Pancreas?')
