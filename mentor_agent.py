"""
mentor_agent.py — Post-audit mentoring agent
Drills into red/amber findings with targeted questions.
Produces specific, actionable next steps per criterion.
"""

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

MENTOR_SYSTEM_PROMPT = """You are an AI governance mentor specializing in healthcare AI systems.
Your role is to help organizations remediate governance gaps identified in a NIST AI RMF + HIPAA audit.

For each governance gap presented to you:
1. Briefly explain WHY this gap is a real risk in healthcare AI context (2 sentences max)
2. Ask ONE diagnostic question to understand the organization's current state
3. Based on their answer, provide a SPECIFIC next step — not generic advice

Rules:
- Be direct and practical — these are operations leaders, not academics
- Reference healthcare BPO context where relevant (RCM, coding, prior auth, clinical ops)
- Never suggest "consult a lawyer" as a primary action — give concrete operational steps
- Frame next steps as 30/60/90 day actions where appropriate
- Keep each response under 150 words"""

NEXT_STEP_SYSTEM_PROMPT = """You are an AI governance action planner for healthcare organizations.
Given a governance gap and a user's answer about their current state, produce ONE specific,
concrete next step they can take in the next 30 days.

Format your response as JSON:
{
  "action": "<specific action in one sentence>",
  "owner": "<suggested role who should own this>",
  "due_days": <integer: suggested days to complete, e.g. 14, 30, 60, 90>,
  "rationale": "<one sentence explaining why this action addresses the gap>"
}

Respond with ONLY the JSON. No markdown, no backticks."""


def get_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))


def get_model():
    return os.getenv("MODEL_NAME", "openai/gpt-oss-120b")


def get_mentor_opening(criterion: dict, use_case: str) -> str:
    """Generate the opening mentor message for a specific red/amber criterion."""
    client = get_client()

    prompt = (
        f"Use case: {use_case}\n\n"
        f"Governance gap found:\n"
        f"Criterion: [{criterion['criterion_id']}] {criterion['criterion_name']}\n"
        f"Function: {criterion['function']}\n"
        f"Score: {criterion['score']}/5\n"
        f"Audit finding: {criterion['rationale']}\n\n"
        f"Start the mentoring conversation for this gap."
    )

    response = get_client().chat.completions.create(
        model=get_model(),
        messages=[
            {"role": "system", "content": MENTOR_SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.3,
        max_tokens=250,
    )
    return response.choices[0].message.content.strip()


def get_mentor_response(criterion: dict, conversation_history: list) -> str:
    """Continue the mentoring conversation."""
    client = get_client()

    context = (
        f"Governance gap: [{criterion['criterion_id']}] {criterion['criterion_name']} "
        f"(Score: {criterion['score']}/5)\n"
        f"Finding: {criterion['rationale']}\n\n"
    )

    messages = [
        {"role": "system", "content": MENTOR_SYSTEM_PROMPT},
        {"role": "user",   "content": context},
    ] + conversation_history

    response = client.chat.completions.create(
        model=get_model(),
        messages=messages,
        temperature=0.3,
        max_tokens=250,
    )
    return response.choices[0].message.content.strip()


def generate_action_item(criterion: dict, user_answer: str) -> dict:
    """
    Given a criterion gap and the user's answer about their current state,
    generate a structured action item for the checklist.
    """
    client = get_client()

    prompt = (
        f"Governance gap: [{criterion['criterion_id']}] {criterion['criterion_name']}\n"
        f"NIST Function: {criterion['function']}\n"
        f"Audit finding: {criterion['rationale']}\n"
        f"Original remediation suggestion: {criterion['remediation']}\n"
        f"User's current state: {user_answer}\n\n"
        f"Generate a specific next action item."
    )

    response = client.chat.completions.create(
        model=get_model(),
        messages=[
            {"role": "system", "content": NEXT_STEP_SYSTEM_PROMPT},
            {"role": "user",   "content": prompt},
        ],
        temperature=0.2,
        max_tokens=200,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        parts = raw.split("```")
        raw = parts[1] if len(parts) > 1 else raw
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        import json
        parsed = json.loads(raw.strip())
        return {
            "criterion_id": criterion["criterion_id"],
            "action":       parsed.get("action", criterion["remediation"]),
            "owner":        parsed.get("owner", ""),
            "due_date":     "",
            "due_days":     parsed.get("due_days", 30),
            "rationale":    parsed.get("rationale", ""),
        }
    except Exception:
        return {
            "criterion_id": criterion["criterion_id"],
            "action":       criterion["remediation"],
            "owner":        "",
            "due_date":     "",
            "due_days":     30,
            "rationale":    "",
        }
