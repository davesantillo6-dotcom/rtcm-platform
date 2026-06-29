Here it is — copy everything between the triple backticks:
python"""
RTCM — Unit Tests: Extended GL Controls

Tests for:
  GL-004: BackdatedEntryControl
  GL-005: UnsupportedTopSideEntryControl

Each control is tested across four scenarios:
  - PASS:            Entry meets all control requirements
  - FAIL:            Entry triggers the control
  - NOT_APPLICABLE:  Entry is outside the control's scope
  - EDGE CASE:       Boundary condition or parameterization test

Author: David Santillo, CPA — Founder, RTCM Platform LLC
"""

import pytest
from datetime import date, datetime
from decimal import Decimal

from src.core.control_engine.controls.gl_controls import (
    BackdatedEntryControl,
    UnsupportedTopSideEntryControl,
)
from src.core.control_engine.engine import (
    ControlResult,
    JournalEntry,
)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

TENANT_ID = "tenant-001"
ENTITY_ID = "entity-west"

PERIOD_OPEN = date(2026, 5, 1)


def make_je(
    source_je_id: str = "JE-9001",
    posted_by: str = "user-bookkeeper",
    posting_date=None,
    entry_datetime=None,
    net_amount: Decimal = Decimal("5000.00"),
    account_code: str = "5000",
    account_type: str = "expense",
    description: str = "Standard operating expense",
    intercompany_flag: bool = False,
    ic_counterparty_entity_id: str = None,
) -> JournalEntry:
    return JournalEntry(
        rtcm_je_id=f"rtcm-{source_je_id}",
        source_je_id=source_je_id,
        tenant_id=TENANT_ID,
        entity_id=ENTITY_ID,
        posted_by_user_id=posted_by,
        approved_by_user_id="user-controller",
        posting_date=posting_date or date(2026, 5, 15),
        entry_datetime=entry_datetime or datetime(2026, 5, 15, 14, 30, 0),
        net_amount=net_amount,
        account_code=account_code,
        account_type=account_type,
        description=description,
        intercompany_flag=intercompany_flag,
        ic_counterparty_entity_id=ic_counterparty_entity_id,
    )


# ─────────────────────────────────────────────────────────────────────────────
# GL-004: BackdatedEntryControl
# ─────────────────────────────────────────────────────────────────────────────

class TestBackdatedEntryControl:

    @pytest.fixture
    def control(self):
        return BackdatedEntryControl()

    def test_pass_current_period_entry(self, control):
        je = make_je(posting_date=date(2026, 5, 15))
        result = control.evaluate(je, TENANT_ID, ENTITY_ID,
                                  period_open_date=PERIOD_OPEN)
        assert result.result == ControlResult.PASS

    def test_pass_within_tolerance_window(self, control):
        je = make_je(posting_date=date(2026, 4, 28))
        result = control.evaluate(je, TENANT_ID, ENTITY_ID,
                                  period_open_date=PERIOD_OPEN)
        assert result.result == ControlResult.PASS

    def test_fail_beyond_tolerance_window(self, control):
        je = make_je(
            source_je_id="JE-BD-001",
            posting_date=date(2026, 4, 21),
            posted_by="user-cfo",
            net_amount=Decimal("95000.00"),
            account_code="4000",
            account_type="revenue",
        )
        result = control.evaluate(je, TENANT_ID, ENTITY_ID,
                                  period_open_date=PERIOD_OPEN)
        assert result.result == ControlResult.FAIL
        assert result.details["days_before_open"] == 10
        assert result.details["posted_by"] == "user-cfo"
        assert "95000" in result.details["amount"]

    def test_fail_exactly_at_tolerance_boundary(self, control):
        je = make_je(posting_date=date(2026, 4, 25))
        result = control.evaluate(je, TENANT_ID, ENTITY_ID,
                                  period_open_date=PERIOD_OPEN)
        assert result.result == ControlResult.FAIL

    def test_pass_exactly_at_tolerance_boundary(self, control):
        je = make_je(posting_date=date(2026, 4, 26))
        result = control.evaluate(je, TENANT_ID, ENTITY_ID,
                                  period_open_date=PERIOD_OPEN)
        assert result.result == ControlResult.PASS

    def test_not_applicable_no_entry_datetime(self, control):
        je = make_je(entry_datetime=None)
        result = control.evaluate(je, TENANT_ID, ENTITY_ID,
                                  period_open_date=PERIOD_OPEN)
        assert result.result == ControlResult.NOT_APPLICABLE

    def test_fail_fallback_no_period_open_date(self, control):
        je = make_je(
            posting_date=date(2026, 4, 1),
            entry_datetime=datetime(2026, 5, 15, 9, 0, 0),
        )
        result = control.evaluate(je, TENANT_ID, ENTITY_ID,
                                  period_open_date=None)
        assert result.result == ControlResult.FAIL
        assert result.details["days_gap"] == 44

    def test_pass_fallback_within_tolerance(self, control):
        je = make_je(
            posting_date=date(2026, 5, 12),
            entry_datetime=datetime(2026, 5, 15, 9, 0, 0),
        )
        result = control.evaluate(je, TENANT_ID, ENTITY_ID,
                                  period_open_date=None)
        assert result.result == ControlResult.PASS

    def test_custom_tolerance_parameter(self, control):
        control.parameters = {"tolerance_days": 0}
        je = make_je(posting_date=date(2026, 4, 30))
        result = control.evaluate(je, TENANT_ID, ENTITY_ID,
                                  period_open_date=PERIOD_OPEN)
        assert result.result == ControlResult.FAIL

    def test_human_detail_populated_on_fail(self, control):
        je = make_je(
            source_je_id="JE-BD-002",
            posting_date=date(2026, 4, 20),
            posted_by="user-senior-acct",
        )
        result = control.evaluate(je, TENANT_ID, ENTITY_ID,
                                  period_open_date=PERIOD_OPEN)
        assert result.result == ControlResult.FAIL
        assert "JE-BD-002" in result.human_detail
        assert "user-senior-acct" in result.human_detail
        assert "2026-04-20" in result.human_detail


# ─────────────────────────────────────────────────────────────────────────────
# GL-005: UnsupportedTopSideEntryControl
# ─────────────────────────────────────────────────────────────────────────────

class TestUnsupportedTopSideEntryControl:

    @pytest.fixture
    def control(self):
        return UnsupportedTopSideEntryControl()

    def test_not_applicable_non_equity_account(self, control):
        je = make_je(
            account_code="5000",
            account_type="expense",
            net_amount=Decimal("50000.00"),
        )
        result = control.evaluate(je, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.NOT_APPLICABLE

    def test_not_applicable_revenue_account(self, control):
        je = make_je(
            account_code="4000",
            account_type="revenue",
            net_amount=Decimal("100000.00"),
            description="Q2 product revenue recognition",
        )
        result = control.evaluate(je, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.NOT_APPLICABLE

    def test_pass_equity_account_below_threshold(self, control):
        je = make_je(
            account_code="3900",
            account_type="retained_earnings",
            net_amount=Decimal("500.00"),
            description="Minor rounding correction",
        )
        result = control.evaluate(je, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.PASS

    def test_fail_equity_account_above_threshold_no_description(self, control):
        je = make_je(
            source_je_id="JE-TS-001",
            posted_by="user-cfo",
            account_code="3900",
            account_type="retained_earnings",
            net_amount=Decimal("210000.00"),
            description="Q3 adj.",
        )
        result = control.evaluate(je, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.FAIL
        assert result.details["amount"] == "210000.00"
        assert result.details["description_length"] == 8
        assert result.details["minimum_description_length"] == 20
        assert result.details["posted_by"] == "user-cfo"

    def test_pass_equity_account_above_threshold_adequate_description(self, control):
        je = make_je(
            account_code="3900",
            account_type="retained_earnings",
            net_amount=Decimal("75000.00"),
            description="Q3 owner distribution per board resolution dated 2026-07-01",
        )
        result = control.evaluate(je, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.PASS

    def test_fail_equity_account_empty_description(self, control):
        je = make_je(
            account_code="3000",
            account_type="equity",
            net_amount=Decimal("50000.00"),
            description="",
        )
        result = control.evaluate(je, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.FAIL
        assert result.details["description_length"] == 0
        assert result.details["description_provided"] == "(none)"

    def test_fail_description_none(self, control):
        je = make_je(
            account_code="3900",
            account_type="retained_earnings",
            net_amount=Decimal("30000.00"),
            description=None,
        )
        result = control.evaluate(je, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.FAIL

    def test_fail_equity_detected_by_account_code_prefix(self, control):
        je = make_je(
            account_code="3500",
            account_type="other",
            net_amount=Decimal("40000.00"),
            description="adj",
        )
        result = control.evaluate(je, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.FAIL

    def test_not_applicable_account_code_not_equity_prefix(self, control):
        je = make_je(
            account_code="1500",
            account_type="asset",
            net_amount=Decimal("100000.00"),
            description="",
        )
        result = control.evaluate(je, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.NOT_APPLICABLE

    def test_custom_threshold_parameter(self, control):
        control.parameters = {
            "threshold": 5000.00,
            "minimum_description_length": 20,
        }
        je = make_je(
            account_code="3900",
            account_type="retained_earnings",
            net_amount=Decimal("10000.00"),
            description="small adj",
        )
        result = control.evaluate(je, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.FAIL

    def test_custom_description_length_parameter(self, control):
        control.parameters = {
            "threshold": 25000.00,
            "minimum_description_length": 50,
        }
        je = make_je(
            account_code="3900",
            account_type="retained_earnings",
            net_amount=Decimal("50000.00"),
            description="Q3 distribution per resolution",
        )
        result = control.evaluate(je, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.FAIL

    def test_custom_equity_prefix_parameter(self, control):
        control.parameters = {
            "threshold": 25000.00,
            "minimum_description_length": 20,
            "equity_prefixes": ("8",),
        }
        je = make_je(
            account_code="8100",
            account_type="other",
            net_amount=Decimal("30000.00"),
            description="adj",
        )
        result = control.evaluate(je, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.FAIL

    def test_pass_exactly_at_threshold(self, control):
        je = make_je(
            account_code="3900",
            account_type="retained_earnings",
            net_amount=Decimal("25000.00"),
            description="adj",
        )
        result = control.evaluate(je, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.PASS

    def test_fail_one_cent_above_threshold(self, control):
        je = make_je(
            account_code="3900",
            account_type="retained_earnings",
            net_amount=Decimal("25000.01"),
            description="adj",
        )
        result = control.evaluate(je, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.FAIL

    def test_description_exactly_at_minimum_length(self, control):
        je = make_je(
            account_code="3900",
            account_type="retained_earnings",
            net_amount=Decimal("30000.00"),
            description="12345678901234567890",
        )
        result = control.evaluate(je, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.PASS

    def test_description_one_char_below_minimum(self, control):
        je = make_je(
            account_code="3900",
            account_type="retained_earnings",
            net_amount=Decimal("30000.00"),
            description="1234567890123456789",
        )
        result = control.evaluate(je, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.FAIL

    def test_human_detail_contains_actionable_information(self, control):
        je = make_je(
            source_je_id="JE-TS-002",
            posted_by="user-controller",
            account_code="3900",
            account_type="retained_earnings",
            net_amount=Decimal("85000.00"),
            description="Q2 adj",
            posting_date=date(2026, 6, 30),
        )
        result = control.evaluate(je, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.FAIL
        assert "3900" in result.human_detail
        assert "85,000" in result.human_detail
        assert "20" in result.human_detail
        assert "user-controller" in result.human_detail


# ─────────────────────────────────────────────────────────────────────────────
# Cross-control integration tests
# ─────────────────────────────────────────────────────────────────────────────

class TestGL004GL005Integration:

    def test_entry_triggers_both_controls(self):
        gl004 = BackdatedEntryControl()
        gl005 = UnsupportedTopSideEntryControl()
        je = make_je(
            source_je_id="JE-BOTH-001",
            posting_date=date(2026, 4, 15),
            account_code="3900",
            account_type="retained_earnings",
            net_amount=Decimal("150000.00"),
            description="adj",
        )
        result_004 = gl004.evaluate(je, TENANT_ID, ENTITY_ID,
                                    period_open_date=PERIOD_OPEN)
        result_005 = gl005.evaluate(je, TENANT_ID, ENTITY_ID)
        assert result_004.result == ControlResult.FAIL
        assert result_005.result == ControlResult.FAIL

    def test_entry_triggers_gl004_not_gl005(self):
        gl004 = BackdatedEntryControl()
        gl005 = UnsupportedTopSideEntryControl()
        je = make_je(
            posting_date=date(2026, 4, 20),
            account_code="5000",
            account_type="expense",
            net_amount=Decimal("30000.00"),
        )
        result_004 = gl004.evaluate(je, TENANT_ID, ENTITY_ID,
                                    period_open_date=PERIOD_OPEN)
        result_005 = gl005.evaluate(je, TENANT_ID, ENTITY_ID)
        assert result_004.result == ControlResult.FAIL
        assert result_005.result == ControlResult.NOT_APPLICABLE

    def test_entry_triggers_gl005_not_gl004(self):
        gl004 = BackdatedEntryControl()
        gl005 = UnsupportedTopSideEntryControl()
        je = make_je(
            posting_date=date(2026, 5, 15),
            account_code="3900",
            account_type="retained_earnings",
            net_amount=Decimal("75000.00"),
            description="adj",
        )
        result_004 = gl004.evaluate(je, TENANT_ID, ENTITY_ID,
                                    period_open_date=PERIOD_OPEN)
        result_005 = gl005.evaluate(je, TENANT_ID, ENTITY_ID)
        assert result_004.result == ControlResult.PASS
        assert result_005.result == ControlResult.FAIL

    def test_clean_entry_passes_both_controls(self):
        gl004 = BackdatedEntryControl()
        gl005 = UnsupportedTopSideEntryControl()
        je = make_je(
            posting_date=date(2026, 5, 15),
            account_code="5000",
            account_type="expense",
            net_amount=Decimal("10000.00"),
            description="Office supplies — May 2026 vendor invoice",
        )
        result_004 = gl004.evaluate(je, TENANT_ID, ENTITY_ID,
                                    period_open_date=PERIOD_OPEN)
        result_005 = gl005.evaluate(je, TENANT_ID, ENTITY_ID)
        assert result_004.result == ControlResult.PASS
        assert result_005.result == ControlResult.NOT_APPLICABLE
