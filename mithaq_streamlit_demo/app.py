from __future__ import annotations
import json, os
import streamlit as st
from agent import parse_proposal
from engine import DemoEngine, AGENT_ID, OPERATION, APPROVED, fingerprint

st.set_page_config(page_title="MITHAQ | Digital Authority Demo", page_icon="🛡️", layout="wide")
st.markdown("""<style>.block-container{max-width:1150px;padding-top:2rem}h1,h2,h3{letter-spacing:-.02em}</style>""", unsafe_allow_html=True)
if "engine" not in st.session_state:
    st.session_state.engine = DemoEngine()
if "draft" not in st.session_state:
    st.session_state.draft = None
if "last" not in st.session_state:
    st.session_state.last = None
if "permit" not in st.session_state:
    st.session_state.permit = None
E = st.session_state.engine
st.title("🛡️ MITHAQ")
st.caption("Digital Authority for AI Agents  ·  Ministry presentation prototype  ·  Fictional payments only")
st.warning("SANDBOX DEMO — No banking connection, no real payments, no verified human identity. Session data is temporary.", icon="⚠️")
with st.sidebar:
    st.header("Demo controls")
    st.write("**Agent:**", AGENT_ID)
    st.write("**Authorization ceiling:** SAR 50,000")
    st.write("**Manager approval:** SAR 50,001–100,000")
    st.write("**Absolute limit:** SAR 100,000")
    st.write("**Approved vendors:** Supplier A, Supplier B")
    st.metric("Fake company balance", f"SAR {E.balance:,.0f}")
    if st.button("Reset demo", use_container_width=True):
        for k in ["engine", "draft", "last", "permit"]:
            st.session_state.pop(k, None)
        st.rerun()

t1, t2, t3, t4 = st.tabs(["🤖 Agent Console", "🔐 Delegated Authority", "✅ Approval Center", "📋 Audit & Evidence"])
with t1:
    st.subheader("Gemini-powered payment proposal")
    st.write("The language model interprets the instruction. MITHAQ—not Gemini—decides whether execution is permitted.")
    request_text = st.text_area("Instruction to Finance Agent", "Pay Supplier A 35,000 SAR for invoice INV-104", height=92)
    mode = st.radio("Proposal source", ["Gemini LLM", "Reliable offline fallback"], horizontal=True)
    try:
        api_key = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
    except Exception:
        api_key = os.environ.get("GEMINI_API_KEY", "")
    if mode == "Gemini LLM" and not api_key:
        st.info("Add GEMINI_API_KEY in Streamlit Cloud → App settings → Secrets to enable Gemini. Offline fallback works without an API key.")
    col_a, col_b = st.columns([1,1])
    with col_a:
        if st.button("1 · Let agent propose transaction", type="primary", use_container_width=True):
            try:
                if mode == "Gemini LLM":
                    if not api_key: raise ValueError("Gemini API key not configured")
                    with st.spinner("Gemini is interpreting the instruction..."):
                        proposal = parse_proposal(request_text, api_key)
                else:
                    # Explicitly deterministic test input; never claimed to be AI.
                    proposal = {"agent_id": AGENT_ID, "operation": OPERATION, "supplier": "Supplier A", "amount_sar": 35000, "invoice": "INV-104"}
                st.session_state.draft = proposal
                st.session_state.last = None
                st.session_state.permit = None
            except Exception as ex:
                st.error(f"Proposal failed: {ex}")
    with col_b:
        st.caption("Offline fallback always proposes Supplier A / SAR 35,000 / INV-104. You can edit the draft below to test any case.")
    if st.session_state.draft:
        d = st.session_state.draft
        st.markdown("#### Agent's proposed tool arguments")
        with st.form("evaluate_form"):
            sup = st.selectbox("Payee", ["Supplier A", "Supplier B", "Unknown"], index=["Supplier A", "Supplier B", "Unknown"].index(d["supplier"]) if d["supplier"] in ["Supplier A", "Supplier B", "Unknown"] else 2)
            amt = st.number_input("Amount (SAR)", min_value=1, max_value=1_000_000, value=min(max(1,d["amount_sar"]),1_000_000), step=5000)
            inv = st.text_input("Invoice", value=d["invoice"])
            submitted = st.form_submit_button("2 · Evaluate via MITHAQ", type="primary")
        if submitted:
            req = {"agent_id":AGENT_ID,"operation":OPERATION,"supplier":sup,"amount_sar":int(amt),"invoice":inv}
            rid,status,reason=E.request(req)
            st.session_state.last={"request_id":rid,"status":status,"reason":reason,"req":req}
            st.session_state.permit = None
        last = st.session_state.last
        if last:
            st.info(f"**MITHAQ: {last['status']}** — {last['reason']} (request: {last['request_id']})")
            if last["status"] == "DENY":
                st.error("Transaction blocked. No permit can be issued.")
            elif last["status"] == "REQUIRE_APPROVAL" and not E.pending[last["request_id"]]["approved"]:
                st.warning("Approval pending. Visit the Approval Center tab; the payment cannot execute yet.")
            else:
                if st.button("3 · Issue transaction-bound permit"):
                    try:
                        st.session_state.permit=E.issue_permit(last["request_id"],last["req"])
                        st.success("Signed demonstration permit issued")
                    except Exception as ex: st.error(str(ex))
            permit=st.session_state.permit
            if permit:
                st.caption("Permit is signed using a fresh per-session HMAC secret. Production should use authenticated principals and durable keys.")
                st.code(json.dumps(permit, indent=2), language="json")
                mutate=st.checkbox("Attack demonstration: change amount AFTER authorization")
                replay=st.checkbox("Attack demonstration: attempt to reuse consumed permit")
                if st.button("4 · Execute at protected payment gateway", type="primary"):
                    execution_req=dict(last["req"])
                    if mutate: execution_req["amount_sar"]+=315000
                    if replay and permit["payload"]["nonce"] not in E.used_nonces:
                        st.warning("Run a normal successful execution first, then select replay and retry.")
                    ok,msg,receipt=E.execute(execution_req,permit)
                    if ok: st.success(msg);st.json(receipt)
                    else: st.error(msg)
with t2:
    st.subheader("Human-to-agent delegation")
    details=dict(E.delegation)
    details["expires_at_utc"] = __import__("datetime").datetime.fromtimestamp(details.pop("expires_at"),tz=__import__("datetime").timezone.utc).isoformat()
    st.json(details)
    st.caption("Demo identity is configured in code, not backed by an enterprise identity provider.")
    if st.button("Revoke delegation for this session"):
        E.delegation["expires_at"]=0
        E.log("DELEGATION_REVOKED_SIMULATED", delegation_id=E.delegation["id"])
        st.warning("Delegation revoked. Future executions will be denied.")
with t3:
    st.subheader("Manager approval queue")
    if not E.pending:
        st.info("No requests awaiting approval. Try a SAR 75,000 payment on the Agent Console tab.")
    for rid, item in list(E.pending.items()):
        with st.container(border=True):
            st.write(f"**{rid}** | {item['request']['supplier']} | SAR {item['request']['amount_sar']:,}")
            st.caption("This is a role-play approval button, not authenticated manager sign-in.")
            if item["approved"]: st.success("Approved in this demo session")
            elif st.button(f"Simulate finance manager approval — {rid}"):
                try: E.approve(rid,"Finance Manager (demo)");st.rerun()
                except Exception as ex: st.error(str(ex))
with t4:
    st.subheader("Audit evidence")
    st.write("These events are recorded in the current session. They are not independently durable or tamper-evident.")
    if E.audit:
        st.dataframe(list(reversed(E.audit)), use_container_width=True, hide_index=True)
        st.download_button("Export audit JSON", json.dumps(E.audit,indent=2), "mithaq_demo_audit.json", mime="application/json")
    else: st.info("No events yet. Start by evaluating a transaction.")
    st.subheader("Simulated settlement receipts")
    if E.payments: st.dataframe(E.payments,use_container_width=True,hide_index=True)
    else: st.info("No payments executed.")
