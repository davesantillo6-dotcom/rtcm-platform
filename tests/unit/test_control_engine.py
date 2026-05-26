Copy everything below this line and paste it into GitHub:

"""
Unit tests for RTCM Control Evaluation Engine.

Tests cover the core control implementations with both positive (pass) and
negative (fail) cases, including edge cases for each control's thresholds.
"""

import pytest
from decimal import Decimal
from datetime import datetime, date, time

from src.core.control_engine.engine import (
    AfterHoursEntryControl,
    ControlEngine,
    ControlResult,
    JournalEntry,
    RoundDollarEntryControl,
    Severity,
    SelfApprovalControl,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TENANT_ID = "tenant-001"
ENTITY_ID = "entity-001"


def make_entry(**kwargs) -> JournalEntry:
    """Factory for test journal entries with sensible defaults."""
    defaults = dict(
        rtcm_je_id="je-test-001",
        tenant_id=TENANT_ID,
        entity_id=ENTITY_ID,
        source_system="quickbooks",
        source_je_id="QBO-JE-1234",
        posting_date=datetime(2026, 5, 15),
        entry_datetime=datetime(2026, 5, 15, 10, 30, 0),  # 10:30 AM
        period="2026-05",
        posted_by_user_id="user-alice",
        approved_by_user_id="user-bob",
        account_code="5100",
        account_type="expense",
        debit_amount=Decimal("1500.00"),
        credit_amount=Decimal("0.00"),
        description="May consulting services",
        reference="INV-0042",
        intercompany_flag=False,
        ic_counterparty_entity_id=None,
        metadata={},
    )
    defaults.update(kwargs)
    return JournalEntry(**defaults)


# ---------------------------------------------------------------------------
# GL-003: Self-Approval Control Tests
# ---------------------------------------------------------------------------

class TestSelfApprovalControl:
    control = SelfApprovalControl()

    def test_pass_when_different_approver(self):
        entry = make_entry(posted_by_user_id="alice", approved_by_user_id="bob")
        result = self.control.evaluate(entry, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.PASS

    def test_fail_when_self_approved(self):
        entry = make_entry(posted_by_user_id="alice", approved_by_user_id="alice")
        result = self.control.evaluate(entry, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.FAIL
        assert result.severity == Severity.CRITICAL
        assert result.alert_required is True
        assert "alice" in result.human_detail

    def test_not_applicable_when_no_approver(self):
        entry = make_entry(approved_by_user_id=None)
        result = self.control.evaluate(entry, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.NOT_APPLICABLE
        assert result.alert_required is False

    def test_result_contains_reference_id(self):
        entry = make_entry(
            rtcm_je_id="je-ref-test",
            posted_by_user_id="alice",
            approved_by_user_id="alice",
        )
        result = self.control.evaluate(entry, TENANT_ID, ENTITY_ID)
        assert result.reference_id == "je-ref-test"

    def test_details_include_users_and_amount(self):
        entry = make_entry(
            posted_by_user_id="alice",
            approved_by_user_id="alice",
            debit_amount=Decimal("25000.00"),
        )
        result = self.control.evaluate(entry, TENANT_ID, ENTITY_ID)
        assert result.details["posting_user"] == "alice"
        assert result.details["approving_user"] == "alice"

    def test_severity_can_be_overridden(self):
        control = SelfApprovalControl(parameters={"override_severity": Severity.HIGH})
        entry = make_entry(posted_by_user_id="alice", approved_by_user_id="alice")
        result = control.evaluate(entry, TENANT_ID, ENTITY_ID)
        assert result.severity == Severity.HIGH


# ---------------------------------------------------------------------------
# GL-001: After-Hours Entry Control Tests
# ---------------------------------------------------------------------------

class TestAfterHoursEntryControl:
    control = AfterHoursEntryControl()

    def test_pass_during_business_hours(self):
        entry = make_entry(entry_datetime=datetime(2026, 5, 15, 10, 30))  # 10:30 AM
        result = self.control.evaluate(entry, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.PASS

    def test_fail_for_midnight_entry(self):
        entry = make_entry(entry_datetime=datetime(2026, 5, 15, 2, 14))  # 2:14 AM
        result = self.control.evaluate(entry, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.FAIL
        assert result.severity == Severity.HIGH

    def test_fail_at_exact_boundary_before_start(self):
        entry = make_entry(entry_datetime=datetime(2026, 5, 15, 5, 59))  # 5:59 AM
        result = self.control.evaluate(entry, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.FAIL

    def test_pass_at_exact_start_boundary(self):
        entry = make_entry(entry_datetime=datetime(2026, 5, 15, 6, 0))  # 6:00 AM
        result = self.control.evaluate(entry, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.PASS

    def test_pass_at_exact_end_boundary(self):
        entry = make_entry(entry_datetime=datetime(2026, 5, 15, 20, 0))  # 8:00 PM
        result = self.control.evaluate(entry, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.PASS

    def test_fail_after_end_boundary(self):
        entry = make_entry(entry_datetime=datetime(2026, 5, 15, 20, 1))  # 8:01 PM
        result = self.control.evaluate(entry, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.FAIL

    def test_not_applicable_when_no_entry_datetime(self):
        entry = make_entry(entry_datetime=None)
        result = self.control.evaluate(entry, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.NOT_APPLICABLE

    def test_custom_business_hours(self):
        control = AfterHoursEntryControl(parameters={
            "business_hours_start": time(8, 0),
            "business_hours_end": time(17, 0),
        })
        entry = make_entry(entry_datetime=datetime(2026, 5, 15, 7, 0))  # 7 AM
        result = control.evaluate(entry, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.FAIL


# ---------------------------------------------------------------------------
# GL-002: Round Dollar Entry Control Tests
# ---------------------------------------------------------------------------

class TestRoundDollarEntryControl:
    control = RoundDollarEntryControl()

    def test_pass_for_normal_amount(self):
        entry = make_entry(debit_amount=Decimal("1523.47"))
        result = self.control.evaluate(entry, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.PASS

    def test_fail_for_large_round_amount(self):
        entry = make_entry(debit_amount=Decimal("50000.00"))
        result = self.control.evaluate(entry, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.FAIL
        assert result.severity == Severity.MEDIUM

    def test_pass_below_minimum_threshold(self):
        entry = make_entry(debit_amount=Decimal("5000.00"))
        result = self.control.evaluate(entry, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.PASS

    def test_fail_at_exact_minimum(self):
        entry = make_entry(debit_amount=Decimal("10000.00"))
        result = self.control.evaluate(entry, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.FAIL

    def test_pass_for_round_amount_not_divisible_by_1000(self):
        entry = make_entry(debit_amount=Decimal("10500.00"))
        result = self.control.evaluate(entry, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.PASS

    def test_credit_entry_uses_absolute_value(self):
        entry = make_entry(
            debit_amount=Decimal("0.00"),
            credit_amount=Decimal("25000.00"),
        )
        result = self.control.evaluate(entry, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.FAIL


# ---------------------------------------------------------------------------
# Control Engine Orchestration Tests
# ---------------------------------------------------------------------------

class TestControlEngine:
    def test_engine_evaluates_all_registered_controls(self):
        engine = ControlEngine()
        engine.register(SelfApprovalControl())
        engine.register(AfterHoursEntryControl())
        engine.register(RoundDollarEntryControl())

        entry = make_entry()
        results = engine.evaluate_transaction(entry, TENANT_ID, ENTITY_ID)
        assert len(results) == 3

    def test_get_failures_filters_correctly(self):
        engine = ControlEngine()
        engine.register(SelfApprovalControl())

        entry = make_entry(posted_by_user_id="alice", approved_by_user_id="alice")
        results = engine.evaluate_transaction(entry, TENANT_ID, ENTITY_ID)
        failures = engine.get_failures(results)

        assert len(failures) == 1
        assert failures[0].control_id == "GL-003"

    def test_empty_engine_returns_empty_results(self):
        engine = ControlEngine()
        entry = make_entry()
        results = engine.evaluate_transaction(entry, TENANT_ID, ENTITY_ID)
        assert results == []
