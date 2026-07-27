# RTCM Platform

**Real-Time Control Monitoring for U.S. Mid-Market and Private Equity-Backed Organizations**

Built by David Santillo, CPA | Founder, RTCM Platform LLC  
[rtcmplatform.com](https://www.rtcmplatform.com) | david@rtcmplatform.com

---

## Development Status

| Milestone | Status |
|-----------|--------|
| LLC formation and EIN |  Complete — May 26, 2026 |
| Initial platform architecture |  Complete — May 26, 2026 |
| Control evaluation engine (GL-001, GL-002, GL-003) |  Complete — May 26, 2026 |
| QuickBooks Online connector |  Complete — May 26, 2026 |
| Business model and go-to-market strategy |  Complete — June 21, 2026 |
| Extended GL controls (GL-004, GL-005) |  Complete — June 28, 2026 |
| Unit test suite — extended GL controls |  Complete — July 5, 2026 |
| SOD controls (SOD-001, SOD-002) |  Complete — July 2026 |
| Intercompany controls (IC-001, IC-002) |  Planned — September 2026 |
| Reconciliation controls (REC-001, REC-002) |  Planned — November 2026 |
| Pilot program launch |  Planned — Q4 2026 |
| General availability |  Planned — Q2 2027 |

---

## The Problem

The United States has a significant and documented gap in financial reporting integrity at the mid-market level. While large public companies subject to Sarbanes-Oxley (SOX) Section 404 deploy extensive internal control frameworks monitored by Big 4 audit firms, the estimated 28 million U.S. small and mid-sized businesses — including thousands of private equity-backed companies — operate with little to no real-time visibility into control failures.

The consequences are measurable:

- The ACFE estimates U.S. organizations lose 5% of annual revenue to fraud
- Private equity portfolio companies — which collectively employ millions of Americans — lack the infrastructure to detect control breakdowns between annual audits
- Existing solutions (SAP GRC, AuditBoard, Workiva) are designed for large enterprises and carry price points inaccessible to mid-market organizations

**RTCM exists to close that gap.**

---

## The Solution

RTCM is a cloud-native SaaS platform that provides continuous, automated monitoring of internal controls for companies that currently rely on periodic, manual review.

The platform ingests data from general ledger systems (QuickBooks Online, NetSuite, Sage Intacct, SAP B1), applies rule-based control tests mapped to the COSO Internal Control — Integrated Framework (2013), and surfaces control failures to finance leaders in real time — not months later during an annual audit.

### Core Modules

| Module | Description |
|--------|-------------|
| **GL Monitor** | Continuous journal entry surveillance: self-approval, backdated entries, after-hours posting, round-dollar entries, unsupported top-side entries |
| **SoD Analyzer** | Real-time Segregation of Duties conflict detection across ERP user roles |
| **Reconciliation Engine** | Automated month-end reconciliation tracking with overdue flagging and open item analysis |
| **Intercompany Monitor** | Multi-entity intercompany balance monitoring and elimination mapping verification |
| **Executive Dashboard** | CFO and Controller-facing control health dashboard with entity-level status, real-time alert feed, 90-day trend analysis, and period-close checklist |
| **Audit Trail Manager** | Immutable exception log with auditor export capability |

---

## Implemented Controls — Current Build

### GL Monitoring
| Control ID | Name | Severity | Status |
|------------|------|----------|--------|
| GL-001 | After-hours entry | High |  Implemented |
| GL-002 | Round dollar entry | Medium |  Implemented |
| GL-003 | Self-approval | Critical |  Implemented |
| GL-004 | Backdated entry to prior period | High |  Implemented |
| GL-005 | Large unsupported top-side entry | Critical |  Implemented |

### Segregation of Duties
| Control ID | Name | Severity | Status |
|------------|------|----------|--------|
| SOD-001 | AP entry + payment release, same user | Critical |  In progress |
| SOD-002 | AR posting + cash receipt, same user | Critical |  In progress |

### Intercompany
| Control ID | Name | Severity | Status |
|------------|------|----------|--------|
| IC-001 | Intercompany pair out of balance | Critical |  Planned — Q4 2026 |
| IC-002 | No elimination mapping | High |  Planned — Q4 2026 |

### Reconciliation
| Control ID | Name | Severity | Status |
|------------|------|----------|--------|
| REC-001 | Account reconciliation overdue | High |  Planned — Q4 2026 |
| REC-002 | Unexplained reconciling item | High |  Planned — Q4 2026 |

---

## Architecture Overview
Full architecture specification: [docs/architecture.md](docs/architecture.md)

## Target Market

RTCM is purpose-built for three customer segments:

**1. Private Equity Portfolio Companies**
PE firms managing multiple portfolio companies need real-time control visibility across their entire portfolio — not a once-a-year audit finding. RTCM provides a consolidated dashboard showing control health across every entity simultaneously.

**2. Mid-Market Companies Preparing for Audit or Transaction**
Companies approaching their first external audit, a strategic sale, or an IPO need to demonstrate internal control maturity quickly. RTCM compresses the timeline for achieving audit-ready control documentation from months to weeks.

**3. CPA Firms and Outsourced CFO Providers**
Regional CPA firms serving mid-market clients can offer RTCM as a managed service through the white-label partner program — creating a recurring revenue stream while expanding RTCM's reach.

Full target market analysis: [docs/business-model.md](docs/business-model.md)

---

## Why This Matters Nationally

The integrity of U.S. financial markets depends on accurate financial reporting at every level of the economy — not just at Fortune 500 companies. Mid-market businesses represent the backbone of the U.S. economy:

- 43.5% of U.S. GDP is generated by small and mid-sized businesses (SBA Office of Advocacy, 2026)
- 62.3 million Americans are employed by small and mid-sized businesses
- Private equity-backed companies alone employ an estimated 12 million Americans across thousands of portfolio companies

When control failures go undetected at these companies, the downstream consequences include investor losses, lender defaults, employee layoffs, and erosion of confidence in private capital markets.

---

## Development Roadmap

| Phase | Timeline | Key Deliverables |
|-------|----------|-----------------|
| Phase 1 | Q3 2026 | QuickBooks connector, GL controls (GL-001 through GL-005), SoD controls, unit test suite |
| Phase 2 | Q4 2026 | IC controls, REC controls, pilot program launch (2–3 clients) |
| Phase 3 | Q1 2027 | NetSuite connector, full web dashboard, alert notification system |
| Phase 4 | Q2 2027 | General availability, CPA firm white-label program, first commercial revenue |

Full roadmap with 36 specific milestones: [docs/roadmap.md](docs/roadmap.md)

---

## Founder

**David Santillo, CPA**  
Founder, RTCM Platform LLC  
Director of Accounting — United Flow Technologies

David designed RTCM from direct experience managing internal controls across a 20+ entity, private equity-backed platform. The control gaps RTCM addresses are not theoretical — they are problems he has identified, documented, and worked to remediate throughout his career spanning Big 4 audit practice and industry leadership roles in mid-market finance.

---

## Early Access — Pilot Program

RTCM is currently accepting applications for the pilot program launching Q4 2026. Pilot participants receive full Professional-tier access at no cost in exchange for structured product feedback.

**Apply:** [rtcmplatform.com](https://www.rtcmplatform.com) → Request a Demo  
**Contact:** david@rtcmplatform.com

---

*RTCM Platform LLC — Texas LLC — EIN 42-2778352*  
*© 2026 RTCM Platform LLC. All rights reserved.*




