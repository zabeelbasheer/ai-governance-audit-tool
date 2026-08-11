"""
nav.py — Shared sidebar navigation with Zeta Health AI branding
"""

import streamlit as st
from auth import logout, ROLE_LABELS

ZETA_MARK_SVG = """
<div style="width:32px;height:32px;border-radius:50%;background:#1a3347;
            border:1.5px solid #e8a020;display:flex;align-items:center;
            justify-content:center;flex-shrink:0">
  <svg width="16" height="16" viewBox="0 0 22 22" xmlns="http://www.w3.org/2000/svg">
    <line x1="4" y1="5" x2="18" y2="5" stroke="#e8a020" stroke-width="2.5" stroke-linecap="round"/>
    <path d="M16 5 Q18 11 4 17" fill="none" stroke="#e8a020" stroke-width="2.5" stroke-linecap="round"/>
    <line x1="4" y1="17" x2="18" y2="17" stroke="#e8a020" stroke-width="2.5" stroke-linecap="round"/>
  </svg>
</div>"""


def render_nav(user: dict):
    with st.sidebar:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;margin:4px 0 16px 0">
          {ZETA_MARK_SVG}
          <div>
            <div style="font-size:8px;color:#b8760a;letter-spacing:2px;font-weight:700">ZETA HEALTH AI</div>
            <div style="font-size:12px;font-weight:700;color:#0f1e2d;font-family:Georgia,serif">Governance Audit</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(
            f"<div style='font-size:11px;color:#666;margin-bottom:4px'>"
            f"<strong>{user['display_name']}</strong></div>"
            f"<div style='font-size:10px;color:#8fa8bf;margin-bottom:12px'>"
            f"{ROLE_LABELS[user['role']]}</div>",
            unsafe_allow_html=True
        )
        st.divider()
        st.page_link("app.py",                label="Dashboard",    icon="📋")
        st.page_link("pages/02_new_audit.py", label="New Audit",    icon="➕")
        st.page_link("pages/03_checklist.py", label="My Checklist", icon="✅")
        st.divider()
        if st.button("Sign Out", use_container_width=True):
            logout()
