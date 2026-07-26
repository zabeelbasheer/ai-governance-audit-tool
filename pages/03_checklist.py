"""
pages/03_checklist.py — Action Checklist Tracker
Builds from red/amber audit results. Users can assign owners, due dates, and track status.
"""

import streamlit as st
from auth import require_auth, ROLE_LABELS
from db import (
    get_session, get_audit_results, get_checklist,
    save_checklist_items, update_checklist_item
)

st.set_page_config(page_title="Action Checklist", page_icon="✅", layout="wide")

user = require_auth()

session_id = st.session_state.get("current_session_id")
if not session_id:
    st.warning("No active audit session. Open an audit from the dashboard first.")
    if st.button("Go to Dashboard"):
        st.switch_page("pages/01_dashboard.py")
    st.stop()

session = get_session(session_id)
if not session:
    st.error("Session not found.")
    st.stop()

st.title("✅ Action Checklist")
st.caption(f"Audit: **{session['title']}** · Score: **{session['overall_pct']}%** · {session['maturity_label']}")
st.divider()

# ── Build checklist from audit results if not yet saved ───────────────────────
existing = get_checklist(session_id)
if not existing:
    results    = get_audit_results(session_id)
    actionable = [r for r in results if r["score"] <= 3 and r["remediation"]]
    if actionable:
        items = [
            {
                "criterion_id": r["criterion_id"],
                "action":       r["remediation"],
                "owner":        "",
                "due_date":     "",
            }
            for r in actionable
        ]
        save_checklist_items(session_id, items)
        existing = get_checklist(session_id)

if not existing:
    st.success("No action items — this audit has no red or amber findings.")
    st.stop()

# ── Summary metrics ───────────────────────────────────────────────────────────
total    = len(existing)
complete = sum(1 for i in existing if i["status"] == "complete")
in_prog  = sum(1 for i in existing if i["status"] == "in_progress")
pending  = sum(1 for i in existing if i["status"] == "pending")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Actions", total)
m2.metric("Pending",       pending)
m3.metric("In Progress",   in_prog)
m4.metric("Complete",      complete)

progress_pct = int((complete / total) * 100) if total else 0
st.progress(progress_pct, text=f"Completion: {progress_pct}%")
st.divider()

# ── Export ────────────────────────────────────────────────────────────────────
csv_lines = ["Criterion,Action,Owner,Due Date,Status"]
for item in existing:
    csv_lines.append(
        f'"{item["criterion_id"]}","{item["action"]}","{item["owner"] or ""}","{item["due_date"] or ""}","{item["status"]}"'
    )
st.download_button(
    "⬇️ Export Checklist (.csv)",
    data="\n".join(csv_lines),
    file_name=f"checklist_audit_{session_id}.csv",
    mime="text/csv",
)

st.divider()

# ── Checklist items ───────────────────────────────────────────────────────────
STATUS_OPTIONS = ["pending", "in_progress", "complete"]
STATUS_EMOJI   = {"pending": "⏳", "in_progress": "🔄", "complete": "✅"}

st.subheader("Action Items")

for item in existing:
    color = "#c0392b" if item["status"] == "pending" else (
            "#e67e22" if item["status"] == "in_progress" else "#27ae60")

    with st.expander(
        f"{STATUS_EMOJI[item['status']]} [{item['criterion_id']}] {item['action'][:80]}…"
        if len(item["action"]) > 80 else
        f"{STATUS_EMOJI[item['status']]} [{item['criterion_id']}] {item['action']}"
    ):
        st.markdown(f"**Full action:** {item['action']}")
        st.markdown(f"**Added:** {item['created_at'][:10]}")

        c1, c2, c3 = st.columns([2, 2, 2])
        with c1:
            new_status = st.selectbox(
                "Status",
                STATUS_OPTIONS,
                index=STATUS_OPTIONS.index(item["status"]),
                key=f"status_{item['id']}",
                format_func=lambda x: f"{STATUS_EMOJI[x]} {x.replace('_',' ').title()}"
            )
        with c2:
            new_owner = st.text_input(
                "Owner",
                value=item["owner"] or "",
                placeholder="Name or team",
                key=f"owner_{item['id']}"
            )
        with c3:
            new_due = st.text_input(
                "Due date",
                value=item["due_date"] or "",
                placeholder="YYYY-MM-DD",
                key=f"due_{item['id']}"
            )

        if st.button("Save", key=f"save_{item['id']}", type="primary"):
            update_checklist_item(item["id"], new_status, new_owner, new_due)
            st.success("Saved.")
            st.rerun()
