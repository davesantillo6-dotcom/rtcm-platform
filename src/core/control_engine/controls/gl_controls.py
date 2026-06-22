"""
RTCM — Extended GL Control Implementations

GL-004: Backdated entry to prior period
GL-005: Large unsupported top-side journal entry

Author: David Santillo, CPA — Founder, RTCM Platform LLC
"""

from __future__ import annotations
from datetime import datetime, date
from decimal import Decimal
from typing import Optional

from src.core.control_engine.engine import (
    BaseControl, ControlEvaluationResult, ControlResult,
    COSOCategory, ControlTrigger, Severity, JournalEntry
)


class BackdatedEntryControl(BaseControl):
    """
    GL-004: Flags journal entries posted to a prior period that has
    already been closed.

    A backdated journal entry is one whose posting date falls before
    the period's official close date by more than the configurable
    tolerance. Legitimate backdated entries do occur — late vendor
    invoices, accrual adjustments, or corrections identified shortly
    after close — but they should be rare and should always carry
    appropriate documentation and approval.

    Backdating becomes a red flag when:
    - The entry is large
    - The entry affects revenue, equity, or key balance sheet accounts
    - The entry lacks supporting documentation
    - The pattern repeats across multiple periods

    In a well-controlled environment, entries to prior closed periods
    require explicit management override authorization and should be
    tracked as an exception. RTCM surfaces every instance for review,
    allowing the Controller to make an informed disposition decision
    rather than discovering backdating patterns months later in an audit.

    COSO: Control Activities
    Severity: High
    Default threshold: Posting date more than 5 days before the
                       period's open date (i.e., 5 days into the
                       subsequent period before the prior period
                       should still be adjustable)
    """
    control_id = "GL-004"
    control_name = "Backdated entry to prior period"
    coso_category = COSOCategory.CONTROL_ACTIVITIES
    trigger = ControlTrigger.TRANSACTION
    default_severity = Severity.HIGH

    DEFAULT_TOLERANCE_DAYS = 5

    def evaluate(
        self,
        data: JournalEntry,
        tenant_id: str,
        entity_id: str,
        period_open_date: Optional[date] = None,
    ) -> ControlEvaluationResult:
        """
        Evaluate whether a journal entry is backdated beyond the
        acceptable tolerance window.

        Args:
            data: The journal entry being evaluated.
            tenant_id: The tenant identifier.
            entity_id: The entity identifier.
            period_open_date: The date the current period was opened.
                Used to determine whether the entry's posting date
                falls in a prior closed period. If None, evaluation
                falls back to comparing entry_datetime to posting_date.
        """
        if data.entry_datetime is None:
            return self._base_result(
                tenant_id, entity_id,
                result=ControlResult.NOT_APPLICABLE,
                reference_id=data.rtcm_je_id,
            )

        tolerance = int(
            self.parameters.get("tolerance_days", self.DEFAULT_TOLERANCE_DAYS)
        )

        # Primary evaluation: compare posting date to period open date
        if period_open_date is not None:
            posting = data.posting_date if isinstance(data.posting_date, date) \
                else data.posting_date.date()
            days_before_open = (period_open_date - posting).days

            if days_before_open > tolerance:
                return self._base_result(
                    tenant_id, entity_id,
                    result=ControlResult.FAIL,
                    reference_id=data.rtcm_je_id,
                    details={
                        "posting_date": str(posting),
                        "period_open_date": str(period_open_date),
                        "days_before_open": days_before_open,
                        "tolerance_days": tolerance,
                        "posted_by": data.posted_by_user_id,
                        "account_code": data.account_code,
                        "amount": str(abs(data.net_amount)),
                    },
                    human_detail=(
                        f"JE '{data.source_je_id}' has a posting date of "
                        f"{posting} — {days_before_open} days before the "
                        f"period open date of {period_open_date} "
                        f"(tolerance: {tolerance} days). "
                        f"Posted by '{data.posted_by_user_id}' to account "
                        f"'{data.account_code}', amount ${abs(data.net_amount):,.2f}."
                    ),
                )

        # Fallback: compare entry_datetime to posting_date
        # A large gap between when an entry was created and its posting
        # date may indicate backdating even without period open date context
        else:
            entry_date = data.entry_datetime.date() \
                if isinstance(data.entry_datetime, datetime) \
                else data.entry_datetime
            posting = data.posting_date if isinstance(data.posting_date, date) \
                else data.posting_date.date()
            days_gap = (entry_date - posting).days

            if days_gap > tolerance:
                return self._base_result(
                    tenant_id, entity_id,
                    result=ControlResult.FAIL,
                    reference_id=data.rtcm_je_id,
                    details={
                        "posting_date": str(posting),
                        "entry_datetime_date": str(entry_date),
                        "days_gap": days_gap,
                        "tolerance_days": tolerance,
                        "posted_by": data.posted_by_user_id,
                    },
                    human_detail=(
                        f"JE '{data.source_je_id}' was created on {entry_date} "
                        f"but has a posting date of {posting} — a gap of "
                        f"{days_gap} days beyond the {tolerance}-day tolerance. "
                        f"Posted by '{data.posted_by_user_id}'."
                    ),
                )

        return self._base_result(
            tenant_id, entity_id,
            result=ControlResult.PASS,
            reference_id=data.rtcm_je_id,
        )


class UnsupportedTopSideEntryControl(BaseControl):
    """
    GL-005: Flags high-value manual journal entries posted directly to
    equity, retained earnings, or top-level consolidation accounts
    without a supporting memo attachment.

    Top-side journal entries are manual adjustments posted above the
    sub-ledger level — typically by senior accounting personnel — to
    record accruals, reclassifications, corrections, or consolidation
    entries that do not flow through normal transaction processing.
    They are a legitimate and necessary part of any close process.

    However, top-side entries are also the mechanism most commonly
    used to manipulate financial statements. Because they are manual,
    they bypass the automated controls embedded in sub-ledger
    transaction processing. Because they are posted by senior personnel,
    they are less likely to be questioned. And because they often affect
    equity or high-level accounts, they can have a material impact on
    reported results without triggering obvious operational alerts.

    RTCM flags any top-side entry above the materiality threshold that
    does not have a description meeting the minimum documentation
    standard. This does not mean the entry is fraudulent — it means
    it requires a reviewer to confirm that documentation exists.

    COSO: Control Activities
    Severity: Critical
    Default threshold: Net amount exceeding $25,000 posted to an
                       equity or retained earnings account with a
                       description of fewer than 20 characters
    """
    control_id = "GL-005"
    control_name = "Large unsupported top-side journal entry"
    coso_category = COSOCategory.CONTROL_ACTIVITIES
    trigger = ControlTrigger.TRANSACTION
    default_severity = Severity.CRITICAL
    pcaob_relevant = True

    DEFAULT_THRESHOLD = Decimal("25000.00")
    MINIMUM_DESCRIPTION_LENGTH = 20

    # Account types that indicate a top-side entry
    TOP_SIDE_ACCOUNT_TYPES = {"equity", "retained_earnings"}

    # Common account code prefixes that indicate equity/retained earnings
    # These are customizable per tenant via parameters
    DEFAULT_EQUITY_PREFIXES = ("3", "39", "390", "3900")

    def evaluate(
        self,
        data: JournalEntry,
        tenant_id: str,
        entity_id: str,
    ) -> ControlEvaluationResult:
        """
        Evaluate whether a journal entry qualifies as a large
        unsupported top-side entry.
        """
        threshold = Decimal(str(
            self.parameters.get("threshold", self.DEFAULT_THRESHOLD)
        ))
        min_desc = int(
            self.parameters.get(
                "minimum_description_length",
                self.MINIMUM_DESCRIPTION_LENGTH
            )
        )
        equity_prefixes = tuple(
            self.parameters.get("equity_prefixes", self.DEFAULT_EQUITY_PREFIXES)
        )

        # Determine if this is a top-side account
        is_top_side = (
            data.account_type in self.TOP_SIDE_ACCOUNT_TYPES
            or data.account_code.startswith(equity_prefixes)
        )

        if not is_top_side:
            return self._base_result(
                tenant_id, entity_id,
                result=ControlResult.NOT_APPLICABLE,
                reference_id=data.rtcm_je_id,
            )

        amount = abs(data.net_amount)

        if amount < threshold:
            return self._base_result(
                tenant_id, entity_id,
                result=ControlResult.PASS,
                reference_id=data.rtcm_je_id,
            )

        # Amount exceeds threshold — check description quality
        description = (data.description or "").strip()
        has_adequate_description = len(description) >= min_desc

        if not has_adequate_description:
            return self._base_result(
                tenant_id, entity_id,
                result=ControlResult.FAIL,
                reference_id=data.rtcm_je_id,
                details={
                    "account_code": data.account_code,
                    "account_type": data.account_type,
                    "amount": str(amount),
                    "threshold": str(threshold),
                    "description_length": len(description),
                    "minimum_description_length": min_desc,
                    "description_provided": description or "(none)",
                    "posted_by": data.posted_by_user_id,
                    "posting_date": str(data.posting_date),
                },
                human_detail=(
                    f"JE '{data.source_je_id}' posts ${amount:,.2f} to "
                    f"equity/retained earnings account '{data.account_code}' "
                    f"with an inadequate description "
                    f"({len(description)} characters, minimum {min_desc} required). "
                    f"Posted by '{data.posted_by_user_id}' on "
                    f"{data.posting_date}. "
                    f"Supporting documentation must be confirmed before this "
                    f"entry can be accepted."
                ),
            )

        return self._base_result(
            tenant_id, entity_id,
            result=ControlResult.PASS,
            reference_id=data.rtcm_je_id,
        )
