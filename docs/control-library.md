# RTCM Control Library

**Document Version:** 1.0
**Last Updated:** May 2026
**Framework Alignment:** COSO Internal Control — Integrated Framework (2013)

---

## Overview

The RTCM control library defines the set of automated control tests the platform evaluates against client financial data. Each control is mapped to the COSO framework component and is parameterized to allow tenant-specific thresholds.

Controls are classified by:
- **Type:** Preventive or Detective
- **Trigger:** Transaction-level (evaluated per JE), Periodic (evaluated on schedule), or Configuration (evaluated when system settings change)
- **Severity:** Critical, High, Medium, Low

---

## COSO Framework Mapping

RTCM controls map to all five components of the COSO Internal Control — Integrated Framework:

1. **Control Environment** — Tone at the top, organizational structure, competence
2. **Risk Assessment** — Identification and analysis of relevant risks
3. **Control Activities** — Policies and procedures to address risks (primary RTCM focus)
4. **Information & Communication** — Quality of information and communication channels
5. **Monitoring** — Ongoing and separate evaluations of internal control

---

## GL Monitoring Controls

| ID | Control Name | COSO | Type | Trigger | Severity | Threshold |
|----|-------------|------|------|---------|----------|-----------|
| GL-001 | After-hours journal entry | Control Activities | Detective | Transaction | High | Posts outside 6am–8pm local time |
| GL-002 | Round dollar entry — high value | Control Activities | Detective | Transaction | Medium | Exact round number > $10,000 |
| GL-003 | Self-approval — posting user equals approver | Control Activities | Preventive | Transaction | Critical | Posted-by = Approved-by |
| GL-004 | Backdated entry to prior period | Control Activities | Detective | Transaction | High | Posting date < period open date by > 5 days |
| GL-005 | Large unsupported top-side entry | Control Activities | Detective | Transaction | Critical | JE to equity/retained earnings > $25,000 without memo |
| GL-006 | High-value manual entry — no approval | Control Activities | Preventive | Transaction | Critical | Manual JE > $50,000 without approval workflow |
| GL-007 | Unusual account combination | Control Activities | Detective | Transaction | Medium | Debit/credit pairing outside defined normal pairs |
| GL-008 | Rapid sequential postings — same user | Control Activities | Detective | Transaction | Medium | Same user posts > 10 JEs within 30 minutes |
| GL-009 | Entry to inactive account | Control Activities | Detective | Transaction | High | Account code flagged as inactive |
| GL-010 | Duplicate entry detection | Control Activities | Detective | Transaction | High | Same amount, account, date within 24 hours by same user |
| GL-011 | Journal entry description missing | Information & Communication | Detective | Transaction | Low | Description blank or < 10 characters |
| GL-012 | Entry to suspense/clearing account — aging | Monitoring | Detective | Periodic | High | Balance in suspense account > $0 for > 30 days |
| GL-013 | Unusual period-end volume spike | Risk Assessment | Detective | Periodic | Medium | JE count in last 3 days > 150% of period average |
| GL-014 | Contra-revenue posting without approval | Control Activities | Preventive | Transaction | High | Credit to revenue account outside billing system |
| GL-015 | Prepaid expense amortization override | Control Activities | Detective | Transaction | Medium | Manual entry to prepaid outside scheduled amortization |

---

## Segregation of Duties Controls

| ID | Control Name | Conflicting Functions | Severity |
|----|-------------|----------------------|---------|
| SOD-001 | AP entry + AP payment — same user | Accounts Payable Data Entry + Payment Release | Critical |
| SOD-002 | AR posting + cash receipt — same user | AR Invoice Entry + Cash Application | Critical |
| SOD-003 | Vendor creation + payment release | Vendor Master Maintenance + Payment Release | Critical |
| SOD-004 | Payroll maintenance + payroll approval | Employee Pay Rate Maintenance + Payroll Approval | Critical |
| SOD-005 | GL posting + GL approval — same user | General Ledger Posting + Journal Entry Approval | High |
| SOD-006 | Purchasing + receiving — same user | Purchase Order Creation + Goods Receipt | High |
| SOD-007 | Fixed asset addition + depreciation adjustment | Fixed Asset Addition + Depreciation Override | High |
| SOD-008 | User administration + any financial function | User/Role Administration + Any Financial Posting Right | Critical |
| SOD-009 | IT system access + financial data access | System Configuration + Financial Data Modification | High |
| SOD-010 | Bank reconciliation + cash posting | Bank Reconciliation + Cash Disbursement Posting | Critical |

---

## Account Reconciliation Controls

| ID | Control Name | COSO | Trigger | Severity | Threshold |
|----|-------------|------|---------|---------|-----------|
| REC-001 | Reconciliation overdue | Monitoring | Periodic | High | No reconciliation submitted > 15 days after period close |
| REC-002 | Unexplained reconciling item — high value | Monitoring | Periodic | High | Open reconciling item > $5,000 with no memo |
| REC-003 | Reconciliation submitted without support | Monitoring | Periodic | Medium | Reconciliation submitted with no attachment |
| REC-004 | Balance sheet account without reconciliation policy | Control Environment | Periodic | Medium | Material account (> $10,000 balance) with no recon assignment |
| REC-005 | Stale reconciling item — prior period | Monitoring | Periodic | High | Reconciling item carrying forward > 2 periods |
| REC-006 | Reconciliation preparer = reviewer | Control Activities | Periodic | Critical | Same user submits and approves reconciliation |

---

## Intercompany Controls

| ID | Control Name | COSO | Trigger | Severity | Threshold |
|----|-------------|------|---------|---------|-----------|
| IC-001 | Intercompany pair out of balance | Control Activities | Transaction | Critical | IC pair imbalance > $500 |
| IC-002 | Intercompany transaction — no elimination mapping | Control Activities | Transaction | High | IC transaction with no elimination rule defined |
| IC-003 | Intercompany balance — period-end aging | Monitoring | Periodic | High | IC payable/receivable unreconciled at period close |
| IC-004 | Intercompany transaction — missing counterparty entity | Information & Communication | Transaction | High | IC flag set but no counterparty entity specified |
| IC-005 | Intercompany markup inconsistency | Control Activities | Periodic | Medium | IC pricing inconsistent with transfer pricing policy |

---

## User Access & Configuration Controls

| ID | Control Name | COSO | Trigger | Severity |
|----|-------------|------|---------|---------|
| ACC-001 | Inactive user with active access | Control Environment | Periodic | Critical |
| ACC-002 | User permissions exceed role template | Control Environment | Configuration | High |
| ACC-003 | Admin role assignment — no approval record | Control Environment | Configuration | Critical |
| ACC-004 | Password policy non-compliance (ERP config) | Control Environment | Configuration | High |
| ACC-005 | Shared user account detected | Control Environment | Configuration | Critical |
| ACC-006 | User with access to multiple entities — no approval | Control Environment | Configuration | Medium |
| ACC-007 | Terminated employee — access not revoked within 24 hours | Control Environment | Configuration | Critical |

---

## Planned Future Controls (Post-Launch)

- **Revenue recognition timing** — ASC 606 milestone/delivery event monitoring
- **Lease obligation tracking** — ASC 842 ROU asset and liability reconciliation
- **Inventory costing** — Standard vs. actual cost variance monitoring (ASC 330)
- **Goodwill impairment indicators** — Triggering event monitoring for ASC 350 assessment
- **Related party transaction flagging** — Automated detection of transactions with entities sharing ownership attributes

---

*The RTCM control library is extensible. New controls can be added without changes to the core engine by implementing the ControlTest interface. Custom controls per client environment are supported via the tenant configuration layer.*
