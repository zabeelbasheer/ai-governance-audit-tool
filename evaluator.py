"""
evaluator.py — 24-criterion governance evaluation engine
Supports optional vendor baseline scores from the vendor knowledge base.
When a vendor baseline exists for a criterion, the LLM is informed and
adjusts its score accordingly — it can go higher or lower based on
deployment-specific context.
"""

import json
import os
import random
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from groq import Groq, RateLimitError
from criteria import CRITERIA, MATURITY_BANDS
from dotenv import load_dotenv

load_dotenv()

# Groq enforces tokens-per-minute as a rolling 60s window, not an
# in-flight cap. A full 24-criterion audit costs roughly 24 * 1600 =
# ~38k tokens, which cannot fit in one minute at any concurrency level.
# Workers therefore have to pace against a shared budget rather than
# race each other into 429s.
TPM_LIMIT = int(os.getenv("GROQ_TPM_LIMIT", "8000"))
TPM_SAFETY = 0.85  # leave headroom; estimates are approximate by nature


class _TokenBudget:
    """Rolling-window token gate shared across evaluation threads."""

    def __init__(self, limit_per_min: int, window: float = 60.0):
        self.budget = max(1, int(limit_per_min * TPM_SAFETY))
        self.window = window
        self._spent = deque()  # (timestamp, tokens)
        self._lock = Lock()

    def _trim(self, now: float):
        while self._spent and now - self._spent[0][0] >= self.window:
            self._spent.popleft()

    def reserve(self, tokens: int):
        """Block until `tokens` fit inside the rolling window, then record them."""
        while True:
            with self._lock:
                now = time.monotonic()
                self._trim(now)
                in_window = sum(t for _, t in self._spent)
                if in_window + tokens <= self.budget or not self._spent:
                    self._spent.append((now, tokens))
                    return
                # Wait only until the oldest entry ages out of the window.
                sleep_for = self.window - (now - self._spent[0][0])
            time.sleep(max(0.05, min(sleep_for, self.window)) + random.uniform(0, 0.25))


_budget = _TokenBudget(TPM_LIMIT)


def _estimate_tokens(system_prompt: str, user_prompt: str, max_completion: int) -> int:
    """Rough token estimate (~4 chars/token) plus the reserved completion."""
    return (len(system_prompt) + len(user_prompt)) // 4 + max_completion


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
    score = critical_flag = rationale = remediation = None
    unscored = False
    max_retries = 4
    max_completion = 300

    user_prompt = build_user_prompt(
        use_case, criterion, vendor_baseline, vendor_note, vendor_name
    )
    est_tokens = _estimate_tokens(SYSTEM_PROMPT, user_prompt, max_completion)

    for attempt in range(max_retries):
        try:
            # Wait for room in the rolling TPM window before spending it.
            _budget.reserve(est_tokens)
            response = client.chat.completions.create(
                model=os.getenv("MODEL_NAME", "openai/gpt-oss-120b"),
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user",   "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=max_completion,
                response_format={"type": "json_object"},
                reasoning_effort="low",
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
            break

        except RateLimitError as e:
            if attempt == max_retries - 1:
                unscored      = True
                score         = None
                critical_flag = False
                rationale     = f"NOT EVALUATED — rate limited after {max_retries} attempts ({e}). This is a tool fault, not a governance finding."
                remediation   = "Re-run this criterion. Do not interpret as a failing score."
                break
            # Groq's retry-after can be milliseconds ("try again in 7.5ms"),
            # which describes when that token count frees up, not when the
            # window has room for a full call. Floor it, and jitter so
            # concurrent workers don't all retry into the same collision.
            retry_after = e.response.headers.get("retry-after")
            try:
                hinted = float(retry_after) if retry_after else 0.0
            except (TypeError, ValueError):
                hinted = 0.0
            wait = max(hinted + 1, 8.0) + random.uniform(0, 2.0)
            time.sleep(wait)

        except Exception as e:
            unscored      = True
            score         = None
            critical_flag = False
            rationale     = f"NOT EVALUATED — {e}. This is a tool fault, not a governance finding."
            remediation   = "Re-run this criterion. Do not interpret as a failing score."
            break

    return {
        **criterion,
        "score":          score,
        "rationale":      rationale,
        "critical_flag":  critical_flag,
        "remediation":    remediation,
        # Unscored criteria contribute nothing to either side of the ratio.
        "weighted_score": 0 if unscored else score * criterion["weight"],
        "vendor_baseline": vendor_baseline,
        "unscored":       unscored,
    }


def run_evaluation(use_case: str, progress_callback=None,
                   vendor_key: str = None) -> dict:
    """
    Run full 24-criterion evaluation.
    If vendor_key is provided, uses vendor baseline scores to inform the LLM.
    """
    from vendor_kb import VENDOR_KB, get_baseline_scores

    baselines = {}
    vendor_name = None

    if vendor_key and vendor_key in VENDOR_KB:
        baselines   = get_baseline_scores(vendor_key)
        vendor_name = VENDOR_KB[vendor_key]["display_name"]
        vendor_cov  = VENDOR_KB[vendor_key]["coverage"]
    else:
        vendor_cov = {}

    results_by_id = {}
    completed = 0
    progress_lock = Lock()

    def _run_one(criterion):
        cid = criterion["id"]
        # Each task gets its own client rather than sharing one across threads.
        return criterion, evaluate_criterion(
            get_client(), use_case, criterion,
            vendor_baseline=baselines.get(cid),
            vendor_note=vendor_cov.get(cid, {}).get("note"),
            vendor_name=vendor_name,
        )

    # Throughput is capped by TPM, not by worker count. Two workers keep
    # some latency overlap while the shared budget gate does the pacing.
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(_run_one, c) for c in CRITERIA]
        for future in as_completed(futures):
            criterion, result = future.result()
            results_by_id[criterion["id"]] = result
            with progress_lock:
                completed += 1
                if progress_callback:
                    progress_callback(completed, len(CRITERIA), criterion["name"])

    # Reassemble in the original criteria order, not completion order.
    results = [results_by_id[c["id"]] for c in CRITERIA]

    scored   = [r for r in results if not r.get("unscored")]
    unscored = [r for r in results if r.get("unscored")]

    # A criterion that never evaluated is excluded from both sides of the
    # ratio. Leaving it in the denominator at score 1 renders a tool fault
    # as a governance failure, which is what put GOV-4 on the front page of
    # the 10 Sep Athens report as a CRITICAL BLOCKER.
    total_weighted = sum(r["weighted_score"] for r in scored)
    max_weighted   = sum(r["weight"] * 5 for r in scored)
    overall_pct    = round((total_weighted / max_weighted) * 100, 1) if max_weighted else 0.0

    band = next(
        (b for b in MATURITY_BANDS if b[0] <= overall_pct < b[1]),
        MATURITY_BANDS[-1]
    )
    maturity_label = band[2]
    maturity_desc  = band[4]

    # Any gap in coverage makes the headline number provisional, and the
    # report has to say so rather than presenting a partial audit as whole.
    if unscored:
        missing = ", ".join(r["id"] for r in unscored)
        maturity_label = f"{maturity_label} (provisional)"
        maturity_desc = (
            f"{maturity_desc} Scored on {len(scored)} of {len(results)} criteria — "
            f"{missing} did not evaluate and are excluded. Re-run before relying on this figure."
        )

    red_items      = [r for r in scored if r["score"] <= 2]
    amber_items    = [r for r in scored if r["score"] == 3]
    green_items    = [r for r in scored if r["score"] >= 4]
    critical_items = [r for r in scored if r["critical_flag"]]

    return {
        "use_case":       use_case,
        "results":        results,
        "overall_pct":    overall_pct,
        "maturity_label": maturity_label,
        "maturity_color": band[3],
        "maturity_desc":  maturity_desc,
        "critical_items": critical_items,
        "red_items":      red_items,
        "amber_items":    amber_items,
        "green_items":    green_items,
        "unscored_items": unscored,
        "criteria_scored": len(scored),
        "criteria_total":  len(results),
        "is_complete":     not unscored,
        "vendor_key":     vendor_key,
        "vendor_name":    vendor_name,
    }
