"""
Backfill merge_code on Mathematics + Science sessions of GPSTR 2026.

Matches by index — each subject's seed script sorted chapters with a
deterministic key before saving, so the i-th chapter in the JSON
(sorted the same way) corresponds to the i-th session in DB.

Usage:  python backfill_merge_codes.py
"""

import os, sys, json
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from dotenv import load_dotenv
load_dotenv()

from mongoengine import connect
connect(db=os.getenv('DB_NAME', 'course_platform'), host=os.getenv('MONGO_URI'))

from models.exam import Exam

EXAM_TITLE = 'GPSTR 2026'

# ── per-subject sort keys, mirroring each seed script ───────────────────────

def _maths_key(c):
    return (c.get('domain', ''), c.get('chapter_name', ''))


# Science seed canonicalizes domain — replicate just enough to match.
_SCI_DOMAIN_MAP = {
    'ಜೀವಶಾಸ್ತ್ರ':                                  'ಜೀವಶಾಸ್ತ್ರ (Biology)',
    'ಜೀವಶಾಸ್ತ್ರ (Biology)':                        'ಜೀವಶಾಸ್ತ್ರ (Biology)',
    'ಭೌತಶಾಸ್ತ್ರ':                                  'ಭೌತಶಾಸ್ತ್ರ (Physics)',
    'ಭೌತಶಾಸ್ತ್ರ (Physics)':                        'ಭೌತಶಾಸ್ತ್ರ (Physics)',
    'ರಸಾಯನಶಾಸ್ತ್ರ':                                 'ರಸಾಯನಶಾಸ್ತ್ರ (Chemistry)',
    'ರಸಾಯನಶಾಸ್ತ್ರ (Chemistry)':                    'ರಸಾಯನಶಾಸ್ತ್ರ (Chemistry)',
    'ಪರಿಸರ ವಿಜ್ಞಾನ (Environmental Science)':       'ಪರಿಸರ ವಿಜ್ಞಾನ (Environmental Science)',
    'ಪರಿಸರ ವಿಜ್ಞಾನ (Ecology)':                     'ಪರಿಸರ ವಿಜ್ಞಾನ (Environmental Science)',
    'ಸಾಮಾನ್ಯ ವಿಜ್ಞಾನ (General Science)':           'ಸಾಮಾನ್ಯ ವಿಜ್ಞಾನ (General Science)',
    'General Science':                              'ಸಾಮಾನ್ಯ ವಿಜ್ಞಾನ (General Science)',
    'ಖಗೋಳ ವಿಜ್ಞಾನ (Astronomy)':                    'ಖಗೋಳ ವಿಜ್ಞಾನ (Astronomy)',
    'ಜೀವಶಾಸ್ತ್ರ (Biology) / ಭೌತಶಾಸ್ತ್ರ (Physics)':  'ಜೀವಶಾಸ್ತ್ರ (Biology)',
    'ಜೀವಶಾಸ್ತ್ರ / ಪರಿಸರ ವಿಜ್ಞಾನ':                    'ಜೀವಶಾಸ್ತ್ರ (Biology)',
}

def _science_key(c):
    domain = _SCI_DOMAIN_MAP.get(c.get('domain', ''), c.get('domain', ''))
    return (
        domain,
        (c.get('classes') or [99])[0],
        (c.get('chapter_numbers') or [999])[0],
        c.get('chapter_name', ''),
    )


JOBS = [
    {
        'subject':  'Mathematics / ಗಣಿತ',
        'data':     'maths_data.json',
        'sort_key': _maths_key,
    },
    {
        'subject':  'Science / ವಿಜ್ಞಾನ',
        'data':     'science_data.json',
        'sort_key': _science_key,
    },
]


def main():
    exam = Exam.objects(title=EXAM_TITLE).first()
    if not exam:
        raise SystemExit(f"Exam not found: {EXAM_TITLE}")

    grand_total = 0
    for job in JOBS:
        path = os.path.join(os.path.dirname(__file__), job['data'])
        if not os.path.exists(path):
            print(f"SKIP {job['subject']}: {job['data']} not found")
            continue

        with open(path, encoding='utf-8') as f:
            chapters = json.load(f)
        chapters.sort(key=job['sort_key'])

        sub = next((s for s in exam.subjects if s.name == job['subject']), None)
        if not sub:
            print(f"SKIP {job['subject']}: subject not found in exam")
            continue
        if len(sub.sessions) != len(chapters):
            print(f"WARNING {job['subject']}: {len(sub.sessions)} sessions vs {len(chapters)} chapters")

        updated = 0
        for sess, ch in zip(sub.sessions, chapters):
            mc = ch.get('merge_code', '')
            if sess.merge_code != mc:
                sess.merge_code = mc
                updated += 1
        print(f"{job['subject']}: {len(sub.sessions)} sessions, merge_code updated on {updated}")
        grand_total += updated

    exam.save()
    print(f"\nTotal updates: {grand_total}")


if __name__ == '__main__':
    main()
