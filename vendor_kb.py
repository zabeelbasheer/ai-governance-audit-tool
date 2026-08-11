"""
vendor_kb.py — Vendor Knowledge Base
Pre-mapped governance coverage for Microsoft, AWS, and Salesforce
against all 24 NIST AI RMF + HIPAA + HITRUST criteria.

Coverage levels:
  "strong"  — vendor explicitly covers this; score baseline 4-5
  "partial" — vendor partially covers; customer must supplement; baseline 3
  "none"    — customer responsibility entirely; no baseline adjustment

Score baselines are suggestions. The evaluator LLM adjusts based on
deployment-specific context described by the user.
"""

VENDOR_KB = {
    "microsoft": {
        "display_name": "Microsoft",
        "products": [
            "Microsoft Copilot", "Copilot for Microsoft 365", "Copilot Cowork",
            "Azure OpenAI Service", "Azure AI Services", "Microsoft 365 Copilot",
            "GitHub Copilot", "Bing Chat Enterprise", "Microsoft Fabric",
        ],
        "detection_keywords": [
            "microsoft", "copilot", "azure openai", "azure ai", "m365",
            "microsoft 365", "office 365", "github copilot", "bing chat",
            "microsoft fabric", "copilot cowork", "teams copilot",
        ],
        "certifications": [
            "ISO 27001", "ISO 27017", "ISO 27018", "SOC 1 Type II",
            "SOC 2 Type II", "HIPAA BAA available", "FedRAMP High",
            "CSA STAR Level 2",
        ],
        "coverage": {
            "GOV-1": {
                "level":    "partial",
                "baseline": 3,
                "note":     "Microsoft provides a Responsible AI Standard and named AI governance roles internally. Customer must designate their own accountability owner for the deployment.",
                "evidence": "Microsoft Responsible AI Standard v2 — microsoft.com/en-us/ai/responsible-ai",
            },
            "GOV-2": {
                "level":    "partial",
                "baseline": 3,
                "note":     "Microsoft's AI principles (fairness, reliability, privacy, inclusiveness, transparency, accountability) provide a policy framework but customer must align to their own org policies.",
                "evidence": "Microsoft AI Principles — microsoft.com/en-us/ai/our-approach",
            },
            "GOV-3": {
                "level":    "strong",
                "baseline": 4,
                "note":     "Microsoft Purview Unified Audit Log captures all Copilot interactions, user prompts, and AI-generated responses with configurable retention up to 10 years.",
                "evidence": "Microsoft Purview Audit — learn.microsoft.com/en-us/purview/audit-solutions-overview",
            },
            "GOV-4": {
                "level":    "none",
                "baseline": 1,
                "note":     "Human oversight of AI outputs is entirely customer-defined. Microsoft provides no default review or override workflow for Copilot outputs.",
                "evidence": "",
            },
            "MAP-1": {
                "level":    "partial",
                "baseline": 3,
                "note":     "Microsoft publishes use case guidance and acceptable use policies per product. Customer must define specific deployment scope and boundaries.",
                "evidence": "Microsoft Copilot Acceptable Use Policy — microsoft.com/en-us/legal/terms-of-use",
            },
            "MAP-2": {
                "level":    "partial",
                "baseline": 3,
                "note":     "Microsoft conducts impact assessments for its own AI systems. Customer must conduct their own stakeholder impact assessment for their specific deployment.",
                "evidence": "Microsoft Responsible AI Impact Assessment — microsoft.com/en-us/ai/tools-practices",
            },
            "MAP-3": {
                "level":    "strong",
                "baseline": 4,
                "note":     "Microsoft maintains comprehensive regulatory compliance including HIPAA, GDPR, FedRAMP, and sector-specific frameworks. BAA available for HIPAA-covered deployments.",
                "evidence": "Microsoft Compliance Center — microsoft.com/en-us/trust-center/compliance/compliance-overview",
            },
            "MAP-4": {
                "level":    "strong",
                "baseline": 5,
                "note":     "Microsoft's Data Processing Agreement (DPA), Online Services Terms (OST), and HIPAA BAA explicitly define data handling, subprocessor obligations, and liability.",
                "evidence": "Microsoft Online Services DPA — microsoft.com/licensing/docs/view/Microsoft-Products-and-Services-Data-Protection-Addendum-DPA",
            },
            "MEA-1": {
                "level":    "partial",
                "baseline": 3,
                "note":     "Microsoft 365 Admin Center provides Copilot usage reports and activity analytics. Demographic bias monitoring across patient or employee populations is customer responsibility.",
                "evidence": "Microsoft 365 Copilot Usage Reports — learn.microsoft.com/en-us/microsoft-365/admin/activity-reports",
            },
            "MEA-2": {
                "level":    "partial",
                "baseline": 3,
                "note":     "Microsoft publishes model performance benchmarks for Azure OpenAI models. Deployment-specific accuracy and recall metrics must be defined and baselined by the customer.",
                "evidence": "Azure OpenAI Model Performance — learn.microsoft.com/en-us/azure/ai-services/openai/concepts/models",
            },
            "MEA-3": {
                "level":    "partial",
                "baseline": 3,
                "note":     "Copilot outputs include content filters and safety classifiers but do not expose confidence scores to end users. Customer must implement confidence handling at the application layer.",
                "evidence": "Azure OpenAI Content Filtering — learn.microsoft.com/en-us/azure/ai-services/openai/concepts/content-filter",
            },
            "MEA-4": {
                "level":    "partial",
                "baseline": 3,
                "note":     "Azure AI monitoring via Azure Monitor and Application Insights supports performance tracking. Model drift detection requires customer-configured alerting.",
                "evidence": "Azure Monitor for AI — learn.microsoft.com/en-us/azure/azure-monitor/overview",
            },
            "MEA-5": {
                "level":    "partial",
                "baseline": 3,
                "note":     "Copilot provides source citations for grounded responses. Full explainability of model reasoning is not exposed to end users. Customer must supplement with process-level documentation.",
                "evidence": "Microsoft Copilot Transparency — microsoft.com/en-us/ai/responsible-ai-resources",
            },
            "MAN-1": {
                "level":    "partial",
                "baseline": 3,
                "note":     "Microsoft provides a security incident response SLA (72-hour breach notification). AI-specific failure response — harmful outputs, hallucinations — is customer responsibility.",
                "evidence": "Microsoft Security Response Center — msrc.microsoft.com",
            },
            "MAN-2": {
                "level":    "strong",
                "baseline": 4,
                "note":     "Azure OpenAI and M365 services support tenant-level disabling, feature flagging, and rollback via admin controls. Decommission procedures are documented.",
                "evidence": "Microsoft 365 Admin Controls — learn.microsoft.com/en-us/microsoft-365/admin/admin-overview",
            },
            "MAN-3": {
                "level":    "strong",
                "baseline": 5,
                "note":     "Microsoft Entra ID (Azure AD) provides RBAC, conditional access, and least-privilege enforcement. Copilot access is controlled via Microsoft 365 license assignment and admin policy.",
                "evidence": "Microsoft Entra ID — microsoft.com/en-us/security/business/identity-access/microsoft-entra-id",
            },
            "HIP-1": {
                "level":    "partial",
                "baseline": 3,
                "note":     "Microsoft's data minimization defaults vary by product. Azure OpenAI in healthcare scenarios requires customer configuration to limit PHI input. Data residency options available.",
                "evidence": "Microsoft Data Residency — microsoft.com/en-us/trust-center/privacy/data-location",
            },
            "HIP-2": {
                "level":    "none",
                "baseline": 1,
                "note":     "Patient consent and transparency obligations when using Copilot in clinical workflows are entirely customer responsibility. Microsoft provides no patient-facing consent mechanism.",
                "evidence": "",
            },
            "HIP-3": {
                "level":    "none",
                "baseline": 1,
                "note":     "Clinical decision support oversight — licensed clinician review before action — is entirely customer responsibility. Microsoft does not enforce clinical review workflows.",
                "evidence": "",
            },
            "HIP-4": {
                "level":    "strong",
                "baseline": 4,
                "note":     "Microsoft Purview Information Protection provides PHI classification labels, data loss prevention (DLP) policies, and sensitivity label enforcement across M365.",
                "evidence": "Microsoft Purview Information Protection — learn.microsoft.com/en-us/purview/information-protection",
            },
            "HIT-1": {
                "level":    "strong",
                "baseline": 5,
                "note":     "Microsoft holds ISO 27001, SOC 2 Type II, and HITRUST CSF certification. Formal information security policies covering AI systems are published and reviewed annually.",
                "evidence": "Microsoft Trust Center — microsoft.com/en-us/trust-center",
            },
            "HIT-2": {
                "level":    "strong",
                "baseline": 4,
                "note":     "Microsoft applies Privacy by Design across Azure and M365. Data minimization, pseudonymization, and privacy impact assessments are embedded in the SDL.",
                "evidence": "Microsoft Privacy by Design — microsoft.com/en-us/trust-center/privacy",
            },
            "HIT-3": {
                "level":    "strong",
                "baseline": 5,
                "note":     "All Microsoft cloud services enforce TLS 1.2+ for data in transit. Azure VNet, Private Link, and ExpressRoute available for network isolation.",
                "evidence": "Microsoft Network Security — learn.microsoft.com/en-us/azure/security/fundamentals/network-overview",
            },
            "HIT-4": {
                "level":    "strong",
                "baseline": 4,
                "note":     "Microsoft 365 and Azure maintain 99.9%+ SLAs with documented failover and disaster recovery. Business continuity plans are published and tested.",
                "evidence": "Microsoft SLA — azure.microsoft.com/en-us/support/legal/sla",
            },
        },
    },

    "aws": {
        "display_name": "Amazon Web Services (AWS)",
        "products": [
            "Amazon Bedrock", "AWS SageMaker", "Amazon Comprehend Medical",
            "Amazon HealthLake", "Amazon Transcribe Medical", "AWS HealthScribe",
            "Amazon Q", "Amazon Kendra", "Amazon Rekognition",
        ],
        "detection_keywords": [
            "aws", "amazon bedrock", "bedrock", "sagemaker", "comprehend medical",
            "healthlake", "transcribe medical", "healthscribe", "amazon q",
            "kendra", "rekognition", "amazon web services", "aws lambda",
        ],
        "certifications": [
            "ISO 27001", "ISO 27017", "ISO 27018", "SOC 1 Type II",
            "SOC 2 Type II", "HIPAA eligible", "FedRAMP High",
            "PCI DSS Level 1", "HITRUST CSF",
        ],
        "coverage": {
            "GOV-1": {
                "level":    "partial",
                "baseline": 3,
                "note":     "AWS publishes its Responsible AI principles but does not mandate or provide accountability ownership for customer deployments. Customer must designate their own AI system owner.",
                "evidence": "AWS Responsible AI — aws.amazon.com/machine-learning/responsible-ai",
            },
            "GOV-2": {
                "level":    "partial",
                "baseline": 3,
                "note":     "AWS AI Service Cards document intended uses, limitations, and design choices for each service. Customer must align these to internal policy frameworks.",
                "evidence": "AWS AI Service Cards — aws.amazon.com/machine-learning/responsible-ai/policy",
            },
            "GOV-3": {
                "level":    "strong",
                "baseline": 5,
                "note":     "AWS CloudTrail logs all API calls across all AWS services including Bedrock and SageMaker. Logs are tamper-evident, configurable for long-term S3 retention, and queryable via Athena.",
                "evidence": "AWS CloudTrail — docs.aws.amazon.com/awscloudtrail/latest/userguide",
            },
            "GOV-4": {
                "level":    "none",
                "baseline": 1,
                "note":     "Human oversight of AI outputs is entirely customer-defined. AWS provides no default human-in-the-loop workflow for Bedrock or SageMaker inference outputs.",
                "evidence": "",
            },
            "MAP-1": {
                "level":    "partial",
                "baseline": 3,
                "note":     "AWS Acceptable Use Policy and individual service documentation define intended use boundaries. Customer must document specific deployment scope.",
                "evidence": "AWS Acceptable Use Policy — aws.amazon.com/aup",
            },
            "MAP-2": {
                "level":    "partial",
                "baseline": 3,
                "note":     "AWS publishes impact assessments for its own AI systems via AI Service Cards. Customer deployment impact assessments are customer responsibility.",
                "evidence": "AWS AI Service Cards — aws.amazon.com/machine-learning/responsible-ai/policy",
            },
            "MAP-3": {
                "level":    "strong",
                "baseline": 4,
                "note":     "AWS maintains HIPAA eligibility across 160+ services including Bedrock and SageMaker. BAA available. Comprehensive regulatory coverage across healthcare, financial, and government sectors.",
                "evidence": "AWS HIPAA Compliance — aws.amazon.com/compliance/hipaa-compliance",
            },
            "MAP-4": {
                "level":    "strong",
                "baseline": 5,
                "note":     "AWS Data Processing Addendum (DPA), BAA, and shared responsibility model explicitly define data handling obligations. Subprocessor list is published and updated.",
                "evidence": "AWS DPA — aws.amazon.com/service-terms",
            },
            "MEA-1": {
                "level":    "partial",
                "baseline": 3,
                "note":     "Amazon SageMaker Clarify provides bias detection and model explainability. Not natively available in Bedrock. Customer must integrate Clarify or equivalent monitoring.",
                "evidence": "SageMaker Clarify — docs.aws.amazon.com/sagemaker/latest/dg/clarify-fairness-and-explainability",
            },
            "MEA-2": {
                "level":    "partial",
                "baseline": 3,
                "note":     "AWS publishes benchmark performance for foundation models on Bedrock. Deployment-specific metrics must be defined and tracked by the customer.",
                "evidence": "Amazon Bedrock Model Evaluation — docs.aws.amazon.com/bedrock/latest/userguide/model-evaluation.html",
            },
            "MEA-3": {
                "level":    "partial",
                "baseline": 3,
                "note":     "Bedrock provides content filtering via Guardrails for Amazon Bedrock. Confidence scores are returned in API responses for SageMaker but not surfaced to end users by default.",
                "evidence": "Amazon Bedrock Guardrails — docs.aws.amazon.com/bedrock/latest/userguide/guardrails.html",
            },
            "MEA-4": {
                "level":    "strong",
                "baseline": 4,
                "note":     "Amazon SageMaker Model Monitor provides automated drift detection with configurable alerting via CloudWatch. Customer must configure monitoring schedules and thresholds.",
                "evidence": "SageMaker Model Monitor — docs.aws.amazon.com/sagemaker/latest/dg/model-monitor.html",
            },
            "MEA-5": {
                "level":    "partial",
                "baseline": 3,
                "note":     "SageMaker Clarify provides feature attribution and SHAP values for explainability. Bedrock does not expose reasoning transparency natively. Customer must implement at application layer.",
                "evidence": "SageMaker Clarify Explainability — docs.aws.amazon.com/sagemaker/latest/dg/clarify-model-explainability.html",
            },
            "MAN-1": {
                "level":    "partial",
                "baseline": 3,
                "note":     "AWS provides a security incident response program with defined SLAs. AI-specific failure handling — hallucinations, harmful outputs — is customer responsibility.",
                "evidence": "AWS Security Incident Response — aws.amazon.com/security/security-bulletins",
            },
            "MAN-2": {
                "level":    "strong",
                "baseline": 4,
                "note":     "AWS supports blue/green deployments, model versioning in SageMaker, and service endpoint deletion for decommissioning. Rollback procedures are documented per service.",
                "evidence": "SageMaker Model Registry — docs.aws.amazon.com/sagemaker/latest/dg/model-registry.html",
            },
            "MAN-3": {
                "level":    "strong",
                "baseline": 5,
                "note":     "AWS IAM provides fine-grained RBAC with resource-level permissions, service control policies, and permission boundaries. Least-privilege is enforced via IAM policies.",
                "evidence": "AWS IAM — docs.aws.amazon.com/IAM/latest/UserGuide",
            },
            "HIP-1": {
                "level":    "partial",
                "baseline": 3,
                "note":     "AWS Bedrock does not use customer data for model training by default. PHI minimization in prompts and outputs requires customer-side data handling controls.",
                "evidence": "Amazon Bedrock Data Privacy — docs.aws.amazon.com/bedrock/latest/userguide/data-protection.html",
            },
            "HIP-2": {
                "level":    "none",
                "baseline": 1,
                "note":     "Patient consent and transparency for AI use in clinical workflows is entirely customer responsibility. AWS provides no patient-facing disclosure mechanism.",
                "evidence": "",
            },
            "HIP-3": {
                "level":    "none",
                "baseline": 1,
                "note":     "Clinical decision support oversight is entirely customer responsibility. AWS HealthScribe and Comprehend Medical are tools — clinical review workflows must be customer-designed.",
                "evidence": "",
            },
            "HIP-4": {
                "level":    "strong",
                "baseline": 4,
                "note":     "Amazon Macie automates PHI discovery and classification in S3. AWS Security Hub provides centralized classification and compliance posture management.",
                "evidence": "Amazon Macie — docs.aws.amazon.com/macie/latest/user/what-is-macie.html",
            },
            "HIT-1": {
                "level":    "strong",
                "baseline": 5,
                "note":     "AWS holds ISO 27001, SOC 2 Type II, HITRUST CSF, and FedRAMP High certifications. AWS Security Policy is published and updated regularly.",
                "evidence": "AWS Compliance Programs — aws.amazon.com/compliance/programs",
            },
            "HIT-2": {
                "level":    "strong",
                "baseline": 4,
                "note":     "AWS Privacy by Design is embedded in service architecture. Amazon Bedrock does not retain customer prompts or completions for model training by default.",
                "evidence": "AWS Privacy — aws.amazon.com/privacy",
            },
            "HIT-3": {
                "level":    "strong",
                "baseline": 5,
                "note":     "All AWS services enforce TLS 1.2+ in transit. VPC, PrivateLink, and Direct Connect provide network isolation. Encryption in transit is on by default.",
                "evidence": "AWS Network Security — docs.aws.amazon.com/security/latest/ug/network-security.html",
            },
            "HIT-4": {
                "level":    "strong",
                "baseline": 4,
                "note":     "AWS maintains 99.9%+ SLAs for Bedrock and SageMaker. Multi-AZ and multi-region failover options available. Business continuity documentation published.",
                "evidence": "AWS SLA — aws.amazon.com/legal/service-level-agreements",
            },
        },
    },

    "salesforce": {
        "display_name": "Salesforce",
        "products": [
            "Salesforce Health Cloud", "Einstein AI", "Einstein GPT",
            "Salesforce Einstein Copilot", "Agentforce", "Einstein Discovery",
            "Einstein Prediction Builder", "MuleSoft AI",
        ],
        "detection_keywords": [
            "salesforce", "health cloud", "einstein ai", "einstein gpt",
            "agentforce", "einstein copilot", "einstein discovery",
            "mulesoft ai", "salesforce crm", "salesforce platform",
        ],
        "certifications": [
            "ISO 27001", "ISO 27018", "SOC 1 Type II", "SOC 2 Type II",
            "HIPAA BAA available", "FedRAMP Moderate", "HITRUST CSF",
            "TRUSTe Privacy Seal",
        ],
        "coverage": {
            "GOV-1": {
                "level":    "partial",
                "baseline": 3,
                "note":     "Salesforce publishes its Trusted AI Principles and Einstein AI guidelines. Customer must designate internal accountability ownership for Health Cloud AI deployments.",
                "evidence": "Salesforce Trusted AI — salesforce.com/company/ethical-and-humane-use",
            },
            "GOV-2": {
                "level":    "partial",
                "baseline": 3,
                "note":     "Salesforce Acceptable Use Policy and Einstein AI guidelines define permitted uses. Customer must align deployments to internal policy frameworks.",
                "evidence": "Salesforce Acceptable Use and External Facing Services Policy — salesforce.com/company/legal/agreements",
            },
            "GOV-3": {
                "level":    "strong",
                "baseline": 4,
                "note":     "Salesforce Shield provides Event Monitoring with detailed audit logs of all Einstein AI interactions, user actions, and data access. Configurable retention up to 10 years.",
                "evidence": "Salesforce Shield Event Monitoring — help.salesforce.com/s/articleView?id=sf.salesforce_shield.htm",
            },
            "GOV-4": {
                "level":    "partial",
                "baseline": 3,
                "note":     "Salesforce Einstein Copilot supports human-in-the-loop via confirmation prompts before taking actions. Full override and shutdown mechanisms must be configured by the customer.",
                "evidence": "Einstein Copilot Actions — help.salesforce.com/s/articleView?id=sf.einstein_copilot.htm",
            },
            "MAP-1": {
                "level":    "partial",
                "baseline": 3,
                "note":     "Salesforce Health Cloud is purpose-built for healthcare CRM with defined clinical and administrative use cases. Specific AI deployment scope must be documented by the customer.",
                "evidence": "Salesforce Health Cloud — salesforce.com/products/health-cloud/overview",
            },
            "MAP-2": {
                "level":    "partial",
                "baseline": 3,
                "note":     "Salesforce conducts impact assessments for Einstein AI features. Customer-specific stakeholder impact assessment for clinical and patient-facing deployments is customer responsibility.",
                "evidence": "Salesforce Responsible AI — salesforce.com/company/ethical-and-humane-use/our-approach-to-responsible-ai",
            },
            "MAP-3": {
                "level":    "strong",
                "baseline": 4,
                "note":     "Salesforce Health Cloud is HIPAA-compliant with BAA available. Comprehensive coverage of healthcare regulatory requirements including 21st Century Cures Act interoperability.",
                "evidence": "Salesforce HIPAA Compliance — salesforce.com/company/privacy/compliance/hipaa",
            },
            "MAP-4": {
                "level":    "strong",
                "baseline": 5,
                "note":     "Salesforce Data Processing Addendum (DPA), BAA, and Master Subscription Agreement define all third-party obligations. Subprocessor list published and updated monthly.",
                "evidence": "Salesforce DPA — salesforce.com/company/legal/agreements/data-processing-addendum",
            },
            "MEA-1": {
                "level":    "partial",
                "baseline": 3,
                "note":     "Salesforce provides Einstein AI usage analytics and adoption metrics. Demographic bias monitoring across patient populations is customer responsibility.",
                "evidence": "Einstein Analytics — help.salesforce.com/s/articleView?id=sf.bi_analytics_home.htm",
            },
            "MEA-2": {
                "level":    "partial",
                "baseline": 3,
                "note":     "Einstein Discovery provides model performance metrics and prediction accuracy scores. Deployment-specific KPIs must be defined and tracked by the customer.",
                "evidence": "Einstein Discovery — help.salesforce.com/s/articleView?id=sf.bi_edd_einstein_discovery.htm",
            },
            "MEA-3": {
                "level":    "strong",
                "baseline": 4,
                "note":     "Einstein Discovery provides confidence scores and prediction rationale for every prediction. Einstein Copilot surfaces grounding citations for responses.",
                "evidence": "Einstein Discovery Confidence Scores — help.salesforce.com/s/articleView?id=sf.bi_edd_prediction_explanation.htm",
            },
            "MEA-4": {
                "level":    "partial",
                "baseline": 3,
                "note":     "Einstein Discovery supports automated model refresh on schedule. Data drift alerting requires customer configuration via Salesforce Flow or external monitoring.",
                "evidence": "Einstein Discovery Model Refresh — help.salesforce.com/s/articleView?id=sf.bi_edd_refresh.htm",
            },
            "MEA-5": {
                "level":    "strong",
                "baseline": 4,
                "note":     "Einstein Discovery provides plain-language prediction explanations with top contributing factors for every output — accessible to non-technical users directly in the UI.",
                "evidence": "Einstein Discovery Explainability — help.salesforce.com/s/articleView?id=sf.bi_edd_prediction_explanation.htm",
            },
            "MAN-1": {
                "level":    "partial",
                "baseline": 3,
                "note":     "Salesforce provides a Trust and Security incident response program with public status page. AI-specific incident response for Einstein outputs is customer responsibility.",
                "evidence": "Salesforce Trust — trust.salesforce.com",
            },
            "MAN-2": {
                "level":    "strong",
                "baseline": 4,
                "note":     "Salesforce supports feature flag management, permission set disabling, and sandbox rollback for Einstein features. Decommission procedures documented in admin guides.",
                "evidence": "Salesforce Feature Management — help.salesforce.com/s/articleView?id=sf.feature_management.htm",
            },
            "MAN-3": {
                "level":    "strong",
                "baseline": 5,
                "note":     "Salesforce provides granular permission sets, profiles, and field-level security for Health Cloud. Einstein AI access is controlled via permission sets and license assignment.",
                "evidence": "Salesforce Health Cloud Security — help.salesforce.com/s/articleView?id=sf.health_cloud_security.htm",
            },
            "HIP-1": {
                "level":    "partial",
                "baseline": 3,
                "note":     "Salesforce Health Cloud supports field-level encryption and data masking for PHI. Minimum necessary configuration must be implemented by the customer.",
                "evidence": "Salesforce Shield Platform Encryption — help.salesforce.com/s/articleView?id=sf.security_pe_overview.htm",
            },
            "HIP-2": {
                "level":    "partial",
                "baseline": 3,
                "note":     "Salesforce Health Cloud supports patient consent management workflows. Patient-facing AI transparency disclosures must be configured by the customer.",
                "evidence": "Health Cloud Consent Management — help.salesforce.com/s/articleView?id=sf.consent_management.htm",
            },
            "HIP-3": {
                "level":    "partial",
                "baseline": 3,
                "note":     "Salesforce Health Cloud supports clinician review workflows via Care Plans and Task management. Mandatory clinical oversight for AI outputs must be enforced by the customer.",
                "evidence": "Health Cloud Care Plans — help.salesforce.com/s/articleView?id=sf.health_cloud_care_plans.htm",
            },
            "HIP-4": {
                "level":    "strong",
                "baseline": 4,
                "note":     "Salesforce Shield Platform Encryption classifies and encrypts PHI fields at rest. Data classification labels supported across Health Cloud objects.",
                "evidence": "Salesforce Shield — help.salesforce.com/s/articleView?id=sf.salesforce_shield.htm",
            },
            "HIT-1": {
                "level":    "strong",
                "baseline": 5,
                "note":     "Salesforce holds ISO 27001, SOC 2 Type II, HITRUST CSF, and FedRAMP Moderate certifications. Security policy published and reviewed annually.",
                "evidence": "Salesforce Security — salesforce.com/company/security",
            },
            "HIT-2": {
                "level":    "strong",
                "baseline": 4,
                "note":     "Salesforce applies Privacy by Design with data residency options, data minimization controls, and privacy impact assessments embedded in Health Cloud architecture.",
                "evidence": "Salesforce Privacy by Design — salesforce.com/company/privacy",
            },
            "HIT-3": {
                "level":    "strong",
                "baseline": 5,
                "note":     "Salesforce enforces TLS 1.2+ for all data in transit. Dedicated instances (Hyperforce) provide network isolation with private connectivity options.",
                "evidence": "Salesforce Network Security — help.salesforce.com/s/articleView?id=sf.security_network.htm",
            },
            "HIT-4": {
                "level":    "strong",
                "baseline": 4,
                "note":     "Salesforce maintains 99.9% SLA with multi-region redundancy. Business continuity and disaster recovery documentation published via Salesforce Trust portal.",
                "evidence": "Salesforce SLA — salesforce.com/company/legal/sfdc-website-terms-of-service.jsp",
            },
        },
    },
}


def get_vendor_by_name(name: str) -> dict | None:
    """Look up a vendor by key name."""
    return VENDOR_KB.get(name.lower())


def detect_vendor(use_case: str) -> str | None:
    """
    Detect vendor from use case description using keyword matching.
    Returns vendor key or None.
    """
    text = use_case.lower()
    # Score each vendor by keyword matches
    scores = {}
    for vendor_key, vendor in VENDOR_KB.items():
        score = sum(1 for kw in vendor["detection_keywords"] if kw in text)
        if score > 0:
            scores[vendor_key] = score
    if not scores:
        return None
    return max(scores, key=scores.get)


def get_baseline_scores(vendor_key: str) -> dict:
    """
    Return per-criterion baseline scores for a vendor.
    Returns {criterion_id: baseline_score}
    """
    vendor = VENDOR_KB.get(vendor_key)
    if not vendor:
        return {}
    return {
        cid: data["baseline"]
        for cid, data in vendor["coverage"].items()
    }


def get_vendor_coverage_summary(vendor_key: str) -> dict:
    """Return a summary of vendor coverage statistics."""
    vendor = VENDOR_KB.get(vendor_key)
    if not vendor:
        return {}

    coverage = vendor["coverage"]
    strong  = sum(1 for v in coverage.values() if v["level"] == "strong")
    partial = sum(1 for v in coverage.values() if v["level"] == "partial")
    none_   = sum(1 for v in coverage.values() if v["level"] == "none")

    return {
        "vendor_name":    vendor["display_name"],
        "products":       vendor["products"],
        "certifications": vendor["certifications"],
        "strong":         strong,
        "partial":        partial,
        "none":           none_,
        "total":          len(coverage),
    }
