"""
Replace each session's `title` with the Kannada-only version
from titles_export_kn.csv (column session_title_kn).

Usage:  python update_titles_kn.py
"""

import os, sys, csv
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
CSV_PATH   = os.path.join(os.path.dirname(__file__), 'titles_export_kn.csv')


def main():
    # subject_name -> { session_no (int) -> kn_title }
    lookup = {}
    with open(CSV_PATH, encoding='utf-8-sig') as f:
        for row in csv.DictReader(f):
            kn = (row.get('session_title_kn') or '').strip()
            if not kn:
                continue
            lookup.setdefault(row['subject'], {})[int(row['session_no'])] = kn

    exam = Exam.objects(title=EXAM_TITLE).first()
    if not exam:
        raise SystemExit(f"Exam not found: {EXAM_TITLE}")

    updated = 0
    skipped = 0
    for sub in exam.subjects:
        sub_lookup = lookup.get(sub.name)
        if not sub_lookup:
            continue
        for i, sess in enumerate(sub.sessions, 1):
            kn = sub_lookup.get(i)
            if not kn:
                skipped += 1
                continue
            if sess.title != kn:
                sess.title = kn
                updated += 1

    exam.save()

    print(f"Exam: {exam.title} ({exam.exam_id})")
    print(f"  Updated:  {updated}")
    print(f"  Skipped:  {skipped} (no Kannada match)")
    print("Done.")


if __name__ == '__main__':
    main()
