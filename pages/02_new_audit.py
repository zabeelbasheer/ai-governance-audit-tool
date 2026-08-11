"""
pages/02_new_audit.py — Zeta Health AI · Governance Audit
Full audit flow with vendor knowledge base integration.
"""

import streamlit as st
import plotly.graph_objects as go
from auth import require_auth, ROLE_LABELS
from nav import render_nav
from db import (
    create_audit_session, get_session, update_session_scores,
    save_audit_results, get_audit_results, update_session_status,
    save_intake_message, get_intake_messages, update_session_enriched,
    save_checklist_items, get_checklist
)
from evaluator import run_evaluation
from report_generator import generate_text_report
from criteria import FUNCTION_COLORS
from intake_agent import get_opening_question, get_next_question, enrich_use_case, build_history_for_llm
from mentor_agent import get_mentor_opening, get_mentor_response, generate_action_item
from vendor_detector import detect_vendor_llm, get_all_vendor_options
from vendor_kb import VENDOR_KB, get_vendor_coverage_summary
from datetime import datetime, timedelta

st.set_page_config(page_title="Zeta Health AI · New Audit", page_icon="🛡️", layout="wide")

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

# ── Session bootstrap ─────────────────────────────────────────────────────────
session_id = st.session_state.get("current_session_id")

if not session_id:
    st.subheader("Step 1 — Describe your AI use case")

    with st.form("intake_form"):
        title        = st.text_input("Audit title", placeholder="e.g. Microsoft Copilot — Prior Auth Decision Support")
        use_case_raw = st.text_area(
            "Briefly describe your AI use case",
            height=140,
            placeholder="What does the AI do? Who uses it? What data does it touch? Which vendor or platform is involved?"
        )
        submitted = st.form_submit_button("Start →", type="primary")

    if submitted:
        if not title.strip() or not use_case_raw.strip():
            st.warning("Both fields are required.")
            st.stop()
        if len(use_case_raw.strip()) < 20:
            st.warning("Provide a bit more detail to get started.")
            st.stop()

        # Detect vendor from description
        with st.spinner("Detecting vendor…"):
            detection = detect_vendor_llm(use_case_raw.strip())

        vendor_key_for_intake = detection.get("vendor_key") if detection.get("detected") else None

        sid = create_audit_session(user["id"], title.strip(), use_case_raw.strip())
        save_intake_message(sid, "user", use_case_raw.strip())
        opening_q = get_opening_question(
            use_case_raw.strip(),
            vendor_key=vendor_key_for_intake,
        )
        save_intake_message(sid, "assistant", opening_q)

        st.session_state.current_session_id = sid
        st.session_state.detected_vendor    = detection
        st.rerun()
    st.stop()

# ── Load session ──────────────────────────────────────────────────────────────
session = get_session(session_id)
if not session:
    st.error("Session not found.")
    st.stop()

st.markdown(f"### {session['title']}")
st.caption(f"Status: **{session['status'].title()}** · Created: {session['created_at'][:10]}")

# ── Vendor selector ───────────────────────────────────────────────────────────
detection    = st.session_state.get("detected_vendor", {})
vendor_opts  = get_all_vendor_options()
opt_labels   = [o["label"] for o in vendor_opts]
opt_keys     = [o["key"]   for o in vendor_opts]

detected_key = detection.get("vendor_key")
default_idx  = opt_keys.index(detected_key) if (detected_key and detected_key in opt_keys) else 0

# Only show "detected" label and auto-expand after a session exists and detection ran
vendor_detected_label = (
    f" — {detection.get('vendor_display', '')} detected"
    if detection.get("detected") and detected_key
    else " — None detected"
)

with st.expander(
    f"🏢 Vendor / Platform{vendor_detected_label}",
    expanded=bool(detected_key)
):
    selected_label = st.selectbox(
        "Select the AI vendor or platform being used",
        opt_labels,
        index=default_idx,
        key="vendor_select",
    )
    selected_key = opt_keys[opt_labels.index(selected_label)]

    if selected_key:
        summary = get_vendor_coverage_summary(selected_key)
        vendor  = VENDOR_KB[selected_key]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Strong coverage",  summary["strong"])
        col2.metric("Partial coverage", summary["partial"])
        col3.metric("Customer owned",   summary["none"])
        col4.metric("Certifications",   len(summary["certifications"]))

        st.markdown(
            f"<div style='font-size:11px;color:#4a6580;margin-top:8px'>"
            f"<strong>Certifications:</strong> {', '.join(summary['certifications'])}</div>",
            unsafe_allow_html=True
        )
        st.caption("Vendor baseline scores will inform the evaluator. You can override any score in the audit results.")
    else:
        st.caption("No vendor selected — all 24 criteria will be scored from scratch.")

st.divider()

# ── Resolve active vendor key (from selectbox, fallback to detected) ──────────
active_vendor_key = selected_key if selected_key else detected_key

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1 — INTAKE
# ══════════════════════════════════════════════════════════════════════════════
if session["status"] == "intake":
    st.subheader("Step 2 — Intake")
    st.caption("The intake agent will ask a few clarifying questions before the audit runs.")

    messages  = get_intake_messages(session_id)
    last_role = messages[-1]["role"] if messages else "assistant"

    for m in messages:
        if m["role"] == "assistant":
            with st.chat_message("assistant", avatar="🛡️"):
                st.markdown(m["content"])
        else:
            with st.chat_message("user", avatar="👤"):
                st.markdown(m["content"])

    if last_role == "user":
        history = build_history_for_llm(messages)
        with st.spinner("Thinking…"):
            next_msg, is_complete = get_next_question(
                history,
                vendor_key=active_vendor_key,
            )

        save_intake_message(session_id, "assistant", next_msg)

        if is_complete:
            with st.spinner("Synthesising your responses…"):
                enriched = enrich_use_case(
                    session["use_case_raw"],
                    build_history_for_llm(get_intake_messages(session_id)),
                    vendor_key=active_vendor_key,
                )
            update_session_enriched(session_id, enriched)
            st.rerun()
        else:
            st.rerun()

    if last_role == "assistant":
        user_reply = st.chat_input("Your answer…")
        if user_reply:
            save_intake_message(session_id, "user", user_reply.strip())
            st.rerun()

    with st.expander("Skip intake and run audit now"):
        st.caption("The audit will run on your original description only.")
        if st.button("Skip → Run Audit directly"):
            update_session_enriched(session_id, session["use_case_raw"])
            update_session_status(session_id, "scoring")
            st.rerun()

    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — SCORING
# ══════════════════════════════════════════════════════════════════════════════
if session["status"] in ("intake", "scoring") and session.get("use_case_enriched"):
    st.subheader("Step 3 — Running Governance Audit")
    use_case_to_score = session.get("use_case_enriched") or session["use_case_raw"]

    with st.expander("View enriched use case profile"):
        st.markdown(use_case_to_score)

    progress_bar = st.progress(0, text="Starting evaluation…")

    def update_progress(current, total, name):
        progress_bar.progress(int((current / total) * 100), text=f"Evaluating {current}/{total}: {name}")

    with st.spinner("Running 24-criterion governance audit…"):
        result = run_evaluation(
            use_case_to_score,
            progress_callback=update_progress,
            vendor_key=active_vendor_key,
        )

    progress_bar.empty()
    save_audit_results(session_id, result["results"])
    update_session_scores(
        session_id,
        result["overall_pct"],
        result["maturity_label"],
        result["maturity_color"],
        result["maturity_desc"],
    )
    update_session_status(session_id, "scored")
    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 3 — RESULTS
# ══════════════════════════════════════════════════════════════════════════════
if session["status"] in ("scored", "mentoring", "complete"):
    results     = get_audit_results(session_id)
    red_items   = [r for r in results if r["score"] <= 2]
    amber_items = [r for r in results if r["score"] == 3]
    green_items = [r for r in results if r["score"] >= 4]
    crit_items  = [r for r in results if r["critical_flag"]]

    # Vendor context banner
    if active_vendor_key and active_vendor_key in VENDOR_KB:
        vendor_info = VENDOR_KB[active_vendor_key]
        st.markdown(
            f'<div style="background:#f7f4ee;border:1px solid #d8d4cc;border-left:3px solid #e8a020;'
            f'padding:10px 16px;border-radius:0 6px 6px 0;margin-bottom:12px;font-size:12px">'
            f'<strong>🏢 Vendor context: {vendor_info["display_name"]}</strong> — '
            f'Baseline scores from vendor knowledge base applied to this audit. '
            f'LLM adjusted scores based on your specific deployment description.'
            f'</div>',
            unsafe_allow_html=True
        )

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Overall Score",       f"{session['overall_pct']}%")
    m2.metric("Maturity",            session["maturity_label"])
    m3.metric("Critical Blockers",   len(crit_items))
    m4.metric("Red / Amber / Green", f"{len(red_items)} / {len(amber_items)} / {len(green_items)}")

    color = session["maturity_color"] or "#888"
    st.markdown(
        f'<div style="background:{color};color:white;padding:12px 20px;'
        f'border-radius:6px;margin:12px 0">'
        f'<strong>{session["maturity_label"]}</strong> — {session["maturity_desc"]}'
        f'</div>',
        unsafe_allow_html=True
    )

    # Radar chart
    st.divider()
    st.subheader("Governance Radar")
    functions = ["GOVERN", "MAP", "MEASURE", "MANAGE", "HIPAA", "HITRUST"]
    fn_scores = {}
    fn_max    = {}
    for r in results:
        fn = r["function"]
        fn_scores[fn] = fn_scores.get(fn, 0) + r["weighted_score"]
        fn_max[fn]    = fn_max.get(fn, 0) + (r["weight"] * 5)

    radar_scores = [
        round((fn_scores.get(fn, 0) / fn_max.get(fn, 1)) * 100, 1)
        for fn in functions
    ]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=radar_scores + [radar_scores[0]],
        theta=functions + [functions[0]],
        fill="toself",
        fillcolor="rgba(26,51,71,0.15)",
        line=dict(color="#1a3347", width=2),
        name="Governance Score",
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], ticksuffix="%")),
        showlegend=False,
        margin=dict(l=40, r=40, t=40, b=40),
        height=360,
    )
    st.plotly_chart(fig, width="stretch")

    fn_cols = st.columns(len(functions))
    for i, fn in enumerate(functions):
        score = radar_scores[i]
        c = "#c0392b" if score < 40 else ("#e67e22" if score < 65 else ("#f1c40f" if score < 80 else "#27ae60"))
        fn_cols[i].markdown(
            f'<div style="text-align:center">'
            f'<div style="font-size:20px;font-weight:700;color:{c}">{score}%</div>'
            f'<div style="font-size:10px;color:#666">{fn}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    # Critical blockers
    if crit_items:
        st.divider()
        st.subheader("⚠️ Critical Blockers")
        for r in crit_items:
            with st.expander(f"[{r['criterion_id']}] {r['criterion_name']}"):
                st.markdown(f"**Rationale:** {r['rationale']}")
                st.markdown(f"**Remediation:** {r['remediation']}")
                if r.get("vendor_baseline"):
                    st.markdown(f"**Vendor baseline:** {r['vendor_baseline']}/5")

    # Risk matrix
    st.divider()
    st.subheader("Risk Matrix")
    tab_all, tab_red, tab_amber, tab_green = st.tabs([
        f"All ({len(results)})",
        f"🔴 Red ({len(red_items)})",
        f"🟡 Amber ({len(amber_items)})",
        f"🟢 Green ({len(green_items)})",
    ])

    def render_list(items):
        if not items:
            st.caption("No items in this category.")
            return
        for r in items:
            score = r["score"]
            bc    = "#c0392b" if score <= 2 else ("#e67e22" if score == 3 else "#27ae60")
            dot   = "🔴" if score <= 2 else ("🟡" if score == 3 else "🟢")
            fn_color  = FUNCTION_COLORS.get(r["function"], "#555")
            crit_tag  = " ⚠️ CRITICAL" if r["critical_flag"] else ""
            vendor_tag = ""
            if r.get("vendor_baseline"):
                vendor_tag = (
                    f'&nbsp;<span style="background:#e8a020;color:white;padding:1px 7px;'
                    f'border-radius:8px;font-size:10px">Vendor base: {r["vendor_baseline"]}/5</span>'
                )
            st.markdown(
                f'<div style="border-left:3px solid {bc};padding:10px 16px;'
                f'margin-bottom:8px;background:#fafafa;border-radius:0 4px 4px 0">'
                f'<strong>{dot} [{r["criterion_id"]}] {r["criterion_name"]}{crit_tag}</strong>'
                f'&nbsp;&nbsp;<span style="background:{fn_color};color:white;padding:2px 8px;'
                f'border-radius:3px;font-size:11px">{r["function"]}</span>'
                f'{vendor_tag}'
                f'&nbsp;&nbsp;<span style="color:{bc};font-weight:600">Score: {score}/5</span><br>'
                f'<span style="color:#555;font-size:13px">{r["rationale"]}</span>'
                + (f'<br><span style="font-size:12px">→ {r["remediation"]}</span>' if r["remediation"] else "")
                + '</div>',
                unsafe_allow_html=True
            )

    with tab_all:   render_list(results)
    with tab_red:   render_list(red_items)
    with tab_amber: render_list(amber_items)
    with tab_green: render_list(green_items)

    # Download + mentor
    st.divider()
    report_data = {
        "use_case":       session.get("use_case_enriched") or session["use_case_raw"],
        "overall_pct":    session["overall_pct"],
        "maturity_label": session["maturity_label"],
        "maturity_desc":  session["maturity_desc"],
        "maturity_color": session["maturity_color"],
        "critical_items": crit_items,
        "red_items":      red_items,
        "amber_items":    amber_items,
        "green_items":    green_items,
        "results":        results,
    }
    col_dl, col_mentor = st.columns([1, 1])
    with col_dl:
        st.download_button(
            "⬇️ Download Audit Report",
            data=generate_text_report(report_data),
            file_name=f"audit_{session_id}_{session['overall_pct']}pct.txt",
            mime="text/plain",
            use_container_width=True,
        )
    with col_mentor:
        if session["status"] == "scored":
            if st.button("🎓 Start Mentor Session →", type="primary", use_container_width=True):
                update_session_status(session_id, "mentoring")
                st.rerun()
        elif session["status"] in ("mentoring", "complete"):
            if st.button("✅ View Checklist →", type="primary", use_container_width=True):
                st.switch_page("pages/03_checklist.py")

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 4 — MENTOR
# ══════════════════════════════════════════════════════════════════════════════
if session["status"] in ("mentoring", "complete"):
    results = get_audit_results(session_id)
    gaps    = [r for r in results if r["score"] <= 3]

    if not gaps:
        st.info("No red or amber items to mentor — your governance posture is strong.")
        st.stop()

    st.divider()
    st.subheader("🎓 Mentor Session")
    st.caption(f"Working through {len(gaps)} governance gaps.")

    if "mentor_criterion_idx" not in st.session_state: st.session_state.mentor_criterion_idx   = 0
    if "mentor_conversations" not in st.session_state: st.session_state.mentor_conversations   = {}
    if "mentor_actions"       not in st.session_state: st.session_state.mentor_actions         = {}

    idx = st.session_state.mentor_criterion_idx
    st.progress(min(idx / len(gaps), 1.0), text=f"Gap {min(idx+1, len(gaps))} of {len(gaps)}")

    if idx >= len(gaps):
        st.success(f"✅ Mentor session complete — {len(st.session_state.mentor_actions)} action items generated.")
        if st.button("Save to Checklist & Finish", type="primary"):
            items = []
            for action_item in st.session_state.mentor_actions.values():
                due = (datetime.now() + timedelta(days=action_item.get("due_days", 30))).strftime("%Y-%m-%d")
                items.append({
                    "criterion_id": action_item["criterion_id"],
                    "action":       action_item["action"],
                    "owner":        action_item.get("owner", ""),
                    "due_date":     due,
                })
            save_checklist_items(session_id, items)
            update_session_status(session_id, "complete")
            for k in ["mentor_criterion_idx", "mentor_conversations", "mentor_actions"]:
                st.session_state.pop(k, None)
            st.switch_page("pages/03_checklist.py")
        st.stop()

    criterion     = gaps[idx]
    criterion_key = criterion["criterion_id"]

    if criterion_key not in st.session_state.mentor_conversations:
        opening = get_mentor_opening(criterion, session.get("use_case_enriched") or session["use_case_raw"])
        st.session_state.mentor_conversations[criterion_key] = [
            {"role": "assistant", "content": opening}
        ]

    score = criterion["score"]
    bc    = "#c0392b" if score <= 2 else "#e67e22"
    st.markdown(
        f'<div style="border-left:3px solid {bc};padding:10px 16px;'
        f'background:#fafafa;margin-bottom:12px;border-radius:0 4px 4px 0">'
        f'<strong>[{criterion["criterion_id"]}] {criterion["criterion_name"]}</strong> — '
        f'Score: {score}/5<br>'
        f'<span style="font-size:13px;color:#555">{criterion["rationale"]}</span>'
        f'</div>',
        unsafe_allow_html=True
    )

    conv = st.session_state.mentor_conversations[criterion_key]
    for m in conv:
        if m["role"] == "assistant":
            with st.chat_message("assistant", avatar="🎓"):
                st.markdown(m["content"])
        else:
            with st.chat_message("user", avatar="👤"):
                st.markdown(m["content"])

    col_input, col_skip = st.columns([4, 1])
    with col_input:
        user_reply = st.chat_input(
            f"Your response for [{criterion_key}]…",
            key=f"mentor_input_{criterion_key}_{idx}"
        )
    with col_skip:
        st.write("")
        st.write("")
        if st.button("Skip →", key=f"skip_{idx}"):
            st.session_state.mentor_actions[criterion_key] = {
                "criterion_id": criterion_key,
                "action":       criterion["remediation"],
                "owner":        "",
                "due_days":     30,
            }
            st.session_state.mentor_criterion_idx += 1
            st.rerun()

    if user_reply:
        conv.append({"role": "user", "content": user_reply.strip()})
        with st.spinner("Generating action item…"):
            action_item  = generate_action_item(criterion, user_reply.strip())
            mentor_reply = get_mentor_response(criterion, conv)
        conv.append({"role": "assistant", "content": mentor_reply})
        st.session_state.mentor_conversations[criterion_key] = conv
        st.session_state.mentor_actions[criterion_key]       = action_item
        st.session_state.mentor_criterion_idx += 1
        st.rerun()
