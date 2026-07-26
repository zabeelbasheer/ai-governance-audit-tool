# AI Governance Audit Tool

> An LLM-powered governance auditor and mentor for healthcare AI deployments — evaluates any AI use case against 24 criteria drawn from NIST AI RMF, HIPAA, and HITRUST CSF, then guides teams to remediation through a conversational mentor and tracked action checklist.

**🚀 Live Demo:** https://ai-governance-audit.streamlit.app

![Python](https://img.shields.io/badge/Python-3.11-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.60-red)
![Groq](https://img.shields.io/badge/Groq-llama--3.3--70b-orange)
![SQLite](https://img.shields.io/badge/DB-SQLite%20→%20PostgreSQL-lightgrey)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## The Problem

Healthcare organizations deploying AI — whether for prior authorization, medical coding, no-show prediction, or clinical decision support — face a governance challenge most teams are not equipped to handle systematically. Compliance officers ask the right questions but lack an AI-specific lens. Operations leaders move fast and assess risk after the fact. Data Protection Officers have no standardized tool to evaluate AI use cases before they go live.

The result: AI systems get deployed with undocumented oversight gaps, untested bias exposure, and no incident response plan — until a payer audit, a CMS review, or a patient harm event forces the issue.

---

## What This Tool Does

This tool takes a plain-English description of an AI use case and runs it through a structured 24-criterion evaluation across five governance frameworks. It does not just score — it mentors. After the audit, a conversational AI guides teams through each gap, asks diagnostic questions about their current state, and generates a specific, owner-assigned action checklist with due dates.

The workflow has three phases:

**Phase 1 — Intake**
A conversational agent asks 5–7 targeted clarifying questions before scoring begins. Questions probe data handling, oversight mechanisms, accountability ownership, deployment context, and known risk controls. Answers are synthesized into an enriched use case profile that produces more accurate scores than a raw description alone.

**Phase 2 — Audit**
The enriched profile is evaluated against all 24 criteria using Groq's llama-3.3-70b-versatile model. Each criterion receives a score of 1–5, a rationale, a critical flag if the gap blocks deployment, and a remediation suggestion. Results are rendered as a traffic-light risk matrix and a radar chart showing governance posture across all five framework functions.

**Phase 3 — Mentor and Checklist**
For every red or amber finding, a mentoring agent explains the risk in healthcare BPO context, asks one diagnostic question about the organization's current state, and generates a tailored action item with a suggested owner and due date. All actions compile into a persistent checklist that teams can track, update, and export — turning the audit from a point-in-time assessment into an ongoing remediation program.

---

## What Makes This Different

Most AI governance tools on GitHub fall into one of three categories: enterprise GRC platforms requiring Java, PostgreSQL, and a DevOps team to deploy; generic NIST RMF checklists with no evaluation layer; or cybersecurity compliance tools focused on infrastructure rather than AI use case risk.

This tool sits in a gap none of them cover: a practitioner-built, healthcare-specific governance auditor that uses an LLM to evaluate — not just list — governance criteria, and that transitions from judge to mentor after scoring.

Three things make it genuinely differentiated:

**Healthcare BPO context baked in.** The HIPAA criteria were written for revenue cycle management, clinical coding, prior authorization, and healthcare contact center operations — not generic healthcare IT. The HITRUST controls were selected specifically for AI systems handling PHI in BPO deployment contexts. The mentor agent references RCM, coding, and clinical ops when giving remediation guidance.

**Mentor mode, not just scorecard.** Every other open-source governance tool stops at the score. This tool continues: it asks what you have in place, listens to your answer, and gives you a specific next step — not "implement an incident response plan" but "assign your RCM ops lead to draft a 3-step AI failure escalation procedure by [date]."

**AD-ready multi-user architecture.** The tool is built for organizational deployment, not solo use. Role-based access (User / AI Governance Auditor / DPO / Admin) controls visibility. Admins and DPOs see all audits across the organization. The auth layer is a direct drop-in replacement for Azure AD SSO via MSAL — the session contract is identical whether authentication comes from the local stub or an AD token.

---

## Governance Framework Coverage

| Function | Framework | Criteria |
|----------|-----------|---------|
| GOVERN | NIST AI RMF | Accountability, policy alignment, audit logging (HITRUST 09.aa), human oversight |
| MAP | NIST AI RMF | Scope clarity, stakeholder impact, regulatory context, third-party risk |
| MEASURE | NIST AI RMF + HITRUST | Monitoring (HITRUST 09.ab), performance metrics, uncertainty handling, drift detection, explainability |
| MANAGE | NIST AI RMF + HITRUST | Incident response, rollback plan, access control (HITRUST 01.a) |
| HIPAA | HIPAA | PHI minimization, patient consent, clinical decision support oversight, information classification (HITRUST 07.a) |
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

## Role-Based Access

| Role | Own Audits | All Audits | Use Case |
|------|-----------|------------|---------|
| User | ✓ | ✗ | Operations staff submitting AI use cases for review |
| AI Governance Auditor | ✓ | ✓ | Reviews all organizational AI deployments |
| Data Protection Officer | ✓ | ✓ | HIPAA/HITRUST accountability owner |
| Admin | ✓ | ✓ | System administration and user management |

---

## Architecture

```
User (plain English use case description)
          │
          ▼
  Intake Agent (Groq LLM)
  5–7 clarifying questions → enriched use case profile
          │
          ▼
  24-Criterion Evaluator (Groq LLM)
  NIST AI RMF + HIPAA + HITRUST CSF
  Score 1–5 per criterion + critical flag + remediation
          │
          ▼
  Results Dashboard
  Overall % score + maturity band + radar chart
  Traffic-light risk matrix (Red / Amber / Green)
          │
          ▼
  Mentor Agent (Groq LLM)
  Per red/amber criterion: diagnostic question → tailored action
          │
          ▼
  Action Checklist (SQLite)
  Owner + due date + status tracking + CSV export
          │
          ▼
  Audit History Dashboard
  Role-based visibility + search by user / title / score
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM inference | Groq API — llama-3.3-70b-versatile |
| Frontend | Streamlit 1.60 |
| Database | SQLite (PostgreSQL-ready — swap connection factory in db.py) |
| Authentication | bcrypt password hashing — AD SSO (MSAL) drop-in ready |
| Charts | Plotly — radar chart for framework function scores |
| Language | Python 3.11 |

---

## Setup

```bash
git clone https://github.com/zabeelbasheer/ai-governance-audit-tool.git
cd ai-governance-audit-tool
uv python pin 3.11
uv sync
cp .env.example .env     # Add your Groq API key
mkdir -p data
uv run streamlit run app.py
```

### `.env`
```
GROQ_API_KEY=your_groq_key_here
MODEL_NAME=llama-3.3-70b-versatile
```

### Demo access
Demo credentials are configured via environment variables (see `.env.example`).
Contact the author via [LinkedIn](https://linkedin.com/in/zabeelbasheer) for evaluation access to the live demo.

---

## Sample Use Cases to Test

**Low scorer — Emerging band:**
> We want to use AI to automate prior authorization decisions for specialty medications. The AI will read clinical notes and approve or deny requests automatically without human review. We have not defined what data it will use, who owns it, or how it will be monitored.

**Mid scorer — Developing band:**
> We are building an AI model to predict patient no-show probability for outpatient scheduling. The model uses historical appointment data and insurance type. Schedulers see a risk score and can send an extra reminder — no patient is denied an appointment. The model is from a third-party vendor under a BAA. We have not conducted a bias audit and have no monitoring plan yet.

**High scorer — Established/Mature band:**
> We are deploying an LLM-powered medical coding assistant for ICD-10 and CPT suggestions from clinical notes. A licensed medical coder must review and accept every suggestion before submission. The system is owned by the Revenue Cycle VP with a named deputy. We use de-identified notes for inference, have a documented rollback plan, conduct quarterly bias audits, and log all accepted and rejected suggestions. Patients are notified via updated privacy policy.

---

## Roadmap

- [ ] Azure AD SSO integration (MSAL — drop-in replacement for auth.py stub)
- [ ] PostgreSQL migration for multi-tenant enterprise deployment
- [ ] EU AI Act criteria layer (Act Article 9 risk management, Article 13 transparency)
- [ ] PDF audit report with organizational letterhead
- [ ] Automated re-audit scheduling (quarterly cadence trigger)
- [ ] API endpoint for integration with existing GRC platforms
- [ ] Bulk use case upload for portfolio-level governance assessment

---

## About the Author

Built by [Zabeel M. Basheer](https://linkedin.com/in/zabeelbasheer) — VP Business Excellence & India Site Lead at Shearwater Health, Lean Six Sigma Master Black Belt, and AIGP candidate. This tool operationalizes the AI governance frameworks tested in the AIGP certification and reflects real deployment contexts encountered in healthcare BPO operations across revenue cycle management, clinical coding, and prior authorization.

---

## Tags

`healthcare-ai` `ai-governance` `nist-ai-rmf` `hipaa` `hitrust` `streamlit` `groq` `enterprise-ai` `aigp` `responsible-ai` `python` `healthcare-bpo`
