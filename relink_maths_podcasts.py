"""
For every Maths session, copy podcast_url + podcast_duration onto each
ModuleVideo from maths_data.json (which already has the S3 URLs).

Idempotent — does NOT touch sessions / titles / locks. Only the
podcast_url + podcast_duration on each module.

Usage:  python relink_maths_podcasts.py
"""
import os, sys, json
try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass

from dotenv import load_dotenv; load_dotenv()
from mongoengine import connect
connect(db=os.getenv('DB_NAME', 'course_platform'), host=os.getenv('MONGO_URI'))

from models.exam import Exam

EXAM_TITLE = 'GPSTR 2026'
SUBJECT    = 'Mathematics / ಗಣಿತ'
DATA_PATH  = os.path.join(os.path.dirname(__file__), 'maths_data.json')


def s3_url(key):
    if not key: return ''
    bucket = os.getenv('AWS_BUCKET', 'azad')
    region = os.getenv('AWS_REGION', 'us-east-1')
    return f'https://{bucket}.s3.{region}.amazonaws.com/{key}'


def main():
    with open(DATA_PATH, encoding='utf-8') as f:
        chapters = json.load(f)
    by_code = {c['merge_code']: c for c in chapters}

    exam = Exam.objects(title=EXAM_TITLE).first()
    sub  = next((s for s in exam.subjects if s.name == SUBJECT), None)
    if not sub:
        raise SystemExit('Maths subject not found')

    relinked = 0
    skipped  = 0
    for sess in sub.sessions:
        ch = by_code.get(sess.merge_code)
        if not ch:
            skipped += 1
            continue
        # Map module_id → podcast info
        pod_by_id = {m.get('module_id'): m for m in ch.get('modules', [])}
        # Sessions store modules in same order as JSON; use ordered match
        for mv, src in zip(sess.module_videos, ch.get('modules', [])):
            url = s3_url(src.get('podcast_s3_key', ''))
            if url and mv.podcast_url != url:
                mv.podcast_url = url
                mv.podcast_duration = src.get('podcast_duration_display', '') or mv.podcast_duration
                relinked += 1

    exam.save()
    print(f'Maths sessions: {len(sub.sessions)}')
    print(f'  Module podcasts relinked: {relinked}')
    print(f'  Sessions skipped (no merge_code match): {skipped}')


if __name__ == '__main__':
    main()
