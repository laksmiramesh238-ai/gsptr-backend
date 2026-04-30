"""
Export all session titles for Maths, Science, and Social Studies under
GPSTR 2026 to a single CSV.

Usage:  python export_titles.py
"""

import os, csv, sys
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
SUBJECTS = [
    'Mathematics / ಗಣಿತ',
    'Science / ವಿಜ್ಞಾನ',
    'Social Studies / ಸಮಾಜ ವಿಜ್ಞಾನ',
]
OUT_PATH = os.path.join(os.path.dirname(__file__), 'titles_export.csv')


def main():
    exam = Exam.objects(title=EXAM_TITLE).first()
    if not exam:
        raise SystemExit(f"Exam not found: {EXAM_TITLE}")

    rows = []
    for sub in exam.subjects:
        if sub.name not in SUBJECTS:
            continue
        for i, sess in enumerate(sub.sessions, 1):
            rows.append({
                'subject': sub.name,
                'session_no': i,
                'session_title': sess.title,
                'module_count': len(sess.module_videos),
                'preview': bool(getattr(sess, 'preview', False)),
                'locked': bool(sess.locked),
            })

    with open(OUT_PATH, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=['subject', 'session_no', 'session_title',
                                          'module_count', 'preview', 'locked'])
        w.writeheader()
        w.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUT_PATH}")
    by_subj = {}
    for r in rows:
        by_subj.setdefault(r['subject'], 0)
        by_subj[r['subject']] += 1
    for k, v in by_subj.items():
        print(f"  {v:>3}  {k}")


if __name__ == '__main__':
    main()
