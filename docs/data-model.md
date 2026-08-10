Copy everything below this line and paste it into GitHub:

# RTCM Platform — Data Model

**Document Version:** 1.0
**Last Updated:** May 2026
**Database:** PostgreSQL 15 with TimescaleDB extension

---

## Entity Relationship Overview

- tenants (1) — (many) entities
- tenants (1) — (many) users
- entities (1) — (many) journal_entries
- entities (1) — (many) control_results
- entities (1) — (many) alerts
- entities (1) — (many) reconciliations
- entities (1) — (0..1) parent entity (self-referential, for consolidation hierarchy)
- users — user_entity_permissions (entity-level access scoping)

---

## Core Tables

### `tenants`
Client organizations — top-level multi-tenancy unit.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| tenant_id | UUID | PK | Unique identifier |
| name | VARCHAR(255) | NOT NULL | Organization name |
| subscription_tier | VARCHAR(50) | | 'starter', 'professional', 'enterprise' |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | Onboarding date |
| is_active | BOOLEAN | DEFAULT TRUE | Soft delete flag |
| settings | JSONB | | Tenant-level configuration |

---

### `entities`
Legal entities within a tenant organization (subsidiaries, divisions).

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| entity_id | UUID | PK | Unique identifier |
| tenant_id | UUID | FK → tenants | Owning tenant |
| name | VARCHAR(255) | NOT NULL | Legal entity name |
| ein | VARCHAR(20) | ENCRYPTED | Employer Identification Number |
| fiscal_year_end | DATE | | e.g., 2026-12-31 |
| reporting_currency | CHAR(3) | DEFAULT 'USD' | ISO currency code |
| parent_entity_id | UUID | FK → entities (nullable) | Parent for consolidation hierarchy |
| erp_source | VARCHAR(50) | | 'quickbooks', 'netsuite', 'sage', 'sapb1', 'csv' |
| erp_connection_id | UUID | FK → erp_connections | Active ERP credential reference |
| period_close_day | INTEGER | DEFAULT 10 | Day of month period is due to close |
| is_active | BOOLEAN | DEFAULT TRUE | |

---

### `journal_entries`
Normalized GL transactions — primary data table. Partitioned by posting_date.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| rtcm_je_id | UUID | PK | RTCM-assigned identifier |
| tenant_id | UUID | FK → tenants | |
| entity_id | UUID | FK → entities | |
| source_system | VARCHAR(50) | NOT NULL | Origin ERP system |
| source_je_id | VARCHAR(100) | NOT NULL | Source system's native ID |
| posting_date | DATE | NOT NULL | GL posting date (partition key) |
| entry_datetime | TIMESTAMPTZ | | When entry was created in source |
| period | CHAR(7) | NOT NULL | 'YYYY-MM' |
| posted_by_user_id | VARCHAR(100) | | Source system user ID |
| approved_by_user_id | VARCHAR(100) | | Nullable if no approval workflow |
| account_code | VARCHAR(50) | NOT NULL | |
| account_type | VARCHAR(20) | | 'asset', 'liability', 'equity', 'revenue', 'expense', 'cogs' |
| debit_amount | NUMERIC(18,2) | DEFAULT 0 | |
| credit_amount | NUMERIC(18,2) | DEFAULT 0 | |
| net_amount | NUMERIC(18,2) | GENERATED | debit_amount - credit_amount |
| currency | CHAR(3) | DEFAULT 'USD' | |
| description | TEXT | | JE memo/description |
| reference | VARCHAR(100) | | Invoice #, check #, etc. |
| cost_center | VARCHAR(50) | | |
| intercompany_flag | BOOLEAN | DEFAULT FALSE | |
| ic_counterparty_entity_id | UUID | FK → entities (nullable) | |
| metadata | JSONB | | Source-specific additional fields |
| ingested_at | TIMESTAMPTZ | DEFAULT NOW() | When RTCM received the record |

**Indexes:**
- (tenant_id, entity_id, period) — primary query pattern
- (tenant_id, entity_id, posted_by_user_id) — user activity queries
- (tenant_id, entity_id, account_code, posting_date) — account balance queries
- (intercompany_flag, ic_counterparty_entity_id) — IC reconciliation

---

### `control_results`
Results of every control evaluation. Append-only — no updates permitted.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| result_id | UUID | PK | |
| tenant_id | UUID | FK → tenants | |
| entity_id | UUID | FK → entities | |
| control_id | VARCHAR(20) | FK → controls | e.g., 'GL-003' |
| evaluated_at | TIMESTAMPTZ | DEFAULT NOW() | |
| result | VARCHAR(20) | CHECK IN ('pass','fail','exception','n/a') | |
| severity | VARCHAR(20) | | Inherited from control at time of eval |
| reference_type | VARCHAR(50) | | 'journal_entry', 'user', 'reconciliation', etc. |
| reference_id | UUID | | FK to triggering record |
| details | JSONB | | Machine-readable exception detail |
| human_detail | TEXT | | Readable exception description |
| alert_generated | BOOLEAN | DEFAULT FALSE | |

---

### `alerts`
User-facing alert records derived from control failures.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| alert_id | UUID | PK | |
| tenant_id | UUID | FK → tenants | |
| entity_id | UUID | FK → entities | |
| result_id | UUID | FK → control_results | Source control failure |
| control_id | VARCHAR(20) | | |
| severity | VARCHAR(20) | | |
| status | VARCHAR(30) | DEFAULT 'open' | 'open', 'in_review', 'remediated', 'accepted_risk', 'false_positive' |
| assigned_to | UUID | FK → users (nullable) | |
| opened_at | TIMESTAMPTZ | DEFAULT NOW() | |
| closed_at | TIMESTAMPTZ | | |
| notes | TEXT | | Reviewer commentary |
| disposition_reason | TEXT | | Required when closing |

---

### `reconciliations`
Account reconciliation submissions and status.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| recon_id | UUID | PK | |
| tenant_id | UUID | FK → tenants | |
| entity_id | UUID | FK → entities | |
| account_code | VARCHAR(50) | NOT NULL | |
| period | CHAR(7) | NOT NULL | |
| status | VARCHAR(30) | | 'not_started', 'in_progress', 'submitted', 'approved', 'overdue' |
| gl_balance | NUMERIC(18,2) | | Balance per GL |
| reconciled_balance | NUMERIC(18,2) | | Balance per reconciliation |
| variance | NUMERIC(18,2) | GENERATED | gl_balance - reconciled_balance |
| preparer_user_id | UUID | FK → users | |
| reviewer_user_id | UUID | FK → users | |
| submitted_at | TIMESTAMPTZ | | |
| approved_at | TIMESTAMPTZ | | |
| has_open_items | BOOLEAN | DEFAULT FALSE | |
| notes | TEXT | | |

---

## Row-Level Security Policies

All core tables implement PostgreSQL Row-Level Security to enforce tenant and entity isolation at the database layer:

```sql
ALTER TABLE journal_entries ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON journal_entries
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

CREATE POLICY entity_scope ON journal_entries
    USING (
        entity_id IN (
            SELECT entity_id FROM user_entity_permissions
            WHERE user_id = current_setting('app.current_user_id')::UUID
        )
    );
```
---

*Full DDL scripts are located in /scripts/migrations/. Schema migrations are managed with Alembic.*
