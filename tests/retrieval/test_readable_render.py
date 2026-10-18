from src.retrieval.readable_render import render_payload


def test_writer_receives_no_quotes_citations_or_hidden_evidence():
    body=render_payload('Question?',[dict(text='Supported statement.',citations=[dict(source='P1',quote='PRIVATE_QUOTE')])])
    assert body==dict(question='Question?',statements=[dict(id=1,text='Supported statement.')])
