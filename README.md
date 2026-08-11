# Zeta Health AI — Governance Audit

> An LLM-powered AI governance auditor and mentor for healthcare deployments. Evaluates any AI use case against 24 criteria drawn from NIST AI RMF, HIPAA, and HITRUST CSF — with vendor-aware scoring for Microsoft, AWS, and Salesforce — then guides teams to remediation through a conversational mentor and tracked action checklist.

**🚀 Live Demo:** https://ai-governance-audit.streamlit.app

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.60-red)
![Groq](https://img.shields.io/badge/Groq-llama--3.3--70b-orange)
![SQLite](https://img.shields.io/badge/DB-SQLite%20→%20PostgreSQL-lightgrey)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## The Problem

Healthcare organisations deploying AI — for prior authorisation, medical coding, no-show prediction, or clinical decision support — face a governance challenge most teams are not equipped to handle systematically. Compliance officers ask the right questions but lack an AI-specific lens. Operations leaders move fast and assess risk after the fact. Data Protection Officers have no standardised tool to evaluate AI use cases before they go live.

Compounding this: most deployments use third-party AI platforms (Microsoft Copilot, AWS Bedrock, Salesforce Einstein) that provide significant built-in governance controls — but teams don't know which gaps remain their responsibility. Every audit starts from scratch even when the vendor has already addressed 60% of the criteria.

---

## What This Tool Does

Describe an AI use case in plain English. The tool detects the vendor or platform involved, pre-loads vendor-confirmed governance controls as baselines, and runs a 24-criterion evaluation — asking the LLM to adjust scores based on your specific deployment context rather than evaluating from zero.

After scoring, a conversational mentor works through each red and amber finding, asks diagnostic questions, and generates a specific action item with a suggested owner and due date. All actions compile into a persistent checklist tracked across sessions.

---

## Vendor Knowledge Base

The tool maintains a pre-mapped knowledge base of AI vendor governance coverage. When a vendor is detected or selected, baseline scores are applied to criteria the vendor demonstrably covers — and the intake agent skips questions about those areas entirely.

### 🏢 Microsoft
**Products:** Copilot for Microsoft 365, Copilot Cowork, Azure OpenAI Service, GitHub Copilot, Microsoft Fabric

**Strongly covered (score baseline 4–5):**
- GOV-3 Audit logging — Microsoft Purview Unified Audit Log
- MAN-3 Access control — Microsoft Entra ID (Azure AD) RBAC
- MAP-4 Third-party risk — Microsoft Online Services DPA + HIPAA BAA
- MAP-3 Regulatory context — HIPAA, FedRAMP, GDPR compliance
- HIT-1 Security policy — ISO 27001, SOC 2 Type II certified
- HIT-2 Data protection by design — Privacy by Design embedded in SDL
- HIT-3 Network controls — TLS 1.2+, Azure Private Link
- HIT-4 Business continuity — 99.9% SLA, multi-region failover
- HIP-4 Information classification — Microsoft Purview MIP labels

**Customer responsibility gaps (not covered by vendor):**
- GOV-4 Human oversight mechanism
- HIP-2 Patient consent and transparency
- HIP-3 Clinical decision support oversight

**Certifications:** ISO 27001, ISO 27017, ISO 27018, SOC 1 Type II, SOC 2 Type II, HIPAA BAA, FedRAMP High

---

### ☁️ Amazon Web Services (AWS)
**Products:** Amazon Bedrock, AWS SageMaker, Amazon Comprehend Medical, Amazon HealthLake, AWS HealthScribe, Amazon Q

**Strongly covered (score baseline 4–5):**
- GOV-3 Audit logging — AWS CloudTrail (tamper-evident, queryable)
- MAN-3 Access control — AWS IAM fine-grained RBAC
- MAP-4 Third-party risk — AWS DPA + HIPAA BAA
- MAP-3 Regulatory context — HIPAA eligible across 160+ services
- MEA-4 Drift detection — SageMaker Model Monitor
- HIP-4 Information classification — Amazon Macie PHI discovery
- HIT-1 Security policy — ISO 27001, SOC 2 Type II, HITRUST CSF
- HIT-2 Data protection by design — Bedrock does not retain prompts by default
- HIT-3 Network controls — TLS 1.2+, VPC, PrivateLink
- HIT-4 Business continuity — 99.9% SLA, multi-AZ failover

**Customer responsibility gaps:**
- GOV-4 Human oversight mechanism
- HIP-2 Patient consent and transparency
- HIP-3 Clinical decision support oversight

**Certifications:** ISO 27001, SOC 2 Type II, HIPAA eligible, FedRAMP High, HITRUST CSF, PCI DSS Level 1

---

### ☁️ Salesforce
**Products:** Health Cloud, Einstein AI, Einstein GPT, Einstein Copilot, Agentforce, Einstein Discovery

**Strongly covered (score baseline 4–5):**
- GOV-3 Audit logging — Salesforce Shield Event Monitoring
- MAP-4 Third-party risk — Salesforce DPA + HIPAA BAA
- MAP-3 Regulatory context — HIPAA Health Cloud, 21st Century Cures Act
- MEA-3 Confidence handling — Einstein Discovery confidence scores
- MEA-5 Explainability — Plain-language prediction explanations in UI
- MAN-3 Access control — Granular permission sets and field-level security
- HIP-4 Information classification — Salesforce Shield Platform Encryption
- HIT-1 Security policy — ISO 27001, SOC 2 Type II, HITRUST CSF
- HIT-2 Data protection by design — Privacy by Design, data residency options
- HIT-3 Network controls — TLS 1.2+, Hyperforce private connectivity
- HIT-4 Business continuity — 99.9% SLA, multi-region redundancy

**Customer responsibility gaps:**
- GOV-4 Human oversight mechanism
- HIP-2 Patient consent and transparency (partial — consent management available but must be configured)

**Certifications:** ISO 27001, ISO 27018, SOC 1 Type II, SOC 2 Type II, HIPAA BAA, FedRAMP Moderate, HITRUST CSF

---

## Governance Framework — 24 Criteria

| Function | Framework | Criteria |
|----------|-----------|---------|
| GOVERN | NIST AI RMF | Accountability, policy alignment, audit logging (HITRUST 09.aa), human oversight |
| MAP | NIST AI RMF | Scope clarity, stakeholder impact, regulatory context, third-party risk |
| MEASURE | NIST AI RMF + HITRUST | Monitoring (HITRUST 09.ab), performance metrics, uncertainty handling, drift detection, explainability |
| MANAGE | NIST AI RMF + HITRUST | Incident response, rollback plan, access control (HITRUST 01.a) |
| HIPAA | HIPAA | PHI minimisation, patient consent, clinical decision support oversight, information classification (HITRUST 07.a) |
| HITRUST | HITRUST CSF | Security policy (05.a), data protection by design (06.d), network controls (09.l), business continuity (11.a) |

---

## Maturity Bands

| Score | Band | Meaning |
|-------|------|---------|
| 0–40% | Emerging | Significant governance gaps. Not ready for deployment. |
| 40–65% | Developing | Partial controls in place. Address red items before go-live. |
| 65–80% | Established | Reasonable controls. Amber items should be scheduled. |
| 80–100% | Mature | Strong governance posture. Maintain and monitor. |

---

## Workflow

```
User describes AI use case (plain English)
          │
          ▼
Vendor Detection (Groq LLM + keyword fallback)
Detects: Microsoft / AWS / Salesforce / None
          │
          ▼
Vendor Knowledge Base lookup
Pre-loads baseline scores for strongly covered criteria
          │
          ▼
Intake Agent (Groq LLM)
5–7 clarifying questions — skips vendor-confirmed areas
Focuses on customer responsibility gaps
          │
          ▼
24-Criterion Evaluator (Groq LLM)
Vendor baselines inform scoring
LLM adjusts based on deployment-specific context
          │
          ▼
Results: Overall % · Maturity band · Radar chart
Traffic-light risk matrix with vendor baseline badges
          │
          ▼
Mentor Agent (Groq LLM)
Per red/amber criterion: diagnostic question → tailored action
          │
          ▼
Action Checklist (SQLite)
Owner · due date · status tracking · CSV export
          │
          ▼
Audit History Dashboard
Role-based visibility · search by user / title / score / vendor
```

---

## Role-Based Access

| Role | Own Audits | All Audits | Use Case |
|------|-----------|------------|---------|
| User | ✓ | ✗ | Operations staff submitting AI use cases |
| AI Governance Auditor | ✓ | ✓ | Reviews all organisational AI deployments |
| Data Protection Officer | ✓ | ✓ | HIPAA/HITRUST accountability owner |
| Admin | ✓ | ✓ | System administration |

Authentication is bcrypt-hashed with environment variable passwords. Designed as a drop-in replacement for Azure AD SSO (MSAL) — session contract is identical.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM inference | Groq API — llama-3.3-70b-versatile |
| Frontend | Streamlit 1.60 |
| Database | SQLite (PostgreSQL-ready) |
| Authentication | bcrypt — Azure AD SSO drop-in ready |
| Charts | Plotly — radar chart across 6 governance functions |
| Vendor KB | Static JSON-style knowledge base (vendor_kb.py) |
| Language | Python 3.11 |

---

## Setup

```bash
git clone https://github.com/zabeelbasheer/ai-governance-audit-tool.git
cd ai-governance-audit-tool
uv python pin 3.11
uv sync
cp .env.example .env
mkdir -p data
uv run streamlit run app.py
```

### `.env`
```
GROQ_API_KEY=your_groq_key_here
MODEL_NAME=llama-3.3-70b-versatile
ADMIN_PASSWORD=YourAdminPassword
AUDITOR_PASSWORD=YourAuditorPassword
DPO_PASSWORD=YourDpoPassword
USER_PASSWORD=YourUserPassword
```

### Demo access
Demo credentials are available on request for evaluation purposes.
Contact the author via [LinkedIn](https://linkedin.com/in/zabeelbasheer).

---

## Sample Use Cases to Test

**Microsoft Copilot — low governance maturity (vendor helps but gaps remain):**
> We are deploying Microsoft Copilot Cowork to assist our prior authorisation clinical reviewers in drafting approval and denial letters based on clinical notes. Reviewers will use Copilot suggestions without a mandatory review step. No patient consent notice has been updated.

**AWS Bedrock — well-governed deployment:**
> We are deploying an Amazon Bedrock-powered ICD-10 coding assistant for our medical coders. A licensed coder must review and accept every suggestion before submission. The system is owned by the Revenue Cycle VP. We use de-identified notes for inference, have a documented rollback plan, conduct quarterly bias audits, and log all accepted and rejected suggestions via CloudTrail.

**No vendor — stress test:**
> We want to use AI to improve our revenue cycle operations.

---

## Roadmap

- [ ] ISO/IEC 42001:2023 criteria layer (expanding to 32 criteria)
- [ ] FastAPI + vanilla JS rebuild for pixel-perfect UI and REST API
- [ ] Azure AD SSO integration (MSAL drop-in)
- [ ] PostgreSQL migration for multi-tenant enterprise deployment
- [ ] EU AI Act Article 9 and 13 criteria
- [ ] PDF audit report with organisational letterhead
- [ ] Additional vendors: Google Vertex AI, Oracle Health, Epic MyChart
- [ ] Automated re-audit scheduling

---

## About

Built by [Zabeel M. Basheer](https://linkedin.com/in/zabeelbasheer) — VP Business Excellence & India Site Lead at Shearwater Health, Lean Six Sigma Master Black Belt, and AIGP candidate. Part of the [Zeta Health AI](https://github.com/zabeelbasheer) portfolio of applied AI tools for healthcare BPO operations.

*Clinical operations, intelligently governed.*

---

## Tags

`healthcare-ai` `ai-governance` `nist-ai-rmf` `hipaa` `hitrust` `streamlit` `groq` `enterprise-ai` `aigp` `responsible-ai` `python` `healthcare-bpo` `vendor-knowledge-base` `microsoft-copilot` `aws-bedrock` `salesforce-health-cloud`
