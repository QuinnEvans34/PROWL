import pytest
from scripts.diagnostics.localizer_resource_profile import summary,stop_reason,LIMITS


def test_summary_preserves_all_timings():
    s=summary([2.,4.,3.]);assert s==dict(samples_seconds=[2.,4.,3.],median_seconds=3.,min_seconds=2.,max_seconds=4.)


@pytest.mark.parametrize('values',[[],[float('nan')],[float('inf')],[0],[-1]])
def test_invalid_samples(values):
    with pytest.raises(ValueError):summary(values)


@pytest.mark.parametrize('change,expected',[
    ({'elapsed':600},'time_cap'),({'rss':LIMITS['rss_bytes']+1},'rss_cap'),
    ({'output':LIMITS['output_bytes']+1},'output_cap'),({'free':0},'free_space_floor'),({'ac':False},'AC_power_lost')])
def test_supervisor_stop_conditions(change,expected):
    args=dict(elapsed=1,rss=100,output=100,free=LIMITS['free_bytes'],ac=True);args.update(change)
    assert stop_reason(**args)==expected


def test_bounded_run_continues():
    assert stop_reason(1,100,100,LIMITS['free_bytes'],True) is None
