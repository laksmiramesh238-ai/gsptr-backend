"""
Lock all content types except video on every session of every subject
in every exam. Audio is unlocked only on Mathematics; locked elsewhere.
Preview is forced off on every session.

Usage:  python lock_content.py
"""

import os, sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from dotenv import load_dotenv
load_dotenv()

from mongoengine import connect
connect(db=os.getenv('DB_NAME', 'course_platform'), host=os.getenv('MONGO_URI'))

from models.exam import Exam

AUDIO_UNLOCKED_SUBJECTS = {
    'Mathematics / ಗಣಿತ',
}


def main():
    total = 0
    audio_open = 0
    preview_cleared = 0

    for exam in Exam.objects():
        for sub in exam.subjects:
            audio_unlocked = sub.name in AUDIO_UNLOCKED_SUBJECTS
            for sess in sub.sessions:
                if getattr(sess, 'preview', False):
                    preview_cleared += 1
                sess.preview = False

                sess.video_locked       = False
                sess.audio_locked       = not audio_unlocked
                sess.notes_locked       = True
                sess.mcq_locked         = True
                sess.descriptive_locked = True
                sess.live_locked        = True

                total += 1
                if audio_unlocked:
                    audio_open += 1
        exam.save()
        print(f"Saved: {exam.title} ({exam.exam_id})")

    print()
    print(f"Sessions touched:                {total}")
    print(f"  Audio unlocked (Mathematics):  {audio_open}")
    print(f"  Audio locked (everything else): {total - audio_open}")
    print(f"  Previews cleared:              {preview_cleared}")
    print("Done.")


if __name__ == '__main__':
    main()
