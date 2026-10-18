import math
import pytest

from src.retrieval.development_ranking import fuse, rank_candidates


def hits(*ids):
    return [dict(passage_id=i, score=.5) for i in ids]


def test_shared_hit_beats_single_first_and_ties_use_id():
    result = fuse(hits('z', 'shared'), hits('a', 'shared'))
    assert [r['passage_id'] for r in result] == ['shared', 'a', 'z']
    assert result[0]['score'] == 2 / 62


def test_empty_and_missing_channel_do_not_invent_hits():
    assert fuse([], []) == []
    assert fuse(hits('only'), []) == [dict(passage_id='only', score=1/61)]


def test_union_capped_deterministically():
    result = fuse(hits(*(f'a{i:02}' for i in range(50))), hits(*(f'b{i:02}' for i in range(50))))
    assert len(result) == 50
    assert [i['passage_id'] for i in result[:4]] == ['a00', 'b00', 'a01', 'b01']


@pytest.mark.parametrize('bad', [hits('a', 'a'), hits(*map(str, range(51))),
    [dict(passage_id='a', score=math.nan)], [dict(passage_id='', score=.2)]])
def test_invalid_rankings_fail(bad):
    with pytest.raises(ValueError):
        fuse(bad, [])


class DB:
    def __init__(self, encoder_id='encoder'):
        self.calls = []
        self.encoder_id = encoder_id

    def execute(self, sql, params):
        self.calls.append((sql, params))
        return self

    def fetchone(self):
        return (self.encoder_id,)

    def fetchall(self):
        return [('p', .8)]


class Encoder:
    id = 'encoder'

    def __init__(self):
        self.inputs = []

    def encode(self, questions):
        self.inputs.extend(questions)
        return [[1.0] + [0.0] * 383]


def test_untrusted_question_is_parameter_not_sql_or_rewrite():
    db, encoder = DB(), Encoder()
    question = "pancreas'); DROP TABLE literature.passages; -- | & !"
    result = rank_candidates(db, 'collection', encoder, question)
    assert encoder.inputs == [question]
    assert all(question not in sql for sql, _ in db.calls)
    assert db.calls[2][1] == (question, 'collection', 50)
    assert result['hybrid'] == [dict(passage_id='p', score=2/61)]


def test_encoder_mismatch_blocks_embedding_and_search():
    db, encoder = DB('other'), Encoder()
    with pytest.raises(ValueError):
        rank_candidates(db, 'collection', encoder, 'pancreas')
    assert len(db.calls) == 1 and not encoder.inputs


@pytest.mark.parametrize('question', ['', ' ', None, 'a'*2001])
def test_invalid_text_fails_before_database(question):
    db = DB()
    with pytest.raises(ValueError):
        rank_candidates(db, 'collection', Encoder(), question)
    assert not db.calls
