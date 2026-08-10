"""
RTCM — Unit Tests: Segregation of Duties Controls

Tests for:
  SOD-001: APSoDControl (AP entry + payment release, same user)
  SOD-002: ARSoDControl (AR posting + cash receipt, same user)
  SoDRoleConflictAnalyzer: Role-level conflict detection

Each control is tested across four scenarios:
  - PASS:            Transaction meets all SoD requirements
  - FAIL:            Transaction triggers the SoD control
  - NOT_APPLICABLE:  Transaction is outside the control's scope
  - EDGE CASE:       Boundary condition or configuration test

Author: David Santillo, CPA — Founder, RTCM Platform LLC
"""

import pytest
from src.core.control_engine.controls.sod_controls import (
    APSoDControl,
    ARSoDControl,
    SoDRoleConflictAnalyzer,
    UserTransaction,
)
from src.core.control_engine.engine import ControlResult


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

TENANT_ID = "tenant-001"
ENTITY_ID = "entity-central"


def make_transaction(
    transaction_id: str = "TXN-5001",
    transaction_type: str = "ap_payment",
    initiated_by: str = "user-ap-clerk",
    released_by: str = "user-controller",
    amount: float = 12500.00,
    vendor_or_customer_id: str = "vendor-abc",
    reference: str = "INV-2026-0714",
    source_system: str = "quickbooks",
) -> UserTransaction:
    """
    Factory helper — returns a UserTransaction with sensible defaults
    so individual tests only need to override the fields they care about.
    """
    return UserTransaction(
        transaction_id=transaction_id,
        tenant_id=TENANT_ID,
        entity_id=ENTITY_ID,
        transaction_type=transaction_type,
        initiated_by_user_id=initiated_by,
        released_by_user_id=released_by,
        amount=amount,
        vendor_or_customer_id=vendor_or_customer_id,
        reference=reference,
        source_system=source_system,
    )


# ─────────────────────────────────────────────────────────────────────────────
# SOD-001: APSoDControl
# ─────────────────────────────────────────────────────────────────────────────

class TestAPSoDControl:
    """
    SOD-001 detects AP transactions where the same user both entered
    the invoice and released the associated payment — eliminating any
    independent check on the validity of the disbursement.

    Business context: this is the most common SoD failure in mid-market
    AP cycles. A single individual who can both create a payable and
    release the payment can direct funds to unauthorized vendors or
    inflate invoice amounts without detection.
    """

    @pytest.fixture
    def control(self):
        return APSoDControl()

    def test_pass_different_users_ap_payment(self, control):
        """
        Standard pass: AP clerk enters the invoice, Controller releases
        the payment. Two different individuals — SoD is maintained.
        """
        txn = make_transaction(
            transaction_type="ap_payment",
            initiated_by="user-ap-clerk",
            released_by="user-controller",
        )
        result = control.evaluate(txn, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.PASS

    def test_fail_same_user_ap_payment(self, control):
        """
        Core failure: AP clerk both enters and releases a $47,500
        payment to a vendor. No independent reviewer approved this
        disbursement.

        Real-world scenario: bookkeeper with both AP entry and payment
        release permissions creates a fictitious vendor and releases
        payment to an account she controls.
        """
        txn = make_transaction(
            transaction_id="TXN-SOD-001",
            transaction_type="ap_payment",
            initiated_by="user-ap-clerk",
            released_by="user-ap-clerk",
            amount=47500.00,
            vendor_or_customer_id="vendor-xyz",
        )
        result = control.evaluate(txn, TENANT_ID, ENTITY_ID)

        assert result.result == ControlResult.FAIL
        assert result.details["initiated_by"] == "user-ap-clerk"
        assert result.details["released_by"] == "user-ap-clerk"
        assert result.details["amount"] == 47500.00
        assert "vendor-xyz" in result.details["vendor_id"]

    def test_fail_same_user_ap_invoice_payment(self, control):
        """
        Same SoD failure on an ap_invoice_payment transaction type —
        confirms the control handles both AP transaction type strings.
        """
        txn = make_transaction(
            transaction_type="ap_invoice_payment",
            initiated_by="user-bookkeeper",
            released_by="user-bookkeeper",
            amount=22000.00,
        )
        result = control.evaluate(txn, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.FAIL

    def test_not_applicable_non_ap_transaction(self, control):
        """
        A GL journal entry is not an AP payment transaction.
        The control should return NOT_APPLICABLE rather than
        evaluating SoD on an out-of-scope transaction type.
        """
        txn = make_transaction(
            transaction_type="gl_journal_entry",
            initiated_by="user-controller",
            released_by="user-controller",
            amount=5000.00,
        )
        result = control.evaluate(txn, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.NOT_APPLICABLE

    def test_not_applicable_no_release_user(self, control):
        """
        If no payment release user is recorded, the control cannot
        evaluate whether SoD was maintained. Returns NOT_APPLICABLE
        rather than a false positive or false negative.

        Common scenario: legacy ERP systems that do not capture
        approval workflow metadata in the transaction record.
        """
        txn = make_transaction(
            transaction_type="ap_payment",
            initiated_by="user-ap-clerk",
            released_by=None,
        )
        result = control.evaluate(txn, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.NOT_APPLICABLE

    def test_fail_human_detail_contains_actionable_information(self, control):
        """
        On failure, human_detail should tell the Controller exactly
        what happened — who, what transaction, what amount, what vendor —
        without requiring them to open the ERP to investigate.
        """
        txn = make_transaction(
            transaction_id="TXN-SOD-002",
            transaction_type="ap_payment",
            initiated_by="user-jsmith",
            released_by="user-jsmith",
            amount=35000.00,
            vendor_or_customer_id="vendor-suspect",
        )
        result = control.evaluate(txn, TENANT_ID, ENTITY_ID)

        assert result.result == ControlResult.FAIL
        assert "user-jsmith" in result.human_detail
        assert "TXN-SOD-002" in result.human_detail
        assert "35,000" in result.human_detail
        assert "vendor-suspect" in result.human_detail

    def test_pass_large_payment_different_users(self, control):
        """
        A large payment with proper SoD — different entry and release
        users — should pass regardless of amount.
        SoD evaluation is binary: either the same user or not.
        Amount is not a factor for this control.
        """
        txn = make_transaction(
            transaction_type="ap_payment",
            initiated_by="user-ap-manager",
            released_by="user-cfo",
            amount=500000.00,
        )
        result = control.evaluate(txn, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.PASS

    def test_fail_small_payment_same_user(self, control):
        """
        A small payment with SoD failure should still fail.
        The control is not amount-based — even a $1.00 AP payment
        released by the same user who entered it is a control failure.
        """
        txn = make_transaction(
            transaction_type="ap_payment",
            initiated_by="user-ap-clerk",
            released_by="user-ap-clerk",
            amount=1.00,
        )
        result = control.evaluate(txn, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.FAIL


# ─────────────────────────────────────────────────────────────────────────────
# SOD-002: ARSoDControl
# ─────────────────────────────────────────────────────────────────────────────

class TestARSoDControl:
    """
    SOD-002 detects AR transactions where the same user both posted
    the receivable and applied the cash receipt — creating the
    conditions for lapping fraud and cash misapplication.

    Business context: lapping is a common AR fraud scheme where cash
    from one customer is misappropriated and concealed by applying
    a subsequent customer's payment to the first account. It requires
    only that one person controls both the AR posting and cash
    application functions — which SOD-002 detects immediately.
    """

    @pytest.fixture
    def control(self):
        return ARSoDControl()

    def test_pass_different_users_ar_receipt(self, control):
        """
        Standard pass: AR clerk posts the invoice, billing manager
        applies the cash receipt. Two different individuals — SoD
        is maintained.
        """
        txn = make_transaction(
            transaction_type="ar_receipt",
            initiated_by="user-ar-clerk",
            released_by="user-billing-manager",
            vendor_or_customer_id="customer-001",
        )
        result = control.evaluate(txn, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.PASS

    def test_fail_same_user_ar_receipt(self, control):
        """
        Core failure: AR clerk both posts the receivable and applies
        the cash receipt. Creates an undetected opportunity for lapping.

        Real-world scenario: AR clerk intercepts a customer check,
        deposits it personally, and applies a subsequent customer's
        payment to cover the first customer's balance — repeating
        indefinitely until caught.
        """
        txn = make_transaction(
            transaction_id="TXN-AR-001",
            transaction_type="ar_receipt",
            initiated_by="user-ar-clerk",
            released_by="user-ar-clerk",
            amount=28000.00,
            vendor_or_customer_id="customer-midwest",
        )
        result = control.evaluate(txn, TENANT_ID, ENTITY_ID)

        assert result.result == ControlResult.FAIL
        assert result.details["initiated_by"] == "user-ar-clerk"
        assert result.details["released_by"] == "user-ar-clerk"
        assert result.details["customer_id"] == "customer-midwest"

    def test_fail_same_user_ar_cash_application(self, control):
        """
        Same SoD failure on ar_cash_application transaction type —
        confirms the control handles both AR transaction type strings.
        """
        txn = make_transaction(
            transaction_type="ar_cash_application",
            initiated_by="user-collections",
            released_by="user-collections",
            amount=15000.00,
        )
        result = control.evaluate(txn, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.FAIL

    def test_not_applicable_non_ar_transaction(self, control):
        """
        An AP payment transaction is outside the scope of SOD-002.
        Should return NOT_APPLICABLE.
        """
        txn = make_transaction(
            transaction_type="ap_payment",
            initiated_by="user-ap-clerk",
            released_by="user-ap-clerk",
        )
        result = control.evaluate(txn, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.NOT_APPLICABLE

    def test_not_applicable_no_release_user(self, control):
        """
        No cash application user recorded — cannot evaluate SoD.
        Returns NOT_APPLICABLE rather than a false result.
        """
        txn = make_transaction(
            transaction_type="ar_receipt",
            initiated_by="user-ar-clerk",
            released_by=None,
        )
        result = control.evaluate(txn, TENANT_ID, ENTITY_ID)
        assert result.result == ControlResult.NOT_APPLICABLE

    def test_fail_human_detail_references_lapping_risk(self, control):
        """
        On failure, human_detail should reference the lapping risk
        specifically — giving the Controller enough context to
        understand why this matters beyond a generic SoD message.
        """
        txn = make_transaction(
            transaction_id="TXN-AR-002",
            transaction_type="ar_receipt",
            initiated_by="user-mlopez",
            released_by="user-mlopez",
            amount=19500.00,
            vendor_or_customer_id="customer-central",
        )
        result = control.evaluate(txn, TENANT_ID, ENTITY_ID)

        assert result.result == ControlResult.FAIL
        assert "user-mlopez" in result.human_detail
        assert "lapping" in result.human_detail.lower()
        assert "customer-central" in result.human_detail


# ─────────────────────────────────────────────────────────────────────────────
# SoDRoleConflictAnalyzer
# ─────────────────────────────────────────────────────────────────────────────

class TestSoDRoleConflictAnalyzer:
    """
    The role conflict analyzer operates at the user access level —
    identifying incompatible role combinations before any transaction
    occurs, rather than detecting failures after the fact.

    This is the preventive complement to the detective controls above.
    """

    @pytest.fixture
    def analyzer(self):
        return SoDRoleConflictAnalyzer()

    def test_no_conflicts_clean_role_set(self, analyzer):
        """
        A user with only AP entry permissions — no payment release —
        has no conflicts. Single-function roles are always clean.
        """
        conflicts = analyzer.evaluate_user_roles(
            user_id="user-ap-clerk",
            assigned_roles=["ap_entry"],
            tenant_id=TENANT_ID,
            entity_id=ENTITY_ID,
        )
        assert len(conflicts) == 0

    def test_detects_ap_entry_plus_payment_release(self, analyzer):
        """
        Core AP SoD conflict: a user with both ap_entry and
        ap_payment_release roles has the access to perform SOD-001
        failures without any system restriction.
        """
        conflicts = analyzer.evaluate_user_roles(
            user_id="user-jsmith",
            assigned_roles=["ap_entry", "ap_payment_release"],
            tenant_id=TENANT_ID,
            entity_id=ENTITY_ID,
        )
        assert len(conflicts) >= 1
        role_pairs = [set(c["conflicting_roles"]) for c in conflicts]
        assert {"ap_entry", "ap_payment_release"} in role_pairs

    def test_detects_ar_posting_plus_cash_application(self, analyzer):
        """
        Core AR SoD conflict: a user with both ar_posting and
        ar_cash_application roles has the access to perform lapping
        without any system restriction.
        """
        conflicts = analyzer.evaluate_user_roles(
            user_id="user-mlopez",
            assigned_roles=["ar_posting", "ar_cash_application"],
            tenant_id=TENANT_ID,
            entity_id=ENTITY_ID,
        )
        assert len(conflicts) >= 1
        role_pairs = [set(c["conflicting_roles"]) for c in conflicts]
        assert {"ar_posting", "ar_cash_application"} in role_pairs

    def test_detects_multiple_conflicts_same_user(self, analyzer):
        """
        A user with an excessive permission set may have multiple
        simultaneous SoD conflicts. The analyzer should return all
        of them — not just the first one found.

        Scenario: a Controller at a small company who accumulated
        permissions over time without a formal access review.
        """
        conflicts = analyzer.evaluate_user_roles(
            user_id="user-over-permissioned",
            assigned_roles=[
                "ap_entry",
                "ap_payment_release",
                "ar_posting",
                "ar_cash_application",
                "gl_journal_entry",
                "gl_journal_approval",
            ],
            tenant_id=TENANT_ID,
            entity_id=ENTITY_ID,
        )
        assert len(conflicts) >= 3

    def test_detects_user_admin_with_financial_roles(self, analyzer):
        """
        A user with system administration access should never hold
        financial transaction roles — they could create users, assign
        themselves permissions, and process transactions without
        any independent check.
        """
        conflicts = analyzer.evaluate_user_roles(
            user_id="user-it-admin",
            assigned_roles=["user_administration", "ap_entry"],
            tenant_id=TENANT_ID,
            entity_id=ENTITY_ID,
        )
        assert len(conflicts) >= 1

    def test_no_conflicts_properly_segregated_team(self, analyzer):
        """
        A properly segregated team where each user has a single
        functional role produces no conflicts across any user.
        """
        team = [
            ("user-ap-entry",    ["ap_entry"]),
            ("user-ap-approval", ["ap_approval"]),
            ("user-ap-payment",  ["ap_payment_release"]),
            ("user-ar-posting",  ["ar_posting"]),
            ("user-ar-cash",     ["ar_cash_application"]),
        ]
        for user_id, roles in team:
            conflicts = analyzer.evaluate_user_roles(
                user_id=user_id,
                assigned_roles=roles,
                tenant_id=TENANT_ID,
                entity_id=ENTITY_ID,
            )
            assert len(conflicts) == 0, (
                f"Unexpected conflict for {user_id} with roles {roles}"
            )

    def test_conflict_detail_contains_user_and_description(self, analyzer):
        """
        Each conflict finding should contain the user ID, the
        conflicting role pair, severity, and a plain-language
        description of the risk — enough for a Controller to act
        without additional research.
        """
        conflicts = analyzer.evaluate_user_roles(
            user_id="user-bwilson",
            assigned_roles=["ap_entry", "ap_payment_release"],
            tenant_id=TENANT_ID,
            entity_id=ENTITY_ID,
        )
        assert len(conflicts) >= 1
        conflict = conflicts[0]
        assert conflict["user_id"] == "user-bwilson"
        assert "conflicting_roles" in conflict
        assert "severity" in conflict
        assert "description" in conflict
        assert "user-bwilson" in conflict["description"]

    def test_severity_is_critical_for_financial_conflicts(self, analyzer):
        """
        All financial SoD conflicts should be classified as Critical
        severity — they represent direct fraud enablement, not
        minor control weaknesses.
        """
        conflicts = analyzer.evaluate_user_roles(
            user_id="user-test",
            assigned_roles=["ap_entry", "ap_payment_release"],
            tenant_id=TENANT_ID,
            entity_id=ENTITY_ID,
        )
        assert all(c["severity"] == "Critical" for c in conflicts)


# ─────────────────────────────────────────────────────────────────────────────
# Cross-control integration: SOD-001 and SOD-002
# ─────────────────────────────────────────────────────────────────────────────

class TestSoDIntegration:
    """
    Confirms that SOD-001 and SOD-002 evaluate independently and
    correctly scope to their respective transaction types.
    """

    def test_ap_failure_does_not_trigger_ar_control(self):
        """
        An AP SoD failure should trigger SOD-001 but return
        NOT_APPLICABLE for SOD-002 — the two controls are scoped
        to different transaction types.
        """
        sod001 = APSoDControl()
        sod002 = ARSoDControl()

        txn = make_transaction(
            transaction_type="ap_payment",
            initiated_by="user-ap-clerk",
            released_by="user-ap-clerk",
        )
        result_001 = sod001.evaluate(txn, TENANT_ID, ENTITY_ID)
        result_002 = sod002.evaluate(txn, TENANT_ID, ENTITY_ID)

        assert result_001.result == ControlResult.FAIL
        assert result_002.result == ControlResult.NOT_APPLICABLE

    def test_ar_failure_does_not_trigger_ap_control(self):
        """
        An AR SoD failure should trigger SOD-002 but return
        NOT_APPLICABLE for SOD-001.
        """
        sod001 = APSoDControl()
        sod002 = ARSoDControl()

        txn = make_transaction(
            transaction_type="ar_receipt",
            initiated_by="user-ar-clerk",
            released_by="user-ar-clerk",
        )
        result_001 = sod001.evaluate(txn, TENANT_ID, ENTITY_ID)
        result_002 = sod002.evaluate(txn, TENANT_ID, ENTITY_ID)

        assert result_001.result == ControlResult.NOT_APPLICABLE
        assert result_002.result == ControlResult.FAIL

    def test_clean_ap_transaction_passes_both_controls(self):
        """
        A properly segregated AP payment passes SOD-001 and returns
        NOT_APPLICABLE for SOD-002 — the expected result for a
        clean AP transaction evaluated against both controls.
        """
        sod001 = APSoDControl()
        sod002 = ARSoDControl()

        txn = make_transaction(
            transaction_type="ap_payment",
            initiated_by="user-ap-clerk",
            released_by="user-controller",
        )
        result_001 = sod001.evaluate(txn, TENANT_ID, ENTITY_ID)
        result_002 = sod002.evaluate(txn, TENANT_ID, ENTITY_ID)

        assert result_001.result == ControlResult.PASS
        assert result_002.result == ControlResult.NOT_APPLICABLE
