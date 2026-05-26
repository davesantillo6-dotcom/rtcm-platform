RTCM — QuickBooks Online Connector

Handles OAuth 2.0 authentication and GL data extraction from QuickBooks Online
via the Intuit QuickBooks API. Normalizes extracted data to the RTCM canonical
journal entry schema.

API Reference: https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/journalentry
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, Generator, List, Optional
import logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# QuickBooks Native Schema Models
# ---------------------------------------------------------------------------

@dataclass
class QBOJournalEntryLine:
    """Represents a single line in a QuickBooks Journal Entry."""
    id: str
    description: Optional[str]
    amount: Decimal
    posting_type: str  # "Debit" or "Credit"
    account_ref: str   # Account ID in QBO
    account_name: str
    class_ref: Optional[str] = None
    department_ref: Optional[str] = None


@dataclass
class QBOJournalEntry:
    """Raw QuickBooks Journal Entry as returned by the API."""
    id: str
    doc_number: Optional[str]
    txn_date: date
    create_time: datetime
    last_updated_time: datetime
    private_note: Optional[str]
    lines: List[QBOJournalEntryLine]
    created_by_id: Optional[str] = None
    adjusted: bool = False
    home_total_amt: Optional[Decimal] = None


# ---------------------------------------------------------------------------
# Connector
# ---------------------------------------------------------------------------

class QuickBooksConnector:
    """
    Extracts journal entry data from QuickBooks Online and normalizes it
    to the RTCM canonical schema.

    Authentication: OAuth 2.0 (access token managed externally via Auth0/Secrets Manager)

    QBO API Endpoint used:
        GET /v3/company/{realmId}/query
        SELECT * FROM JournalEntry WHERE TxnDate >= '{start}' AND TxnDate <= '{end}'
    """

    QBO_API_BASE = "https://quickbooks.api.intuit.com/v3/company"
    PAGE_SIZE = 1000  # QBO max per query

    def __init__(
        self,
        realm_id: str,
        access_token: str,
        entity_id: str,
        tenant_id: str,
    ):
        self.realm_id = realm_id
        self.access_token = access_token
        self.entity_id = entity_id
        self.tenant_id = tenant_id

    def _build_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "Content-Type": "application/text",
        }

    def _query_url(self) -> str:
        return f"{self.QBO_API_BASE}/{self.realm_id}/query"

    def fetch_journal_entries(
        self,
        start_date: date,
        end_date: date,
    ) -> Generator[QBOJournalEntry, None, None]:
        """
        Yields QBOJournalEntry objects for the specified date range.
        Handles QBO pagination automatically.
        """
        start_pos = 1
        while True:
            query = (
                f"SELECT * FROM JournalEntry "
                f"WHERE TxnDate >= '{start_date.isoformat()}' "
                f"AND TxnDate <= '{end_date.isoformat()}' "
                f"STARTPOSITION {start_pos} MAXRESULTS {self.PAGE_SIZE}"
            )
            # NOTE: Actual HTTP call implemented in production via httpx async client
            raw_entries = self._execute_query(query)

            if not raw_entries:
                break

            for raw in raw_entries:
                yield self._parse_entry(raw)

            if len(raw_entries) < self.PAGE_SIZE:
                break

            start_pos += self.PAGE_SIZE

    def _execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Executes a QBO query and returns raw response items.
        In production: async httpx call with retry logic and rate-limit handling.
        """
        logger.debug("QBO query: %s", query)
        # Production implementation: httpx.AsyncClient POST to self._query_url()
        return []

    def _parse_entry(self, raw: Dict[str, Any]) -> QBOJournalEntry:
        """Parse a raw QBO API response dict into a typed QBOJournalEntry."""
        lines = []
        for line in raw.get("Line", []):
            detail = line.get("JournalEntryLineDetail", {})
            lines.append(QBOJournalEntryLine(
                id=line.get("Id", ""),
                description=line.get("Description"),
                amount=Decimal(str(line.get("Amount", "0"))),
                posting_type=detail.get("PostingType", "Debit"),
                account_ref=detail.get("AccountRef", {}).get("value", ""),
                account_name=detail.get("AccountRef", {}).get("name", ""),
                class_ref=detail.get("ClassRef", {}).get("value") if detail.get("ClassRef") else None,
                department_ref=detail.get("DepartmentRef", {}).get("value") if detail.get("DepartmentRef") else None,
            ))

        return QBOJournalEntry(
            id=raw["Id"],
            doc_number=raw.get("DocNumber"),
            txn_date=date.fromisoformat(raw["TxnDate"]),
            create_time=datetime.fromisoformat(raw["MetaData"]["CreateTime"].rstrip("Z")),
            last_updated_time=datetime.fromisoformat(raw["MetaData"]["LastUpdatedTime"].rstrip("Z")),
            private_note=raw.get("PrivateNote"),
            lines=lines,
        )

    def normalize_to_rtcm(self, entry: QBOJournalEntry) -> List[Dict[str, Any]]:
        """
        Converts a QBOJournalEntry to a list of RTCM canonical journal entry dicts.
        Each line in QBO maps to one RTCM record.
        """
        normalized = []
        for line in entry.lines:
            debit = line.amount if line.posting_type == "Debit" else Decimal("0")
            credit = line.amount if line.posting_type == "Credit" else Decimal("0")

            normalized.append({
                "tenant_id": self.tenant_id,
                "entity_id": self.entity_id,
                "source_system": "quickbooks",
                "source_je_id": f"{entry.id}-{line.id}",
                "posting_date": entry.txn_date.isoformat(),
                "entry_datetime": entry.create_time.isoformat(),
                "period": f"{entry.txn_date.year}-{entry.txn_date.month:02d}",
                "posted_by_user_id": entry.created_by_id or "unknown",
                "approved_by_user_id": None,  # QBO does not expose approver
                "account_code": line.account_ref,
                "account_type": None,  # Resolved via chart of accounts lookup
                "debit_amount": str(debit),
                "credit_amount": str(credit),
                "description": line.description or entry.private_note or "",
                "reference": entry.doc_number,
                "cost_center": line.department_ref,
                "intercompany_flag": False,  # Determined via entity mapping rules
                "ic_counterparty_entity_id": None,
                "metadata": {
                    "qbo_je_id": entry.id,
                    "qbo_adjusted": entry.adjusted,
                    "class_ref": line.class_ref,
                },
            })

        return normalized
