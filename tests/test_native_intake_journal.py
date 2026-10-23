from src.data.manifest_records import canonical
from scripts.diagnostics.qualify_native_intake import read_journal


def test_historical_double_newline_and_current_canonical_records(tmp_path):
    p=tmp_path/'journal.jsonl'
    p.write_bytes(canonical(dict(case_id='a'))+b'\n'+canonical(dict(case_id='b')))
    assert read_journal(p)==[dict(case_id='a'),dict(case_id='b')]
