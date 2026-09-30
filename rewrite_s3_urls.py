"""
Rewrite every stored URL in course_platform (courses, chapters, exams/
sessions/module_videos, test question images) that points at the OLD
S3/CloudFront domain, so it points at the NEW one instead — same domain
swap, same path/key preserved. Part of the AWS account migration.

Only ever touches the course_platform database (gsptr's own) — never
azad-db or any other database on the shared Atlas cluster.

Dry-run by default (prints old -> new per document, writes nothing).
--apply actually performs the updates.

Usage:
  python rewrite_s3_urls.py            # dry run
  python rewrite_s3_urls.py --apply    # actually rewrite
"""
import os, sys
from urllib.parse import urlparse, urlunparse

try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass

from dotenv import load_dotenv; load_dotenv()
from pymongo import MongoClient

MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = os.getenv('DB_NAME', 'course_platform')

OLD_HOSTS = {
    'd1ytcm2rfo0yep.cloudfront.net',
    'azad.s3.us-east-1.amazonaws.com',
    'azad.s3.amazonaws.com',
}
NEW_HOST = os.getenv('CLOUDFRONT_DOMAIN', 'd3bvnyjr8ehzld.cloudfront.net')


def rewrite(url):
    """Return the rewritten URL, or None if it doesn't need changing."""
    if not url or not isinstance(url, str) or not url.startswith('http'):
        return None
    p = urlparse(url)
    if p.netloc not in OLD_HOSTS:
        return None
    return urlunparse(p._replace(netloc=NEW_HOST, scheme='https'))


def main():
    apply = '--apply' in sys.argv
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]

    changes = []  # (collection, doc_id, field_path, old, new)

    # ── courses.thumbnail_url ──
    for co in db.courses.find({}, {'thumbnail_url': 1}):
        new = rewrite(co.get('thumbnail_url'))
        if new:
            changes.append(('courses', co['_id'], 'thumbnail_url', co['thumbnail_url'], new))

    # ── chapters (video/pdf/audio) ──
    for ch in db.chapters.find({}):
        t = ch.get('type')
        sub = ch.get(t) or {}
        if t == 'video':
            for f in ('video_url', 'thumbnail'):
                new = rewrite(sub.get(f))
                if new:
                    changes.append(('chapters', ch['_id'], f'video.{f}', sub.get(f), new))
        elif t == 'pdf':
            new = rewrite(sub.get('pdf_url'))
            if new:
                changes.append(('chapters', ch['_id'], 'pdf.pdf_url', sub.get('pdf_url'), new))
        elif t == 'audio':
            new = rewrite(sub.get('audio_url'))
            if new:
                changes.append(('chapters', ch['_id'], 'audio.audio_url', sub.get('audio_url'), new))

    # ── exams (thumbnail + subjects/sessions/module_videos) ──
    for ex in db.exams.find({}):
        new = rewrite(ex.get('thumbnail_url'))
        if new:
            changes.append(('exams', ex['_id'], 'thumbnail_url', ex.get('thumbnail_url'), new))
        for si, sub in enumerate(ex.get('subjects', [])):
            for ssi, sess in enumerate(sub.get('sessions', [])):
                for f in ('notes_pdf_url', 'audio_url', 'full_video_url'):
                    new = rewrite(sess.get(f))
                    if new:
                        path = f'subjects.{si}.sessions.{ssi}.{f}'
                        changes.append(('exams', ex['_id'], path, sess.get(f), new))
                for mi, mv in enumerate(sess.get('module_videos', [])):
                    for f in ('video_url', 'podcast_url'):
                        new = rewrite(mv.get(f))
                        if new:
                            path = f'subjects.{si}.sessions.{ssi}.module_videos.{mi}.{f}'
                            changes.append(('exams', ex['_id'], path, mv.get(f), new))

    # ── tests (question images, real URLs only — placeholder text like "<image>" is skipped by rewrite()) ──
    for t in db.tests.find({}):
        for qi, q in enumerate(t.get('questions', [])):
            new = rewrite(q.get('question_image'))
            if new:
                changes.append(('tests', t['_id'], f'questions.{qi}.question_image', q.get('question_image'), new))
            for k in 'abcd':
                opt = q.get('option_' + k) or {}
                new = rewrite(opt.get('image_url'))
                if new:
                    path = f'questions.{qi}.option_{k}.image_url'
                    changes.append(('tests', t['_id'], path, opt.get('image_url'), new))

    print(f'Found {len(changes)} URL(s) to rewrite across course_platform.')
    print()
    for coll, doc_id, field, old, new in changes[:30]:
        print(f'[{coll}] {doc_id} .{field}')
        print(f'    {old}')
        print(f' -> {new}')
    if len(changes) > 30:
        print(f'... and {len(changes) - 30} more')

    if not apply:
        print()
        print('Dry run only. Re-run with --apply to actually write these changes.')
        return

    print()
    print('Applying...')
    done = 0
    for coll, doc_id, field, old, new in changes:
        db[coll].update_one({'_id': doc_id}, {'$set': {field: new}})
        done += 1
    print(f'Updated {done} field(s).')


if __name__ == '__main__':
    main()
