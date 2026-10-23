import json
import pytest
from scripts.diagnostics.launch_lenovo_endurance import audit_gate


@pytest.fixture
def packet(tmp_path):
    h=tmp_path/'handoff';a=tmp_path/'audit';c=tmp_path/'cache'
    (h/'metadata').mkdir(parents=True);a.mkdir();c.mkdir()
    def put(path,value):path.write_text(json.dumps(value))
    put(a/'summary.json',dict(completed=True,passed=2,failed=0,cache=str(c)))
    put(a/'resources.json',dict(workers_reaped=True))
    put(h/'metadata/target-states.json',{'t':'positive','v':'positive'})
    put(a/'input-control.json',dict(train=['t'],validation=['v'],target_states={'t':'positive','v':'positive'}))
    inventory=[]
    for name in ('t','v'):
        hashes={k:k+name for k in ('ct','pancreas','lesion')}
        inventory += [dict(case_id=name,kind=k,sha256=v) for k,v in hashes.items()]
        put(c/(name+'.json'),dict(source_sha256=hashes))
    put(h/'metadata/source-file-hashes.json',inventory)
    return h,a,c,put


def test_exact_admitted_sources_pass(packet):
    h,a,c,put=packet;audit_gate(h,a,expected_count=2)


@pytest.mark.parametrize('change',['source','state','failure','missing'])
def test_admission_change_refused(packet,change):
    h,a,c,put=packet
    if change=='source':put(c/'t.json',dict(source_sha256={'ct':'different'}))
    elif change=='state':put(h/'metadata/target-states.json',{'t':'reference_empty','v':'positive'})
    elif change=='failure':put(a/'summary.json',dict(completed=True,passed=1,failed=1,cache=str(c)))
    else:put(h/'metadata/source-file-hashes.json',[])
    with pytest.raises(ValueError):audit_gate(h,a,expected_count=2)
