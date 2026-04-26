"""
Seed script — replace the Mathematics subject of GPSTR 2026
with chapters loaded from maths_data.json (extracted from index.html).

Each chapter (merge_code) becomes one Session under a single
"Mathematics / ಗಣಿತ" subject. Sessions are sorted by domain then
chapter_name, with the domain prefixed to the title for visual grouping.
Per-module podcasts ride along on each ModuleVideo.

Usage:
    cd backend
    python seed_exam_maths.py
"""

import os, json
from dotenv import load_dotenv
from mongoengine import connect

from models.exam import Exam, Subject, Session, ModuleVideo

load_dotenv()

connect(
    db=os.getenv('DB_NAME', 'course_platform'),
    host=os.getenv('MONGO_URI'),
)

EXAM_TITLE   = 'GPSTR 2026'
SUBJECT_NAME = 'Mathematics / ಗಣಿತ'
DATA_PATH    = os.path.join(os.path.dirname(__file__), 'maths_data.json')


def s3_url(key: str) -> str:
    """Build origin S3 URL — utils.cdn.cdn_url rewrites it to CloudFront at read time."""
    if not key:
        return ''
    bucket = os.getenv('AWS_BUCKET', 'azad')
    region = os.getenv('AWS_REGION', 'us-east-1')
    return f'https://{bucket}.s3.{region}.amazonaws.com/{key}'


def build_session(chapter: dict) -> Session:
    domain        = chapter.get('domain', '')
    chapter_name  = chapter.get('chapter_name', '')
    classes       = chapter.get('classes') or []
    chapter_nums  = chapter.get('chapter_numbers') or []

    title_parts = []
    if domain:
        title_parts.append(domain)
    title_parts.append(chapter_name)
    suffix = []
    if classes:
        suffix.append(f"Class {','.join(str(c) for c in classes)}")
    if chapter_nums:
        suffix.append(f"Ch {','.join(str(n) for n in chapter_nums)}")
    title = ' · '.join(title_parts)
    if suffix:
        title = f"{title}  ({' · '.join(suffix)})"

    fv = chapter.get('full_video') or {}
    full_video_url      = s3_url(fv.get('s3_key', ''))
    full_video_duration = fv.get('duration_display', '')

    module_videos = []
    for m in chapter.get('modules') or []:
        module_videos.append(ModuleVideo(
            title            = m.get('module_title', ''),
            video_url        = s3_url(m.get('s3_key', '')),
            duration         = m.get('duration_display', ''),
            podcast_url      = s3_url(m.get('podcast_s3_key', '')),
            podcast_duration = m.get('podcast_duration_display', ''),
            slides_count     = int(m.get('total_slides') or 0),
        ))

    return Session(
        title               = title,
        locked              = False,
        notes_locked        = True,   # no notes seeded yet
        mcq_locked          = True,   # no mcqs seeded yet
        descriptive_locked  = True,   # no descriptives seeded yet
        audio_locked        = True,   # session-level audio not used (per-module podcasts instead)
        video_locked        = False,
        live_locked         = True,
        full_video_url      = full_video_url,
        full_video_duration = full_video_duration,
        module_videos       = module_videos,
    )


def main():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        chapters = json.load(f)

    chapters.sort(key=lambda c: (c.get('domain', ''), c.get('chapter_name', '')))

    exam = Exam.objects(title=EXAM_TITLE).first()
    if not exam:
        raise SystemExit(f"Exam not found: {EXAM_TITLE}. Run seed_exam2.py first.")

    sessions = [build_session(c) for c in chapters]
    new_subject = Subject(name=SUBJECT_NAME, locked=False, sessions=sessions)

    replaced = False
    rebuilt_subjects = []
    for sub in exam.subjects:
        if sub.name == SUBJECT_NAME:
            rebuilt_subjects.append(new_subject)
            replaced = True
        else:
            rebuilt_subjects.append(sub)
    if not replaced:
        rebuilt_subjects.append(new_subject)

    exam.subjects = rebuilt_subjects
    exam.save()

    total_modules    = sum(len(s.module_videos) for s in sessions)
    total_video_secs = sum(
        (c.get('full_video') or {}).get('duration_seconds', 0) for c in chapters
    )
    total_pod_secs = sum(
        (m.get('podcast_duration_seconds') or 0)
        for c in chapters for m in (c.get('modules') or [])
    )
    total_slides = sum(int(c.get('total_slides') or 0) for c in chapters)

    print(f"Updated exam: {exam.title} ({exam.exam_id})")
    print(f"  {'Replaced' if replaced else 'Added'} subject: {SUBJECT_NAME}")
    print(f"  Chapters/sessions: {len(sessions)}")
    print(f"  Module videos:     {total_modules}")
    print(f"  Total slides:      {total_slides}")
    print(f"  Full-video hours:  {total_video_secs/3600:.1f}")
    print(f"  Podcast hours:     {total_pod_secs/3600:.1f}")


if __name__ == '__main__':
    main()
