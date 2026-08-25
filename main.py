"""
main.py — Zeta Health AI portfolio hub.

AIGAT is mounted at "/", so the bare service URL goes directly to the
tool, not a detour through the portfolio landing page. The landing
page lives at "/portfolio" instead. This is a deliberate trade for
right now: two separate Render services (this one and HR Policy RAG)
means there's no single domain root that can neutrally be "the
portfolio home" without it being someone's tool link first. Once a
real custom domain exists, the landing page can reclaim the true root
and each tool can live at its own clean sub-path or subdomain instead.

Route registration order matters here: /portfolio is registered before
the mount, so it's matched first. Everything else falls through to the
mounted app.

Important: mounting a sub-app via app.mount() does NOT propagate that
sub-app's lifespan to the parent. Each mounted app's startup logic
(here, init_db) has to be called explicitly from the parent's own
lifespan, or it silently never runs, confirmed the hard way, this
app had been running for days against a database that only existed
because it predated this mount structure.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse

from governance_audit_app import app as governance_audit_app
from db import init_db as init_governance_audit_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_governance_audit_db()
    yield

app = FastAPI(title="Zeta Health AI", lifespan=lifespan)


@app.get("/portfolio")
def portfolio():
    return FileResponse("landing.html")

app.mount("/", governance_audit_app)
