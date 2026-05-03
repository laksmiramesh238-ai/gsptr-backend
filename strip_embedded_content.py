"""
Strip notes_html / mcqs / descriptive_questions out of every embedded
Session in every Exam to bring the Exam document back under 16 MB.

After this runs, run seed_notes_questions.py — it now writes to the
SessionContent collection instead of embedding.

Usage:  python strip_embedded_content.py
"""
import os, sys
try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass

from dotenv import load_dotenv; load_dotenv()
from mongoengine import connect
connect(db=os.getenv('DB_NAME', 'course_platform'), host=os.getenv('MONGO_URI'))

from models.exam import Exam

def main():
    cleared = 0
    for exam in Exam.objects():
        for sub in exam.subjects:
            for sess in sub.sessions:
                if sess.notes_html or sess.mcqs or sess.descriptive_questions:
                    cleared += 1
                sess.notes_html = ''
                sess.mcqs = []
                sess.descriptive_questions = []
        exam.save()
        print(f"Stripped: {exam.title}")
    print(f"Sessions cleared: {cleared}")

if __name__ == '__main__':
    main()
