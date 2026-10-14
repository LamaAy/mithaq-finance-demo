"""MITHAQ standalone demonstration engine. NOT a production authorization service."""
from __future__ import annotations
import hashlib, hmac, json, secrets, time
from datetime import datetime, timezone

AUTO_LIMIT = 50_000
APPROVAL_LIMIT = 100_000
APPROVED = {"Supplier A": "SA-DEMO-001", "Supplier B": "SA-DEMO-002"}
AGENT_ID = "finance_agent_01"
OPERATION = "pay_supplier"

def canonical(req: dict) -> bytes:
    keys = {"agent_id": req["agent_id"], "operation": req["operation"], "supplier": req["supplier"], "amount_sar": req["amount_sar"], "invoice": req["invoice"]}
    return json.dumps(keys, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()

def fingerprint(req: dict) -> str:
    return hashlib.sha256(canonical(req)).hexdigest()

def evaluate(req: dict, delegation: dict) -> tuple[str, str]:
    if req.get("agent_id") != delegation["agent_id"] or req.get("operation") != OPERATION:
        return "DENY", "Agent or operation is not authorized"
    if time.time() > delegation["expires_at"]:
        return "DENY", "Delegation has expired"
    if req.get("supplier") not in delegation["suppliers"]:
        return "DENY", "Supplier is not on the approved list"
    amount = req.get("amount_sar")
    if type(amount) is not int or amount <= 0:
        return "DENY", "Amount must be a positive whole number of SAR"
    if not isinstance(req.get("invoice"), str) or not req["invoice"].strip():
        return "DENY", "Invoice number is required"
    if amount > delegation["approval_limit"]:
        return "DENY", "Amount exceeds the absolute organizational limit"
    if amount > delegation["auto_limit"]:
        return "REQUIRE_APPROVAL", "Manager approval is required"
    return "ALLOW", "Within active delegated authority"

class DemoEngine:
    def __init__(self):
        self.key = secrets.token_bytes(32)
        self.delegation = {"id": "DEL-2026-DEMO-001", "delegator": "Procurement Director (fictional)", "agent_id": AGENT_ID, "suppliers": sorted(APPROVED), "auto_limit": AUTO_LIMIT, "approval_limit": APPROVAL_LIMIT, "expires_at": time.time() + 86400}
        self.balance = 300_000
        self.payments = []
        self.audit = []
        self.used_nonces = set()
        self.pending = {}
        self.requests = {}

    def log(self, event, **detail):
        entry = {"timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "event": event, **detail}
        self.audit.append(entry)
        return entry

    def request(self, req):
        status, reason = evaluate(req, self.delegation)
        rid = "REQ-" + secrets.token_hex(4).upper()
        h = fingerprint(req)
        self.requests[rid] = {"hash": h, "decision": status}
        self.log("POLICY_DECISION", request_id=rid, decision=status, reason=reason, request_hash=h[:16])
        if status == "REQUIRE_APPROVAL":
            self.pending[rid] = {"request": dict(req), "hash": h, "approved": False}
        return rid, status, reason

    def approve(self, rid, approver: str):
        item = self.pending.get(rid)
        if not item:
            raise ValueError("No pending request")
        if item["approved"]:
            raise ValueError("Already approved")
        # Demonstration only: approver identity is selected in the UI, not authenticated.
        if approver != "Finance Manager (demo)":
            raise ValueError("Approver is not authorized")
        status, reason = evaluate(item["request"], self.delegation)
        if status != "REQUIRE_APPROVAL" or fingerprint(item["request"]) != item["hash"]:
            raise ValueError("Pending request no longer meets approval rules")
        item["approved"] = True
        self.log("HUMAN_APPROVAL_SIMULATED", request_id=rid, approver=approver)

    def issue_permit(self, rid, req):
        record = self.requests.get(rid)
        if not record or record["hash"] != fingerprint(req):
            raise ValueError("Request was not evaluated or its details changed")
        status, reason = evaluate(req, self.delegation)
        if status == "DENY":
            raise ValueError(reason)
        if status == "REQUIRE_APPROVAL":
            pending = self.pending.get(rid)
            if not pending or not pending["approved"] or pending["hash"] != fingerprint(req):
                raise ValueError("Verified approval for exactly this transaction is missing")
        payload = {"rid": rid, "hash": fingerprint(req), "nonce": secrets.token_hex(12), "expires": int(time.time()) + 120, "delegation_id": self.delegation["id"]}
        msg = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        signature = hmac.new(self.key, msg, hashlib.sha256).hexdigest()
        self.log("PERMIT_ISSUED", request_id=rid, permit_nonce=payload["nonce"])
        return {"payload": payload, "signature": signature}

    def execute(self, req, permit):
        p = permit.get("payload", {})
        msg = json.dumps(p, sort_keys=True, separators=(",", ":")).encode()
        expected = hmac.new(self.key, msg, hashlib.sha256).hexdigest()
        reason = None
        if not hmac.compare_digest(expected, permit.get("signature", "")):
            reason = "Permit signature invalid"
        elif int(time.time()) > p.get("expires", 0):
            reason = "Permit expired"
        elif p.get("nonce") in self.used_nonces:
            reason = "Permit replay blocked"
        elif p.get("hash") != fingerprint(req):
            reason = "Transaction was modified after authorization"
        elif p.get("delegation_id") != self.delegation["id"]:
            reason = "Delegation mismatch"
        else:
            status, rule_reason = evaluate(req, self.delegation)
            if status == "DENY":
                reason = rule_reason
            elif status == "REQUIRE_APPROVAL":
                pending = self.pending.get(p.get("rid"))
                if not pending or not pending["approved"] or pending["hash"] != fingerprint(req):
                    reason = "Approval missing or not tied to transaction"
            if not reason and req["amount_sar"] > self.balance:
                reason = "Insufficient simulated balance"
        if reason:
            self.log("EXECUTION_BLOCKED", reason=reason, request_hash=fingerprint(req)[:16])
            return False, reason, None
        # Consume before mutation; in production use atomic durable storage.
        self.used_nonces.add(p["nonce"])
        self.balance -= req["amount_sar"]
        receipt = {"receipt_id": "SIM-" + secrets.token_hex(5).upper(), "request_id": p["rid"], "delegation_id": p["delegation_id"], "request_hash": p["hash"], "amount_sar": req["amount_sar"], "supplier": req["supplier"], "new_fake_balance_sar": self.balance, "status": "SIMULATED_SETTLEMENT"}
        self.payments.append(receipt)
        self.log("SIMULATED_EXECUTION", **receipt)
        return True, "Simulated payment completed", receipt
