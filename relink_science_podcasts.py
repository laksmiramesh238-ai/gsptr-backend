"""
Set podcast_url on every Science ModuleVideo, using the upload pattern:
  s3://azad/podcasts/science/<merge_code>/<module_id>.wav

Module IDs come from science_data.json (same source the user's upload
script used). No S3 verification — URLs are constructed deterministically.
Files that don't exist yet will 404 at request time; they'll resolve as
the user uploads them.

Usage:  python relink_science_podcasts.py
"""

import os, sys, json
try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass

from dotenv import load_dotenv; load_dotenv()
from mongoengine import connect
connect(db=os.getenv('DB_NAME', 'course_platform'), host=os.getenv('MONGO_URI'))

from models.exam import Exam

EXAM_TITLE = 'GPSTR 2026'
SUBJECT    = 'Science / ವಿಜ್ಞಾನ'
DATA_PATH  = os.path.join(os.path.dirname(__file__), 'science_data.json')

BUCKET = os.getenv('AWS_BUCKET', 'azad')
REGION = os.getenv('AWS_REGION', 'us-east-1')


def s3_url(key):
    return f'https://{BUCKET}.s3.{REGION}.amazonaws.com/{key}'


def main():
    with open(DATA_PATH, encoding='utf-8') as f:
        chapters = json.load(f)
    by_code = {c['merge_code']: c for c in chapters}

    exam = Exam.objects(title=EXAM_TITLE).first()
    sub  = next((s for s in exam.subjects if s.name == SUBJECT), None)
    if not sub:
        raise SystemExit('Science subject not found')

    linked = 0
    no_match = 0
    for sess in sub.sessions:
        ch = by_code.get(sess.merge_code)
        if not ch:
            no_match += 1
            continue
        for mv, src in zip(sess.module_videos, ch.get('modules', [])):
            module_id = src.get('module_id', '')
            if not module_id: continue
            url = s3_url(f'podcasts/science/{ch["merge_code"]}/{module_id}.wav')
            if mv.podcast_url != url:
                mv.podcast_url = url
                linked += 1

    exam.save()
    print(f'Science sessions: {len(sub.sessions)}')
    print(f'  Module podcasts linked: {linked}')
    print(f'  Sessions with no science_data match: {no_match}')


if __name__ == '__main__':
    main()
