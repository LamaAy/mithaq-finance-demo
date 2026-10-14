# MITHAQ — Finance Agent Authorization Demo

A **standalone research/demo prototype** for a Ministry of Investment presentation. This project does **not** include the user's existing MITHAQ backend, and does not connect to a bank. It demonstrates Gemini-assisted payment proposal, policy evaluation, simulated approval, signed one-time execution permits, fake balance changes, and downloadable session audit events.

## Run locally

Use Python 3.11 or 3.12.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Provide a Gemini key in `.streamlit/secrets.toml` (copy the `.example` file) or the `GEMINI_API_KEY` environment variable. **Never commit secrets to GitHub**. Without a key, choose **Reliable offline fallback** within the app.

## Deploy on GitHub + Streamlit Community Cloud

1. Create a repository named `mithaq-finance-demo` on GitHub. Upload the files and directories from this folder (do NOT upload actual `secrets.toml`).
2. Go to https://share.streamlit.io/ → **Create app** → choose your GitHub repository, branch `main`, entrypoint `app.py`.
3. Under **Advanced settings → Secrets**, add `GEMINI_API_KEY = "YOUR_OWN_KEY"`.
4. Choose Python 3.12, deploy, and open the provided `.streamlit.app` URL.
5. Keep the app private/restricted when practical, since the LLM key may otherwise be consumed by public visitors.

## Live demo script

- In **Gemini LLM** mode ask: `Pay Supplier A 35000 SAR for invoice INV-104`. Review the extracted fields. Click **Evaluate**, **Issue permit**, **Execute**. Show fake balance decrease and audit receipt.
- Use **Reliable offline fallback** to rehearse without network dependencies; manually edit amount to 75000, evaluate, visit **Approval Center**, click simulated manager approval, return to console and issue/execute permit.
- Request `Unknown` supplier: DENY.
- Issue fresh permit for 35000 and enable **change amount AFTER authorization** before execution: DENY, balance unchanged.
- After a successful execution, click Execute again with the same permit: replay blocked.
- Revoke delegation and try another payment: DENY.

## Tests

```bash
python -m unittest discover -s tests -v
python -m py_compile app.py agent.py engine.py
```

## Honest limitations (must disclose)

- **Not the existing MITHAQ source code**; integration requires that repository or code.
- Streamlit `session_state` is per-session and ephemeral; approvals, HMAC key, fake balance, and audit records disappear on reset/restart.
- Manager approval in this demo is **not authenticated**. This design does not provide robust separation of duties or enterprise authorization.
- A Gemini LLM extracts a **proposed** payment; the model cannot authorize or directly execute it. Human clicks are required to evaluate and execute.
- No bank connection; receipts are **simulation artifacts**, not proofs of actual funds movement.
- HMAC signs demo permits; production requires external authenticated execution services, atomic durable nonce handling, independent keys, hardened parsing, proper authorization on every endpoint, and protected tamper-evident logging.
- Never present this as production-ready fintech security or compliance certification.
