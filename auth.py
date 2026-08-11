"""
auth.py — Authentication stub
Designed to be replaced by AD SSO (SAML2 / OAuth2 / MSAL) with zero changes
to the rest of the app. The session contract (st.session_state.user) stays
identical whether auth comes from this stub or Azure AD.

AD migration path:
  1. Replace verify_credentials() with MSAL token validation
  2. Replace the login form with an Azure AD redirect
  3. Map AD group claims to roles in get_role_from_claims()
  4. Everything else in the app remains unchanged
"""

import streamlit as st
import bcrypt
from db import get_user_by_email, update_last_login, init_db


ROLE_LABELS = {
    "user":    "User",
    "auditor": "AI Governance Auditor",
    "dpo":     "Data Protection Officer",
    "admin":   "System Admin",
}


def verify_credentials(email: str, password: str):
    """Returns user dict on success, None on failure."""
    user = get_user_by_email(email.strip().lower())
    if not user:
        return None
    try:
        if bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            update_last_login(user["id"])
            return user
    except Exception:
        pass
    return None


def render_login():
    """Renders the login form. Returns True if authenticated this call."""
    st.markdown("""
    <style>
    .login-container {
        max-width: 420px;
        margin: 60px auto 0;
        padding: 40px;
        border: 1px solid #ddd;
        border-radius: 8px;
        background: #fff;
    }
    .login-logo {
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 4px;
        color: #1a1a1a;
    }
    .login-sub {
        font-size: 13px;
        color: #666;
        margin-bottom: 28px;
    }
    .login-notice {
        font-size: 11px;
        color: #999;
        margin-top: 20px;
        padding-top: 16px;
        border-top: 1px solid #eee;
    }
    </style>
    <style>
    .login-wrap {
        max-width: 420px;
        margin: 60px auto 0;
        padding: 40px;
        border: 1px solid #d8d4cc;
        border-radius: 8px;
        background: #fff;
    }
    .login-sub {
        font-size: 13px;
        color: #666;
        margin-bottom: 28px;
    }
    .login-notice {
        font-size: 11px;
        color: #999;
        margin-top: 20px;
        padding-top: 16px;
        border-top: 1px solid #eee;
        text-align: center;
    }
    </style>
    <div class="login-wrap">
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px">
        <div style="width:40px;height:40px;border-radius:50%;background:#1a3347;
                    border:2px solid #e8a020;display:flex;align-items:center;
                    justify-content:center;flex-shrink:0">
          <svg width="20" height="20" viewBox="0 0 22 22" xmlns="http://www.w3.org/2000/svg">
            <line x1="4" y1="5" x2="18" y2="5" stroke="#e8a020" stroke-width="2.5" stroke-linecap="round"/>
            <path d="M16 5 Q18 11 4 17" fill="none" stroke="#e8a020" stroke-width="2.5" stroke-linecap="round"/>
            <line x1="4" y1="17" x2="18" y2="17" stroke="#e8a020" stroke-width="2.5" stroke-linecap="round"/>
          </svg>
        </div>
        <div>
          <div style="font-size:8px;color:#b8760a;letter-spacing:2.5px;font-weight:700">ZETA HEALTH AI</div>
          <div style="font-size:18px;font-weight:700;color:#0f1e2d;font-family:Georgia,serif;line-height:1.1">Governance Audit</div>
        </div>
      </div>
      <div class="login-sub">Sign in with your organisational account</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        email    = st.text_input("Email address", placeholder="you@shearwater.com")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", use_container_width=True, type="primary")

    st.markdown("""
    <div style="max-width:420px;margin:0 auto;font-size:11px;color:#999;text-align:center;margin-top:8px">
    This system is for authorized users only. All activity is logged.<br>
    <span style="color:#1a3a4a">Single Sign-On (AD) integration active in production.</span>
    </div>
    """, unsafe_allow_html=True)

    if submitted:
        if not email or not password:
            st.error("Enter your email and password.")
            return False
        user = verify_credentials(email, password)
        if user:
            st.session_state.user = user
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect email or password. Contact your administrator if you need access.")
            return False
    return False


def require_auth():
    """
    Call at the top of every page.
    Renders login if not authenticated, returns user dict if authenticated.
    """
    init_db()
    if not st.session_state.get("authenticated"):
        render_login()
        st.stop()
    return st.session_state.user


def can_view_all(user: dict) -> bool:
    """Auditors, DPOs and admins can see all sessions."""
    return user["role"] in ("auditor", "dpo", "admin")


def logout():
    for key in ["user", "authenticated", "current_session_id", "intake_complete"]:
        st.session_state.pop(key, None)
    st.rerun()
