"""Local, offline smart checks. These are heuristics, NOT government verification."""
import re
from datetime import date
from difflib import SequenceMatcher

def age_on(dob: date, today: date | None = None) -> int:
    t = today or date.today()
    return t.year - dob.year - ((t.month, t.day) < (dob.month, dob.day))

def check_nid(nid: str, dob: date):
    """Return (ok, messages). Format/consistency only: 10 (smart), 13 or 17 (legacy)."""
    msgs = []
    if not nid.isdigit():
        return False, ['NID must contain digits only.']
    if len(nid) not in (10, 13, 17):
        return False, ['NID must be 10, 13 or 17 digits.']
    if len(set(nid)) == 1 or nid in ('1234567890', '1234567890123'):
        return False, ['NID looks like a placeholder pattern.']
    if len(nid) == 17 and nid[:4] != str(dob.year):
        msgs.append(f'17-digit NID starts with {nid[:4]} but DOB year is {dob.year}.')
    return (not msgs), msgs

def check_adult(dob: date, minimum=18):
    a = age_on(dob)
    return (a >= minimum), a

def check_phone(p: str):
    return bool(re.fullmatch(r'01[3-9]\d{8}', p))

def is_bangla(text: str):
    letters = [c for c in text if c.isalpha()]
    return bool(letters) and all('\u0980' <= c <= '\u09FF' for c in letters)

def is_english_name(text: str):
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z .'\-]{1,80}", text.strip()))

def similarity(a: str, b: str) -> float:
    n = lambda s: re.sub(r'\s+', ' ', s.strip().lower())
    return SequenceMatcher(None, n(a), n(b)).ratio()

def clean_title(name: str) -> str:
    return ' '.join(w.capitalize() for w in name.split())
