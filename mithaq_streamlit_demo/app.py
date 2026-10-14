"""MITHAQ bilingual Streamlit demonstration (Arabic / English, no LLM).

Requires the existing engine.py (DemoEngine, AGENT_ID, OPERATION).
All financial activity is fictional. No real agent or banking connection.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
import streamlit as st
from engine import DemoEngine, AGENT_ID, OPERATION

st.set_page_config(page_title="MITHAQ | ميثاق", page_icon="🛡️", layout="wide")

if "language" not in st.session_state:
    st.session_state.language = "العربية"
if "engine" not in st.session_state:
    st.session_state.engine = DemoEngine()
if "last" not in st.session_state:
    st.session_state.last = None
if "permit" not in st.session_state:
    st.session_state.permit = None

E = st.session_state.engine

with st.sidebar:
    st.selectbox("Language / اللغة", ["العربية", "English"], key="language")

AR = st.session_state.language == "العربية"

st.markdown("""<style>
.block-container {max-width: 1150px; padding-top: 1.6rem;}
h1,h2,h3 {letter-spacing:-0.02em;}
""" + ("""
.stApp, [data-testid="stSidebar"] {direction:rtl; text-align:right;}
[data-testid="stTabs"] [role="tablist"] {direction:rtl;}
input, textarea {direction:rtl; text-align:right;}
""" if AR else """
.stApp, [data-testid="stSidebar"] {direction:ltr; text-align:left;}
input, textarea {direction:ltr; text-align:left;}
""") + """
pre, code, [data-testid="stJson"] {direction:ltr; text-align:left;}
</style>""", unsafe_allow_html=True)

TEXT = {
    "ar": {
        "subtitle":"منصة حوكمة صلاحيات الوكلاء الأذكياء",
        "features":"التفويض الرقمي · تقييم السياسات · الموافقات البشرية · تصريح التنفيذ · سجل التدقيق",
        "explain":"في هذه النسخة تُنشأ طلبات الدفع لمحاكاة أفعال وكيل ذكي، ثم يتحقق محرك ميثاق من الصلاحيات قبل التنفيذ. لا يُستخدم نموذج لغوي.",
        "disclaimer":"بيئة تجريبية: لا تحويلات مالية حقيقية، ولا تحقق فعلي من هوية المدير، والبيانات مؤقتة لكل جلسة.",
        "controls":"لوحة التحكم", "agent":"معرّف الوكيل", "auto":"حد التنفيذ التلقائي", "approval_range":"الموافقة الإدارية", "absolute":"الحد الأعلى", "vendors":"الموردون المعتمدون", "balance":"الرصيد التجريبي", "count":"العمليات المنفذة", "reset":"إعادة ضبط العرض",
        "tab_ops":"💼 محاكاة العمليات", "tab_deleg":"🔐 التفويض والصلاحيات", "tab_approve":"✅ مركز الموافقات", "tab_audit":"📋 سجل التدقيق",
        "create":"إنشاء طلب دفع تجريبي", "intro":"اختاري سيناريو أو أدخلي تفاصيل الطلب، ثم اختبري كيف يقرر ميثاق السماح أو طلب الموافقة أو الرفض.",
        "scenario":"سيناريو العرض", "scenarios":["عملية مصرح بها — 35,000 ريال", "تتطلب موافقة — 75,000 ريال", "مستفيد غير معتمد — 20,000 ريال", "تجاوز الحد — 150,000 ريال", "طلب مخصص"],
        "suppliers":["المورد أ (معتمد)", "المورد ب (معتمد)", "مستفيد غير معتمد"],
        "supplier":"المستفيد", "amount":"المبلغ (ريال سعودي)", "invoice":"رقم الفاتورة", "evaluate":"١ · التحقق من الصلاحيات", "evaluation_error":"تعذر تقييم الطلب", "decision":"قرار ميثاق", "request_id":"رقم الطلب", "deny":"العملية مرفوضة. لا يمكن إصدار تصريح تنفيذ.", "pending":"تحتاج العملية إلى موافقة. انتقلي إلى مركز الموافقات أولًا.", "permit_button":"٢ · إصدار تصريح التنفيذ", "permit_ok":"تم إصدار تصريح تجريبي مرتبط بالعملية.", "permit_error":"تعذر إصدار التصريح", "permit_view":"عرض تصريح التنفيذ", "permit_note":"يستخدم العرض توقيع HMAC بمفتاح مؤقت للجلسة، دون هوية إنتاجية موثقة.",
        "security":"اختبارات الحماية", "mutate":"تغيير المبلغ بعد التصريح (+315,000 ريال)", "replay":"محاولة إعادة استخدام التصريح", "execute":"٣ · التنفيذ عبر البوابة المحمية", "replay_tip":"لتجربة إعادة الاستخدام، نفذي الطلب بنجاح أولًا ثم حاولي تنفيذه مرة ثانية.", "executed":"اكتمل الدفع التجريبي", "blocked":"تم منع التنفيذ", "execution_error":"تعذر التنفيذ",
        "deleg_title":"التفويض الممنوح للوكيل", "delegator":"المفوّض (تجريبي)", "delegator_name":"مدير المشتريات", "auto_limit":"الحد التلقائي", "approval_limit":"حد الموافقة", "deleg_id":"معرّف التفويض", "expires":"انتهاء التفويض (UTC)", "deleg_note":"الهوية مضبوطة داخل نموذج تجريبي، ولا تعتمد على نظام مؤسسي للتحقق من المستخدمين.", "revoke":"إلغاء التفويض", "revoked":"أُلغي التفويض؛ يجب منع العمليات اللاحقة.",
        "queue":"طلبات الموافقة الإدارية", "no_pending":"لا توجد طلبات موافقة. جربي سيناريو 75,000 ريال.", "approved":"تمت الموافقة تجريبيًا", "approve_button":"محاكاة موافقة المدير المالي", "approval_error":"تعذرت الموافقة", "approval_note":"زر الموافقة محاكاة، وليس تحققًا من هوية مدير حقيقي.",
        "audit_title":"سجل القرارات وعمليات التنفيذ", "audit_note":"توجد السجلات داخل جلسة Streamlit فقط؛ ليست مخزنة دائمًا ولا مقاومة للتلاعب بصورة مستقلة.", "download":"تنزيل سجل التدقيق JSON", "no_audit":"لا توجد أحداث بعد. ابدئي بتقييم عملية.", "receipts":"إيصالات الدفع التجريبي", "no_receipts":"لم تنفذ أي عملية بعد.", "footer":"ميثاق | نموذج أولي للعرض — جميع المدفوعات افتراضية", "sar":"ر.س", "from_to":"50,001–100,000 ريال", "max_amount":"100,000 ريال", "approved_list":"المورد أ، المورد ب"
    },
    "en": {
        "subtitle":"Digital Authority & Governance for AI Agents",
        "features":"Delegated Authority · Policy Decisions · Human Approval · Execution Permits · Audit Evidence",
        "explain":"This version simulates an AI agent's payment request. MITHAQ independently checks authorization before execution. No language model is used.",
        "disclaimer":"SANDBOX DEMO: No real payments, no authenticated manager identity, and only temporary session data.",
        "controls":"Demo controls", "agent":"Agent ID", "auto":"Automatic authorization", "approval_range":"Manager approval", "absolute":"Absolute limit", "vendors":"Approved suppliers", "balance":"Simulated balance", "count":"Executed payments", "reset":"Reset demo",
        "tab_ops":"💼 Operation Simulator", "tab_deleg":"🔐 Delegated Authority", "tab_approve":"✅ Approval Center", "tab_audit":"📋 Audit & Evidence",
        "create":"Create simulated payment request", "intro":"Choose a scenario or customize the request to see MITHAQ allow, require approval, or deny an operation.",
        "scenario":"Demo scenario", "scenarios":["Authorized payment — SAR 35,000", "Requires approval — SAR 75,000", "Unapproved beneficiary — SAR 20,000", "Over the limit — SAR 150,000", "Custom request"],
        "suppliers":["Supplier A (approved)", "Supplier B (approved)", "Unapproved beneficiary"],
        "supplier":"Beneficiary", "amount":"Amount (SAR)", "invoice":"Invoice", "evaluate":"1 · Evaluate with MITHAQ", "evaluation_error":"Unable to evaluate request", "decision":"MITHAQ decision", "request_id":"Request ID", "deny":"Request denied. No execution permit can be issued.", "pending":"Manager approval is required. Visit Approval Center first.", "permit_button":"2 · Issue execution permit", "permit_ok":"Transaction-bound demonstration permit issued.", "permit_error":"Cannot issue permit", "permit_view":"View execution permit", "permit_note":"This demo uses a temporary, per-session HMAC key, without authenticated production identities.",
        "security":"Security tests", "mutate":"Change amount after authorization (+SAR 315,000)", "replay":"Attempt to reuse the permit", "execute":"3 · Execute through protected gateway", "replay_tip":"To test replay, first execute successfully, then try to execute again.", "executed":"Simulated payment completed", "blocked":"Execution blocked", "execution_error":"Execution error",
        "deleg_title":"Agent delegation", "delegator":"Delegator (simulated)", "delegator_name":"Procurement Director", "auto_limit":"Automatic limit", "approval_limit":"Approval limit", "deleg_id":"Delegation ID", "expires":"Expires at (UTC)", "deleg_note":"Identity is predefined for this demonstration, not authenticated by an enterprise identity provider.", "revoke":"Revoke delegation", "revoked":"Delegation revoked. Subsequent actions should be denied.",
        "queue":"Manager approval requests", "no_pending":"No pending approvals. Try the SAR 75,000 scenario.", "approved":"Approved in this demo session", "approve_button":"Simulate finance manager approval", "approval_error":"Approval failed", "approval_note":"This is a simulation button, not authenticated manager sign-in.",
        "audit_title":"Decision and execution audit", "audit_note":"Audit events are stored only in this Streamlit session, not in durable or independently tamper-evident storage.", "download":"Download audit JSON", "no_audit":"No audit events yet. Evaluate a request to begin.", "receipts":"Simulated settlement receipts", "no_receipts":"No simulated payments have been executed.", "footer":"MITHAQ | Demonstration prototype — all transactions are fictional", "sar":"SAR", "from_to":"SAR 50,001–100,000", "max_amount":"SAR 100,000", "approved_list":"Supplier A, Supplier B"
    }
}
t = TEXT["ar" if AR else "en"]

REASONS = {
    "Agent or operation is not authorized":"الوكيل أو العملية غير مصرّح بها",
    "Delegation has expired":"انتهت صلاحية التفويض",
    "Supplier is not on the approved list":"المستفيد غير موجود في قائمة الموردين المعتمدين",
    "Amount must be a positive whole number of SAR":"يجب أن يكون المبلغ عددًا صحيحًا موجبًا",
    "Invoice number is required":"رقم الفاتورة مطلوب",
    "Amount exceeds the absolute organizational limit":"المبلغ يتجاوز الحد الأعلى المعتمد",
    "Manager approval is required":"تتطلب العملية موافقة المدير المالي",
    "Within active delegated authority":"العملية ضمن التفويض الساري",
    "Transaction was modified after authorization":"تم تعديل تفاصيل العملية بعد إصدار التصريح",
    "Permit replay blocked":"تم منع إعادة استخدام تصريح سبق استهلاكه",
    "Permit expired":"انتهت صلاحية تصريح التنفيذ",
    "Insufficient simulated balance":"الرصيد التجريبي غير كافٍ",
    "Simulated payment completed":"اكتمل الدفع التجريبي",
    "Permit signature invalid":"توقيع التصريح غير صحيح",
    "Delegation mismatch":"التفويض لا يطابق التصريح",
    "Approval missing or not tied to transaction":"الموافقة مفقودة أو غير مرتبطة بالعملية",
}
DECISIONS = {"ALLOW":("مسموح" if AR else "ALLOW"), "REQUIRE_APPROVAL":("يتطلب موافقة" if AR else "REQUIRE APPROVAL"), "DENY":("مرفوض" if AR else "DENY")}
SUPPLIER_IDS = ["Supplier A", "Supplier B", "Unknown"]
SUPPLIER_NAMES = dict(zip(SUPPLIER_IDS, t["suppliers"]))
def label_reason(msg):
    return REASONS.get(str(msg), str(msg)) if AR else str(msg)
def money(value):
    return f"{value:,.0f} {t['sar']}" if AR else f"{t['sar']} {value:,.0f}"
def reset():
    for key in ("engine", "last", "permit"):
        st.session_state.pop(key, None)
    st.rerun()

st.title("🛡️ ميثاق | MITHAQ" if AR else "🛡️ MITHAQ")
st.markdown(f"**{t['subtitle']}**")
st.caption(t["features"])

with st.sidebar:
    st.header(t["controls"])
    st.write(f"**{t['agent']}:** {AGENT_ID}")
    st.write(f"**{t['auto']}:** {money(50_000)}")
    st.write(f"**{t['approval_range']}:** {t['from_to']}")
    st.write(f"**{t['absolute']}:** {t['max_amount']}")
    st.write(f"**{t['vendors']}:** {t['approved_list']}")
    st.metric(t["balance"], money(E.balance))
    st.metric(t["count"], len(E.payments))
    if st.button(t["reset"], use_container_width=True):
        reset()

ops, delegation_tab, approval_tab, audit_tab = st.tabs([t["tab_ops"],t["tab_deleg"],t["tab_approve"],t["tab_audit"]])
with ops:
    st.subheader(t["create"])
    st.write(t["intro"])
    scenario_index = st.selectbox(t["scenario"], range(5), format_func=lambda i: t["scenarios"][i], key="scenario")
    examples = [("Supplier A",35000,"INV-104"),("Supplier B",75000,"INV-205"),("Unknown",20000,"INV-306"),("Supplier A",150000,"INV-407"),("Supplier A",35000,"INV-104")]
    supplier_default, amount_default, invoice_default = examples[scenario_index]
    with st.form("payment_request"):
        supplier = st.selectbox(t["supplier"], SUPPLIER_IDS, index=SUPPLIER_IDS.index(supplier_default), format_func=lambda s: SUPPLIER_NAMES[s])
        amount = st.number_input(t["amount"], min_value=1, max_value=1_000_000, value=amount_default, step=1000)
        invoice = st.text_input(t["invoice"], value=invoice_default)
        submitted = st.form_submit_button(t["evaluate"], type="primary", use_container_width=True)
    if submitted:
        st.session_state.last = None
        st.session_state.permit = None
        request = {"agent_id":AGENT_ID,"operation":OPERATION,"supplier":supplier,"amount_sar":int(amount),"invoice":invoice.strip()}
        try:
            rid, status, reason = E.request(request)
            st.session_state.last = {"request_id":rid,"status":status,"reason":reason,"req":request}
        except Exception as exc:
            st.error(f"{t['evaluation_error']}: {label_reason(exc)}")
    last = st.session_state.last
    if last:
        status = last["status"]
        st.subheader(t["decision"])
        message = f"**{DECISIONS.get(status,status)}** — {label_reason(last['reason'])}"
        if status == "ALLOW": st.success(message)
        elif status == "REQUIRE_APPROVAL": st.warning(message)
        else: st.error(message)
        st.caption(f"{t['request_id']}: {last['request_id']}")
        pending = E.pending.get(last["request_id"])
        approved = bool(pending and pending.get("approved"))
        if status == "DENY":
            st.error(t["deny"])
        elif status == "REQUIRE_APPROVAL" and not approved:
            st.warning(t["pending"])
        else:
            if st.button(t["permit_button"], use_container_width=True):
                try:
                    st.session_state.permit = E.issue_permit(last["request_id"],last["req"])
                    st.success(t["permit_ok"])
                except Exception as exc:
                    st.error(f"{t['permit_error']}: {label_reason(exc)}")
        permit = st.session_state.permit
        if permit:
            with st.expander(t["permit_view"]):
                st.json(permit)
                st.caption(t["permit_note"])
            st.subheader(t["security"])
            mutate = st.checkbox(t["mutate"])
            replay = st.checkbox(t["replay"])
            if st.button(t["execute"], type="primary", use_container_width=True):
                req = dict(last["req"])
                if mutate: req["amount_sar"] += 315000
                if replay and permit["payload"]["nonce"] not in E.used_nonces:
                    st.info(t["replay_tip"])
                try:
                    ok,msg,receipt = E.execute(req,permit)
                    if ok:
                        st.success(t["executed"])
                        if receipt: st.json(receipt)
                    else:
                        st.error(f"{t['blocked']}: {label_reason(msg)}")
                except Exception as exc:
                    st.error(f"{t['execution_error']}: {label_reason(exc)}")

with delegation_tab:
    st.subheader(t["deleg_title"])
    d = dict(E.delegation)
    expiry = d.pop("expires_at")
    st.metric(t["delegator"], t["delegator_name"])
    st.metric(t["auto_limit"], money(d["auto_limit"]))
    st.metric(t["approval_limit"], money(d["approval_limit"]))
    st.write(f"**{t['deleg_id']}:** {d['id']}")
    st.write(f"**{t['agent']}:** {d['agent_id']}")
    st.write(f"**{t['vendors']}:** {', '.join(SUPPLIER_NAMES.get(x,x) for x in d['suppliers'])}")
    st.write(f"**{t['expires']}:** {datetime.fromtimestamp(expiry,tz=timezone.utc).isoformat()}")
    st.caption(t["deleg_note"])
    if st.button(t["revoke"]):
        E.delegation["expires_at"] = 0
        E.log("DELEGATION_REVOKED_SIMULATED", delegation_id=d["id"])
        st.warning(t["revoked"])

with approval_tab:
    st.subheader(t["queue"])
    if not E.pending:
        st.info(t["no_pending"])
    for rid,item in list(E.pending.items()):
        with st.container(border=True):
            req = item["request"]
            st.write(f"**{t['request_id']}:** {rid}")
            st.write(f"**{t['supplier']}:** {SUPPLIER_NAMES.get(req['supplier'],req['supplier'])}")
            st.write(f"**{t['amount']}:** {money(req['amount_sar'])}")
            st.write(f"**{t['invoice']}:** {req['invoice']}")
            if item["approved"]:
                st.success(t["approved"])
            elif st.button(t["approve_button"], key=f"approve_{rid}"):
                try:
                    E.approve(rid,"Finance Manager (demo)")
                    st.rerun()
                except Exception as exc:
                    st.error(f"{t['approval_error']}: {label_reason(exc)}")
    st.caption(t["approval_note"])

with audit_tab:
    st.subheader(t["audit_title"])
    st.caption(t["audit_note"])
    if E.audit:
        st.dataframe(list(reversed(E.audit)), use_container_width=True, hide_index=True)
        st.download_button(t["download"], json.dumps(E.audit,indent=2,ensure_ascii=False),file_name="mithaq_demo_audit.json",mime="application/json")
    else:
        st.info(t["no_audit"])
    st.subheader(t["receipts"])
    if E.payments:
        st.dataframe(E.payments, use_container_width=True, hide_index=True)
    else:
        st.info(t["no_receipts"])

st.divider()
st.caption(t["footer"])
