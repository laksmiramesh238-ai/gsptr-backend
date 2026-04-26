"""
Seed script — replace the Science subject of GPSTR 2026 with chapters
loaded from science_data.json (extracted from science_preview.html).

Each chapter (merge_code) becomes one Session under the existing
"Science / ವಿಜ್ಞಾನ" subject. Sessions are sorted by canonical domain
then class then chapter_name, with the domain prefixed to the title.

Domain values in the source are inconsistent (e.g. "ಜೀವಶಾಸ್ತ್ರ" and
"ಜೀವಶಾಸ್ತ್ರ (Biology)" appear as separate strings). They are
canonicalized via DOMAIN_MAP below before grouping.

Usage:
    cd backend
    python seed_exam_science.py
"""

import os, sys, json
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
from dotenv import load_dotenv
from mongoengine import connect

from models.exam import Exam, Subject, Session, ModuleVideo
from models.assessment import Assessment  # noqa: F401  — register doc for ReferenceField

load_dotenv()

connect(
    db=os.getenv('DB_NAME', 'course_platform'),
    host=os.getenv('MONGO_URI'),
)

EXAM_TITLE   = 'GPSTR 2026'
SUBJECT_NAME = 'Science / ವಿಜ್ಞಾನ'
DATA_PATH    = os.path.join(os.path.dirname(__file__), 'science_data.json')

DOMAIN_MAP = {
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


def canonical_domain(raw: str) -> str:
    return DOMAIN_MAP.get(raw, raw)


def s3_url(key: str) -> str:
    if not key:
        return ''
    bucket = os.getenv('AWS_BUCKET', 'azad')
    region = os.getenv('AWS_REGION', 'us-east-1')
    return f'https://{bucket}.s3.{region}.amazonaws.com/{key}'


def build_session(chapter: dict) -> Session:
    domain        = canonical_domain(chapter.get('domain', ''))
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
        notes_locked        = True,
        mcq_locked          = True,
        descriptive_locked  = True,
        audio_locked        = False,  # ready for podcasts when added
        video_locked        = False,
        live_locked         = True,
        full_video_url      = full_video_url,
        full_video_duration = full_video_duration,
        module_videos       = module_videos,
    )


def main():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        chapters = json.load(f)

    chapters.sort(key=lambda c: (
        canonical_domain(c.get('domain', '')),
        (c.get('classes') or [99])[0],
        (c.get('chapter_numbers') or [999])[0],
        c.get('chapter_name', ''),
    ))

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

    from collections import Counter
    canon_counts = Counter(canonical_domain(c.get('domain', '')) for c in chapters)

    print(f"Updated exam: {exam.title} ({exam.exam_id})")
    print(f"  {'Replaced' if replaced else 'Added'} subject: {SUBJECT_NAME}")
    print(f"  Chapters/sessions: {len(sessions)}")
    print(f"  Module videos:     {total_modules}")
    print(f"  Total slides:      {total_slides}")
    print(f"  Full-video hours:  {total_video_secs/3600:.1f}")
    print(f"  Podcast hours:     {total_pod_secs/3600:.1f}")
    print(f"  Domains (canonical):")
    for d, n in canon_counts.most_common():
        print(f"    {n:>3}  {d}")


if __name__ == '__main__':
    main()
