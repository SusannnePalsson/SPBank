from flow_main import extract_summary

def test_extract_summary_parses_counts():
    sample = '''
[customers] inserted=581, skipped_existing=419
[accounts ] inserted=1000, skipped_existing=0, missing_owner=0
[transactions] inserted=99695, skipped_existing=0, missing_accounts=0
[flagged] inserted=6771, skipped_existing=0, missing_tx=0
'''
    summary = extract_summary(sample)
    assert summary["customers"] == (581, 419)
    assert summary["accounts"]  == (1000, 0, 0)
    assert summary["transactions"] == (99695, 0, 0)
    assert summary["flagged"] == (6771, 0, 0)

def test_summary_patterns_are_case_insensitive():
    sample = "[Customers] INSERTED=1, SKIPPED_EXISTING=2"
    s = extract_summary(sample)
    assert s["customers"] == (1, 2)