"""
pages/02_new_audit.py — Full audit flow
Phase 1: Intake (conversational agent)
Phase 2: Scoring (20-criterion evaluator)
Phase 3: Results + Radar chart
Phase 4: Mentor (per red/amber criterion)
Phase 5: Checklist generation
"""

import streamlit as st
import plotly.graph_objects as go
from auth import require_auth, ROLE_LABELS
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
from datetime import datetime, timedelta

st.set_page_config(page_title="New Audit", page_icon="🛡️", layout="wide")
user = require_auth()
from nav import render_nav
render_nav(user)

st.title("AI Governance Audit")
st.caption(f"Signed in as **{user['display_name']}** · {ROLE_LABELS[user['role']]}")
st.divider()

# ── Session bootstrap ─────────────────────────────────────────────────────────
session_id = st.session_state.get("current_session_id")

if not session_id:
    st.subheader("Step 1 — Describe your AI use case")
    with st.form("intake_form"):
        title        = st.text_input("Audit title", placeholder="e.g. No-show Prediction Model — Phase 1")
        use_case_raw = st.text_area(
            "Briefly describe your AI use case",
            height=140,
            placeholder="What does the AI do? Who uses it? What data does it touch?"
        )
        submitted = st.form_submit_button("Start →", type="primary")

    if submitted:
        if not title.strip() or not use_case_raw.strip():
            st.warning("Both fields are required.")
            st.stop()
        if len(use_case_raw.strip()) < 20:
            st.warning("Provide a bit more detail to get started.")
            st.stop()
        sid = create_audit_session(user["id"], title.strip(), use_case_raw.strip())
        save_intake_message(sid, "user", use_case_raw.strip())
        # Get opening question from intake agent
        opening_q = get_opening_question(use_case_raw.strip())
        save_intake_message(sid, "assistant", opening_q)
        st.session_state.current_session_id = sid
        st.rerun()
    st.stop()

# ── Load session ──────────────────────────────────────────────────────────────
session  = get_session(session_id)
if not session:
    st.error("Session not found.")
    st.stop()

st.markdown(f"### {session['title']}")
st.caption(f"Status: **{session['status'].title()}** · Created: {session['created_at'][:10]}")
st.divider()

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1 — INTAKE CONVERSATION
# ══════════════════════════════════════════════════════════════════════════════
if session["status"] == "intake":
    st.subheader("Step 1 — Intake")
    st.caption("The intake agent will ask a few clarifying questions before the audit runs. Answer as specifically as you can.")

    messages = get_intake_messages(session_id)

    # Render conversation
    for m in messages:
        if m["role"] == "assistant":
            with st.chat_message("assistant", avatar="🛡️"):
                st.markdown(m["content"])
        else:
            with st.chat_message("user", avatar="👤"):
                st.markdown(m["content"])

    # Check if last message was from assistant (awaiting user reply)
    # or from user (need next agent question)
    last_role = messages[-1]["role"] if messages else "assistant"

    if last_role == "user":
        # Build history and get next question or completion
        history = build_history_for_llm(messages)
        with st.spinner("Thinking…"):
            next_msg, is_complete = get_next_question(history)

        save_intake_message(session_id, "assistant", next_msg)

        if is_complete:
            # Enrich use case and move to scoring phase
            with st.spinner("Synthesizing your responses…"):
                enriched = enrich_use_case(session["use_case_raw"], build_history_for_llm(
                    get_intake_messages(session_id)
                ))
            update_session_enriched(session_id, enriched)
            st.rerun()
        else:
            st.rerun()

    # User input box
    if last_role == "assistant":
        user_reply = st.chat_input("Your answer…")
        if user_reply:
            save_intake_message(session_id, "user", user_reply.strip())
            st.rerun()

    # Skip intake option
    with st.expander("Skip intake and run audit now"):
        st.caption("The audit will run on your original description only — no enrichment.")
        if st.button("Skip → Run Audit directly"):
            update_session_enriched(session_id, session["use_case_raw"])
            update_session_status(session_id, "scoring")
            st.rerun()

    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — SCORING
# ══════════════════════════════════════════════════════════════════════════════
if session["status"] in ("intake", "scoring") and session.get("use_case_enriched"):
    # Auto-trigger scoring after intake completes
    st.subheader("Step 2 — Running Governance Audit")

    use_case_to_score = session.get("use_case_enriched") or session["use_case_raw"]

    with st.expander("View enriched use case profile"):
        st.markdown(use_case_to_score)

    progress_bar = st.progress(0, text="Starting evaluation…")

    def update_progress(current, total, name):
        progress_bar.progress(int((current / total) * 100), text=f"Evaluating {current}/{total}: {name}")

    with st.spinner("Running 20-criterion governance audit…"):
        result = run_evaluation(use_case_to_score, progress_callback=update_progress)

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
# PHASE 3 — RESULTS + RADAR CHART
# ══════════════════════════════════════════════════════════════════════════════
if session["status"] in ("scored", "mentoring", "complete"):
    results     = get_audit_results(session_id)
    red_items   = [r for r in results if r["score"] <= 2]
    amber_items = [r for r in results if r["score"] == 3]
    green_items = [r for r in results if r["score"] >= 4]
    crit_items  = [r for r in results if r["critical_flag"]]

    # Score summary
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

    # ── Radar chart ──────────────────────────────────────────────────────────
    st.divider()
    st.subheader("Governance Radar")

    functions   = ["GOVERN", "MAP", "MEASURE", "MANAGE", "HIPAA", "HITRUST"]
    fn_scores   = {}
    fn_max      = {}

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
        fillcolor="rgba(26, 58, 74, 0.2)",
        line=dict(color="#1a3a4a", width=2),
        name="Governance Score",
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], ticksuffix="%"),
        ),
        showlegend=False,
        margin=dict(l=40, r=40, t=40, b=40),
        height=380,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Function score breakdown
    fn_cols = st.columns(len(functions))
    for i, fn in enumerate(functions):
        score = radar_scores[i]
        c = "#c0392b" if score < 40 else ("#e67e22" if score < 65 else ("#f1c40f" if score < 80 else "#27ae60"))
        fn_cols[i].markdown(
            f'<div style="text-align:center">'
            f'<div style="font-size:22px;font-weight:700;color:{c}">{score}%</div>'
            f'<div style="font-size:11px;color:#666">{fn}</div>'
            f'</div>',
            unsafe_allow_html=True
        )

    # ── Critical blockers ────────────────────────────────────────────────────
    if crit_items:
        st.divider()
        st.subheader("⚠️ Critical Blockers")
        for r in crit_items:
            with st.expander(f"[{r['criterion_id']}] {r['criterion_name']}"):
                st.markdown(f"**Rationale:** {r['rationale']}")
                st.markdown(f"**Remediation:** {r['remediation']}")

    # ── Risk matrix tabs ─────────────────────────────────────────────────────
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
            bc  = "#c0392b" if score <= 2 else ("#e67e22" if score == 3 else "#27ae60")
            dot = "🔴" if score <= 2 else ("🟡" if score == 3 else "🟢")
            fn_color = FUNCTION_COLORS.get(r["function"], "#555")
            crit_tag = " ⚠️ CRITICAL" if r["critical_flag"] else ""
            st.markdown(
                f'<div style="border-left:3px solid {bc};padding:10px 16px;'
                f'margin-bottom:8px;background:#fafafa;border-radius:0 4px 4px 0">'
                f'<strong>{dot} [{r["criterion_id"]}] {r["criterion_name"]}{crit_tag}</strong>'
                f'&nbsp;&nbsp;<span style="background:{fn_color};color:white;padding:2px 8px;'
                f'border-radius:3px;font-size:11px">{r["function"]}</span>'
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

    # ── Download report ───────────────────────────────────────────────────────
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
# PHASE 4 — MENTOR SESSION
# ══════════════════════════════════════════════════════════════════════════════
if session["status"] in ("mentoring", "complete"):
    results     = get_audit_results(session_id)
    gaps        = [r for r in results if r["score"] <= 3]

    if not gaps:
        st.info("No red or amber items to mentor — your governance posture is strong.")
        st.stop()

    st.divider()
    st.subheader("🎓 Mentor Session")
    st.caption(f"Working through {len(gaps)} governance gaps. For each one, the mentor will guide you to a specific next action.")

    # Track which criterion is active in mentor session
    if "mentor_criterion_idx" not in st.session_state:
        st.session_state.mentor_criterion_idx = 0
    if "mentor_conversations" not in st.session_state:
        st.session_state.mentor_conversations = {}
    if "mentor_actions" not in st.session_state:
        st.session_state.mentor_actions = {}

    idx = st.session_state.mentor_criterion_idx

    # Progress
    st.progress(
        min(idx / len(gaps), 1.0),
        text=f"Gap {min(idx+1, len(gaps))} of {len(gaps)}"
    )

    if idx >= len(gaps):
        st.success(f"✅ Mentor session complete — {len(st.session_state.mentor_actions)} action items generated.")

        # Save all mentor-generated actions to checklist
        if st.button("Save to Checklist & Finish", type="primary"):
            from datetime import datetime, timedelta
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
            st.session_state.pop("mentor_criterion_idx", None)
            st.session_state.pop("mentor_conversations", None)
            st.session_state.pop("mentor_actions", None)
            st.switch_page("pages/03_checklist.py")
        st.stop()

    criterion = gaps[idx]
    criterion_key = criterion["criterion_id"]

    # Initialize conversation for this criterion
    if criterion_key not in st.session_state.mentor_conversations:
        opening = get_mentor_opening(criterion, session.get("use_case_enriched") or session["use_case_raw"])
        st.session_state.mentor_conversations[criterion_key] = [
            {"role": "assistant", "content": opening}
        ]

    # Show criterion context
    score = criterion["score"]
    bc = "#c0392b" if score <= 2 else "#e67e22"
    st.markdown(
        f'<div style="border-left:3px solid {bc};padding:10px 16px;'
        f'background:#fafafa;margin-bottom:12px;border-radius:0 4px 4px 0">'
        f'<strong>[{criterion["criterion_id"]}] {criterion["criterion_name"]}</strong> — '
        f'Score: {score}/5<br>'
        f'<span style="font-size:13px;color:#555">{criterion["rationale"]}</span>'
        f'</div>',
        unsafe_allow_html=True
    )

    # Render mentor conversation
    conv = st.session_state.mentor_conversations[criterion_key]
    for m in conv:
        if m["role"] == "assistant":
            with st.chat_message("assistant", avatar="🎓"):
                st.markdown(m["content"])
        else:
            with st.chat_message("user", avatar="👤"):
                st.markdown(m["content"])

    # Action buttons
    col_input, col_skip = st.columns([4, 1])

    with col_input:
        user_reply = st.chat_input(f"Your response for [{criterion_key}]…", key=f"mentor_input_{criterion_key}_{idx}")

    with col_skip:
        st.write("")
        st.write("")
        if st.button("Skip →", key=f"skip_{idx}"):
            # Use original remediation as fallback action
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

        # Generate action item from user's answer
        with st.spinner("Generating action item…"):
            action_item = generate_action_item(criterion, user_reply.strip())
            mentor_reply = get_mentor_response(criterion, conv)

        conv.append({"role": "assistant", "content": mentor_reply})
        st.session_state.mentor_conversations[criterion_key] = conv
        st.session_state.mentor_actions[criterion_key] = action_item

        # Auto-advance after one exchange
        st.session_state.mentor_criterion_idx += 1
        st.rerun()
