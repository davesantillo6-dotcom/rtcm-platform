# RTCM Platform — Technical Architecture

**Document Version:** 1.0
**Last Updated:** May 2026
**Author:** David Santillo, CPA — Founder, RTCM LLC
**Status:** Design Phase — Pre-Development

---

## 1. Overview

This document describes the technical architecture of the Real-Time Control Monitoring (RTCM) platform. RTCM is designed as a cloud-native, multi-tenant SaaS application that ingests financial transaction data from enterprise resource planning (ERP) systems, evaluates that data against a library of internal control tests, and delivers real-time alerting and reporting to finance leaders and external auditors.

The architecture prioritizes:
- **Security and data integrity** — financial data requires immutable audit trails and strict access controls
- **Multi-tenancy with entity isolation** — each client organization and its subsidiary entities must be logically separated
- **Horizontal scalability** — GL transaction volumes vary widely; the processing layer must scale without degrading performance
- **Extensibility** — new ERP connectors and control tests must be addable without core system changes
- **Auditability of the platform itself** — metadata about every control evaluation must be retained for regulatory review
- 
---

## 2. High-Level Architecture

RTCM follows an event-driven microservices architecture organized into four primary layers:

- **Ingestion Layer** — ERP Connectors, Schema Normalization, Data Validation, Kafka Event Bus
- **Processing Layer** — Control Evaluation Engine, Anomaly Detection, SoD Analyzer, Reconciliation Engine, Intercompany Monitor
- **Storage Layer** — PostgreSQL, TimescaleDB, S3, Redis
- **Presentation Layer** — REST API (FastAPI), React Dashboard, Webhook Dispatcher, Audit Export Service

---

## 3. Ingestion Layer

### 3.1 ERP Connectors

| Connector | Integration Method | Data Extracted |
|-----------|-------------------|---------------|
| QuickBooks Online | OAuth 2.0 REST API | JE, Chart of Accounts, Vendors, AR/AP aging |
| NetSuite | SuiteAnalytics Connect (JDBC/ODBC) | Full GL, subsidiary data, intercompany transactions |
| Sage Intacct | XML API / REST | Multi-entity GL, allocations, consolidation data |
| SAP Business One | Service Layer REST API | GL entries, business partners, inventory movements |
| Generic CSV | SFTP / Secure Upload | Flat-file journal entry data (standardized template) |

### 3.2 Canonical Schema

All source data is normalized to the RTCM canonical journal entry schema before entering the processing layer:

- rtcm_je_id, tenant_id, entity_id
- source_system, source_je_id
- posting_date, created_datetime, period (YYYY-MM)
- posted_by_user_id, approved_by_user_id
- account_code, account_type, debit_amount, credit_amount
- description, reference, cost_center
- intercompany_flag, intercompany_counterparty_entity_id

### 3.3 Data Validation

Every record is validated against:
- **Debit/credit balance** — each journal entry must balance to zero
- **Period validity** — no entries to closed periods without override flag
- **User attribution** — posting user must exist in the entity's user registry
- **Account existence** — account code must exist in the current chart of accounts
- **Duplicate detection** — source JE ID uniqueness per entity per source system

---

## 4. Processing Layer

### 4.1 Control Evaluation Engine

The Control Evaluation Engine evaluates each normalized transaction against a library of parameterized control tests.

| ID | Control Name | Category | Trigger |
|----|-------------|----------|---------|
| GL-001 | After-hours journal entry | Control Activities | JE posted outside 6am–8pm |
| GL-002 | Round dollar entry — high value | Control Activities | Exact round number > $10,000 |
| GL-003 | Self-approval | Control Activities | Posted-by = Approved-by |
| GL-004 | Backdated entry — prior period | Control Activities | Posting date < period open by > 5 days |
| GL-005 | Top-side adjustment without support | Control Activities | JE to equity without memo |
| SOD-001 | AP entry + AP payment — same user | Control Activities | User has conflicting AP roles |
| REC-001 | Account reconciliation overdue | Monitoring | No recon submitted > 15 days post-close |
| IC-001 | Intercompany out of balance | Control Activities | IC pair imbalance > $500 |

Full control library: /docs/control-library.md

### 4.2 Anomaly Detection Service

- **Isolation Forest** — unsupervised detection of statistically unusual journal entries
- **LSTM Time-Series Model** — account balance forecasting with deviation alerts
- **Benford's Law Analysis** — first-digit frequency analysis on GL amounts
- **Velocity Monitoring** — flags users with transaction volumes 2+ standard deviations from baseline

### 4.3 Segregation of Duties (SoD) Analyzer

1. Ingests user-role matrix from source ERP
2. Maps each role to functional permission set
3. Evaluates every user against 150+ SoD conflict rules
4. Produces conflict matrix with severity classifications and remediations

### 4.4 Reconciliation Engine

- Tracks which accounts require reconciliation by type and balance threshold
- Monitors submission status and aging
- Validates completeness (supporting documents, open item explanations)
- Flags stale reconciling items per configurable aging thresholds

### 4.5 Intercompany Monitor

- Maintains real-time map of intercompany transaction pairs across all entities
- Detects out-of-balance positions as transactions post (not at period-end)
- Validates elimination rule mapping for all IC transactions
- Produces pre-close IC reconciliation report per consolidation entity

---

## 5. Storage Layer

### 5.1 Design Principles

- **Tenant isolation via Row-Level Security (RLS)** — PostgreSQL RLS policies prevent cross-tenant data access
- **Entity-level scoping** — every record carries tenant_id and entity_id
- **Immutable audit log** — control_results and alert_events are append-only
- **Data retention** — raw GL data retained 7 years; control results retained indefinitely

### 5.2 Core Tables

- **tenants** — client organizations (top-level multi-tenancy)
- **entities** — legal entities within a tenant, with parent_entity_id for consolidation hierarchy
- **journal_entries** — normalized GL transactions, partitioned by posting_date
- **control_results** — append-only evaluation results with disposition tracking
- **alerts** — user-facing alerts with status, assignment, and notes
- **reconciliations** — account reconciliation submissions and approval status

Full schema: /docs/data-model.md

---

## 6. Security Architecture

- **Auth0** — identity management with SAML/SSO and MFA enforcement
- **RBAC** — four roles: Admin, Controller, Reviewer, Auditor (read-only)
- **Entity-scoped permissions** — users may have different roles per entity
- **AES-256 encryption at rest**, TLS 1.3 in transit
- **AWS Secrets Manager** — no plaintext credential storage
- **SOC 2 Type II** targeted for Q2 2027

---

## 7. Infrastructure (AWS)

| Component | AWS Service |
|-----------|------------|
| Application containers | ECS Fargate |
| Relational database | RDS PostgreSQL (Multi-AZ) |
| Message queue | Amazon MSK (Managed Kafka) |
| Caching | ElastiCache (Redis) |
| Object storage | S3 |
| Secrets management | AWS Secrets Manager |
| Monitoring | CloudWatch + Grafana |
| CDN | CloudFront |

---

## 8. API Design

Base URL: https://api.rtcmplatform.com/v1

Key endpoint groups:
- /entities — entity management and hierarchy
- /journal-entries — GL data ingestion and query
- /controls — control library and results
- /alerts — alert retrieval and disposition
- /reports — dashboard data and audit packages

Full specification: /docs/api-spec.md

---

*This architecture document is a living specification updated as development progresses.*
