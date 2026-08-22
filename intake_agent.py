"""
intake_agent.py — Pre-audit conversational intake agent
Asks targeted clarifying questions one at a time before scoring begins.
Vendor-aware: skips questions about criteria already strongly covered by
the selected vendor.
"""

import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

BASE_INTAKE_PROMPT = """You are an AI governance intake specialist for healthcare organizations.
Your job is to gather enough information about an AI use case to conduct a thorough
governance audit against NIST AI RMF, HIPAA, and HITRUST criteria.

You ask ONE focused question at a time. Questions should uncover gaps in:
- Data: what data is used, whether it includes PHI, how it is handled
- Oversight: who reviews outputs, what human-in-the-loop controls exist
- Accountability: who owns the system, who is responsible for failures
- Deployment: who are the end users, what decisions does the AI influence
- Risk controls: monitoring, rollback, incident response plans

Rules:
- Ask only ONE question per response
- Keep questions concise and plain English — no jargon
- After 5-6 questions, if you have enough context, respond with exactly:
  INTAKE_COMPLETE
  followed by a structured summary of everything learned
- If the user's answer is vague, probe deeper before moving on
- Never ask about topics already clearly covered in prior answers
- Never ask about topics listed under VENDOR COVERAGE ALREADY CONFIRMED below"""

ENRICHMENT_SYSTEM_PROMPT = """You are an AI governance documentation specialist.
Given a conversation between an intake agent and a user describing an AI use case,
produce a single enriched use case description that synthesizes all information gathered.

The enriched description must:
- Be written in clear prose (3-5 paragraphs)
- Cover: purpose, data used, user population, oversight mechanisms,
  accountability ownership, deployment context, and known risk controls
- Explicitly state when something is unknown or not yet in place
- Note vendor-provided controls where confirmed
- Be suitable as input for a detailed NIST AI RMF + HIPAA + HITRUST governance audit

Respond with only the enriched description. No preamble, no labels."""


def get_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))


def get_model():
    return os.getenv("MODEL_NAME", "openai/gpt-oss-120b")


def build_vendor_context(vendor_key: str = None) -> str:
    """
    Build a vendor coverage summary to inject into the intake prompt.
    Only includes 'strong' coverage items — these are confirmed by vendor
    and the intake agent should not ask about them.
    """
    if not vendor_key:
        return ""

    try:
        from vendor_kb import VENDOR_KB
        vendor = VENDOR_KB.get(vendor_key)
        if not vendor:
            return ""

        strong_items = [
            f"- {cid}: {data['note'].split('.')[0]}"
            for cid, data in vendor["coverage"].items()
            if data["level"] == "strong"
        ]

        customer_items = [
            f"- {cid}: {data['note'].split('.')[0]}"
            for cid, data in vendor["coverage"].items()
            if data["level"] == "none"
        ]

        lines = [
            f"\nVENDOR: {vendor['display_name']}",
            f"Certifications: {', '.join(vendor['certifications'][:4])}",
            "",
            "VENDOR COVERAGE ALREADY CONFIRMED (do NOT ask about these):",
        ] + strong_items

        if customer_items:
            lines += [
                "",
                "CUSTOMER RESPONSIBILITY GAPS (prioritise questions on these):",
            ] + customer_items

        return "\n".join(lines)

    except Exception:
        return ""


def get_intake_system_prompt(vendor_key: str = None) -> str:
    """Build the full intake system prompt with optional vendor context."""
    vendor_context = build_vendor_context(vendor_key)
    if vendor_context:
        return BASE_INTAKE_PROMPT + "\n" + vendor_context
    return BASE_INTAKE_PROMPT


def get_opening_question(use_case: str, vendor_key: str = None) -> str:
    """Generate the first targeted question based on the raw use case."""
    client = get_client()
    system_prompt = get_intake_system_prompt(vendor_key)

    response = client.chat.completions.create(
        model=get_model(),
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": (
                    f"The user described this AI use case:\n\n{use_case}\n\n"
                    f"Ask your first clarifying question — focusing on governance "
                    f"gaps not already covered by the vendor."
                )
            }
        ],
        temperature=0.3,
        max_tokens=200,
    )
    return response.choices[0].message.content.strip()


def get_next_question(conversation_history: list,
                      vendor_key: str = None) -> tuple[str, bool]:
    """
    Given conversation history, return (next_question, is_complete).
    If complete, next_question contains the structured summary.
    """
    client = get_client()
    system_prompt = get_intake_system_prompt(vendor_key)

    response = client.chat.completions.create(
        model=get_model(),
        messages=[{"role": "system", "content": system_prompt}] + conversation_history,
        temperature=0.3,
        max_tokens=400,
    )
    content = response.choices[0].message.content.strip()

    if "INTAKE_COMPLETE" in content:
        summary = content.replace("INTAKE_COMPLETE", "").strip()
        return summary, True

    return content, False


def enrich_use_case(use_case_raw: str, conversation_history: list,
                    vendor_key: str = None) -> str:
    """
    Synthesize the raw use case + conversation into an enriched description.
    Includes vendor-confirmed controls in the enriched profile.
    """
    client = get_client()

    vendor_note = ""
    if vendor_key:
        try:
            from vendor_kb import VENDOR_KB
            vendor = VENDOR_KB.get(vendor_key)
            if vendor:
                strong = [
                    f"{cid}: {data['note']}"
                    for cid, data in vendor["coverage"].items()
                    if data["level"] == "strong"
                ]
                vendor_note = (
                    f"\n\nVendor-confirmed controls ({vendor['display_name']}):\n"
                    + "\n".join(strong)
                )
        except Exception:
            pass

    messages = [
        {"role": "system", "content": ENRICHMENT_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"Original use case description:\n{use_case_raw}\n\n"
                f"Intake conversation:\n"
                + "\n".join(
                    f"{m['role'].upper()}: {m['content']}"
                    for m in conversation_history
                )
                + vendor_note
            )
        }
    ]

    response = client.chat.completions.create(
        model=get_model(),
        messages=messages,
        temperature=0.2,
        max_tokens=800,
    )
    return response.choices[0].message.content.strip()


def build_history_for_llm(messages: list) -> list:
    """Convert DB message format to LLM conversation format."""
    return [
        {"role": m["role"], "content": m["content"]}
        for m in messages
    ]
