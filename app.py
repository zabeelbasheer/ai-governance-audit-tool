"""
app.py — Zeta Health AI · Governance Audit
Entry point and dashboard.
"""

import streamlit as st
from auth import require_auth, can_view_all, logout, ROLE_LABELS
from db import get_sessions_for_user, get_all_sessions
from nav import render_nav

st.set_page_config(
    page_title="Zeta Health AI · Governance Audit",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container { padding-top: 1rem !important; }
[data-testid="stSidebarNav"] { display: none; }
</style>
""", unsafe_allow_html=True)

user = require_auth()
render_nav(user)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;align-items:center;gap:14px;margin:8px 0 6px 0">
  <div style="width:44px;height:44px;border-radius:50%;background:#1a3347;
              border:2px solid #e8a020;display:flex;align-items:center;
              justify-content:center;flex-shrink:0">
    <svg width="22" height="22" viewBox="0 0 22 22" xmlns="http://www.w3.org/2000/svg">
      <line x1="4" y1="5" x2="18" y2="5" stroke="#e8a020" stroke-width="2.5" stroke-linecap="round"/>
      <path d="M16 5 Q18 11 4 17" fill="none" stroke="#e8a020" stroke-width="2.5" stroke-linecap="round"/>
      <line x1="4" y1="17" x2="18" y2="17" stroke="#e8a020" stroke-width="2.5" stroke-linecap="round"/>
    </svg>
  </div>
  <div>
    <div style="font-size:9px;color:#b8760a;letter-spacing:2.5px;font-weight:700;margin-bottom:2px">ZETA HEALTH AI</div>
    <div style="font-size:22px;font-weight:700;color:#0f1e2d;font-family:Georgia,serif;line-height:1.1">Governance Audit</div>
    <div style="font-size:11px;color:#4a6580;margin-top:2px">Clinical operations, intelligently governed.</div>
  </div>
</div>
""", unsafe_allow_html=True)
st.divider()

# ── Load sessions ─────────────────────────────────────────────────────────────
if can_view_all(user):
    sessions = get_all_sessions()
    st.subheader("All Audit Sessions")
    st.caption("You have elevated access — viewing all organisational audits.")
else:
    sessions = get_sessions_for_user(user["id"])
    st.subheader("My Audit Sessions")

# ── Search ────────────────────────────────────────────────────────────────────
search = st.text_input(
    "🔍 Search",
    placeholder="Search by user, title, score, or vendor…",
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
        q in s.get("maturity_label", "").lower() or
        q in (s.get("vendor_name") or "").lower()
    ]

# ── Label maps ────────────────────────────────────────────────────────────────
STATUS_EMOJI  = {"intake": "📝", "scored": "📊", "mentoring": "🎓", "complete": "📋"}
STATUS_LABELS = {"intake": "In Progress", "scored": "Scored",
                 "mentoring": "In Review", "complete": "Action Pending"}
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
    h1, h2, h3, h4, h5, h6, h7 = st.columns([3, 2, 1, 1, 1, 1, 1])
    h1.markdown("**Audit Title**")
    h2.markdown("**Submitted by**")
    h3.markdown("**Vendor**")
    h4.markdown("**Score**")
    h5.markdown("**Maturity**")
    h6.markdown("**Status**")
    h7.markdown("**Action**")
    st.markdown("<hr style='margin:4px 0 8px'>", unsafe_allow_html=True)

    for s in sessions:
        c1, c2, c3, c4, c5, c6, c7 = st.columns([3, 2, 1, 1, 1, 1, 1])

        c1.markdown(
            f"**{s['title']}**  \n"
            f"<span style='font-size:11px;color:#888'>{s['created_at'][:10]}</span>",
            unsafe_allow_html=True
        )
        c2.markdown(
            f"{s.get('display_name','—')}  \n"
            f"<span style='font-size:11px;color:#888'>{s.get('email','')}</span>",
            unsafe_allow_html=True
        )

        vendor = s.get("vendor_name") or "—"
        c3.markdown(f"<span style='font-size:11px'>{vendor}</span>", unsafe_allow_html=True)

        if s["overall_pct"] is not None:
            c4.markdown(f"**{s['overall_pct']}%**")
        else:
            c4.markdown("—")

        if s["maturity_label"]:
            color = MATURITY_COLORS.get(s["maturity_label"], "#888")
            c5.markdown(
                f'<span style="color:{color};font-weight:600">{s["maturity_label"]}</span>',
                unsafe_allow_html=True
            )
            if s["status"] == "complete" and s["maturity_label"] in ("Emerging", "Developing"):
                c5.markdown(
                    '<span style="font-size:10px;color:#c0392b">⚠️ Action required</span>',
                    unsafe_allow_html=True
                )
        else:
            c5.markdown("—")

        c6.markdown(
            f"{STATUS_EMOJI.get(s['status'],'—')} "
            f"{STATUS_LABELS.get(s['status'], s['status'].title())}"
        )

        with c7:
            if st.button("Open", key=f"open_{s['id']}"):
                st.session_state.current_session_id = s["id"]
                for key in ["mentor_criterion_idx", "mentor_conversations", "mentor_actions"]:
                    st.session_state.pop(key, None)
                st.switch_page("pages/02_new_audit.py")

        st.markdown("<hr style='margin:4px 0;opacity:0.2'>", unsafe_allow_html=True)
