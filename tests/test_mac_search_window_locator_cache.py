from scripts.diagnostics.run_mac_search_window_locator_20261111_v3 import cache_ranges


def test_cache_ranges_cover_every_scan_and_isolate_large_scans():
    rows = [{'native_shape': (100, 100, 100)}] * 13
    rows += [{'native_shape': (500, 500, 400)}]
    rows += [{'native_shape': (500, 400, 240)}] * 5
    assert cache_ranges(rows) == [[0, 10], [10, 13], [13, 14], [14, 17], [17, 19]]
