import json
import os
from groq import Groq
from criteria import CRITERIA, MATURITY_BANDS


def get_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))


SYSTEM_PROMPT = """You are a strict AI governance auditor specializing in healthcare AI systems.
Evaluate AI use cases against governance criteria. Be strict — if the description does not 
explicitly address a criterion, assume the worst and score low.
Always respond with valid JSON only. No markdown, no backticks, no explanation outside the JSON."""


def build_user_prompt(use_case: str, criterion: dict) -> str:
    return f"""Evaluate this AI use case against one governance criterion.

AI Use Case:
{use_case}

Criterion ID: {criterion['id']}
Criterion Name: {criterion['name']}
Function: {criterion['function']}
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


def evaluate_criterion(client: Groq, use_case: str, criterion: dict) -> dict:
    try:
        response = client.chat.completions.create(
            model=os.getenv("MODEL_NAME", "llama3-70b-8192"),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": build_user_prompt(use_case, criterion)},
            ],
            temperature=0.1,
            max_tokens=300,
        )
        raw = response.choices[0].message.content.strip()

        # Strip markdown fences if model adds them
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.startswith("json"):
                raw = raw[4:]

        parsed = json.loads(raw.strip())
        score = max(1, min(5, int(parsed["score"])))
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
    }


def run_evaluation(use_case: str, progress_callback=None) -> dict:
    client  = get_client()
    results = []

    for i, criterion in enumerate(CRITERIA):
        result = evaluate_criterion(client, use_case, criterion)
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
    }
