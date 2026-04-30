"""
Seed script — add/replace Ancient History chapters under the existing
"Social Studies / ಸಮಾಜ ವಿಜ್ಞಾನ" subject of GPSTR 2026.

Each chapter becomes one Session prefixed with the domain
"Ancient History (ಪ್ರಾಚೀನ ಇತಿಹಾಸ)" so it groups visually alongside
Medieval History sessions (which use no domain prefix).

Existing sessions whose title starts with the Ancient History domain
are removed first; everything else (Medieval History, etc.) is left
untouched. Video URLs are direct CloudFront URLs.

Usage:
    cd backend
    python seed_exam_social_ancient.py
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
SUBJECT_NAME = 'Social Studies / ಸಮಾಜ ವಿಜ್ಞಾನ'
DOMAIN       = 'Ancient History (ಪ್ರಾಚೀನ ಇತಿಹಾಸ)'
DATA_PATH    = os.path.join(os.path.dirname(__file__), 'social_ancient_history_data.json')


def build_session(chapter: dict) -> Session:
    chapter_name = chapter.get('chapter_name', '')
    title = f"{DOMAIN} · {chapter_name}"

    module_videos = [
        ModuleVideo(
            title     = m.get('title', ''),
            video_url = m.get('video_url', ''),
        )
        for m in chapter.get('modules') or []
    ]

    return Session(
        title               = title,
        locked              = False,
        notes_locked        = True,
        mcq_locked          = True,
        descriptive_locked  = True,
        audio_locked        = True,
        video_locked        = False,
        live_locked         = True,
        full_video_url      = chapter.get('full_video_url', ''),
        full_video_duration = '',
        module_videos       = module_videos,
    )


def main():
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        chapters = json.load(f)

    chapters.sort(key=lambda c: c.get('chapter_name', ''))

    exam = Exam.objects(title=EXAM_TITLE).first()
    if not exam:
        raise SystemExit(f"Exam not found: {EXAM_TITLE}. Run seed_exam2.py first.")

    subject = next((s for s in exam.subjects if s.name == SUBJECT_NAME), None)
    if not subject:
        raise SystemExit(f"Subject not found: {SUBJECT_NAME}. Run seed_exam2.py first.")

    kept = [s for s in subject.sessions if not s.title.startswith(DOMAIN)]
    new_sessions = [build_session(c) for c in chapters]
    subject.sessions = kept + new_sessions

    exam.save()

    total_modules = sum(len(s.module_videos) for s in new_sessions)
    print(f"Updated exam:    {exam.title} ({exam.exam_id})")
    print(f"  Subject:       {SUBJECT_NAME}")
    print(f"  Domain:        {DOMAIN}")
    print(f"  Kept sessions: {len(kept)}")
    print(f"  New sessions:  {len(new_sessions)}")
    print(f"  Module videos: {total_modules}")


if __name__ == '__main__':
    main()
