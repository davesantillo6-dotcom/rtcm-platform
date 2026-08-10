Copy everything below this line and paste it into GitHub:

"""
RTCM Control Evaluation Engine
Core module for evaluating financial controls against normalized GL data.

Author: David Santillo, CPA — Founder, RTCM LLC
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, time
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class ControlResult(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    EXCEPTION = "exception"
    NOT_APPLICABLE = "not_applicable"


class Severity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class COSOCategory(str, Enum):
    CONTROL_ENVIRONMENT = "Control Environment"
    RISK_ASSESSMENT = "Risk Assessment"
    CONTROL_ACTIVITIES = "Control Activities"
    INFORMATION_COMMUNICATION = "Information & Communication"
    MONITORING = "Monitoring"


class ControlTrigger(str, Enum):
    TRANSACTION = "transaction"  # Evaluated per journal entry
    PERIODIC = "periodic"        # Evaluated on a schedule (daily, monthly)
    CONFIGURATION = "configuration"  # Evaluated when system config changes

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

@dataclass
class JournalEntry:
    """Canonical RTCM journal entry — normalized from any source ERP."""
    rtcm_je_id: str
    tenant_id: str
    entity_id: str
    source_system: str
    source_je_id: str
    posting_date: datetime
    entry_datetime: Optional[datetime]
    period: str  # YYYY-MM
    posted_by_user_id: str
    approved_by_user_id: Optional[str]
    account_code: str
    account_type: str
    debit_amount: Decimal
    credit_amount: Decimal
    description: str
    reference: Optional[str]
    intercompany_flag: bool = False
    ic_counterparty_entity_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def net_amount(self) -> Decimal:
        return self.debit_amount - self.credit_amount

    @property
    def is_self_approved(self) -> bool:
        return (
            self.approved_by_user_id is not None
            and self.posted_by_user_id == self.approved_by_user_id
        )


@dataclass
class ControlEvaluationResult:
    """Output of a single control test evaluation."""
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    entity_id: str = ""
    control_id: str = ""
    control_name: str = ""
    evaluated_at: datetime = field(default_factory=datetime.utcnow)
    result: ControlResult = ControlResult.PASS
    severity: Severity = Severity.LOW
    reference_type: str = "journal_entry"
    reference_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    human_detail: str = ""
    alert_required: bool = False


# ---------------------------------------------------------------------------
# Base Control Class
# ---------------------------------------------------------------------------

class BaseControl(ABC):
    """
    Abstract base class for all RTCM control tests.

    Subclasses implement the evaluate method, which receives a data payload
    and returns a ControlEvaluationResult.

    Controls are designed to be stateless — all context needed for evaluation
    is passed in via the data payload and parameters dict.
    """

    control_id: str
    control_name: str
    coso_category: COSOCategory
    trigger: ControlTrigger
    default_severity: Severity
    pcaob_relevant: bool = False

    def __init__(self, parameters: Optional[Dict[str, Any]] = None):
        self.parameters = parameters or {}

    @abstractmethod
    def evaluate(
        self,
        data: Any,
        tenant_id: str,
        entity_id: str,
    ) -> ControlEvaluationResult:
        """
        Evaluate the control against the provided data.
        Returns a ControlEvaluationResult indicating pass, fail, or exception.
        """
        ...

    def _base_result(
        self,
        tenant_id: str,
        entity_id: str,
        result: ControlResult,
        reference_id: Optional[str] = None,
        details: Optional[Dict] = None,
        human_detail: str = "",
    ) -> ControlEvaluationResult:
        severity = self.parameters.get("override_severity", self.default_severity)
        return ControlEvaluationResult(
            tenant_id=tenant_id,
            entity_id=entity_id,
            control_id=self.control_id,
            control_name=self.control_name,
            result=result,
            severity=severity,
            reference_type="journal_entry",
            reference_id=reference_id,
            details=details or {},
            human_detail=human_detail,
            alert_required=(result == ControlResult.FAIL),
        )


# ---------------------------------------------------------------------------
# GL Control Implementations
# ---------------------------------------------------------------------------

class SelfApprovalControl(BaseControl):
    """
    GL-003: Detects journal entries where the posting user is also the approver.

    Segregation of duties requires that the person who creates a transaction
    cannot be the same person who authorizes it. Self-approval is a critical
    control failure that enables fraudulent transactions to be created and
    approved without independent review.

    COSO: Control Activities
    Severity: Critical
    """
    control_id = "GL-003"
    control_name = "Self-approval — posting user equals approver"
    coso_category = COSOCategory.CONTROL_ACTIVITIES
    trigger = ControlTrigger.TRANSACTION
    default_severity = Severity.CRITICAL
    pcaob_relevant = True

    def evaluate(
        self,
        data: JournalEntry,
        tenant_id: str,
        entity_id: str,
    ) -> ControlEvaluationResult:
        if data.approved_by_user_id is None:
            return self._base_result(
                tenant_id, entity_id,
                result=ControlResult.NOT_APPLICABLE,
                reference_id=data.rtcm_je_id,
            )

        if data.is_self_approved:
            return self._base_result(
                tenant_id, entity_id,
                result=ControlResult.FAIL,
                reference_id=data.rtcm_je_id,
                details={
                    "posting_user": data.posted_by_user_id,
                    "approving_user": data.approved_by_user_id,
                    "je_amount": str(data.net_amount),
                    "posting_date": data.posting_date.isoformat(),
                },
                human_detail=(
                    f"User '{data.posted_by_user_id}' posted and self-approved "
                    f"JE '{data.source_je_id}' (${abs(data.net_amount):,.2f}) "
                    f"on {data.posting_date.strftime('%B %d, %Y')}."
                ),
            )

        return self._base_result(
            tenant_id, entity_id,
            result=ControlResult.PASS,
            reference_id=data.rtcm_je_id,
        )


class AfterHoursEntryControl(BaseControl):
    """
    GL-001: Flags journal entries posted outside normal business hours.

    Journal entries posted in the middle of the night or on weekends are
    statistically more likely to represent unauthorized or fraudulent activity.
    While not definitively fraudulent, after-hours entries warrant review,
    particularly for high-value or equity-impacting transactions.

    COSO: Control Activities
    Severity: High
    Default threshold: Outside 6:00 AM to 8:00 PM local time
    """
    control_id = "GL-001"
    control_name = "After-hours journal entry"
    coso_category = COSOCategory.CONTROL_ACTIVITIES
    trigger = ControlTrigger.TRANSACTION
    default_severity = Severity.HIGH

    DEFAULT_START = time(6, 0)   # 6:00 AM
    DEFAULT_END = time(20, 0)    # 8:00 PM

    def evaluate(
        self,
        data: JournalEntry,
        tenant_id: str,
        entity_id: str,
    ) -> ControlEvaluationResult:
        if data.entry_datetime is None:
            return self._base_result(
                tenant_id, entity_id,
                result=ControlResult.NOT_APPLICABLE,
                reference_id=data.rtcm_je_id,
            )

        start = self.parameters.get("business_hours_start", self.DEFAULT_START)
        end = self.parameters.get("business_hours_end", self.DEFAULT_END)
        entry_time = data.entry_datetime.time()

        if not (start <= entry_time <= end):
            return self._base_result(
                tenant_id, entity_id,
                result=ControlResult.FAIL,
                reference_id=data.rtcm_je_id,
                details={
                    "entry_time": entry_time.strftime("%H:%M"),
                    "business_hours": f"{start.strftime('%H:%M')} to {end.strftime('%H:%M')}",
                    "posting_user": data.posted_by_user_id,
                },
                human_detail=(
                    f"JE '{data.source_je_id}' was posted at "
                    f"{entry_time.strftime('%I:%M %p')} by '{data.posted_by_user_id}', "
                    f"outside normal business hours ({start.strftime('%I:%M %p')} to "
                    f"{end.strftime('%I:%M %p')})."
                ),
            )

        return self._base_result(
            tenant_id, entity_id,
            result=ControlResult.PASS,
            reference_id=data.rtcm_je_id,
        )


class RoundDollarEntryControl(BaseControl):
    """
    GL-002: Flags large round-dollar journal entries.

    Naturally occurring financial transactions rarely result in perfectly round
    numbers. A high-value entry with an exact round-dollar amount (e.g., $50,000.00)
    may indicate a manually fabricated or estimated entry that warrants scrutiny.

    COSO: Control Activities
    Severity: Medium
    Default threshold: Amounts > $10,000 that are exact multiples of $1,000
    """
    control_id = "GL-002"
    control_name = "Round dollar entry — high value"
    coso_category = COSOCategory.CONTROL_ACTIVITIES
    trigger = ControlTrigger.TRANSACTION
    default_severity = Severity.MEDIUM

    DEFAULT_MINIMUM = Decimal("10000.00")
    DEFAULT_ROUND_FACTOR = Decimal("1000.00")

    def evaluate(
        self,
        data: JournalEntry,
        tenant_id: str,
        entity_id: str,
    ) -> ControlEvaluationResult:
        minimum = Decimal(str(self.parameters.get("minimum_amount", self.DEFAULT_MINIMUM)))
        factor = Decimal(str(self.parameters.get("round_factor", self.DEFAULT_ROUND_FACTOR)))

        amount = abs(data.net_amount)

        if amount >= minimum and amount % factor == 0:
            return self._base_result(
                tenant_id, entity_id,
                result=ControlResult.FAIL,
                reference_id=data.rtcm_je_id,
                details={
                    "amount": str(amount),
                    "threshold": str(minimum),
                    "posting_user": data.posted_by_user_id,
                },
                human_detail=(
                    f"JE '{data.source_je_id}' has a round-dollar amount of "
                    f"${amount:,.2f}, which is above the ${minimum:,.0f} threshold "
                    f"and exactly divisible by ${factor:,.0f}."
                ),
            )

        return self._base_result(
            tenant_id, entity_id,
            result=ControlResult.PASS,
            reference_id=data.rtcm_je_id,
        )


# ---------------------------------------------------------------------------
# Control Engine
# ---------------------------------------------------------------------------

class ControlEngine:
    """
    Orchestrates evaluation of all applicable controls against incoming data.

    Usage:
        engine = ControlEngine()
        engine.register(SelfApprovalControl())
        engine.register(AfterHoursEntryControl())

        results = engine.evaluate_transaction(journal_entry, tenant_id, entity_id)
    """

    def __init__(self):
        self._transaction_controls: List[BaseControl] = []
        self._periodic_controls: List[BaseControl] = []

    def register(self, control: BaseControl) -> None:
        """Register a control with the engine."""
        if control.trigger == ControlTrigger.TRANSACTION:
            self._transaction_controls.append(control)
        elif control.trigger == ControlTrigger.PERIODIC:
            self._periodic_controls.append(control)

    def evaluate_transaction(
        self,
        entry: JournalEntry,
        tenant_id: str,
        entity_id: str,
    ) -> List[ControlEvaluationResult]:
        """
        Evaluate all registered transaction controls against a single journal entry.
        Returns a list of results (one per control).
        """
        results = []
        for control in self._transaction_controls:
            result = control.evaluate(entry, tenant_id, entity_id)
            results.append(result)
        return results

    def get_failures(
        self,
        results: List[ControlEvaluationResult],
    ) -> List[ControlEvaluationResult]:
        """Filter results to failures only."""
        return [r for r in results if r.result == ControlResult.FAIL]
