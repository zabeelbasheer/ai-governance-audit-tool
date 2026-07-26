"""
recalculate.py — Recalculate all existing audit scores against 24 criteria
Run once after updating criteria.py to v2.0

Usage:
    uv run python recalculate.py
"""

from dotenv import load_dotenv
load_dotenv()

import sys
from db import get_conn, save_audit_results, update_session_scores
from evaluator import run_evaluation
from criteria import MATURITY_BANDS


def recalculate_all():
    conn = get_conn()
    sessions = conn.execute(
        "SELECT * FROM audit_sessions WHERE status IN ('scored','mentoring','complete')"
    ).fetchall()
    conn.close()

    if not sessions:
        print("No scored sessions found. Nothing to recalculate.")
        return

    print(f"Found {len(sessions)} session(s) to recalculate.\n")

    for s in sessions:
        session = dict(s)
        use_case = session.get("use_case_enriched") or session["use_case_raw"]
        print(f"  Recalculating session {session['id']}: {session['title']}...")

        try:
            result = run_evaluation(use_case)
            save_audit_results(session["id"], result["results"])
            update_session_scores(
                session["id"],
                result["overall_pct"],
                result["maturity_label"],
                result["maturity_color"],
                result["maturity_desc"],
            )
            print(f"  ✓ Session {session['id']} — {result['overall_pct']}% ({result['maturity_label']})\n")
        except Exception as e:
            print(f"  ✗ Session {session['id']} failed: {e}\n")

    print("Recalculation complete.")


if __name__ == "__main__":
    recalculate_all()
