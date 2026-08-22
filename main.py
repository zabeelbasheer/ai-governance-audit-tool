"""
main.py — Zeta Health AI · Governance Audit
FastAPI + vanilla JS web layer, phase 1 of the Streamlit migration.

Phase 1 scope: dashboard shell, session-cookie auth, session list, search.
Reuses db.py and auth.verify_credentials unchanged. The Streamlit app.py
and pages/ directory are left in place until later phases are ported.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from db import init_db, get_sessions_for_user, get_all_sessions
from auth import verify_credentials, ROLE_LABELS


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


@app.get("/")
def index():
    return FileResponse("index.html")
