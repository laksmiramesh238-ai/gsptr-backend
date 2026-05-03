"""
Backfill merge_code on every Mathematics session of GPSTR 2026.

Matches by index — the maths seed script sorted chapters by
(domain, chapter_name) before saving, so the i-th chapter in
maths_data.json (sorted the same way) corresponds to the i-th
session in DB.

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

EXAM_TITLE   = 'GPSTR 2026'
SUBJECT_NAME = 'Mathematics / ಗಣಿತ'
DATA_PATH    = os.path.join(os.path.dirname(__file__), 'maths_data.json')


def main():
    with open(DATA_PATH, encoding='utf-8') as f:
        chapters = json.load(f)
    chapters.sort(key=lambda c: (c.get('domain', ''), c.get('chapter_name', '')))

    exam = Exam.objects(title=EXAM_TITLE).first()
    if not exam:
        raise SystemExit(f"Exam not found: {EXAM_TITLE}")

    sub = next((s for s in exam.subjects if s.name == SUBJECT_NAME), None)
    if not sub:
        raise SystemExit(f"Subject not found: {SUBJECT_NAME}")

    if len(sub.sessions) != len(chapters):
        print(f"WARNING: {len(sub.sessions)} sessions vs {len(chapters)} source chapters — alignment may be off")

    updated = 0
    for sess, ch in zip(sub.sessions, chapters):
        mc = ch.get('merge_code', '')
        if sess.merge_code != mc:
            sess.merge_code = mc
            updated += 1

    exam.save()
    print(f"Maths sessions: {len(sub.sessions)}")
    print(f"merge_code updated on: {updated}")


if __name__ == '__main__':
    main()
