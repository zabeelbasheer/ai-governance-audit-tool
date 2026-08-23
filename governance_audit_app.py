"""
governance_audit_app.py — Zeta Health AI · Governance Audit
FastAPI + vanilla JS web layer, phases 1 and 2 of the Streamlit migration.

Phase 1: dashboard shell, session-cookie auth, session list, search.
Phase 2: vendor detection, intake chat, evaluation, results view.
Reuses db.py, auth.py, vendor_detector.py, intake_agent.py, and
evaluator.py unchanged. The Streamlit app.py and pages/ directory are
left in place until phases 3 and 4 are ported.
"""

import os
import threading
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from db import (
    init_db, get_sessions_for_user, get_all_sessions,
    create_audit_session, update_session_vendor, update_session_enriched,
    update_session_scores, update_session_status, get_session, save_audit_results,
    get_audit_results, save_intake_message, get_intake_messages,
    save_checklist_items, get_checklist,
)
from auth import verify_credentials, ROLE_LABELS
from vendor_detector import detect_vendor_llm, get_all_vendor_options
from vendor_kb import VENDOR_KB
from intake_agent import get_opening_question, get_next_question, enrich_use_case, build_history_for_llm
from evaluator import run_evaluation
from mentor_agent import get_mentor_opening, get_mentor_response, generate_action_item


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Zeta Health AI · Governance Audit", lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "dev-secret-change-in-production"),
)


def can_view_all(role: str) -> bool:
    """Auditors, DPOs and admins can see all sessions. Mirrors auth.can_view_all."""
    return role in ("auditor", "dpo", "admin")


class LoginBody(BaseModel):
    email: str
    password: str


@app.post("/api/login")
def login(body: LoginBody, request: Request):
    user = verify_credentials(body.email, body.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password. Contact your administrator if you need access.",
        )
    session_user = {
        "id": user["id"],
        "email": user["email"],
        "display_name": user["display_name"],
        "role": user["role"],
    }
    request.session["user"] = session_user
    return {"user": session_user, "role_label": ROLE_LABELS[user["role"]]}


@app.post("/api/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@app.get("/api/me")
def me(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not signed in.")
    return {"user": user, "role_label": ROLE_LABELS[user["role"]]}


@app.get("/api/sessions")
def sessions(request: Request, q: str = ""):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not signed in.")

    rows = get_all_sessions() if can_view_all(user["role"]) else get_sessions_for_user(user["id"])

    if q:
        ql = q.lower()
        rows = [
            r for r in rows
            if ql in (r.get("title") or "").lower()
            or ql in (r.get("display_name") or "").lower()
            or ql in (r.get("email") or "").lower()
            or ql in str(r.get("overall_pct") or "").lower()
            or ql in (r.get("maturity_label") or "").lower()
            or ql in (r.get("vendor_name") or "").lower()
        ]

    return {"sessions": rows, "can_view_all": can_view_all(user["role"])}


# ── Phase 2: new audit flow ──────────────────────────────────────────────────

EVAL_PROGRESS: dict[int, dict] = {}


def _vendor_key_for_session(session: dict) -> str | None:
    """Reverse-lookup vendor_key from the display name stored on the session."""
    stored = session.get("vendor_name")
    if not stored:
        return None
    for key, v in VENDOR_KB.items():
        if v["display_name"] == stored:
            return key
    return None


@app.get("/api/vendors")
def list_vendors(request: Request):
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="Not signed in.")
    return {"vendors": get_all_vendor_options()}


class NewAuditBody(BaseModel):
    title: str = ""
    use_case: str
    vendor_key: str | None = None  # None = auto-detect
    skip_intake: bool = False


@app.post("/api/audits")
def start_audit(body: NewAuditBody, request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not signed in.")
    if not body.use_case.strip():
        raise HTTPException(status_code=400, detail="Describe the AI use case before starting.")

    vendor_key = body.vendor_key
    vendor_display = None
    if vendor_key and vendor_key in VENDOR_KB:
        vendor_display = VENDOR_KB[vendor_key]["display_name"]
    elif not vendor_key:
        detection = detect_vendor_llm(body.use_case)
        if detection.get("detected"):
            vendor_key = detection.get("vendor_key")
            vendor_display = detection.get("vendor_display") or (
                VENDOR_KB[vendor_key]["display_name"] if vendor_key in VENDOR_KB else None
            )

    use_case = body.use_case.strip()
    title = body.title.strip() or (use_case[:60] + ("…" if len(use_case) > 60 else ""))

    if body.skip_intake:
        # Preliminary audit: score the raw description as-is, no clarifying questions.
        # Scores from this path are a rough pass, not the full picture, the intake
        # conversation exists specifically to close gaps a short description leaves open.
        session_id = create_audit_session(user["id"], title, use_case)
        if vendor_display:
            update_session_vendor(session_id, vendor_display)
        return {
            "session_id": session_id,
            "vendor_key": vendor_key,
            "vendor_display": vendor_display,
            "skip_intake": True,
        }

    try:
        opening_q = get_opening_question(use_case, vendor_key)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Couldn't reach the intake model, nothing was saved. Try again. ({e})",
        )

    session_id = create_audit_session(user["id"], title, use_case)
    if vendor_display:
        update_session_vendor(session_id, vendor_display)
    save_intake_message(session_id, "assistant", opening_q)

    return {
        "session_id": session_id,
        "vendor_key": vendor_key,
        "vendor_display": vendor_display,
        "question": opening_q,
    }


class IntakeAnswerBody(BaseModel):
    answer: str


@app.post("/api/audits/{session_id}/intake")
def intake_answer(session_id: int, body: IntakeAnswerBody, request: Request):
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="Not signed in.")

    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Audit session not found.")
    if not body.answer.strip():
        raise HTTPException(status_code=400, detail="Answer can't be empty.")

    save_intake_message(session_id, "user", body.answer.strip())
    history = build_history_for_llm(get_intake_messages(session_id))
    vendor_key = _vendor_key_for_session(session)

    try:
        content, complete = get_next_question(history, vendor_key)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Couldn't reach the intake model. Your answer was saved, try sending again. ({e})",
        )

    if complete:
        try:
            enriched = enrich_use_case(session["use_case_raw"], history, vendor_key)
        except Exception as e:
            raise HTTPException(
                status_code=502,
                detail=f"Intake finished but the summary step failed. Try again. ({e})",
            )
        update_session_enriched(session_id, enriched)
        return {"complete": True, "summary": content}

    save_intake_message(session_id, "assistant", content)
    return {"complete": False, "question": content}


def _run_evaluation_background(session_id: int, use_case: str, vendor_key: str | None):
    def progress_cb(done, total, name):
        EVAL_PROGRESS[session_id] = {"done": done, "total": total, "current": name, "complete": False}

    EVAL_PROGRESS[session_id] = {"done": 0, "total": 24, "current": "Starting…", "complete": False}
    try:
        result = run_evaluation(use_case, progress_callback=progress_cb, vendor_key=vendor_key)
        save_audit_results(session_id, result["results"])
        update_session_scores(
            session_id, result["overall_pct"], result["maturity_label"],
            result["maturity_color"], result["maturity_desc"],
        )
        EVAL_PROGRESS[session_id] = {"done": 24, "total": 24, "current": "Done", "complete": True}
    except Exception as e:
        EVAL_PROGRESS[session_id] = {"done": 0, "total": 24, "current": f"Error: {e}", "complete": True, "error": True}


@app.post("/api/audits/{session_id}/evaluate")
def start_evaluation(session_id: int, request: Request):
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="Not signed in.")

    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Audit session not found.")

    use_case = session.get("use_case_enriched") or session["use_case_raw"]
    vendor_key = _vendor_key_for_session(session)

    thread = threading.Thread(
        target=_run_evaluation_background, args=(session_id, use_case, vendor_key), daemon=True
    )
    thread.start()
    return {"status": "started"}


@app.get("/api/audits/{session_id}/evaluate/progress")
def evaluation_progress(session_id: int, request: Request):
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="Not signed in.")
    return EVAL_PROGRESS.get(session_id, {"done": 0, "total": 24, "current": "", "complete": False})


@app.get("/api/audits/{session_id}")
def get_audit(session_id: int, request: Request):
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="Not signed in.")
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Audit session not found.")
    return {"session": session, "results": get_audit_results(session_id)}


# ── Phase 3: mentor flow ──────────────────────────────────────────────────────

MENTOR_STATE: dict[int, dict] = {}


def _red_amber_criteria(session_id: int) -> list[dict]:
    """Criteria scoring 3 or below, the same red/amber threshold evaluator.py uses."""
    return [r for r in get_audit_results(session_id) if r["score"] <= 3]


@app.post("/api/audits/{session_id}/mentor/start")
def start_mentoring(session_id: int, request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not signed in.")

    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Audit session not found.")
    if session["status"] not in ("scored", "mentoring"):
        raise HTTPException(status_code=400, detail="This audit hasn't been scored yet.")

    gaps = _red_amber_criteria(session_id)
    if not gaps:
        update_session_status(session_id, "complete")
        return {"done": True, "no_gaps": True}

    use_case = session.get("use_case_enriched") or session["use_case_raw"]
    MENTOR_STATE[session_id] = {"gaps": gaps, "index": 0, "items": [], "use_case": use_case}
    update_session_status(session_id, "mentoring")

    current = gaps[0]
    try:
        opening = get_mentor_opening(current, use_case)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Couldn't reach the mentor model. Try again. ({e})")

    MENTOR_STATE[session_id]["current_opening"] = opening

    return {
        "done": False,
        "index": 0,
        "total": len(gaps),
        "criterion": current,
        "message": opening,
    }


class MentorAnswerBody(BaseModel):
    answer: str


@app.post("/api/audits/{session_id}/mentor/answer")
def mentor_answer(session_id: int, body: MentorAnswerBody, request: Request):
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="Not signed in.")

    state = MENTOR_STATE.get(session_id)
    if not state:
        raise HTTPException(status_code=400, detail="No mentoring session in progress, start one first.")
    if not body.answer.strip():
        raise HTTPException(status_code=400, detail="Answer can't be empty.")

    current = state["gaps"][state["index"]]
    answer = body.answer.strip()

    try:
        closing = get_mentor_response(
            current,
            [
                {"role": "assistant", "content": state.get("current_opening", "")},
                {"role": "user", "content": answer},
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Couldn't reach the mentor model. Try again. ({e})")

    try:
        action_item = generate_action_item(current, answer)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Couldn't generate the action item. Try again. ({e})")

    due_days = action_item.get("due_days") or 30
    action_item["due_date"] = (datetime.now() + timedelta(days=due_days)).strftime("%Y-%m-%d")

    state["items"].append(action_item)
    save_checklist_items(session_id, state["items"])

    state["index"] += 1
    if state["index"] >= len(state["gaps"]):
        update_session_status(session_id, "complete")
        del MENTOR_STATE[session_id]
        return {"done": True, "closing_message": closing, "action_item": action_item}

    next_criterion = state["gaps"][state["index"]]
    try:
        next_opening = get_mentor_opening(next_criterion, state["use_case"])
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Couldn't reach the mentor model. Try again. ({e})")
    state["current_opening"] = next_opening

    return {
        "done": False,
        "index": state["index"],
        "total": len(state["gaps"]),
        "criterion": next_criterion,
        "message": next_opening,
        "closing_message": closing,
        "action_item": action_item,
    }


@app.get("/api/audits/{session_id}/checklist")
def get_audit_checklist(session_id: int, request: Request):
    if not request.session.get("user"):
        raise HTTPException(status_code=401, detail="Not signed in.")
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Audit session not found.")
    return {"items": get_checklist(session_id)}


@app.get("/")
def index():
    return FileResponse("index.html")
