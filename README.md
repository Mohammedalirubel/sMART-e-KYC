# Smart e-KYC — Streamlit demo, future-ready

**Demonstration only.** The app does not query the Election Commission/NID service, compare faces, send SMS, screen sanctions, open accounts, or store records. Use **fictional test information and test images only**. Never use real customer NID images on Streamlit Community Cloud.

## Quick start (Windows / local)

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## GitHub + Streamlit Community Cloud

1. Create a **private** GitHub repo for this pilot and upload `app.py`, `requirements.txt`, `services/`, and `.streamlit/config.toml`.
2. In https://share.streamlit.io choose **Create app** → GitHub repo → branch `main` → entrypoint `app.py`.
3. Deploy. Test using fabricated data. A private GitHub repository does **not** necessarily mean the deployed app is private: check Streamlit app sharing settings and avoid real data regardless.
4. On Android/iPhone open the deployed HTTPS URL in Chrome/Safari. Streamlit is a responsive web app, not an APK or App Store binary.

## Current demo steps

Account product and e-KYC path → NID front/back and DOB → selfie capture → **on-screen** demo OTP (3 minutes, 5 tries) → customer information → nominee information/photo (minor guardian inputs) → review and demo submission.

No OCR, liveness, face matching, identity confirmation, customer ID generation, bank approval, account creation, or server-side persistence occurs. Demo identity and OTP must never be treated as evidence of actual verification.

## Regulatory mapping

Source: Bangladesh Bank BRPD-1 Circular No. 08, 11 March 2026 (effective 1 September 2026): Sections 2.2, 3.3, 3.2.5, 3.3.2–3.3.3, 4, 5.1–5.3. Self-check-in face model; OCR in Bangla and English; selfie matched to EC reference; retry/session limits; nominee ID retained (verification not mandatory); sanctions screening; risk grading for regular e-KYC; audit logs; local/private-cloud data storage and third-party safeguards.

**The current demo is not compliant production software.** Required controls are intentionally not implemented.

## Future integration plan

`services/integrations.py` defines interfaces only (all raise NotImplementedError):

- `NIDGateway`: authorized government-vetted NID validation and OCR extraction
- `BiometricGateway`: presentation attack detection and 1:1 matching to authorized reference photo, enforcing face retry limits
- `SMSGateway`: real OTP, expiration, replay prevention, rate limits, verified registered number
- `ComplianceGateway`: UN sanctions, PEP/IP/adverse media, CDD/EDD, Annexure-2 risk grading
- `CoreBankingGateway`: maker-checker approval and CBS account opening

Before connecting real customers: move processing to a bank-controlled backend; add consent, data minimization, encryption at rest/in transit, authorized access, audit logs, retention/deletion policy, fraud monitoring, secure secrets, maker-checker controls, security testing, approved hosting, approved third parties, and non-biometric fallback. Do not transmit customer data outside Bangladesh without applicable Bangladesh Bank approval.

## Workbook field mapping (account info.xlsx)

- Customer: unique customer ID, name, NID, DOB, father, mother, present/permanent addresses, NID photo, matching result, phone, OTP confirmation, selfie.
- Nominee: unique nominee ID and nominee identity/photo/details, entered by customer; minor guardian data where applicable.
- Account: customer ID, account name/number, nominee ID, balance, phone.

The workbook is a **reference schema**, not a populated customer database. Account numbers and balances must only be supplied by CBS in production. No user data is exported in this demo.

## Important production caveats

The sample app does not enforce all Bangladesh Bank regulatory requirements (including face retry limits, sanctions, signatures, risk grading, periodic reviews, secure recordkeeping, and mandatory account-opening notifications). These must be implemented and approved before live use.
