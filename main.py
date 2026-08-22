"""
main.py — Zeta Health AI portfolio hub.

Serves the landing page at "/" and mounts individual project apps as
sub-applications at their own path prefixes. This is the consolidation
point so future projects add one mount line each instead of a separate
paid Render service per project.
"""

from fastapi import FastAPI
from fastapi.responses import FileResponse

from governance_audit_app import app as governance_audit_app

app = FastAPI(title="Zeta Health AI")

app.mount("/governance-audit", governance_audit_app)


@app.get("/")
def landing():
    return FileResponse("landing.html")
