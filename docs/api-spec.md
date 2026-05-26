Copy everything below this line and paste it into GitHub:

# RTCM Platform — REST API Specification

**Version:** v1
**Base URL:** https://api.rtcmplatform.com/v1
**Authentication:** Bearer token (JWT, issued via Auth0)
**Format:** JSON
**Last Updated:** May 2026

---

## Authentication

All requests require a valid JWT in the Authorization header:
Authorization: Bearer <jwt_token>

Tokens are scoped to a tenant_id and a set of entity-level permissions. The API enforces tenant isolation at the middleware layer — no cross-tenant data access is possible.

---

## Endpoints

### Entities

#### GET /entities
Returns all entities the authenticated user has access to within their tenant.

**Response:**
```json
{
  "entities": [
    {
      "entity_id": "uuid",
      "name": "UFT West LLC",
      "fiscal_year_end": "2026-12-31",
      "erp_source": "quickbooks",
      "parent_entity_id": "uuid or null",
      "is_active": true
    }
  ]
}
```

---

### Journal Entries

#### GET /journal-entries
Query normalized GL data for one or more entities.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| entity_id | UUID | Yes | Target entity |
| period | string | No | Filter by period (YYYY-MM) |
| account_code | string | No | Filter by account |
| posted_by | string | No | Filter by user ID |
| intercompany_only | boolean | No | Return only IC transactions |
| from_date | date | No | Posting date range start |
| to_date | date | No | Posting date range end |
| page | integer | No | Pagination (default 1) |
| page_size | integer | No | Results per page (max 1000) |

**Response:**
```json
{
  "total": 1482,
  "page": 1,
  "page_size": 100,
  "journal_entries": [
    {
      "rtcm_je_id": "uuid",
      "source_je_id": "JE-00412",
      "posting_date": "2026-05-15",
      "period": "2026-05",
      "posted_by_user_id": "user123",
      "account_code": "5100",
      "account_type": "expense",
      "debit_amount": 15000.00,
      "credit_amount": 0.00,
      "description": "May consulting services",
      "intercompany_flag": false
    }
  ]
}
```

#### POST /journal-entries/ingest
Manually ingest journal entries via CSV upload or JSON array (for generic CSV connector).

---

### Controls

#### GET /controls
Returns the full control library available to the tenant.

**Response:**
```json
{
  "controls": [
    {
      "control_id": "GL-003",
      "name": "Self-approval — posting user equals approver",
      "coso_category": "Control Activities",
      "type": "preventive",
      "trigger": "transaction",
      "severity": "critical",
      "is_enabled": true,
      "tenant_parameters": {
        "override_severity": null
      }
    }
  ]
}
```

#### GET /controls/{control_id}/results
Returns historical evaluation results for a specific control.

**Query Parameters:** entity_id, period, result (pass/fail/exception), from_date, to_date

---

### Alerts

#### GET /alerts
Returns open and closed alerts for the authenticated user's accessible entities.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| entity_id | UUID | Filter by entity |
| status | string | 'open', 'in_review', 'closed' |
| severity | string | 'critical', 'high', 'medium', 'low' |
| control_id | string | Filter by specific control |
| assigned_to | UUID | Filter by assigned reviewer |
| period | string | Filter by GL period |

**Response:**
```json
{
  "total": 14,
  "alerts": [
    {
      "alert_id": "uuid",
      "control_id": "GL-003",
      "control_name": "Self-approval",
      "entity_name": "UFT West LLC",
      "severity": "critical",
      "status": "open",
      "opened_at": "2026-05-16T02:14:33Z",
      "human_detail": "User jsmith posted and self-approved JE-00412 ($15,000 expense) at 2:14 AM on May 16.",
      "reference_type": "journal_entry",
      "reference_id": "uuid"
    }
  ]
}
```

#### PATCH /alerts/{alert_id}
Update alert status and add reviewer notes.

**Request Body:**
```json
{
  "status": "remediated",
  "notes": "Spoke with jsmith — approval workflow misconfigured. IT corrected SoD settings on 5/17.",
  "disposition_reason": "Control deficiency remediated. No financial statement impact."
}
```

---

### Reports

#### GET /reports/dashboard
Returns aggregated dashboard data: alert counts by severity, control pass rates, period trend.

#### GET /reports/audit-package
Generates an audit-ready export package for a specified entity and period, including:
- Control test results summary
- All exceptions with disposition notes
- Journal entry population with anomaly flags
- Reconciliation status report
- SoD conflict matrix

**Query Parameters:** entity_id (required), period (required), format ('json' or 'xlsx')

#### GET /reports/intercompany
Returns intercompany reconciliation status for all entity pairs within the tenant.

---

### Webhooks

#### POST /webhooks
Register a webhook URL to receive real-time alert notifications.

**Request Body:**
```json
{
  "url": "https://your-system.com/rtcm-webhook",
  "events": ["alert.created", "alert.severity_escalated"],
  "entity_ids": ["uuid"],
  "severity_filter": ["critical", "high"]
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request — invalid parameters |
| 401 | Unauthorized — missing or invalid JWT |
| 403 | Forbidden — insufficient entity permissions |
| 404 | Not Found |
| 422 | Unprocessable Entity — validation failure |
| 429 | Rate Limited — 1,000 requests/minute per tenant |
| 500 | Internal Server Error |

---

## Rate Limits

- Standard: 1,000 requests/minute per tenant
- Ingestion endpoints: 10,000 records/minute per tenant
- Audit export: 10 requests/hour per tenant

---

*API versioning: Breaking changes will result in a new major version (v2). Minor additions are backward compatible within v1.*
