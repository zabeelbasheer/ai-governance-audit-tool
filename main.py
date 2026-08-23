"""
main.py — Zeta Health AI portfolio hub.

Serves the landing page at "/" and mounts individual project apps as
sub-applications at their own path prefixes. This is the consolidation
point so future projects add one mount line each instead of a separate
paid Render service per project.

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

app.mount("/governance-audit", governance_audit_app)


@app.get("/")
def landing():
    return FileResponse("landing.html")
