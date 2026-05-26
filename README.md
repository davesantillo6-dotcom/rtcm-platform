## The Problem

The United States has a significant and documented gap in financial reporting integrity at the mid-market level. While large public companies subject to Sarbanes-Oxley (SOX) Section 404 deploy extensive internal control frameworks monitored by Big 4 audit firms, the estimated **28 million U.S. small and mid-sized businesses** — including thousands of private equity-backed companies — operate with little to no real-time visibility into control failures.

The consequences are measurable:
- The ACFE estimates U.S. organizations lose **5% of annual revenue** to fraud, totaling over **$4.7 trillion annually**
- The SEC imposed **$6.4 billion in enforcement actions** in FY2023 alone, a significant portion tied to control failures at non-accelerated filers
- Financial restatements at private and mid-market companies increased **18% from 2019–2023**, driven primarily by control deficiencies that manual quarterly reviews failed to detect
- Private equity portfolio companies — which collectively employ millions of Americans — lack the infrastructure to detect control breakdowns between annual audits

Existing solutions are designed for large enterprises (SAP GRC, AuditBoard, Workiva) and carry price points and implementation costs that make them inaccessible to mid-market organizations. No purpose-built, affordable, cloud-native platform currently serves this segment.

**RTCM exists to close that gap.**

---

## The Solution

RTCM is a cloud-native SaaS platform that provides **continuous, automated monitoring of internal controls** — the financial checks and processes that ensure accurate reporting — for companies that currently rely on periodic, manual review.

The platform ingests data from general ledger systems (QuickBooks, Sage, NetSuite, SAP B1), applies rule-based and ML-augmented control tests, and surfaces anomalies, exceptions, and control failures to finance leaders in real time — not months later during an annual audit.

### Core Capabilities

| Module | Description |
|--------|-------------|
| **GL Monitor** | Continuous journal entry surveillance: unusual posting times, round-dollar entries, override detection, segregation of duties violations |
| **Account Reconciliation Engine** | Automated month-end reconciliation with variance flagging and aging analysis |
| **Intercompany Control Suite** | Multi-entity elimination monitoring and intercompany out-of-balance detection |
| **User Access & Segregation Monitor** | Real-time SoD (Segregation of Duties) conflict detection across ERP roles |
| **Narrative Intelligence** | AI-assisted control narrative generation and documentation — maps actual system behavior to stated control language |
| **Audit Trail Manager** | Immutable log management with exception tagging for auditor export |
| **Executive Dashboard** | CFO/Audit Committee-facing risk heatmaps, trend analysis, and period-over-period comparison |

---

## Architecture Overview
┌─────────────────────────────────────────────────────────────────┐
│                        RTCM Platform                            │
├─────────────────┬───────────────────┬───────────────────────────┤
│   Data Layer    │  Processing Layer  │     Presentation Layer    │
├─────────────────┼───────────────────┼───────────────────────────┤
│                 │                   │                           │
│  ERP Connectors │  Control Engine   │  Web Dashboard (React)    │
│  ─ QuickBooks   │  ─ Rule Evaluator │  ─ CFO View               │
│  ─ NetSuite     │  ─ ML Anomaly Det.│  ─ Controller View        │
│  ─ Sage Intacct │  ─ SoD Analyzer   │  ─ Auditor Export View    │
│  ─ SAP B1       │  ─ Threshold Mgr  │                           │
│  ─ Generic CSV  │                   │  API Layer (REST/GraphQL)  │
│                 │  Alert Engine     │  ─ Webhook notifications   │
│  Data Warehouse │  ─ Priority Queue │  ─ Third-party integr.    │
│  (PostgreSQL +  │  ─ Routing Rules  │  ─ Audit firm data export  │
│   TimescaleDB)  │  ─ Notification   │                           │
│                 │    Dispatcher     │                           │
└─────────────────┴───────────────────┴───────────────────────────┘

See [`/docs/architecture.md`](docs/architecture.md) for full technical specification.

---

## Target Market

RTCM is purpose-built for:

- **Private equity portfolio companies** — PE-backed businesses that need audit-ready control documentation across multiple entities and fiscal years
- **Mid-market private companies** ($10M–$500M revenue) preparing for an IPO, acquisition, or first external audit
- **Multi-entity consolidators** — regional distributors, service platforms, and roll-up organizations managing 3–20 legal entities under a single finance team
- **CPA firms and outsourced CFO providers** — firms serving mid-market clients who want automated monitoring delivered as a managed service

---

## Why This Matters Nationally

The integrity of U.S. financial markets depends on accurate financial reporting at every level of the economy — not just at Fortune 500 companies. Mid-market businesses represent the backbone of the U.S. economy:

- **48% of U.S. GDP** is generated by companies with fewer than 500 employees (SBA, 2023)
- **61.7 million Americans** are employed by small and mid-sized businesses
- Private equity-backed companies alone employ an estimated **12 million Americans** across thousands of portfolio companies

When control failures go undetected at these companies, the downstream consequences include investor losses, lender defaults, employee layoffs, tax revenue shortfalls, and erosion of confidence in private capital markets. RTCM addresses this as infrastructure — not a product — for a healthier national financial ecosystem.

---

## Technical Stack

| Layer | Technology |
|-------|-----------|
| Backend API | Python (FastAPI) |
| Data Processing | Apache Kafka, dbt, Pandas |
| Database | PostgreSQL, TimescaleDB (time-series) |
| ML/Anomaly Detection | scikit-learn, Isolation Forest, LSTM |
| Frontend | React + TypeScript, Recharts |
| Infrastructure | AWS (ECS, RDS, S3, CloudWatch) |
| Auth | Auth0 (RBAC with entity-level scoping) |
| CI/CD | GitHub Actions |

---

## Repository Structure
rtcm-platform/
├── docs/
│   ├── architecture.md          # Full system architecture
│   ├── data-model.md            # Entity-relationship diagram and schema
│   ├── api-spec.md              # REST API specification
│   ├── control-library.md       # Control test definitions and COSO mapping
│   └── roadmap.md               # Development phases and milestones
├── src/
│   ├── api/                     # FastAPI application
│   ├── core/
│   │   ├── control_engine/      # Rule evaluation and control testing
│   │   ├── anomaly_detection/   # ML-based GL surveillance
│   │   └── sod_analyzer/        # Segregation of duties analysis
│   ├── integrations/
│   │   ├── quickbooks/          # QuickBooks Online connector
│   │   ├── netsuite/            # NetSuite SuiteAnalytics connector
│   │   └── sage/                # Sage Intacct connector
│   └── ui/                      # React frontend application
├── tests/
│   ├── unit/
│   └── integration/
└── .github/
└── workflows/               # CI/CD pipeline definitions

---

## Development Roadmap

See [`/docs/roadmap.md`](docs/roadmap.md) for full milestone detail.

**Phase 1 — Foundation (Q3 2026):** Core data ingestion, GL Monitor, basic dashboard
**Phase 2 — Control Engine (Q4 2026):** Full control library, SoD analyzer, reconciliation engine
**Phase 3 — Intelligence Layer (Q1 2027):** ML anomaly detection, Narrative Intelligence module
**Phase 4 — Market Launch (Q2 2027):** Pilot client onboarding, CPA firm partnerships

---

## Founder

**David Santillo, CPA**
Director of Accounting — United Flow Technologies (UFT)
*Former Big 4 audit experience | 10+ years U.S. GAAP financial reporting and multi-entity consolidation*

David designed RTCM from direct experience managing internal controls across a 10+ entity, private equity-backed platform. The control gaps RTCM addresses are not theoretical — they are problems he has observed and worked around throughout his career in mid-market finance.

---

## Contact & Partnerships

For pilot program inquiries, CPA firm partnerships, or investor discussions:
📧 david@rtcmplatform.com
🌐 rtcmplatform.com *(coming soon)*

---

*RTCM is proprietary software under active development. All rights reserved. © 2026 RTCM LLC.*
