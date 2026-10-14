
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

import streamlit as st

from agent import parse_proposal
from engine import DemoEngine, AGENT_ID, OPERATION, APPROVED


# ============================================================
# MITHAQ — Digital Authority for AI Agents
# ============================================================

st.set_page_config(
    page_title="MITHAQ | AI Agent Governance",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
    }
    h1, h2, h3 {
        letter-spacing: -0.02em;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "engine" not in st.session_state:
    st.session_state.engine = DemoEngine()

if "draft" not in st.session_state:
    st.session_state.draft = None

if "last" not in st.session_state:
    st.session_state.last = None

if "permit" not in st.session_state:
    st.session_state.permit = None

E = st.session_state.engine


def get_api_key():
    try:
        return st.secrets.get(
            "GEMINI_API_KEY",
            os.environ.get("GEMINI_API_KEY", ""),
        )
    except Exception:
        return os.environ.get("GEMINI_API_KEY", "")


def clear_transaction():
    st.session_state.draft = None
    st.session_state.last = None
    st.session_state.permit = None


def reset_demo():
    for key in ["engine", "draft", "last", "permit"]:
        st.session_state.pop(key, None)
    st.rerun()


def show_decision(status, reason):
    if status == "ALLOW":
        st.success(f"ALLOW — {reason}")

    elif status == "REQUIRE_APPROVAL":
        st.warning(f"REQUIRE APPROVAL — {reason}")

    else:
        st.error(f"DENY — {reason}")


# ============================================================
# HEADER
# ============================================================

st.title("🛡️ MITHAQ")

st.markdown(
    "**Digital Authority & Governance for AI Agents**"
)

st.caption(
    "Verifiable Delegation · Policy Enforcement · "
    "Human Approval · Execution Control · Audit Evidence"
)

st.info(
    "MITHAQ governs what AI agents are authorized to execute, "
    "independently of the language model."
)

st.warning(
    "SANDBOX ENVIRONMENT — Fictional payments only. "
    "No real banking integration or authenticated manager approval. "
    "Session data is temporary.",
    icon="⚠️",
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("🛡️ MITHAQ")
    st.caption("Agent Governance Console")

    st.divider()

    st.subheader("Agent Identity")
    st.write("**Agent ID:**", AGENT_ID)
    st.write("**Operation:**", OPERATION)

    st.divider()

    st.subheader("Authority Policy")

    st.metric(
        "Automatic Authorization Limit",
        "SAR 50,000",
    )

    st.write("**Manager approval:** SAR 50,001–100,000")
    st.write("**Absolute limit:** SAR 100,000")
    st.write("**Approved suppliers:** Supplier A, Supplier B")

    st.divider()

    st.subheader("Simulated Account")

    st.metric(
        "Available Balance",
        f"SAR {E.balance:,.0f}",
    )

    st.metric(
        "Executed Payments",
        len(E.payments),
    )

    st.divider()

    if st.button(
        "Reset Demo Environment",
        use_container_width=True,
    ):
        reset_demo()


# ============================================================
# TABS
# ============================================================

tab_agent, tab_authority, tab_approval, tab_audit = st.tabs(
    [
        "🤖 AI Agent Console",
        "🔐 Delegated Authority",
        "✅ Approval Center",
        "📋 Audit & Evidence",
    ]
)


# ============================================================
# TAB 1 — AI AGENT
# ============================================================

with tab_agent:

    st.header("AI Finance Agent")

    st.write(
        "The AI Agent interprets payment instructions and "
        "proposes financial operations. MITHAQ independently "
        "evaluates whether each operation is authorized."
    )

    st.subheader("1. Payment Instruction")

    request_text = st.text_area(
        "Enter an instruction for the AI Agent",
        value=(
            "Pay Supplier A 35,000 SAR "
            "for invoice INV-104"
        ),
        height=100,
    )

    mode = st.radio(
        "Agent execution mode",
        [
            "Live AI Agent",
            "Offline Demo Mode",
        ],
        horizontal=True,
    )

    api_key = get_api_key()

    if mode == "Live AI Agent" and not api_key:
        st.warning(
            "AI service is not configured. "
            "Add the API credential in application secrets "
            "or select Offline Demo Mode."
        )

    if st.button(
        "Generate Payment Proposal",
        type="primary",
        use_container_width=True,
    ):

        clear_transaction()

        try:

            if mode == "Live AI Agent":

                if not api_key:
                    raise ValueError(
                        "AI service credential is missing."
                    )

                with st.spinner(
                    "MITHAQ AI Agent is processing the request..."
                ):
                    proposal = parse_proposal(
                        request_text,
                        api_key,
                    )

            else:

                # Deterministic fallback for live presentations.
                # This mode does not interpret the user's text.
                proposal = {
                    "agent_id": AGENT_ID,
                    "operation": OPERATION,
                    "supplier": "Supplier A",
                    "amount_sar": 35000,
                    "invoice": "INV-104",
                }

            st.session_state.draft = proposal

            st.success(
                "Payment proposal generated. "
                "No transaction has been executed."
            )

        except Exception as exc:

            st.error(
                f"AI Agent proposal failed: {exc}"
            )

    if mode == "Offline Demo Mode":
        st.caption(
            "Offline Mode creates a fixed sample proposal "
            "for Supplier A / SAR 35,000 / INV-104. "
            "Edit the proposal to test other scenarios."
        )

    # --------------------------------------------------------
    # PROPOSAL
    # --------------------------------------------------------

    if st.session_state.draft:

        proposal = st.session_state.draft

        st.divider()
        st.subheader("2. Proposed Financial Operation")

        suppliers = [
            "Supplier A",
            "Supplier B",
            "Unknown",
        ]

        current_supplier = proposal.get(
            "supplier",
            "Unknown",
        )

        supplier_index = (
            suppliers.index(current_supplier)
            if current_supplier in suppliers
            else 2
        )

        with st.form("authorization_form"):

            supplier = st.selectbox(
                "Beneficiary",
                suppliers,
                index=supplier_index,
            )

            amount = st.number_input(
                "Amount (SAR)",
                min_value=1,
                max_value=1_000_000,
                value=min(
                    max(
                        1,
                        int(proposal["amount_sar"]),
                    ),
                    1_000_000,
                ),
                step=1000,
            )

            invoice = st.text_input(
                "Invoice Reference",
                value=proposal["invoice"],
            )

            evaluate = st.form_submit_button(
                "Evaluate with MITHAQ",
                type="primary",
                use_container_width=True,
            )

        # ----------------------------------------------------
        # AUTHORIZATION
        # ----------------------------------------------------

        if evaluate:

            st.session_state.last = None
            st.session_state.permit = None

            request = {
                "agent_id": AGENT_ID,
                "operation": OPERATION,
                "supplier": supplier,
                "amount_sar": int(amount),
                "invoice": invoice,
            }

            try:

                request_id, status, reason = E.request(
                    request
                )

                st.session_state.last = {
                    "request_id": request_id,
                    "status": status,
                    "reason": reason,
                    "req": request,
                }

            except Exception as exc:
                st.error(
                    f"Authorization failed: {exc}"
                )

        # ----------------------------------------------------
        # DECISION
        # ----------------------------------------------------

        last = st.session_state.last

        if last:

            st.divider()
            st.subheader("3. MITHAQ Authorization Decision")

            show_decision(
                last["status"],
                last["reason"],
            )

            st.caption(
                f"Authorization Request ID: "
                f"{last['request_id']}"
            )

            request_id = last["request_id"]

            if last["status"] == "DENY":

                st.error(
                    "The requested operation is prohibited. "
                    "No execution permit will be issued."
                )

            elif (
                last["status"] == "REQUIRE_APPROVAL"
                and not E.pending.get(
                    request_id, {}
                ).get("approved", False)
            ):

                st.warning(
                    "Human approval is required. "
                    "Open the Approval Center to review "
                    "this transaction."
                )

            else:

                if st.button(
                    "Issue Execution Permit",
                    use_container_width=True,
                ):

                    try:

                        permit = E.issue_permit(
                            request_id,
                            last["req"],
                        )

                        st.session_state.permit = permit

                        st.success(
                            "Transaction-bound authorization "
                            "permit issued."
                        )

                    except Exception as exc:
                        st.error(str(exc))

            # ------------------------------------------------
            # EXECUTION
            # ------------------------------------------------

            permit = st.session_state.permit

            if permit:

                st.divider()
                st.subheader("4. Protected Execution Gateway")

                st.write(
                    "MITHAQ has issued an authorization permit. "
                    "The protected payment gateway must verify "
                    "the permit before execution."
                )

                with st.expander(
                    "View Authorization Permit"
                ):
                    st.json(permit)

                st.subheader("Security Demonstration")

                mutate = st.checkbox(
                    "Attempt unauthorized amount modification",
                    help=(
                        "Modify the amount after the permit "
                        "has been issued."
                    ),
                )

                replay = st.checkbox(
                    "Attempt permit replay",
                    help=(
                        "Reuse a previously consumed permit."
                    ),
                )

                if st.button(
                    "Execute Through Protected Gateway",
                    type="primary",
                    use_container_width=True,
                ):

                    execution_request = dict(
                        last["req"]
                    )

                    if mutate:
                        execution_request[
                            "amount_sar"
                        ] += 315000

                    nonce = permit.get(
                        "payload", {}
                    ).get("nonce")

                    if (
                        replay
                        and nonce not in E.used_nonces
                    ):
                        st.info(
                            "Execute the normal transaction "
                            "first, then attempt to reuse "
                            "the same permit."
                        )

                    try:

                        success, message, receipt = E.execute(
                            execution_request,
                            permit,
                        )

                        if success:

                            st.success(message)

                            if receipt:
                                st.subheader(
                                    "Execution Receipt"
                                )
                                st.json(receipt)

                            st.balloons()

                        else:

                            st.error(
                                f"Execution Blocked: {message}"
                            )

                    except Exception as exc:

                        st.error(
                            f"Gateway execution error: {exc}"
                        )


# ============================================================
# TAB 2 — DELEGATED AUTHORITY
# ============================================================

with tab_authority:

    st.header("Delegated Authority")

    st.write(
        "MITHAQ verifies the scope of authority delegated "
        "to an AI Agent before allowing sensitive operations."
    )

    delegation = dict(E.delegation)

    expiry = delegation.pop(
        "expires_at",
        0,
    )

    delegation["expires_at_utc"] = (
        datetime.fromtimestamp(
            expiry,
            tz=timezone.utc,
        ).isoformat()
    )

    st.subheader("Active Delegation Record")
    st.json(delegation)

    st.caption(
        "Identity and delegation are simulated in this "
        "prototype. Production integration requires "
        "authenticated principals and verified delegation."
    )

    st.divider()
    st.subheader("Delegation Controls")

    if st.button(
        "Revoke Agent Delegation",
        use_container_width=True,
    ):

        E.delegation["expires_at"] = 0

        E.log(
            "DELEGATION_REVOKED_SIMULATED",
            delegation_id=E.delegation["id"],
        )

        st.warning(
            "Delegation revoked. Subsequent authorization "
            "and execution attempts should be denied."
        )


# ============================================================
# TAB 3 — APPROVAL CENTER
# ============================================================

with tab_approval:

    st.header("Human Approval Center")

    st.write(
        "Sensitive operations exceeding the automatic "
        "authorization limit require an additional "
        "approval before execution."
    )

    if not E.pending:

        st.info(
            "No pending requests. "
            "Try a SAR 75,000 transaction from "
            "the AI Agent Console."
        )

    for request_id, item in list(
        E.pending.items()
    ):

        with st.container(border=True):

            req = item["request"]

            st.markdown(
                f"**Request:** {request_id}"
            )

            st.write(
                f"**Beneficiary:** {req['supplier']}"
            )

            st.write(
                f"**Amount:** SAR "
                f"{req['amount_sar']:,}"
            )

            st.write(
                f"**Invoice:** {req['invoice']}"
            )

            if item["approved"]:

                st.success(
                    "Approved in demonstration session."
                )

            else:

                st.warning(
                    "Awaiting finance manager approval."
                )

                if st.button(
                    "Simulate Manager Approval",
                    key=f"approve_{request_id}",
                    use_container_width=True,
                ):

                    try:

                        E.approve(
                            request_id,
                            "Finance Manager (demo)",
                        )

                        st.rerun()

                    except Exception as exc:
                        st.error(str(exc))

    st.caption(
        "Approval controls are simulated. "
        "They do not verify the identity of a real manager."
    )


# ============================================================
# TAB 4 — AUDIT & EVIDENCE
# ============================================================

with tab_audit:

    st.header("Audit & Execution Evidence")

    st.write(
        "Inspect authorization decisions, approvals, "
        "execution attempts and simulated settlements."
    )

    st.caption(
        "Audit records are stored in the current "
        "Streamlit session and are not durable "
        "or independently tamper-evident."
    )

    st.subheader("Authorization Audit Trail")

    if E.audit:

        st.dataframe(
            list(reversed(E.audit)),
            use_container_width=True,
            hide_index=True,
        )

        st.download_button(
            "Download Audit Records",
            data=json.dumps(
                E.audit,
                indent=2,
                ensure_ascii=False,
                default=str,
            ),
            file_name="mithaq_audit.json",
            mime="application/json",
            use_container_width=True,
        )

    else:

        st.info(
            "No audit events yet. "
            "Evaluate a transaction to generate records."
        )

    st.divider()

    st.subheader("Simulated Payment Receipts")

    if E.payments:

        st.dataframe(
            E.payments,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No simulated payments have been executed."
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "MITHAQ | Digital Authority & Governance for AI Agents "
    "— Demonstration Prototype"
)
