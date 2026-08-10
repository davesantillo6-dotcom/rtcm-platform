# RTCM Platform — Development Roadmap

**Document Version:** 1.0
**Last Updated:** May 2026
**Author:** David Santillo, CPA — Founder, RTCM LLC

---

## Overview

RTCM will be developed in four phases over approximately 18 months, progressing from foundational infrastructure through a controlled market launch. Each phase produces a testable, demonstrable increment of the platform.

The roadmap reflects a deliberate sequencing: build the data pipeline and core control engine before adding intelligence-layer features, and validate with real client data before scaling.

---

## Phase 1 — Foundation (Q3 2026, ~3 months)

**Goal:** A working data ingestion pipeline and basic GL monitoring dashboard with at least one ERP connector operational.

### Milestones

| ID | Milestone | Target Date |
|----|-----------|-------------|
| 1.1 | LLC formation, banking, and initial capitalization complete | July 2026 |
| 1.2 | Development environment established (AWS, CI/CD, GitHub Actions) | July 2026 |
| 1.3 | Canonical journal entry schema finalized and documented | July 2026 |
| 1.4 | QuickBooks Online connector — read-only GL extraction functional | August 2026 |
| 1.5 | Schema normalization service operational | August 2026 |
| 1.6 | PostgreSQL + TimescaleDB schema deployed (core tables) | August 2026 |
| 1.7 | GL-001 through GL-005 control tests implemented and tested | September 2026 |
| 1.8 | Basic web dashboard — alert list view, entity selector, period filter | September 2026 |
| 1.9 | Internal demo environment loaded with synthetic GL data | September 2026 |

### Deliverables
- Working QuickBooks to RTCM data pipeline (read-only)
- 5 operational GL control tests
- Functional internal dashboard (not customer-facing)
- Technical architecture documentation finalized

---

## Phase 2 — Control Engine (Q4 2026, ~3 months)

**Goal:** Full control library implemented, SoD analyzer operational, reconciliation tracking live, and first external pilot engagement initiated.

### Milestones

| ID | Milestone | Target Date |
|----|-----------|-------------|
| 2.1 | Full GL control library (20+ tests) implemented | October 2026 |
| 2.2 | SoD Analyzer — role ingestion and conflict detection operational | October 2026 |
| 2.3 | Reconciliation Engine — tracking and overdue alerting | November 2026 |
| 2.4 | Intercompany Monitor — basic out-of-balance detection | November 2026 |
| 2.5 | NetSuite connector — extraction and normalization | November 2026 |
| 2.6 | Multi-entity / multi-tenant data isolation validated | November 2026 |
| 2.7 | Alert management workflow (acknowledge, disposition, notes) | December 2026 |
| 2.8 | First external pilot client onboarded (PE-backed portfolio company) | December 2026 |
| 2.9 | Pilot feedback incorporated into product backlog | December 2026 |

### Deliverables
- Production-grade control engine with 20+ tests
- SoD analyzer covering 150+ conflict rules
- First external pilot engagement
- Pilot feedback report

---

## Phase 3 — Intelligence Layer (Q1 2027, ~3 months)

**Goal:** ML-based anomaly detection operational, Narrative Intelligence module in beta, and at least 3 pilot clients active.

### Milestones

| ID | Milestone | Target Date |
|----|-----------|-------------|
| 3.1 | Isolation Forest anomaly detection model trained and deployed | January 2027 |
| 3.2 | Benford's Law analysis module | January 2027 |
| 3.3 | LSTM account balance forecasting model (beta) | February 2027 |
| 3.4 | Narrative Intelligence module — control documentation generation (beta) | February 2027 |
| 3.5 | Audit Export Service — auditor-facing report package | February 2027 |
| 3.6 | Sage Intacct connector | March 2027 |
| 3.7 | SOC 2 Type II readiness assessment initiated | March 2027 |
| 3.8 | 3 active pilot clients | March 2027 |
| 3.9 | CPA firm partnership program framework established | March 2027 |

### Deliverables
- ML-powered anomaly detection in production
- Narrative Intelligence beta
- Auditor export package
- 3 pilot client relationships

---

## Phase 4 — Market Launch (Q2 2027, ~3 months)

**Goal:** General availability launch, active commercial relationships, and SOC 2 Type II certification in progress.

### Milestones

| ID | Milestone | Target Date |
|----|-----------|-------------|
| 4.1 | Self-service onboarding flow (no-touch setup for QuickBooks clients) | April 2027 |
| 4.2 | Pricing and subscription management infrastructure | April 2027 |
| 4.3 | First paid commercial customers | April 2027 |
| 4.4 | CPA firm white-label pilot (2 firms) | May 2027 |
| 4.5 | Marketing site and content launch | May 2027 |
| 4.6 | SOC 2 Type II audit fieldwork initiated | May 2027 |
| 4.7 | First Series Seed fundraise initiated (if appropriate) | June 2027 |
| 4.8 | 10+ paying customers | June 2027 |
| 4.9 | First full-time hire (engineering) | June 2027 |

### Deliverables
- General availability product
- First commercial revenue
- SOC 2 Type II in progress
- CPA firm channel established

---

## Long-Term Vision (2028 and beyond)

- **Regulatory Intelligence Layer** — auto-mapping of RTCM controls to SEC/PCAOB reporting requirements for companies preparing for public offerings
- **CFO Co-Pilot** — AI-assisted period-close management with predictive flagging of issues before they become material
- **Audit Firm Integration API** — direct data feed to Big 4 and regional firm audit platforms, reducing audit preparation time for mid-market clients
- **ESG/Non-Financial Controls** — extension of the control monitoring framework to environmental and social reporting data integrity

---

## Resource Plan

| Phase | Headcount (FTE equivalent) | Key Roles |
|-------|--------------------------|-----------|
| Phase 1 | 1–2 | Founder + contract backend engineer |
| Phase 2 | 2–3 | + contract frontend engineer |
| Phase 3 | 3–4 | + part-time data scientist |
| Phase 4 | 5–10 | First full-time hires (engineer + customer success) |

---

*This roadmap is subject to revision based on pilot client feedback, fundraising, and technical learnings. Last reviewed May 2026.*
