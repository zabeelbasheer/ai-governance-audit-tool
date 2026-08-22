"""
evaluator.py — 24-criterion governance evaluation engine
Supports optional vendor baseline scores from the vendor knowledge base.
When a vendor baseline exists for a criterion, the LLM is informed and
adjusts its score accordingly — it can go higher or lower based on
deployment-specific context.
"""

import json
import os
from groq import Groq
from criteria import CRITERIA, MATURITY_BANDS
from dotenv import load_dotenv

load_dotenv()


def get_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))


SYSTEM_PROMPT = """You are a strict AI governance auditor specializing in healthcare AI systems.
Evaluate AI use cases against governance criteria. Be strict — if the description does not
explicitly address a criterion, assume the worst and score low.
Always respond with valid JSON only. No markdown, no backticks, no explanation outside the JSON."""


def build_user_prompt(use_case: str, criterion: dict,
                      vendor_baseline: int = None,
                      vendor_note: str = None,
                      vendor_name: str = None) -> str:

    vendor_section = ""
    if vendor_baseline and vendor_name:
        vendor_section = f"""
Vendor context: This deployment uses {vendor_name}.
Vendor baseline score for this criterion: {vendor_baseline}/5
Vendor note: {vendor_note or "No specific note."}

Adjust your score UP if the deployment-specific description adds controls beyond what the vendor provides.
Adjust your score DOWN if the description reveals gaps or misconfigurations in vendor controls.
State the adjustment reason in your rationale.
"""

    return f"""Evaluate this AI use case against one governance criterion.

AI Use Case:
{use_case}
{vendor_section}
Criterion ID: {criterion['id']}
Criterion Name: {criterion['name']}
Function: {criterion['function']}
Framework: {criterion.get('framework', 'NIST AI RMF')}
What to evaluate: {criterion['description']}

Scoring:
- 1 = completely unaddressed
- 2 = mentioned but no real controls
- 3 = partially addressed
- 4 = mostly addressed with minor gaps
- 5 = fully and explicitly addressed

Respond with ONLY this JSON object:
{{
  "score": <integer 1-5>,
  "rationale": "<2-3 sentences explaining the score>",
  "critical_flag": <true if this blocks deployment, false otherwise>,
  "remediation": "<one concrete action to improve this, or empty string if score is 5>"
}}"""


def evaluate_criterion(client: Groq, use_case: str, criterion: dict,
                       vendor_baseline: int = None,
                       vendor_note: str = None,
                       vendor_name: str = None) -> dict:
    try:
        response = client.chat.completions.create(
            model=os.getenv("MODEL_NAME", "openai/gpt-oss-120b"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": build_user_prompt(
                    use_case, criterion, vendor_baseline, vendor_note, vendor_name
                )},
            ],
            temperature=0.1,
            max_tokens=300,
        )
        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.startswith("json"):
                raw = raw[4:]
        parsed = json.loads(raw.strip())
        score         = max(1, min(5, int(parsed["score"])))
        critical_flag = bool(parsed.get("critical_flag", False))
        rationale     = str(parsed.get("rationale", ""))
        remediation   = str(parsed.get("remediation", ""))
    except Exception as e:
        score         = 1
        critical_flag = False
        rationale     = f"Evaluation failed ({e}) — defaulting to lowest score."
        remediation   = "Re-run evaluation or assess this criterion manually."

    return {
        **criterion,
        "score":          score,
        "rationale":      rationale,
        "critical_flag":  critical_flag,
        "remediation":    remediation,
        "weighted_score": score * criterion["weight"],
        "vendor_baseline": vendor_baseline,
    }


def run_evaluation(use_case: str, progress_callback=None,
                   vendor_key: str = None) -> dict:
    """
    Run full 24-criterion evaluation.
    If vendor_key is provided, uses vendor baseline scores to inform the LLM.
    """
    from vendor_kb import VENDOR_KB, get_baseline_scores

    client   = get_client()
    results  = []
    baselines = {}
    vendor_name = None

    if vendor_key and vendor_key in VENDOR_KB:
        baselines   = get_baseline_scores(vendor_key)
        vendor_name = VENDOR_KB[vendor_key]["display_name"]
        vendor_cov  = VENDOR_KB[vendor_key]["coverage"]
    else:
        vendor_cov = {}

    for i, criterion in enumerate(CRITERIA):
        cid             = criterion["id"]
        vendor_baseline = baselines.get(cid)
        vendor_note     = vendor_cov.get(cid, {}).get("note")

        result = evaluate_criterion(
            client, use_case, criterion,
            vendor_baseline=vendor_baseline,
            vendor_note=vendor_note,
            vendor_name=vendor_name,
        )
        results.append(result)
        if progress_callback:
            progress_callback(i + 1, len(CRITERIA), criterion["name"])

    total_weighted = sum(r["weighted_score"] for r in results)
    max_weighted   = sum(c["weight"] * 5 for c in CRITERIA)
    overall_pct    = round((total_weighted / max_weighted) * 100, 1)

    band = next(
        (b for b in MATURITY_BANDS if b[0] <= overall_pct < b[1]),
        MATURITY_BANDS[-1]
    )

    red_items      = [r for r in results if r["score"] <= 2]
    amber_items    = [r for r in results if r["score"] == 3]
    green_items    = [r for r in results if r["score"] >= 4]
    critical_items = [r for r in results if r["critical_flag"]]

    return {
        "use_case":       use_case,
        "results":        results,
        "overall_pct":    overall_pct,
        "maturity_label": band[2],
        "maturity_color": band[3],
        "maturity_desc":  band[4],
        "critical_items": critical_items,
        "red_items":      red_items,
        "amber_items":    amber_items,
        "green_items":    green_items,
        "vendor_key":     vendor_key,
        "vendor_name":    vendor_name,
    }
