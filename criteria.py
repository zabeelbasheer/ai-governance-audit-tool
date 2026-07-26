"""
criteria.py — 24 governance criteria
NIST AI RMF (GOVERN, MAP, MEASURE, MANAGE) + HIPAA + HITRUST CSF
Version 2.0 — 4 NIST criteria replaced with HITRUST equivalents
             + 4 net-new HITRUST criteria
"""

CRITERIA = [
    # ── GOVERN ────────────────────────────────────────────────────────────────
    {
        "id": "GOV-1",
        "function": "GOVERN",
        "name": "Accountability ownership",
        "description": "Is there a named owner or team accountable for the AI system's outcomes and risks?",
        "weight": 1.5,
        "framework": "NIST AI RMF",
    },
    {
        "id": "GOV-2",
        "function": "GOVERN",
        "name": "Policy alignment",
        "description": "Does the AI use case align with the organization's existing policies, ethical guidelines, and regulatory obligations?",
        "weight": 1.5,
        "framework": "NIST AI RMF",
    },
    {
        # Replaces GOV-3 (Documentation & audit trail)
        "id": "GOV-3",
        "function": "GOVERN",
        "name": "Audit logging policy (HITRUST 09.aa)",
        "description": "Is there a formal audit logging policy defining what AI system events must be logged, retained, and reviewed? Does it specify retention periods, access controls on logs, and review cadence?",
        "weight": 1.0,
        "framework": "HITRUST CSF 09.aa",
    },
    {
        "id": "GOV-4",
        "function": "GOVERN",
        "name": "Human oversight mechanism",
        "description": "Is there a defined process for humans to review, override, or shut down the AI system?",
        "weight": 2.0,
        "framework": "NIST AI RMF",
    },

    # ── MAP ───────────────────────────────────────────────────────────────────
    {
        "id": "MAP-1",
        "function": "MAP",
        "name": "Use case scope clarity",
        "description": "Is the intended purpose, user population, and deployment context clearly defined and bounded?",
        "weight": 1.0,
        "framework": "NIST AI RMF",
    },
    {
        "id": "MAP-2",
        "function": "MAP",
        "name": "Stakeholder impact assessment",
        "description": "Have potentially affected stakeholders — patients, employees, or third parties — been identified and considered?",
        "weight": 1.5,
        "framework": "NIST AI RMF",
    },
    {
        "id": "MAP-3",
        "function": "MAP",
        "name": "Regulatory context awareness",
        "description": "Does the use case account for applicable regulations (HIPAA, FDA, state AI laws, CMS rules)?",
        "weight": 2.0,
        "framework": "NIST AI RMF",
    },
    {
        "id": "MAP-4",
        "function": "MAP",
        "name": "Third-party AI risk passthrough",
        "description": "If using a third-party AI vendor or model, are their governance and data handling obligations contractually defined?",
        "weight": 1.5,
        "framework": "NIST AI RMF",
    },

    # ── MEASURE ───────────────────────────────────────────────────────────────
    {
        # Replaces MEA-1 (Bias & fairness testing)
        "id": "MEA-1",
        "function": "MEASURE",
        "name": "Monitoring system use (HITRUST 09.ab)",
        "description": "Is there an active monitoring program for the AI system that tracks usage patterns, detects anomalies, tests for demographic bias across patient or user populations, and produces regular monitoring reports?",
        "weight": 2.0,
        "framework": "HITRUST CSF 09.ab",
    },
    {
        "id": "MEA-2",
        "function": "MEASURE",
        "name": "Performance metrics defined",
        "description": "Are accuracy, precision, recall, or other relevant performance metrics defined and baselined?",
        "weight": 1.5,
        "framework": "NIST AI RMF",
    },
    {
        "id": "MEA-3",
        "function": "MEASURE",
        "name": "Uncertainty and confidence handling",
        "description": "Does the system communicate confidence levels or flag low-confidence outputs for human review?",
        "weight": 1.5,
        "framework": "NIST AI RMF",
    },
    {
        "id": "MEA-4",
        "function": "MEASURE",
        "name": "Monitoring and drift detection",
        "description": "Is there a plan to monitor model performance over time and detect data or concept drift?",
        "weight": 1.5,
        "framework": "NIST AI RMF",
    },
    {
        "id": "MEA-5",
        "function": "MEASURE",
        "name": "Explainability",
        "description": "Can the system's outputs be explained to end users and affected parties in plain language?",
        "weight": 1.5,
        "framework": "NIST AI RMF",
    },

    # ── MANAGE ────────────────────────────────────────────────────────────────
    {
        "id": "MAN-1",
        "function": "MANAGE",
        "name": "Incident response plan",
        "description": "Is there a defined process for responding to AI failures, harmful outputs, or adversarial attacks?",
        "weight": 2.0,
        "framework": "NIST AI RMF",
    },
    {
        "id": "MAN-2",
        "function": "MANAGE",
        "name": "Rollback and decommission plan",
        "description": "Is there a defined process to roll back or retire the AI system if it causes harm?",
        "weight": 1.5,
        "framework": "NIST AI RMF",
    },
    {
        # Replaces MAN-3 (Access control)
        "id": "MAN-3",
        "function": "MANAGE",
        "name": "Access control policy (HITRUST 01.a)",
        "description": "Is there a formal access control policy governing who can access the AI system, its training data, outputs, and audit logs? Does it specify role-based access, least privilege, and periodic access reviews as required by HITRUST Control 01.a?",
        "weight": 1.0,
        "framework": "HITRUST CSF 01.a",
    },

    # ── HIPAA ─────────────────────────────────────────────────────────────────
    {
        "id": "HIP-1",
        "function": "HIPAA",
        "name": "PHI data minimization",
        "description": "Does the system limit use of Protected Health Information to the minimum necessary for its function?",
        "weight": 2.0,
        "framework": "HIPAA",
    },
    {
        "id": "HIP-2",
        "function": "HIPAA",
        "name": "Patient consent and transparency",
        "description": "Are patients or relevant parties informed when AI is used in decisions that affect their care or data?",
        "weight": 2.0,
        "framework": "HIPAA",
    },
    {
        "id": "HIP-3",
        "function": "HIPAA",
        "name": "Clinical decision support oversight",
        "description": "If the AI supports clinical decisions, is a licensed clinician required to review outputs before action is taken?",
        "weight": 2.0,
        "framework": "HIPAA",
    },
    {
        # Replaces HIP-4 (Data breach & security safeguards)
        "id": "HIP-4",
        "function": "HIPAA",
        "name": "Information classification (HITRUST 07.a)",
        "description": "Has PHI and sensitive data used by the AI system been formally classified? Are classification levels enforced through data handling procedures, labeling, and access controls as defined by HITRUST Control 07.a?",
        "weight": 1.5,
        "framework": "HITRUST CSF 07.a",
    },

    # ── HITRUST (net-new) ─────────────────────────────────────────────────────
    {
        "id": "HIT-1",
        "function": "HITRUST",
        "name": "Information security policy (HITRUST 05.a)",
        "description": "Does the organization have a formal information security policy that explicitly covers AI systems, is approved by leadership, communicated to all relevant staff, and reviewed at defined intervals?",
        "weight": 1.5,
        "framework": "HITRUST CSF 05.a",
    },
    {
        "id": "HIT-2",
        "function": "HITRUST",
        "name": "Data protection by design (HITRUST 06.d)",
        "description": "Was privacy engineering embedded into the AI system design from inception — including data minimization, anonymization where possible, and privacy impact assessment — rather than added after deployment?",
        "weight": 2.0,
        "framework": "HITRUST CSF 06.d",
    },
    {
        "id": "HIT-3",
        "function": "HITRUST",
        "name": "Network controls for data transmission (HITRUST 09.l)",
        "description": "Are AI system inputs (e.g. clinical notes, patient records) and outputs (e.g. predictions, recommendations) transmitted over secure, encrypted channels with defined network access controls?",
        "weight": 1.5,
        "framework": "HITRUST CSF 09.l",
    },
    {
        "id": "HIT-4",
        "function": "HITRUST",
        "name": "Business continuity for AI systems (HITRUST 11.a)",
        "description": "Is the AI system covered by the organization's business continuity and disaster recovery plan? Are availability SLAs defined, failover procedures documented, and clinical workflow fallbacks established for when the AI system is unavailable?",
        "weight": 1.5,
        "framework": "HITRUST CSF 11.a",
    },
]

FUNCTION_COLORS = {
    "GOVERN":  "#1a3a4a",
    "MAP":     "#2c1a4a",
    "MEASURE": "#1a4a2c",
    "MANAGE":  "#4a3a1a",
    "HIPAA":   "#4a1a1a",
    "HITRUST": "#1a2a4a",
}

MATURITY_BANDS = [
    (0,  40,  "Emerging",    "#c0392b", "Significant governance gaps. Not ready for deployment."),
    (40, 65,  "Developing",  "#e67e22", "Partial controls in place. Address red items before go-live."),
    (65, 80,  "Established", "#f1c40f", "Reasonable controls. Amber items should be scheduled."),
    (80, 100, "Mature",      "#27ae60", "Strong governance posture. Maintain and monitor."),
]
