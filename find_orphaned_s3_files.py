"""
Compare every object actually in the S3 bucket against every URL/key
referenced anywhere in the database, and report what's sitting in S3
but not linked from any document — i.e. safe-to-review storage waste.

Read-only. Does not delete or modify anything.

Scans for referenced URLs across:
  - courses.thumbnail_url
  - chapters.video.{video_url,thumbnail}, .pdf.pdf_url, .audio.audio_url
  - exams.thumbnail_url
  - exams.subjects[].sessions[].{notes_pdf_url,audio_url,full_video_url}
  - exams.subjects[].sessions[].module_videos[].{video_url,podcast_url}
  - tests.questions[].question_image / option_[abcd].image_url
    (only counted if they look like a real URL, not placeholder text)

Usage:
  python find_orphaned_s3_files.py                 # summary + samples
  python find_orphaned_s3_files.py --full-list out.csv   # also write every orphan to CSV
"""
import os, sys, csv
from urllib.parse import urlparse

try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass

from dotenv import load_dotenv; load_dotenv()
import boto3
from pymongo import MongoClient

MONGO_URI = os.getenv('MONGO_URI')
DB_NAME   = os.getenv('DB_NAME', 'course_platform')
AWS_ACCESS_KEY_ID     = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION            = os.getenv('AWS_REGION', 'us-east-1')
AWS_BUCKET            = os.getenv('AWS_BUCKET', 'azad')
CLOUDFRONT_DOMAIN     = os.getenv('CLOUDFRONT_DOMAIN', '')

OUR_HOSTS = {
    f'{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com',
    f'{AWS_BUCKET}.s3.amazonaws.com',
    CLOUDFRONT_DOMAIN,
}


def url_to_key(url: str):
    """Return the S3 key a URL points to, or None if it's not one of our hosts."""
    if not url or not isinstance(url, str):
        return None
    url = url.strip()
    if not url.startswith('http'):
        return None  # placeholder text like "<image>", not a real URL
    p = urlparse(url)
    if p.netloc not in OUR_HOSTS:
        return None
    return p.path.lstrip('/')


def list_all_s3_objects():
    s3 = boto3.client(
        's3', aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY, region_name=AWS_REGION,
    )
    objs = {}
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=AWS_BUCKET):
        for obj in page.get('Contents', []):
            objs[obj['Key']] = obj['Size']
    return objs


def collect_referenced_keys(db):
    keys = set()

    def add(url):
        k = url_to_key(url)
        if k:
            keys.add(k)

    for co in db.courses.find({}, {'thumbnail_url': 1}):
        add(co.get('thumbnail_url'))

    for ch in db.chapters.find({}):
        t = ch.get('type')
        sub = ch.get(t) or {}
        if t == 'video':
            add(sub.get('video_url')); add(sub.get('thumbnail'))
        elif t == 'pdf':
            add(sub.get('pdf_url'))
        elif t == 'audio':
            add(sub.get('audio_url'))

    for ex in db.exams.find({}):
        add(ex.get('thumbnail_url'))
        for sub in ex.get('subjects', []):
            for sess in sub.get('sessions', []):
                add(sess.get('notes_pdf_url'))
                add(sess.get('audio_url'))
                add(sess.get('full_video_url'))
                for mv in sess.get('module_videos', []):
                    add(mv.get('video_url'))
                    add(mv.get('podcast_url'))

    for t in db.tests.find({}):
        for q in t.get('questions', []):
            add(q.get('question_image'))
            for k in 'abcd':
                add((q.get('option_' + k) or {}).get('image_url'))

    return keys


def human(n):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if n < 1024:
            return f'{n:.1f} {unit}'
        n /= 1024
    return f'{n:.1f} TB'


def main():
    full_list_path = None
    if '--full-list' in sys.argv:
        idx = sys.argv.index('--full-list')
        full_list_path = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else 'orphans.csv'

    c = MongoClient(MONGO_URI)
    db = c[DB_NAME]

    print('Listing all S3 objects...')
    s3_objects = list_all_s3_objects()
    total_size = sum(s3_objects.values())
    print(f'  {len(s3_objects)} objects, {human(total_size)} total')

    print('Collecting referenced keys from MongoDB...')
    referenced = collect_referenced_keys(db)
    print(f'  {len(referenced)} unique keys referenced')

    orphan_keys = sorted(set(s3_objects) - referenced)
    orphan_size = sum(s3_objects[k] for k in orphan_keys)

    referenced_but_missing = sorted(k for k in referenced if k not in s3_objects)

    print()
    print('=== SUMMARY ===')
    print(f'  Total in S3:        {len(s3_objects)} objects, {human(total_size)}')
    print(f'  Referenced in DB:   {len(referenced) - len(referenced_but_missing)} objects')
    print(f'  ORPHANED (unused):  {len(orphan_keys)} objects, {human(orphan_size)}')
    if referenced_but_missing:
        print(f'  DB points at missing S3 objects: {len(referenced_but_missing)}  (broken links — separate issue)')

    # Breakdown by top-level folder
    from collections import defaultdict
    by_folder = defaultdict(lambda: [0, 0])
    for k in orphan_keys:
        folder = k.split('/')[0] if '/' in k else '(root)'
        by_folder[folder][0] += 1
        by_folder[folder][1] += s3_objects[k]
    print()
    print('=== ORPHANED, BY FOLDER ===')
    for folder, (cnt, sz) in sorted(by_folder.items(), key=lambda x: -x[1][1]):
        print(f'  {folder:24s} {cnt:5d} files   {human(sz)}')

    print()
    print('=== SAMPLE ORPHANS (first 20) ===')
    for k in orphan_keys[:20]:
        print(f'  {human(s3_objects[k]):>10s}  {k}')
    if len(orphan_keys) > 20:
        print(f'  ... and {len(orphan_keys) - 20} more')

    if referenced_but_missing:
        print()
        print('=== DB references pointing at S3 objects that no longer exist (first 20) ===')
        for k in referenced_but_missing[:20]:
            print(f'  {k}')

    if full_list_path:
        with open(full_list_path, 'w', newline='', encoding='utf-8') as f:
            w = csv.writer(f)
            w.writerow(['key', 'size_bytes', 'size_human'])
            for k in orphan_keys:
                w.writerow([k, s3_objects[k], human(s3_objects[k])])
        print()
        print(f'Full orphan list written to {full_list_path}')


if __name__ == '__main__':
    main()
