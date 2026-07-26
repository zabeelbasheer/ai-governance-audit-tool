"""
app.py — Entry point, doubles as Dashboard
"""

import streamlit as st
from auth import require_auth, can_view_all, logout, ROLE_LABELS
from db import get_sessions_for_user, get_all_sessions
from nav import render_nav

st.set_page_config(
    page_title="AI Governance Audit Tool",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

user = require_auth()
render_nav(user)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🛡️ AI Governance Audit Tool")
st.caption(f"Signed in as **{user['display_name']}** · {ROLE_LABELS[user['role']]}")
st.divider()

# ── Load sessions ─────────────────────────────────────────────────────────────
if can_view_all(user):
    sessions = get_all_sessions()
    st.subheader("All Audit Sessions")
    st.caption("You have elevated access — viewing all organizational audits.")
else:
    sessions = get_sessions_for_user(user["id"])
    st.subheader("My Audit Sessions")

# ── Search ────────────────────────────────────────────────────────────────────
search = st.text_input(
    "🔍 Search",
    placeholder="Search by user, idea title, or audit score…",
    label_visibility="collapsed"
)

col_new, _ = st.columns([1, 4])
with col_new:
    if st.button("＋ New Audit", type="primary", use_container_width=True):
        for key in ["current_session_id", "intake_complete",
                    "mentor_criterion_idx", "mentor_conversations", "mentor_actions"]:
            st.session_state.pop(key, None)
        st.switch_page("pages/02_new_audit.py")

st.divider()

# ── Filter ────────────────────────────────────────────────────────────────────
if search:
    q = search.lower()
    sessions = [
        s for s in sessions if
        q in s["title"].lower() or
        q in s.get("display_name", "").lower() or
        q in s.get("email", "").lower() or
        q in str(s.get("overall_pct", "")).lower() or
        q in s.get("maturity_label", "").lower()
    ]

# ── Label maps ────────────────────────────────────────────────────────────────
STATUS_EMOJI = {
    "intake":    "📝",
    "scored":    "📊",
    "mentoring": "🎓",
    "complete":  "📋",
}

STATUS_LABELS = {
    "intake":    "In Progress",
    "scored":    "Scored",
    "mentoring": "In Review",
    "complete":  "Action Pending",
}

MATURITY_COLORS = {
    "Emerging":    "#c0392b",
    "Developing":  "#e67e22",
    "Established": "#f1c40f",
    "Mature":      "#27ae60",
}

# ── Table ─────────────────────────────────────────────────────────────────────
if not sessions:
    st.info("No audits found. Start a new audit to get going.")
else:
    h1, h2, h3, h4, h5, h6 = st.columns([3, 2, 1, 1, 1, 1])
    h1.markdown("**Audit Title**")
    h2.markdown("**Submitted by**")
    h3.markdown("**Score**")
    h4.markdown("**Maturity**")
    h5.markdown("**Status**")
    h6.markdown("**Action**")
    st.markdown("<hr style='margin:4px 0 8px'>", unsafe_allow_html=True)

    for s in sessions:
        c1, c2, c3, c4, c5, c6 = st.columns([3, 2, 1, 1, 1, 1])

        c1.markdown(
            f"**{s['title']}**  \n"
            f"<span style='font-size:11px;color:#888'>{s['created_at'][:10]}</span>",
            unsafe_allow_html=True
        )
        c2.markdown(
            f"{s.get('display_name', '—')}  \n"
            f"<span style='font-size:11px;color:#888'>{s.get('email', '')}</span>",
            unsafe_allow_html=True
        )

        if s["overall_pct"] is not None:
            c3.markdown(f"**{s['overall_pct']}%**")
        else:
            c3.markdown("—")

        if s["maturity_label"]:
            color = MATURITY_COLORS.get(s["maturity_label"], "#888")
            c4.markdown(
                f'<span style="color:{color};font-weight:600">{s["maturity_label"]}</span>',
                unsafe_allow_html=True
            )
            if s["status"] == "complete" and s["maturity_label"] in ("Emerging", "Developing"):
                c4.markdown(
                    '<span style="font-size:10px;color:#c0392b">⚠️ Action required</span>',
                    unsafe_allow_html=True
                )
        else:
            c4.markdown("—")

        c5.markdown(
            f"{STATUS_EMOJI.get(s['status'], '—')} "
            f"{STATUS_LABELS.get(s['status'], s['status'].title())}"
        )

        with c6:
            if st.button("Open", key=f"open_{s['id']}"):
                st.session_state.current_session_id = s["id"]
                for key in ["mentor_criterion_idx", "mentor_conversations", "mentor_actions"]:
                    st.session_state.pop(key, None)
                st.switch_page("pages/02_new_audit.py")

        st.markdown("<hr style='margin:4px 0;opacity:0.2'>", unsafe_allow_html=True)
