import streamlit as st
import secrets, hmac, hashlib, time
from datetime import date

from services import validators as V, image_quality as IQ, risk as R

st.set_page_config(page_title='Smart e-KYC | Demo', page_icon='🏦', layout='centered')
st.markdown('<style>.block-container{max-width:680px;padding-top:1.4rem}'
            'div.stButton>button{width:100%;border-radius:12px}h1{color:#12366a}</style>',
            unsafe_allow_html=True)

STEPS = ['Account', 'NID', 'Face', 'OTP', 'Customer', 'Nominee', 'Review']
IDLE_LIMIT, OTP_TTL, OTP_COOLDOWN, OTP_MAX_SENDS, OTP_MAX_TRIES = 900, 180, 30, 3, 5
BLOBS = ['front', 'back', 'selfie', 'nominee_photo', 'guardian_photo']
DEFAULTS = dict(step=0, otp_digest=None, otp_exp=0.0, otp_tries=0, otp_sends=0, otp_last=0.0,
                otp_verified=False, blobs={}, last_active=time.time(), consent=False,
                dob=date(1995, 1, 1), nominee_dob=date(1990, 1, 1))

def wipe():
    st.session_state.clear()

# ---------- session hygiene: idle timeout ----------
if time.time() - st.session_state.get('last_active', time.time()) > IDLE_LIMIT:
    wipe(); st.session_state['expired'] = True
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)
st.session_state.last_active = time.time()
S = st.session_state

# Keep widget values when navigating back/forward (Streamlit drops keys of unrendered widgets).
for k in list(S.keys()):
    if k not in BLOBS and not k.startswith('FormSubmitter'):
        try: S[k] = S[k]
        except Exception: pass

def keep_blob(key):
    f = S.get(key)
    if f is not None: S.blobs[key] = f.getvalue()
    elif key in S.blobs and key not in S: pass
    return S.blobs.get(key)

def quality_panel(label, data):
    r = IQ.analyze(data)
    m = r['metrics']
    if r['ok']:
        st.success(f"{label}: quality OK · {m['width']}×{m['height']} · sharpness {m['sharpness']}")
    else:
        for i in r['issues']: st.warning(f'{label}: {i}')
    return r['ok']

# ---------- header ----------
st.title('🏦 Smart e-KYC Onboarding')
st.caption('PROTOTYPE ONLY · Smart checks run locally · No government NID verification, SMS delivery or account creation')
st.warning('DEMO MODE: Identity verification is NOT connected to the Election Commission. Never use this app to approve real customers.')
if S.pop('expired', False):
    st.info('Session cleared after 15 minutes of inactivity to protect your data.')

step = S.step
st.progress((step + 1) / len(STEPS))
st.caption(' → '.join(('**' + s + '**' if i == step else ('✅ ' + s if i < step else s)) for i, s in enumerate(STEPS)))

def go(n):
    S.step = max(0, min(6, n)); st.rerun()

# ---------- sidebar smart assistant ----------
HINTS = ['Pick the product that matches your needs. Simplified e-KYC suits low-value accounts.',
         'Place the NID flat, fully in frame, without glare. Both sides are checked for sharpness and light.',
         'Face the light, remove cap/glasses, keep a neutral expression.',
         'Use your own registered number. Codes expire in 3 minutes.',
         'Use names exactly as on your NID. Bangla name must be in Bangla script.',
         'Nominee should be a person you trust and who is not you.',
         'Check every line. Fix anything flagged before submitting.']
with st.sidebar:
    st.subheader('🤖 Smart assistant')
    st.write(HINTS[step])
    st.metric('Journey completed', f'{int(step / 6 * 100)}%')
    st.caption('Idle sessions auto-clear after 15 minutes.')
    if st.button('🗑️ Erase all my session data'):
        wipe(); st.rerun()

# ---------- steps ----------
if step == 0:
    st.selectbox('Account product', ['Savings Account', 'Current Account', 'Limited Transactions Account'], key='product')
    st.selectbox('e-KYC path', ['Regular e-KYC', 'Simplified e-KYC (eligible products only)'], key='path')
    if S.product == 'Current Account' and S.path.startswith('Simplified'):
        st.warning('Current accounts normally need Regular e-KYC. Switch path to continue.')
    st.checkbox('I consent to collection and processing of my data for this demo.', key='consent')
    ok = S.consent and not (S.product == 'Current Account' and S.path.startswith('Simplified'))
    if st.button('Start onboarding', disabled=not ok): go(1)

elif step == 1:
    st.text_input('NID number', key='nid', max_chars=17)
    st.date_input('Date of birth', min_value=date(1900, 1, 1), max_value=date.today(), key='dob')
    st.file_uploader('NID front (demo only)', type=['png', 'jpg', 'jpeg'], key='front')
    st.file_uploader('NID back (demo only)', type=['png', 'jpg', 'jpeg'], key='back')
    nid, dob = S.get('nid', ''), S.dob
    nid_ok = False
    if nid:
        nid_ok, msgs = V.check_nid(nid, dob)
        if nid_ok: st.success(f'NID format valid ({len(nid)}-digit {"smart" if len(nid)==10 else "legacy"} NID).')
        for m in msgs: st.error(m)
    adult, age = V.check_adult(dob)
    if not adult: st.error(f'Applicant must be 18+ (calculated age {age}).')
    f, b = keep_blob('front'), keep_blob('back')
    imgs_ok = True
    for label, data in (('NID front', f), ('NID back', b)):
        if data: imgs_ok &= quality_panel(label, data)
    if f and b and f == b: st.error('Front and back images are identical.'); imgs_ok = False
    st.info('Production: perform OCR and verify NID, DOB, and identity against an authorized NID service. This prototype checks format and image quality only.')
    if st.button('Continue', disabled=not (nid_ok and adult and f and b and imgs_ok)): go(2)

elif step == 2:
    st.camera_input('Take a live selfie (demo capture only)', key='selfie')
    sd = keep_blob('selfie')
    q_ok = quality_panel('Selfie', sd) if sd else False
    st.info('Production: PAD/liveness detection + server-side 1:1 facial comparison with the authorized EC reference photo. Not performed here.')
    if st.button('Continue to mobile verification', disabled=not q_ok): go(3)

elif step == 3:
    st.text_input('Mobile number (01XXXXXXXXX)', key='phone', max_chars=11)
    phone = S.get('phone', '')
    if phone and not V.check_phone(phone): st.error('Enter a valid Bangladesh mobile number.')
    wait = max(0, int(OTP_COOLDOWN - (time.monotonic() - S.otp_last))) if S.otp_sends else 0
    label = 'Generate demo OTP' if not S.otp_sends else (f'Resend in {wait}s' if wait else 'Resend demo OTP')
    if S.otp_sends >= OTP_MAX_SENDS: st.error('Maximum OTP requests reached for this session.')
    if st.button(label, disabled=wait > 0 or S.otp_sends >= OTP_MAX_SENDS or not V.check_phone(phone)):
        otp = f'{secrets.randbelow(1000000):06d}'
        S.otp_digest = hashlib.sha256(otp.encode()).digest()
        S.otp_exp, S.otp_last = time.monotonic() + OTP_TTL, time.monotonic()
        S.otp_tries, S.otp_verified, S.demo_otp = 0, False, otp
        S.otp_sends += 1; st.rerun()
    if S.otp_digest and not S.otp_verified:
        left = max(0, int(S.otp_exp - time.monotonic()))
        st.info(f'DEMO OTP (not sent by SMS): {S.get("demo_otp")} · expires in {left // 60}:{left % 60:02d} · '
                f'{OTP_MAX_TRIES - S.otp_tries} tries left')
        code = st.text_input('Enter OTP', max_chars=6, type='password')
        if st.button('Verify OTP'):
            if left == 0: st.error('OTP expired. Generate another.')
            elif S.otp_tries >= OTP_MAX_TRIES: st.error('Too many attempts. Generate another.')
            elif not (code.isdigit() and len(code) == 6): st.error('OTP is 6 digits.')
            else:
                S.otp_tries += 1
                if hmac.compare_digest(hashlib.sha256(code.encode()).digest(), S.otp_digest):
                    S.otp_verified = True; S.pop('demo_otp', None); st.rerun()
                else: st.error(f'Invalid code. {OTP_MAX_TRIES - S.otp_tries} tries left.')
    if S.otp_verified: st.success('Demo OTP verified')
    if st.button('Continue', disabled=not S.otp_verified): go(4)

elif step == 4:
    st.text_input('Full name (English)', key='name')
    st.text_input('Full name (Bangla)', key='name_bn')
    st.text_input('Father’s name', key='father')
    st.text_input('Mother’s name', key='mother')
    st.text_input('Present address', key='address')
    same = st.checkbox('Permanent address is same as present', key='same_addr')
    if same: S.permanent = S.get('address', '')
    st.text_input('Permanent address', key='permanent', disabled=same)
    st.text_input('Profession', key='profession')
    st.number_input('Monthly income (BDT)', min_value=0, step=1000, key='income')
    st.text_input('Source of funds', key='source')
    errs = []
    name = S.get('name', '')
    if name and not V.is_english_name(name): errs.append('English name: letters, spaces, . - \' only.')
    elif name and name != V.clean_title(name): st.caption(f'Suggested format: **{V.clean_title(name)}**')
    if S.get('name_bn') and not V.is_bangla(S.name_bn): errs.append('Bangla name must be written in Bangla script.')
    for k, lbl in (('father', 'Father'), ('mother', 'Mother')):
        if S.get(k) and V.similarity(S[k], name) > 0.9 and name: errs.append(f'{lbl}’s name matches the applicant’s name.')
    if S.get('father') and S.get('mother') and V.similarity(S.father, S.mother) > 0.9: errs.append('Father and mother names are identical.')
    for e in errs: st.error(e)
    if S.get('profession') and S.get('source'):
        _, age = V.check_adult(S.dob)
        grade, score, why = R.indicate(S.product, S.path, S.income, S.source, S.profession, age, '')
        S.risk = (grade, score, why)
        icon = {'Low': '🟢', 'Medium': '🟡', 'High': '🔴'}[grade]
        with st.expander(f'{icon} Demo risk indicator: {grade} (score {score})'):
            st.write('\n'.join('- ' + w for w in why))
            st.caption('Heuristic preview only; real grading follows the bank’s Annexure-2 policy.')
    st.caption('Production: verified identity fields should be read-only unless correction is authorized and audited.')
    need = ['name', 'name_bn', 'father', 'mother', 'address', 'permanent', 'profession', 'source']
    if st.button('Continue', disabled=not (all(S.get(k) for k in need) and not errs)): go(5)

elif step == 5:
    st.text_input('Nominee full name', key='nominee_name')
    st.date_input('Nominee date of birth', min_value=date(1900, 1, 1), max_value=date.today(), key='nominee_dob')
    st.selectbox('Relationship', ['Spouse', 'Father', 'Mother', 'Son', 'Daughter', 'Sibling', 'Other'], key='relationship')
    st.text_input('Nominee NID (adult) or birth registration number (minor)', key='nominee_id')
    st.file_uploader('Nominee photograph', type=['png', 'jpg', 'jpeg'], key='nominee_photo')
    n_age, c_age = V.age_on(S.nominee_dob), V.age_on(S.dob)
    minor = n_age < 18
    errs = []
    if minor:
        st.info(f'Nominee is a minor (age {n_age}). Guardian details are required.')
        st.text_input('Guardian name', key='guardian')
        st.text_input('Guardian ID', key='guardian_id')
        st.file_uploader('Guardian photo', type=['png', 'jpg', 'jpeg'], key='guardian_photo')
        keep_blob('guardian_photo')
    nid_n = S.get('nominee_id', '')
    if nid_n and nid_n == S.get('nid'): errs.append('Nominee ID is the same as the applicant’s NID.')
    if nid_n and not minor and not (nid_n.isdigit() and len(nid_n) in (10, 13, 17)): errs.append('Adult nominee NID must be 10, 13 or 17 digits.')
    if nid_n and minor and len(nid_n) not in (13, 17): errs.append('Birth registration numbers are 13 or 17 digits.')
    if S.get('nominee_name') and V.similarity(S.nominee_name, S.get('name', '')) > 0.9: errs.append('Nominee name matches the applicant’s name.')
    rel = S.relationship
    if rel in ('Father', 'Mother') and n_age <= c_age: errs.append(f'A {rel.lower()} should be older than the applicant.')
    if rel in ('Son', 'Daughter') and n_age >= c_age: errs.append(f'A {rel.lower()} should be younger than the applicant.')
    if rel == 'Spouse' and minor: errs.append('A spouse nominee cannot be a minor.')
    for e in errs: st.error(e)
    pd_ = keep_blob('nominee_photo')
    p_ok = quality_panel('Nominee photo', pd_) if pd_ else False
    st.info('Nominee identity-document preservation is required; verification is not mandatory under the cited guideline.')
    g_ok = (not minor) or all(S.get(k) for k in ('guardian', 'guardian_id'))
    if st.button('Review application', disabled=not (S.get('nominee_name') and nid_n and p_ok and g_ok and not errs)): go(6)

else:
    st.subheader('Application review')
    grade, score, why = S.get('risk', ('n/a', 0, []))
    checks = [('Consent given', S.consent), ('NID format valid', V.check_nid(S.get('nid', ''), S.dob)[0]),
              ('Applicant is an adult', V.check_adult(S.dob)[0]), ('NID images captured', bool(S.blobs.get('front') and S.blobs.get('back'))),
              ('Selfie captured', bool(S.blobs.get('selfie'))), ('Demo OTP verified', S.otp_verified),
              ('Nominee photo captured', bool(S.blobs.get('nominee_photo')))]
    st.progress(sum(ok for _, ok in checks) / len(checks), text=f'Readiness {sum(ok for _, ok in checks)}/{len(checks)}')
    for label, ok in checks: st.write(('✅ ' if ok else '❌ ') + label)
    st.divider()
    st.write('**Product:**', S.product); st.write('**e-KYC route:**', S.path)
    st.write('**Customer:**', S.get('name')); st.write('**NID:**', '••••' + S.get('nid', '')[-4:])
    st.write('**Mobile:**', '••••' + S.get('phone', '')[-4:]); st.write('**Nominee:**', S.get('nominee_name'), f'({S.relationship})')
    st.write('**Demo risk indicator:**', grade)
    if grade == 'High': st.warning('High indicator: production would route this to enhanced due diligence.')
    st.checkbox('I confirm the information provided is accurate.', key='declaration')
    st.checkbox('I acknowledge that production account opening requires bank screening, appropriate signature, and approval.', key='ack')
    if st.button('Submit DEMO application', disabled=not (S.get('declaration') and S.get('ack') and all(ok for _, ok in checks))):
        st.success('Demo application captured in this browser session only. No account has been opened.')
        st.warning('Production gating: NID verification + face match + sanctions screening + risk grading (if regular) + signature + core banking approval.')
        st.balloons()

if step > 0 and st.button('← Back'): go(step - 1)
st.divider()
st.caption('No application database is configured. Uploaded images and data remain only in session memory; use synthetic test information. Do not deploy publicly for real NID data.')
