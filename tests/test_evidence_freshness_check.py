import sys
import os
from datetime import date
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from evidence_freshness_check import check


def make_row(**overrides):
    row = {"evidence_id": "EV-001", "control_id": "CC1.1", "description": "d", "last_updated": "2026-01-01", "owner": "IT"}
    row.update(overrides)
    return row


def test_fresh_evidence_is_not_flagged():
    stale, critical = check([make_row(last_updated="2026-09-10")], stale_days=90, hard_fail_days=180, today=date(2026, 9, 17))
    assert stale == []
    assert critical == []


def test_evidence_past_stale_days_is_warning():
    stale, critical = check([make_row(last_updated="2026-05-01")], stale_days=90, hard_fail_days=180, today=date(2026, 9, 17))
    assert len(stale) == 1
    assert critical == []


def test_evidence_past_hard_fail_days_is_critical():
    stale, critical = check([make_row(last_updated="2025-12-01")], stale_days=90, hard_fail_days=180, today=date(2026, 9, 17))
    assert len(critical) == 1


def test_unparseable_date_is_critical():
    stale, critical = check([make_row(last_updated="not-a-date")], stale_days=90, hard_fail_days=180, today=date(2026, 9, 17))
    assert len(critical) == 1
