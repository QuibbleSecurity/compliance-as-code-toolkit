import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
from validate_control_mapping import validate


def make_row(**overrides):
    row = {
        "control_id": "CC1.1", "framework": "SOC2", "control_family": "Control Environment",
        "control_description": "desc", "status": "Met", "risk_rating": "", "evidence_id": "EV-001",
    }
    row.update(overrides)
    return row


def test_clean_row_has_no_issues():
    errors, warnings = validate([make_row()])
    assert errors == []
    assert warnings == []


def test_missing_control_id_is_error():
    errors, warnings = validate([make_row(control_id="")])
    assert any("missing control_id" in e for e in errors)


def test_invalid_status_is_error():
    errors, warnings = validate([make_row(status="Kinda Met")])
    assert any("invalid status" in e for e in errors)


def test_met_without_evidence_is_warning():
    errors, warnings = validate([make_row(status="Met", evidence_id="")])
    assert any("no evidence_id is linked" in w for w in warnings)


def test_high_risk_not_met_without_evidence_is_critical_error():
    errors, warnings = validate([make_row(status="Not Met", risk_rating="High", evidence_id="")])
    assert any("CRITICAL GAP" in e for e in errors)


def test_duplicate_control_id_same_framework_is_error():
    rows = [make_row(control_id="CC1.1"), make_row(control_id="CC1.1")]
    errors, warnings = validate(rows)
    assert any("Duplicate control_id" in e for e in errors)
