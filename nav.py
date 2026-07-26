"""
nav.py — Shared sidebar navigation
Call render_nav() at the top of every page after require_auth()
"""

import streamlit as st
from auth import logout, ROLE_LABELS


def render_nav(user: dict):
    with st.sidebar:
        st.markdown(f"**{user['display_name']}**")
        st.caption(ROLE_LABELS[user["role"]])
        st.divider()
        st.page_link("app.py",                label="Dashboard",    icon="📋")
        st.page_link("pages/02_new_audit.py", label="New Audit",    icon="➕")
        st.page_link("pages/03_checklist.py", label="My Checklist", icon="✅")
        st.divider()
        if st.button("Sign Out", use_container_width=True):
            logout()
