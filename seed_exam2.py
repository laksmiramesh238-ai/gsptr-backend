"""
Seed script — GPSTR (Graduate Primary School Teacher Recruitment) exam.
Run:  python seed_exam.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from mongoengine import connect
connect(db=os.getenv('DB_NAME', 'course_platform'), host=os.getenv('MONGO_URI'))

from models.exam import (
    Exam, Subject, Session, MCQQuestion, DescriptiveQuestion,
    ModuleVideo, ExamLiveClass,
)
from models.assessment import Assessment, AssessmentQuestion

# ── CloudFront base ────────────────────────────────────────────────────────────

CF = "https://d34wwgjscxms4y.cloudfront.net"
SOCIAL_BASE = f"{CF}/GPSTR/Courses/Social/MedivalHistory"

# ── Helper: build video URL ────────────────────────────────────────────────────

def video_url(session_id, filename):
    return f"{SOCIAL_BASE}/{session_id}/{filename}"

# ── Social Studies Sessions ────────────────────────────────────────────────────

social_sessions = [

    Session(
        title='6 ರಿಂದ 14ನೇ ಶತಮಾನದ ಉತ್ತರ ಭಾರತದ ರಾಜ ಮನೆತನಗಳು',
        locked=False,
        notes_locked=False, mcq_locked=False, descriptive_locked=False,
        audio_locked=False, video_locked=False, live_locked=False,

        notes_html="""
<h2>Session 1 — 6 ರಿಂದ 14ನೇ ಶತಮಾನದ ಉತ್ತರ ಭಾರತದ ರಾಜ ಮನೆತನಗಳು</h2>
<p>This session covers the major ruling dynasties of North India from the 6th to 14th centuries.</p>
<ul>
  <li><strong>ಕಾರ್ಕೋಟ ವಂಶ:</strong> History, rule and contributions</li>
  <li><strong>ರಜಪೂತರು:</strong> Introduction and characteristics</li>
  <li><strong>ಗುರ್ಜರ-ಪ್ರತೀಹಾರ, ಪಾರಮಾರ, ಚಂದೇಲ, ಚೌಹಾಣ, ಸೋಲಂಕಿ, ಗಹಡ್ವಾಲ, ಗುಹಿಲ ವಂಶಗಳು</strong></li>
  <li><strong>ಆರ್ಥಿಕ ಮತ್ತು ಸಾಮಾಜಿಕ ಸ್ಥಿತಿ</strong></li>
  <li><strong>ಪಾಲರು</strong></li>
</ul>
""".strip(),
        notes_pdf_url='',

        mcqs=[
            MCQQuestion(
                question='ರಾಜಪೂತ ವಂಶದ ಪ್ರಮುಖ ಲಕ್ಷಣ ಯಾವುದು?',
                options=['ವ್ಯಾಪಾರ', 'ಯುದ್ಧ ಶೌರ್ಯ', 'ಕೃಷಿ', 'ವಿಜ್ಞಾನ'],
                answer=1,
                explanation='ರಜಪೂತರು ತಮ್ಮ ಯುದ್ಧ ಶೌರ್ಯ ಮತ್ತು ಧೈರ್ಯಕ್ಕೆ ಹೆಸರಾಗಿದ್ದರು.',
            ),
            MCQQuestion(
                question='ಪೃಥ್ವಿರಾಜ ಚೌಹಾಣ ಯಾವ ವಂಶಕ್ಕೆ ಸೇರಿದ್ದ?',
                options=['ಪಾಲ', 'ಚಂದೇಲ', 'ಚೌಹಾಣ', 'ಸೋಲಂಕಿ'],
                answer=2,
                explanation='ಪೃಥ್ವಿರಾಜ ಚೌಹಾಣ ಚೌಹಾಣ ವಂಶದ ಪ್ರಮುಖ ರಾಜ.',
            ),
            MCQQuestion(
                question='ಪಾಲ ವಂಶ ಮುಖ್ಯವಾಗಿ ಯಾವ ಭಾಗದಲ್ಲಿ ಆಳಿತು?',
                options=['ರಾಜಸ್ಥಾನ', 'ಬಂಗಾಳ ಮತ್ತು ಬಿಹಾರ', 'ಗುಜರಾತ್', 'ಪಂಜಾಬ್'],
                answer=1,
                explanation='ಪಾಲ ವಂಶ ಬಂಗಾಳ ಮತ್ತು ಬಿಹಾರದಲ್ಲಿ ಆಳ್ವಿಕೆ ನಡೆಸಿತು.',
            ),
            MCQQuestion(
                question='ಕಾರ್ಕೋಟ ವಂಶ ಯಾವ ಪ್ರದೇಶದಲ್ಲಿ ಆಳಿತು?',
                options=['ಕಾಶ್ಮೀರ', 'ಗುಜರಾತ್', 'ಬಂಗಾಳ', 'ಮಹಾರಾಷ್ಟ್ರ'],
                answer=0,
                explanation='ಕಾರ್ಕೋಟ ವಂಶ ಕಾಶ್ಮೀರದಲ್ಲಿ ಆಳ್ವಿಕೆ ನಡೆಸಿತು.',
            ),
            MCQQuestion(
                question='ಗುರ್ಜರ-ಪ್ರತೀಹಾರ ವಂಶದ ಪ್ರಮುಖ ರಾಜ ಯಾರು?',
                options=['ಮಿಹಿರ ಭೋಜ', 'ಮಹಮ್ಮದ್ ಘಜ್ನಿ', 'ರಾಣಾ ಸಾಂಗ', 'ಕೃಷ್ಣ I'],
                answer=0,
                explanation='ಮಿಹಿರ ಭೋಜ ಗುರ್ಜರ-ಪ್ರತೀಹಾರ ವಂಶದ ಅತ್ಯಂತ ಪ್ರಭಾವಶಾಲಿ ರಾಜ.',
            ),
        ],

        descriptive_questions=[
            DescriptiveQuestion(
                question='ರಜಪೂತ ವಂಶಗಳ ಸಾಂಸ್ಕೃತಿಕ ಕೊಡುಗೆಗಳನ್ನು ವಿವರಿಸಿ.',
                answer='ರಜಪೂತರು ವಾಸ್ತುಶಿಲ್ಪ, ಸಾಹಿತ್ಯ ಮತ್ತು ಕಲೆಯಲ್ಲಿ ಮಹತ್ತರ ಕೊಡುಗೆ ನೀಡಿದ್ದಾರೆ. ಖಜುರಾಹೋ ದೇವಾಲಯಗಳು, ಚಿತ್ತೋಡ್‌ಘಡ್ ಕೋಟೆ ಇವರ ವಾಸ್ತುಶಿಲ್ಪ ಕೌಶಲ್ಯಕ್ಕೆ ಸಾಕ್ಷಿ. ಅವರ ಕಾಲದಲ್ಲಿ ಹಿಂದಿ ಸಾಹಿತ್ಯ ಬೆಳೆಯಿತು.',
            ),
            DescriptiveQuestion(
                question='ಪಾಲ ವಂಶದ ಬೌದ್ಧ ಧರ್ಮದ ಕೊಡುಗೆಗಳನ್ನು ವಿವರಿಸಿ.',
                answer='ಪಾಲ ರಾಜರು ಬೌದ್ಧ ಧರ್ಮದ ಪ್ರಬಲ ಪೋಷಕರಾಗಿದ್ದರು. ನಳಂದ ಮತ್ತು ವಿಕ್ರಮಶಿಲಾ ವಿಶ್ವವಿದ್ಯಾಲಯಗಳನ್ನು ಅಭಿವೃದ್ಧಿಪಡಿಸಿದರು. ಬೌದ್ಧ ಕಲೆ ಮತ್ತು ಶಿಲ್ಪಕಲೆ ಈ ಕಾಲದಲ್ಲಿ ಅತ್ಯಂತ ಉತ್ಕರ್ಷಕ್ಕೆ ತಲುಪಿತು.',
            ),
        ],

        audio_url='',
        full_video_url=video_url('session_01', 'session_01_full.mp4'),
        full_video_duration='',
        module_videos=[
            ModuleVideo(title='01 — ಕಾರ್ಕೋಟ ವಂಶ: ಇತಿಹಾಸ, ಆಳ್ವಿಕೆ ಮತ್ತು ಕೊಡುಗೆಗಳು',       video_url=video_url('session_01', 'sections/01.mp4'),          duration=''),
            ModuleVideo(title='02 — ರಜಪೂತರು: ಒಂದು ಪರಿಚಯ',                              video_url=video_url('session_01', 'sections/02.mp4'),          duration=''),
            ModuleVideo(title='03 — ಗುರ್ಜರ-ಪ್ರತೀಹಾರ ವಂಶ',                              video_url=video_url('session_01', 'sections/03_-.mp4'),        duration=''),
            ModuleVideo(title='04 — ಪಾರಮಾರರು',                                          video_url=video_url('session_01', 'sections/04.mp4'),          duration=''),
            ModuleVideo(title='05 — ಚಂದೇಲರು',                                           video_url=video_url('session_01', 'sections/05.mp4'),          duration=''),
            ModuleVideo(title='06 — ಚೌಹಾಣ ವಂಶ ಮತ್ತು ಪೃಥ್ವಿರಾಜ ಚೌಹಾಣ',                  video_url=video_url('session_01', 'sections/06.mp4'),          duration=''),
            ModuleVideo(title='07 — ಸೋಲಂಕಿಯರು',                                         video_url=video_url('session_01', 'sections/07.mp4'),          duration=''),
            ModuleVideo(title='08 — ಗಹಡ್ವಾಲರು',                                         video_url=video_url('session_01', 'sections/08.mp4'),          duration=''),
            ModuleVideo(title='09 — ಗುಹಿಲರು',                                           video_url=video_url('session_01', 'sections/09.mp4'),          duration=''),
            ModuleVideo(title='10 — ಆರ್ಥಿಕ ಮತ್ತು ಸಾಮಾಜಿಕ ಸ್ಥಿತಿ',                      video_url=video_url('session_01', 'sections/10.mp4'),          duration=''),
            ModuleVideo(title='11 — ರಜಪೂತರ ಕಲೆ, ವಾಸ್ತುಶಿಲ್ಪ ಮತ್ತು ಸಾಹಿತ್ಯಿಕ ಕೊಡುಗೆಗಳು', video_url=video_url('session_01', 'sections/11.mp4'),          duration=''),
            ModuleVideo(title='12 — ರಜಪೂತರ ಗುಣಧರ್ಮಗಳು',                                video_url=video_url('session_01', 'sections/12.mp4'),          duration=''),
            ModuleVideo(title='13 — ಪಾಲರು',                                             video_url=video_url('session_01', 'sections/13.mp4'),          duration=''),
        ],
        live_classes=[
            ExamLiveClass(
                title='Social Studies Session 1 — Live Doubt Clearing',
                description='Interactive session to clear doubts on North Indian dynasties (6th–14th century).',
                date='2026-04-15', time='7:00 PM IST', join_url='',
            ),
        ],
    ),

    Session(
        title='ಅರಬ್ಬರು ಮತ್ತು ಟರ್ಕರ ದಾಳಿ',
        locked=False,
        notes_locked=False, mcq_locked=False, descriptive_locked=False,
        audio_locked=False, video_locked=False, live_locked=False,

        notes_html="""
<h2>Session 2 — ಅರಬ್ಬರು ಮತ್ತು ಟರ್ಕರ ದಾಳಿ</h2>
<p>This session covers the Arab and Turkic invasions of India.</p>
<ul>
  <li><strong>ವಿದೇಶಿ ಆಕ್ರಮಣಗಳು:</strong> Overview of foreign invasions</li>
  <li><strong>ಅರಬ್ಬರ ದಾಳಿ:</strong> Muhammad bin Qasim and conquest of Sindh</li>
  <li><strong>ಟರ್ಕರ ದಾಳಿಗಳು:</strong> Mahmud of Ghazni and Muhammad Ghori</li>
</ul>
""".strip(),
        notes_pdf_url='',

        mcqs=[
            MCQQuestion(
                question='ಮಹಮ್ಮದ್ ಬಿನ್ ಕಾಸಿಂ ಭಾರತದಲ್ಲಿ ಯಾವ ಪ್ರದೇಶವನ್ನು ವಶಪಡಿಸಿಕೊಂಡ?',
                options=['ಪಂಜಾಬ್', 'ಸಿಂಧ್', 'ರಾಜಸ್ಥಾನ', 'ಗುಜರಾತ್'],
                answer=1,
                explanation='ಮಹಮ್ಮದ್ ಬಿನ್ ಕಾಸಿಂ 712 ರಲ್ಲಿ ಸಿಂಧ್ ಅನ್ನು ವಶಪಡಿಸಿಕೊಂಡ.',
            ),
            MCQQuestion(
                question='ಮಹಮ್ಮದ್ ಘಜ್ನಿ ಸೋಮನಾಥ ದೇವಾಲಯವನ್ನು ಎಷ್ಟನೇ ಬಾರಿ ದಾಳಿ ಮಾಡಿದ?',
                options=['5ನೇ', '11ನೇ', '17ನೇ', '3ನೇ'],
                answer=2,
                explanation='ಮಹಮ್ಮದ್ ಘಜ್ನಿ 1025 ರಲ್ಲಿ 17ನೇ ದಾಳಿಯಲ್ಲಿ ಸೋಮನಾಥ ದೇವಾಲಯವನ್ನು ಲೂಟಿ ಮಾಡಿದ.',
            ),
            MCQQuestion(
                question='ತರಾಯಿನ್ ಎರಡನೇ ಯುದ್ಧ (1192) ಯಾರ ನಡುವೆ ನಡೆಯಿತು?',
                options=['ಮಹಮ್ಮದ್ ಘೋರಿ ಮತ್ತು ಪೃಥ್ವಿರಾಜ ಚೌಹಾಣ', 'ಬಾಬರ್ ಮತ್ತು ಇಬ್ರಾಹಿಂ ಲೋಧಿ', 'ಅಕ್ಬರ್ ಮತ್ತು ರಾಣಾ ಪ್ರತಾಪ', 'ಘಜ್ನಿ ಮತ್ತು ಜಯಪಾಲ'],
                answer=0,
                explanation='1192 ರಲ್ಲಿ ತರಾಯಿನ್ ಎರಡನೇ ಯುದ್ಧದಲ್ಲಿ ಮಹಮ್ಮದ್ ಘೋರಿ ಪೃಥ್ವಿರಾಜ ಚೌಹಾಣನನ್ನು ಸೋಲಿಸಿದ.',
            ),
            MCQQuestion(
                question='ಅರಬ್ಬರ ದಾಳಿ ಭಾರತದ ಮೇಲೆ ಯಾವ ಶತಮಾನದಲ್ಲಿ ನಡೆಯಿತು?',
                options=['5ನೇ', '6ನೇ', '8ನೇ', '10ನೇ'],
                answer=2,
                explanation='ಅರಬ್ಬರ ದಾಳಿ 8ನೇ ಶತಮಾನದಲ್ಲಿ (712 AD) ನಡೆಯಿತು.',
            ),
            MCQQuestion(
                question='ಮಹಮ್ಮದ್ ಘಜ್ನಿ ಭಾರತದ ಮೇಲೆ ಒಟ್ಟು ಎಷ್ಟು ದಾಳಿ ನಡೆಸಿದ?',
                options=['10', '15', '17', '20'],
                answer=2,
                explanation='ಮಹಮ್ಮದ್ ಘಜ್ನಿ 1000 ರಿಂದ 1027 ರ ನಡುವೆ ಭಾರತದ ಮೇಲೆ 17 ದಾಳಿ ನಡೆಸಿದ.',
            ),
        ],

        descriptive_questions=[
            DescriptiveQuestion(
                question='ಮಹಮ್ಮದ್ ಘಜ್ನಿ ಮತ್ತು ಮಹಮ್ಮದ್ ಘೋರಿಯ ದಾಳಿಗಳ ನಡುವಿನ ವ್ಯತ್ಯಾಸಗಳನ್ನು ವಿವರಿಸಿ.',
                answer='ಮಹಮ್ಮದ್ ಘಜ್ನಿ ಲೂಟಿಯ ಉದ್ದೇಶದಿಂದ ದಾಳಿ ನಡೆಸಿದ ಮತ್ತು ವಾಪಸ್ ಹೋಗುತ್ತಿದ್ದ. ಮಹಮ್ಮದ್ ಘೋರಿ ಭಾರತದಲ್ಲಿ ಸ್ಥಾಯಿ ಸಾಮ್ರಾಜ್ಯ ಸ್ಥಾಪಿಸಲು ಬಂದ ಮತ್ತು ದೆಹಲಿ ಸುಲ್ತಾನಶಾಹಿಗೆ ಅಡಿಪಾಯ ಹಾಕಿದ.',
            ),
        ],

        audio_url='',
        full_video_url=video_url('session_02', 'session_02_full.mp4'),
        full_video_duration='',
        module_videos=[
            ModuleVideo(title='01 — ವಿದೇಶಿ ಆಕ್ರಮಣಗಳು',                                       video_url=video_url('session_02', 'sections/01.mp4'), duration=''),
            ModuleVideo(title='02 — ಅರಬ್ಬರ ದಾಳಿ',                                             video_url=video_url('session_02', 'sections/02.mp4'), duration=''),
            ModuleVideo(title='03 — ಟರ್ಕರ ದಾಳಿಗಳು: ಮಹಮ್ಮದ್ ಘಜ್ನಿ ಮತ್ತು ಮಹಮ್ಮದ್ ಘೋರಿ',          video_url=video_url('session_02', 'sections/03.mp4'), duration=''),
        ],
        live_classes=[
            ExamLiveClass(
                title='Social Studies Session 2 — Live Doubt Clearing',
                description='Doubt clearing on Arab and Turkic invasions of India.',
                date='2026-04-22', time='7:00 PM IST', join_url='',
            ),
        ],
    ),

    Session(
        title='ದೆಹಲಿ ಸುಲ್ತಾನರು',
        locked=False,
        notes_locked=False, mcq_locked=False, descriptive_locked=False,
        audio_locked=False, video_locked=False, live_locked=False,

        notes_html="""
<h2>Session 3 — ದೆಹಲಿ ಸುಲ್ತಾನರು</h2>
<ul>
  <li><strong>ಗುಲಾಮಿ ಸಂತತಿ (1206–1290):</strong> ಸ್ಥಾಪನೆ ಮತ್ತು ಪ್ರಮುಖ ಸುಲ್ತಾನರು</li>
  <li><strong>ಖಿಲ್ಜಿ ಸಂತತಿ (1290–1320):</strong> ಅಲ್ಲಾವುದ್ದೀನ್ ಖಿಲ್ಜಿಯ ಸುಧಾರಣೆಗಳು</li>
  <li><strong>ತುಘಲಕ್ ಸಂತತಿ (1320–1399):</strong> ಮಹಮ್ಮದ್ ಬಿನ್ ತುಘಲಕ್‌ನ ಪ್ರಯೋಗಗಳು</li>
  <li><strong>ಸಯ್ಯದ್ ಮತ್ತು ಲೋಧಿ ಸಂತತಿಗಳು (1414–1526)</strong></li>
  <li><strong>ದೆಹಲಿ ಸುಲ್ತಾನರ ಕೊಡುಗೆಗಳು</strong></li>
</ul>
""".strip(),
        notes_pdf_url='',

        mcqs=[
            MCQQuestion(
                question='ದೆಹಲಿ ಸುಲ್ತಾನಶಾಹಿಯ ಸ್ಥಾಪಕ ಯಾರು?',
                options=['ಮಹಮ್ಮದ್ ಘೋರಿ', 'ಕುತುಬ್ ಉದ್-ದೀನ್ ಐಬಕ್', 'ಇಲ್ಟುಟ್ಮಿಶ್', 'ರಜಿಯಾ ಸುಲ್ತಾನ'],
                answer=1,
                explanation='ಕುತುಬ್ ಉದ್-ದೀನ್ ಐಬಕ್ 1206 ರಲ್ಲಿ ದೆಹಲಿ ಸುಲ್ತಾನಶಾಹಿ ಸ್ಥಾಪಿಸಿದ.',
            ),
            MCQQuestion(
                question='ಅಲ್ಲಾವುದ್ದೀನ್ ಖಿಲ್ಜಿ ಯಾವ ಮಾರುಕಟ್ಟೆ ಸುಧಾರಣೆ ಜಾರಿಗೆ ತಂದ?',
                options=['ಮುಕ್ತ ವ್ಯಾಪಾರ', 'ಬೆಲೆ ನಿಯಂತ್ರಣ ವ್ಯವಸ್ಥೆ', 'ಸಂಪೂರ್ಣ ರಾಷ್ಟ್ರೀಕರಣ', 'ತೆರಿಗೆ ರಹಿತ ವ್ಯಾಪಾರ'],
                answer=1,
                explanation='ಅಲ್ಲಾವುದ್ದೀನ್ ಖಿಲ್ಜಿ ದ್ರವ್ಯ ಮತ್ತು ಸರಕುಗಳ ಬೆಲೆ ನಿಯಂತ್ರಿಸಲು ಮಾರುಕಟ್ಟೆ ಸುಧಾರಣೆ ಜಾರಿಗೊಳಿಸಿದ.',
            ),
            MCQQuestion(
                question='ಮಹಮ್ಮದ್ ಬಿನ್ ತುಘಲಕ್ ರಾಜಧಾನಿಯನ್ನು ಎಲ್ಲಿಂದ ಎಲ್ಲಿಗೆ ಸ್ಥಳಾಂತರಿಸಿದ?',
                options=['ಆಗ್ರಾದಿಂದ ದೆಹಲಿಗೆ', 'ದೆಹಲಿಯಿಂದ ದೌಲತಾಬಾದ್‌ಗೆ', 'ಲಾಹೋರ್‌ನಿಂದ ದೆಹಲಿಗೆ', 'ದೆಹಲಿಯಿಂದ ಆಗ್ರಾಗೆ'],
                answer=1,
                explanation='ಮಹಮ್ಮದ್ ಬಿನ್ ತುಘಲಕ್ ರಾಜಧಾನಿಯನ್ನು ದೆಹಲಿಯಿಂದ ದೌಲತಾಬಾದ್‌ಗೆ ಸ್ಥಳಾಂತರಿಸಿದ.',
            ),
            MCQQuestion(
                question='ದೆಹಲಿ ಸುಲ್ತಾನಶಾಹಿಯ ಏಕೈಕ ಮಹಿಳಾ ಸುಲ್ತಾನ ಯಾರು?',
                options=['ನೂರ್ ಜಹಾನ್', 'ರಜಿಯಾ ಸುಲ್ತಾನ', 'ಚಾಂದ್ ಬೀಬಿ', 'ಮುಮ್ತಾಜ್ ಮಹಲ್'],
                answer=1,
                explanation='ರಜಿಯಾ ಸುಲ್ತಾನ ದೆಹಲಿ ಸುಲ್ತಾನಶಾಹಿಯ ಏಕೈಕ ಮಹಿಳಾ ಸುಲ್ತಾನ (1236–1240).',
            ),
            MCQQuestion(
                question='ಕುತುಬ್ ಮಿನಾರ್ ಅನ್ನು ಯಾರು ನಿರ್ಮಿಸಿದರು?',
                options=['ಅಕ್ಬರ್', 'ಕುತುಬ್ ಉದ್-ದೀನ್ ಐಬಕ್ ಮತ್ತು ಇಲ್ಟುಟ್ಮಿಶ್', 'ಮಹಮ್ಮದ್ ಘೋರಿ', 'ಔರಂಗಜೇಬ್'],
                answer=1,
                explanation='ಕುತುಬ್ ಮಿನಾರ್ ನಿರ್ಮಾಣ ಕುತುಬ್ ಉದ್-ದೀನ್ ಐಬಕ್ ಆರಂಭಿಸಿ, ಇಲ್ಟುಟ್ಮಿಶ್ ಪೂರ್ಣಗೊಳಿಸಿದ.',
            ),
        ],

        descriptive_questions=[
            DescriptiveQuestion(
                question='ಅಲ್ಲಾವುದ್ದೀನ್ ಖಿಲ್ಜಿಯ ಆಡಳಿತ ಸುಧಾರಣೆಗಳನ್ನು ವಿವರಿಸಿ.',
                answer='ಅಲ್ಲಾವುದ್ದೀನ್ ಖಿಲ್ಜಿ ಬೆಲೆ ನಿಯಂತ್ರಣ, ಭೂ ಕಂದಾಯ ಸುಧಾರಣೆ, ಬಲಿಷ್ಠ ಸೈನ್ಯ ನಿರ್ಮಾಣ ಮತ್ತು ದಿವಾನ್-ಇ-ರಿಯಾಸತ್ ಸ್ಥಾಪಿಸಿದ. ಘೋಡಾ ಮತ್ತು ಸೈನಿಕರ ವಿವರಗಳ ನೋಂದಣಿ ಮೂಲಕ ಭ್ರಷ್ಟಾಚಾರ ತಡೆದ.',
            ),
        ],

        audio_url='',
        full_video_url=video_url('session_03', 'session_03_full.mp4'),
        full_video_duration='',
        module_videos=[
            ModuleVideo(title='01 — ಗುಲಾಮಿ ಸಂತತಿ: ಸ್ಥಾಪನೆ ಮತ್ತು ಪ್ರಮುಖ ಸುಲ್ತಾನರು (1206–1290)',             video_url=video_url('session_03', 'sections/01_1206-1290.mp4'),  duration=''),
            ModuleVideo(title='02 — ಖಿಲ್ಜಿ ಸಂತತಿ: ಅಲ್ಲಾವುದ್ದೀನ್ ಖಿಲ್ಜಿಯ ಆಳ್ವಿಕೆ ಮತ್ತು ಸುಧಾರಣೆಗಳು (1290–1320)', video_url=video_url('session_03', 'sections/02_1290-1320.mp4'),  duration=''),
            ModuleVideo(title='03 — ತುಘಲಕ್ ಸಂತತಿ ಮತ್ತು ಮಹಮ್ಮದ್ ಬಿನ್ ತುಘಲಕ್‌ನ ಪ್ರಯೋಗಗಳು (1320–1399)',         video_url=video_url('session_03', 'sections/03_1320-1399.mp4'),  duration=''),
            ModuleVideo(title='04 — ಸಯ್ಯದ್ ಮತ್ತು ಲೋಧಿ ಸಂತತಿಗಳು (1414–1526)',                               video_url=video_url('session_03', 'sections/04_1414-1526.mp4'),  duration=''),
            ModuleVideo(title='05 — ದೆಹಲಿ ಸುಲ್ತಾನರ ಕೊಡುಗೆಗಳು: ಆಡಳಿತ, ಸಮಾಜ ಮತ್ತು ಸಂಸ್ಕೃತಿ',                 video_url=video_url('session_03', 'sections/05.mp4'),           duration=''),
            ModuleVideo(title='06 — ಕಾಲಗಣನೆ',                                                               video_url=video_url('session_03', 'sections/06_._..mp4'),        duration=''),
        ],
        live_classes=[
            ExamLiveClass(
                title='Social Studies Session 3 — Live Doubt Clearing',
                description='Doubt clearing on Delhi Sultanate dynasties and reforms.',
                date='2026-04-29', time='7:00 PM IST', join_url='',
            ),
        ],
    ),

    Session(
        title='ಪಾಶ್ಚಾತ್ಯ ಧರ್ಮಗಳು',
        locked=False,
        notes_locked=False, mcq_locked=False, descriptive_locked=False,
        audio_locked=False, video_locked=False, live_locked=False,

        notes_html="""
<h2>Session 4 — ಪಾಶ್ಚಾತ್ಯ ಧರ್ಮಗಳು</h2>
<ul>
  <li><strong>ಯಹೂದಿ ಧರ್ಮ:</strong> ಇತಿಹಾಸ, ಪವಿತ್ರ ಗ್ರಂಥ ಮತ್ತು ಕಟ್ಟಳೆಗಳು</li>
  <li><strong>ಪಾರ್ಸಿ ಧರ್ಮ (ಜೊರಾಷ್ಟ್ರಿಯನ್ ಧರ್ಮ)</strong></li>
  <li><strong>ಕ್ರೈಸ್ತ ಧರ್ಮ:</strong> ಯೇಸು ಕ್ರಿಸ್ತ, ಬೋಧನೆಗಳು ಮತ್ತು ಪಂಗಡಗಳು</li>
  <li><strong>ಇಸ್ಲಾಂ ಧರ್ಮ:</strong> ಉಗಮ, ಕುರಾನ್, ಖಲೀಫರು ಮತ್ತು ಪಂಗಡಗಳು</li>
</ul>
""".strip(),
        notes_pdf_url='',

        mcqs=[
            MCQQuestion(
                question='ಇಸ್ಲಾಂ ಧರ್ಮದ ಪವಿತ್ರ ಗ್ರಂಥ ಯಾವುದು?',
                options=['ಬೈಬಲ್', 'ತೋರಾ', 'ಕುರಾನ್', 'ಅವೆಸ್ತಾ'],
                answer=2,
                explanation='ಕುರಾನ್ ಇಸ್ಲಾಂ ಧರ್ಮದ ಪವಿತ್ರ ಗ್ರಂಥ.',
            ),
            MCQQuestion(
                question='ಪ್ರವಾದಿ ಮೊಹಮ್ಮದ್ ಅವರ ಮಕ್ಕಾದಿಂದ ಮದೀನಾಗೆ ವಲಸೆಯನ್ನು ಏನೆಂದು ಕರೆಯುತ್ತಾರೆ?',
                options=['ಜಿಹಾದ್', 'ಹಿಜಿರಾ', 'ರಮಝಾನ್', 'ಹಜ್'],
                answer=1,
                explanation='ಹಿಜಿರಾ (622 AD) ಇಸ್ಲಾಂ ಕ್ಯಾಲೆಂಡರ್‌ನ ಆರಂಭಬಿಂದು.',
            ),
            MCQQuestion(
                question='ಯಹೂದಿ ಧರ್ಮದ ಪವಿತ್ರ ಗ್ರಂಥ ಯಾವುದು?',
                options=['ಕುರಾನ್', 'ಬೈಬಲ್', 'ತೋರಾ', 'ಅವೆಸ್ತಾ'],
                answer=2,
                explanation='ತೋರಾ ಯಹೂದಿ ಧರ್ಮದ ಪ್ರಮುಖ ಪವಿತ್ರ ಗ್ರಂಥ.',
            ),
            MCQQuestion(
                question='ಜೊರಾಷ್ಟ್ರಿಯನ್ ಧರ್ಮದ ಪ್ರವಾದಿ ಯಾರು?',
                options=['ಮೊಹಮ್ಮದ್', 'ಯೇಸು', 'ಜರಥ್ರುಷ್ಟ್ರ', 'ಅಬ್ರಹಾಂ'],
                answer=2,
                explanation='ಜರಥ್ರುಷ್ಟ್ರ (Zoroaster) ಪಾರ್ಸಿ ಧರ್ಮದ ಸ್ಥಾಪಕ ಪ್ರವಾದಿ.',
            ),
            MCQQuestion(
                question='ಇಸ್ಲಾಂ ಧರ್ಮದ ಎರಡು ಪ್ರಮುಖ ಪಂಗಡಗಳು ಯಾವವು?',
                options=['ಕ್ಯಾಥೊಲಿಕ್ ಮತ್ತು ಪ್ರೊಟೆಸ್ಟಂಟ್', 'ಸುನ್ನಿ ಮತ್ತು ಶಿಯಾ', 'ಸೂಫಿ ಮತ್ತು ವಹಾಬಿ', 'ಶಾಫಿ ಮತ್ತು ಹನಾಫಿ'],
                answer=1,
                explanation='ಸುನ್ನಿ ಮತ್ತು ಶಿಯಾ ಇಸ್ಲಾಂ ಧರ್ಮದ ಎರಡು ಪ್ರಮುಖ ಪಂಗಡಗಳು.',
            ),
        ],

        descriptive_questions=[
            DescriptiveQuestion(
                question='ಇಸ್ಲಾಂ ಧರ್ಮದ ಐದು ಸ್ತಂಭಗಳನ್ನು ವಿವರಿಸಿ.',
                answer='ಇಸ್ಲಾಂ ಧರ್ಮದ ಐದು ಸ್ತಂಭಗಳು: 1. ಶಹಾದಾ (ಏಕದೇವ ನಂಬಿಕೆ), 2. ಸಲಾತ್ (ದಿನಕ್ಕೆ 5 ಬಾರಿ ನಮಾಜ್), 3. ಝಕಾತ್ (ದಾನ), 4. ಸಾಮ್ (ರಮಝಾನ್ ಉಪವಾಸ), 5. ಹಜ್ (ಮಕ್ಕಾ ಯಾತ್ರೆ).',
            ),
        ],

        audio_url='',
        full_video_url=video_url('session_04', 'session_04_full.mp4'),
        full_video_duration='',
        module_videos=[
            ModuleVideo(title='01 — ಪಾಶ್ಚಾತ್ಯ ಧರ್ಮಗಳು: ಒಂದು ಪರಿಚಯ',                         video_url=video_url('session_04', 'sections/01.mp4'), duration=''),
            ModuleVideo(title='02 — ಯಹೂದಿ ಧರ್ಮ (ಜುಡಾಯಿಸಂ)',                                video_url=video_url('session_04', 'sections/02.mp4'), duration=''),
            ModuleVideo(title='03 — ಯಹೂದ್ಯರ ಇತಿಹಾಸ',                                       video_url=video_url('session_04', 'sections/03.mp4'), duration=''),
            ModuleVideo(title='04 — ಯಹೂದಿ ಪವಿತ್ರ ಗ್ರಂಥ ಮತ್ತು ಕಟ್ಟಳೆಗಳು',                     video_url=video_url('session_04', 'sections/04.mp4'), duration=''),
            ModuleVideo(title='05 — ಪಾರ್ಸಿ ಧರ್ಮ (ಜೊರಾಷ್ಟ್ರಿಯನ್ ಧರ್ಮ)',                       video_url=video_url('session_04', 'sections/05.mp4'), duration=''),
            ModuleVideo(title='06 — ಕ್ರೈಸ್ತ ಧರ್ಮ: ಯೇಸು ಕ್ರಿಸ್ತರ ಜನನ ಮತ್ತು ದೀಕ್ಷೆ',             video_url=video_url('session_04', 'sections/06.mp4'), duration=''),
            ModuleVideo(title='07 — ಯೇಸುವಿನ ಸೇವೆ ಮತ್ತು ಶಿಲುಬೆಗೇರಿಸುವಿಕೆ',                    video_url=video_url('session_04', 'sections/07.mp4'), duration=''),
            ModuleVideo(title='08 — ಯೇಸು ಕ್ರಿಸ್ತರ ಬೋಧನೆಗಳು',                               video_url=video_url('session_04', 'sections/08.mp4'), duration=''),
            ModuleVideo(title='09 — ಕ್ರೈಸ್ತ ಧರ್ಮದ ಪ್ರಚಾರ ಮತ್ತು ಪಂಗಡಗಳು',                     video_url=video_url('session_04', 'sections/09.mp4'), duration=''),
            ModuleVideo(title='10 — ಇಸ್ಲಾಂ ಧರ್ಮ: ಉಗಮ ಮತ್ತು ಪ್ರವಾದಿ ಮೊಹಮ್ಮದ್',                video_url=video_url('session_04', 'sections/10.mp4'), duration=''),
            ModuleVideo(title='11 — ಪ್ರವಾದಿ ಮೊಹಮ್ಮದ್: ದೈವಿಕ ಸಂದೇಶ ಮತ್ತು ಕುರಾನ್',             video_url=video_url('session_04', 'sections/11.mp4'), duration=''),
            ModuleVideo(title='12 — ಹಿಜಿರಾ ಮತ್ತು ಇಸ್ಲಾಂ ಧರ್ಮದ ಪ್ರಚಾರ',                       video_url=video_url('session_04', 'sections/12.mp4'), duration=''),
            ModuleVideo(title='13 — ಇಸ್ಲಾಂ ಧರ್ಮದ ಬೋಧನೆಗಳು ಮತ್ತು ಆಚರಣೆಗಳು',                  video_url=video_url('session_04', 'sections/13.mp4'), duration=''),
            ModuleVideo(title='14 — ಖಲೀಫರು ಮತ್ತು ಇಸ್ಲಾಂ ಧರ್ಮದ ಪಂಗಡಗಳು',                     video_url=video_url('session_04', 'sections/14.mp4'), duration=''),
        ],
        live_classes=[
            ExamLiveClass(
                title='Social Studies Session 4 — Live Doubt Clearing',
                description='Doubt clearing on Western religions — Judaism, Christianity, Islam.',
                date='2026-05-06', time='7:00 PM IST', join_url='',
            ),
        ],
    ),

    Session(
        title='ಭಕ್ತಿ ಚಳುವಳಿ',
        locked=False,
        notes_locked=False, mcq_locked=False, descriptive_locked=False,
        audio_locked=False, video_locked=False, live_locked=False,

        notes_html="""
<h2>Session 5 — ಭಕ್ತಿ ಚಳುವಳಿ</h2>
<ul>
  <li><strong>ಉಗಮ ಮತ್ತು ಸಾರ:</strong> ಭಕ್ತಿ ಚಳುವಳಿಯ ಹಿನ್ನೆಲೆ</li>
  <li><strong>ಶಂಕರಾಚಾರ್ಯರು:</strong> ಅದ್ವೈತ ಸಿದ್ಧಾಂತ</li>
  <li><strong>ರಾಮಾನುಜಾಚಾರ್ಯರು:</strong> ವಿಶಿಷ್ಟಾದ್ವೈತ ಸಿದ್ಧಾಂತ</li>
  <li><strong>ಮಧ್ವಾಚಾರ್ಯರು:</strong> ದ್ವೈತ ಸಿದ್ಧಾಂತ</li>
  <li><strong>ಕರ್ನಾಟಕ:</strong> ಬಸವಣ್ಣ, ದಾಸರು ಮತ್ತು ಶರೀಫರು</li>
  <li><strong>ಗುರುನಾನಕ್ ಮತ್ತು ಸಿಖ್ ಧರ್ಮ, ಸೂಫಿ ಪಂಥ</strong></li>
</ul>
""".strip(),
        notes_pdf_url='',

        mcqs=[
            MCQQuestion(
                question='ಅದ್ವೈತ ತತ್ವಶಾಸ್ತ್ರದ ಪ್ರತಿಪಾದಕರು ಯಾರು?',
                options=['ರಾಮಾನುಜಾಚಾರ್ಯರು', 'ಮಧ್ವಾಚಾರ್ಯರು', 'ಶಂಕರಾಚಾರ್ಯರು', 'ಬಸವಣ್ಣ'],
                answer=2,
                explanation='ಶಂಕರಾಚಾರ್ಯರು ಅದ್ವೈತ ತತ್ವಶಾಸ್ತ್ರ ಪ್ರತಿಪಾದಿಸಿದರು — ಬ್ರಹ್ಮ ಮಾತ್ರ ಸತ್ಯ, ಜಗತ್ತು ಮಿಥ್ಯ.',
            ),
            MCQQuestion(
                question='ಕರ್ನಾಟಕದ ಯಾವ ಸಂತ ವಚನ ಚಳುವಳಿ ಆರಂಭಿಸಿದರು?',
                options=['ಪುರಂದರದಾಸರು', 'ಕನಕದಾಸರು', 'ಬಸವಣ್ಣ', 'ಅಕ್ಕಮಹಾದೇವಿ'],
                answer=2,
                explanation='ಬಸವಣ್ಣ 12ನೇ ಶತಮಾನದಲ್ಲಿ ವಚನ ಚಳುವಳಿ ಮತ್ತು ಲಿಂಗಾಯತ ಧರ್ಮ ಸ್ಥಾಪಿಸಿದರು.',
            ),
            MCQQuestion(
                question='ಸಿಖ್ ಧರ್ಮದ ಸ್ಥಾಪಕರು ಯಾರು?',
                options=['ಗುರು ಗೋಬಿಂದ್ ಸಿಂಗ್', 'ಗುರು ನಾನಕ್', 'ಗುರು ತೇಗ್ ಬಹಾದ್ದೂರ್', 'ಗುರು ಅರ್ಜನ್'],
                answer=1,
                explanation='ಗುರು ನಾನಕ್ (1469–1539) ಸಿಖ್ ಧರ್ಮದ ಸ್ಥಾಪಕರು.',
            ),
            MCQQuestion(
                question='ದ್ವೈತ ತತ್ವಶಾಸ್ತ್ರ ಪ್ರತಿಪಾದಿಸಿದ ಕರ್ನಾಟಕದ ತತ್ವಜ್ಞಾನಿ ಯಾರು?',
                options=['ಶಂಕರಾಚಾರ್ಯರು', 'ರಾಮಾನುಜಾಚಾರ್ಯರು', 'ಮಧ್ವಾಚಾರ್ಯರು', 'ಬಸವಣ್ಣ'],
                answer=2,
                explanation='ಮಧ್ವಾಚಾರ್ಯರು (1238–1317) ದ್ವೈತ ತತ್ವಶಾಸ್ತ್ರ ಪ್ರತಿಪಾದಿಸಿದರು.',
            ),
            MCQQuestion(
                question='ಸೂಫಿ ಪಂಥ ಯಾವ ಧರ್ಮಕ್ಕೆ ಸಂಬಂಧಿಸಿದೆ?',
                options=['ಹಿಂದೂ ಧರ್ಮ', 'ಬೌದ್ಧ ಧರ್ಮ', 'ಇಸ್ಲಾಂ ಧರ್ಮ', 'ಜೈನ ಧರ್ಮ'],
                answer=2,
                explanation='ಸೂಫಿ ಪಂಥ ಇಸ್ಲಾಂ ಧರ್ಮದ ಅತೀಂದ್ರಿಯ (mystical) ಶಾಖೆ.',
            ),
        ],

        descriptive_questions=[
            DescriptiveQuestion(
                question='ಕರ್ನಾಟಕದ ಭಕ್ತಿ ಪರಂಪರೆಯ ಪ್ರಮುಖ ಸಂತರ ಕೊಡುಗೆಗಳನ್ನು ವಿವರಿಸಿ.',
                answer='ಬಸವಣ್ಣ ಜಾತಿ ವ್ಯವಸ್ಥೆ ವಿರುದ್ಧ ಹೋರಾಡಿ ವಚನ ಸಾಹಿತ್ಯ ನೀಡಿದರು. ಪುರಂದರದಾಸರು ಕರ್ನಾಟಕ ಸಂಗೀತದ ಪಿತಾಮಹ ಎನಿಸಿದರು. ಕನಕದಾಸರು ಕೀರ್ತನೆಗಳ ಮೂಲಕ ಸಾಮಾಜಿಕ ಸಮಾನತೆ ಬೋಧಿಸಿದರು. ಶಿಶುನಾಳ ಶರೀಫರು ಹಿಂದೂ-ಮುಸ್ಲಿಂ ಐಕ್ಯತೆ ಸಾರಿದರು.',
            ),
        ],

        audio_url='',
        full_video_url=video_url('session_05', 'session_05_full.mp4'),
        full_video_duration='',
        module_videos=[
            ModuleVideo(title='01 — ಭಕ್ತಿ ಚಳುವಳಿ: ಉಗಮ, ಸಾರ ಮತ್ತು ಬೆಳವಣಿಗೆ',              video_url=video_url('session_05', 'sections/01.mp4'), duration=''),
            ModuleVideo(title='02 — ಶಂಕರಾಚಾರ್ಯರು ಮತ್ತು ಅದ್ವೈತ ಸಿದ್ಧಾಂತ',                video_url=video_url('session_05', 'sections/02.mp4'), duration=''),
            ModuleVideo(title='03 — ರಾಮಾನುಜಾಚಾರ್ಯರು ಮತ್ತು ವಿಶಿಷ್ಟಾದ್ವೈತ ಸಿದ್ಧಾಂತ',        video_url=video_url('session_05', 'sections/03.mp4'), duration=''),
            ModuleVideo(title='04 — ಮಧ್ವಾಚಾರ್ಯರು ಮತ್ತು ದ್ವೈತ ಸಿದ್ಧಾಂತ',                 video_url=video_url('session_05', 'sections/04.mp4'), duration=''),
            ModuleVideo(title='05 — ಕರ್ನಾಟಕದ ಭಕ್ತಿ ಪರಂಪರೆ: ಬಸವಣ್ಣ, ದಾಸರು ಮತ್ತು ಶರೀಫರು', video_url=video_url('session_05', 'sections/05.mp4'), duration=''),
            ModuleVideo(title='06 — ಉತ್ತರ ಭಾರತದ ಪ್ರಮುಖ ಭಕ್ತಿ ಸಂತರು',                    video_url=video_url('session_05', 'sections/06.mp4'), duration=''),
            ModuleVideo(title='07 — ಗುರುನಾನಕ್ ಮತ್ತು ಸಿಖ್ ಧರ್ಮ',                        video_url=video_url('session_05', 'sections/07.mp4'), duration=''),
            ModuleVideo(title='08 — ಪೂರ್ವ ಮತ್ತು ಪಶ್ಚಿಮ ಭಾರತದ ಸಂತರು',                   video_url=video_url('session_05', 'sections/08.mp4'), duration=''),
            ModuleVideo(title='09 — ಸೂಫಿ ಪಂಥ: ತತ್ವಗಳು ಮತ್ತು ಪ್ರಮುಖ ಸಂತರು',             video_url=video_url('session_05', 'sections/09.mp4'), duration=''),
            ModuleVideo(title='10 — ಭಕ್ತಿ ಚಳವಳಿಯ ಪರಿಣಾಮಗಳು',                           video_url=video_url('session_05', 'sections/10.mp4'), duration=''),
        ],
        live_classes=[
            ExamLiveClass(
                title='Social Studies Session 5 — Live Doubt Clearing',
                description='Doubt clearing on Bhakti Movement — saints, philosophies and impact.',
                date='2026-05-13', time='7:00 PM IST', join_url='',
            ),
        ],
    ),

    Session(
        title='ಮೊಘಲರು',
        locked=False,
        notes_locked=False, mcq_locked=False, descriptive_locked=False,
        audio_locked=False, video_locked=False, live_locked=False,

        notes_html="""
<h2>Session 6 — ಮೊಘಲರು</h2>
<ul>
  <li><strong>ಬಾಬರ್ ಮತ್ತು ಹುಮಾಯೂನ್:</strong> ಮೊಘಲ್ ಸಾಮ್ರಾಜ್ಯದ ಸ್ಥಾಪನೆ</li>
  <li><strong>ಅಕ್ಬರ್:</strong> ಸಾಮ್ರಾಜ್ಯ ವಿಸ್ತರಣೆ ಮತ್ತು ದೀನ್-ಇ-ಇಲಾಹಿ</li>
  <li><strong>ಜಹಾಂಗೀರ್, ಷಹಜಹಾನ್, ಔರಂಗಜೇಬ್</strong></li>
  <li><strong>ಆಡಳಿತ, ಆರ್ಥಿಕ ವ್ಯವಸ್ಥೆ ಮತ್ತು ಸಾಂಸ್ಕೃತಿಕ ಕೊಡುಗೆಗಳು</strong></li>
  <li><strong>ಮೊಘಲ್ ಸಾಮ್ರಾಜ್ಯದ ಅವನತಿ</strong></li>
</ul>
""".strip(),
        notes_pdf_url='',

        mcqs=[
            MCQQuestion(
                question='ಮೊಘಲ್ ಸಾಮ್ರಾಜ್ಯ ಸ್ಥಾಪನೆಗೆ ಕಾರಣವಾದ ಯುದ್ಧ ಯಾವುದು?',
                options=['ತರಾಯಿನ್ ಯುದ್ಧ', 'ಪಾಣಿಪತ್ ಮೊದಲ ಯುದ್ಧ (1526)', 'ಖಾನ್ವಾ ಯುದ್ಧ', 'ಹಲ್ದಿಘಾಟ್ ಯುದ್ಧ'],
                answer=1,
                explanation='1526 ರ ಪಾಣಿಪತ್ ಮೊದಲ ಯುದ್ಧದಲ್ಲಿ ಬಾಬರ್ ಇಬ್ರಾಹಿಂ ಲೋಧಿಯನ್ನು ಸೋಲಿಸಿ ಮೊಘಲ್ ಸಾಮ್ರಾಜ್ಯ ಸ್ಥಾಪಿಸಿದ.',
            ),
            MCQQuestion(
                question='ತಾಜ್ ಮಹಲ್ ಯಾರು ನಿರ್ಮಿಸಿದರು?',
                options=['ಅಕ್ಬರ್', 'ಜಹಾಂಗೀರ್', 'ಷಹಜಹಾನ್', 'ಔರಂಗಜೇಬ್'],
                answer=2,
                explanation='ಷಹಜಹಾನ್ ತನ್ನ ಪತ್ನಿ ಮುಮ್ತಾಜ್ ಮಹಲ್ ಸ್ಮರಣೆಯಲ್ಲಿ ತಾಜ್ ಮಹಲ್ ನಿರ್ಮಿಸಿದ.',
            ),
            MCQQuestion(
                question='ಅಕ್ಬರ್ ಪ್ರಾರಂಭಿಸಿದ ಧಾರ್ಮಿಕ ಚಳುವಳಿ ಯಾವುದು?',
                options=['ಭಕ್ತಿ ಚಳುವಳಿ', 'ದೀನ್-ಇ-ಇಲಾಹಿ', 'ಸೂಫಿ ಪಂಥ', 'ನಿರ್ಗುಣ ಭಕ್ತಿ'],
                answer=1,
                explanation='ಅಕ್ಬರ್ ದೀನ್-ಇ-ಇಲಾಹಿ ಎಂಬ ಸಾರ್ವತ್ರಿಕ ಧರ್ಮ ಪ್ರಸ್ತಾಪಿಸಿದ.',
            ),
            MCQQuestion(
                question='ಮೊಘಲ್ ಕಾಲದ ಭೂ ಕಂದಾಯ ವ್ಯವಸ್ಥೆ ಯಾವುದು?',
                options=['ರಯ್ಯತ್ವಾರಿ', 'ಜಮೀನ್ದಾರಿ', 'ಜಾಬ್ತಿ ವ್ಯವಸ್ಥೆ', 'ಮಹಲ್ವಾರಿ'],
                answer=2,
                explanation='ಅಕ್ಬರ್ ಕಾಲದಲ್ಲಿ ಟೋಡರ್‌ಮಲ್ ಜಾಬ್ತಿ ವ್ಯವಸ್ಥೆ (ಅಳತೆ ಆಧಾರಿತ ಕಂದಾಯ) ಜಾರಿಗೊಳಿಸಿದ.',
            ),
            MCQQuestion(
                question='ಔರಂಗಜೇಬ್ ಯಾವ ತೆರಿಗೆ ಮರು ಜಾರಿಗೊಳಿಸಿದ?',
                options=['ಝಕಾತ್', 'ಜಿಜಿಯಾ', 'ಖರಾಜ್', 'ಉಶ್ರ್'],
                answer=1,
                explanation='ಔರಂಗಜೇಬ್ ಅಕ್ಬರ್ ರದ್ದುಪಡಿಸಿದ್ದ ಜಿಜಿಯಾ (ಹಿಂದೂ ತೆರಿಗೆ) ಮರು ಜಾರಿಗೊಳಿಸಿದ.',
            ),
        ],

        descriptive_questions=[
            DescriptiveQuestion(
                question='ಅಕ್ಬರ್‌ನ ಧಾರ್ಮಿಕ ನೀತಿ ಮತ್ತು ರಾಷ್ಟ್ರ ನಿರ್ಮಾಣದಲ್ಲಿ ಅದರ ಪಾತ್ರ ವಿವರಿಸಿ.',
                answer='ಅಕ್ಬರ್ ಸಲ್ಹ್-ಇ-ಕುಲ್ (ಸಾರ್ವತ್ರಿಕ ಶಾಂತಿ) ನೀತಿ ಅನುಸರಿಸಿದ. ಜಿಜಿಯಾ ರದ್ದುಪಡಿಸಿದ, ಹಿಂದೂ ರಾಜಕುಮಾರಿಯರನ್ನು ವಿವಾಹವಾದ, ಹಿಂದೂ ಮಂಸಬ್ದಾರರನ್ನು ನೇಮಿಸಿದ. ದೀನ್-ಇ-ಇಲಾಹಿ ಮೂಲಕ ಏಕತೆ ಸಾಧಿಸಲು ಯತ್ನಿಸಿದ.',
            ),
        ],

        audio_url='',
        full_video_url=video_url('session_06', 'session_06_full.mp4'),
        full_video_duration='',
        module_videos=[
            ModuleVideo(title='01 — ಮೊಘಲ್ ಸಾಮ್ರಾಜ್ಯದ ಸ್ಥಾಪನೆ: ಬಾಬರ್ ಮತ್ತು ಹುಮಾಯೂನ್',                    video_url=video_url('session_06', 'sections/01.mp4'), duration=''),
            ModuleVideo(title='02 — ಅಕ್ಬರ್: ಸಾಮ್ರಾಜ್ಯ ವಿಸ್ತರಣೆ, ಆಡಳಿತ ಮತ್ತು ಧಾರ್ಮಿಕ ನೀತಿ',               video_url=video_url('session_06', 'sections/02.mp4'), duration=''),
            ModuleVideo(title='03 — ಜಹಾಂಗೀರ್, ಷಹಜಹಾನ್ ಮತ್ತು ಔರಂಗಜೇಬ್: ಆಳ್ವಿಕೆ ಮತ್ತು ಸಂಘರ್ಷಗಳು',          video_url=video_url('session_06', 'sections/03.mp4'), duration=''),
            ModuleVideo(title='04 — ಮೊಘಲರ ಆಡಳಿತ ಮತ್ತು ಆರ್ಥಿಕ ವ್ಯವಸ್ಥೆ',                                  video_url=video_url('session_06', 'sections/04.mp4'), duration=''),
            ModuleVideo(title='05 — ಮೊಘಲರ ಸಾಂಸ್ಕೃತಿಕ ಕೊಡುಗೆಗಳು: ಸಾಹಿತ್ಯ, ಕಲೆ ಮತ್ತು ವಾಸ್ತುಶಿಲ್ಪ',           video_url=video_url('session_06', 'sections/05.mp4'), duration=''),
            ModuleVideo(title='06 — ಮೊಘಲ್ ಸಾಮ್ರಾಜ್ಯದ ಅವನತಿ',                                             video_url=video_url('session_06', 'sections/06.mp4'), duration=''),
        ],
        live_classes=[
            ExamLiveClass(
                title='Social Studies Session 6 — Live Doubt Clearing',
                description='Doubt clearing on the Mughal Empire — rulers, reforms and decline.',
                date='2026-05-20', time='7:00 PM IST', join_url='',
            ),
        ],
    ),

    Session(
        title='ಶಿವಾಜಿ ಮತ್ತು ಮರಾಠರು',
        locked=False,
        notes_locked=False, mcq_locked=False, descriptive_locked=False,
        audio_locked=False, video_locked=False, live_locked=False,

        notes_html="""
<h2>Session 7 — ಶಿವಾಜಿ ಮತ್ತು ಮರಾಠರು</h2>
<ul>
  <li><strong>ಮರಾಠರ ಉದಯ:</strong> ಶಿವಾಜಿಯ ಆರಂಭಿಕ ಜೀವನ</li>
  <li><strong>ಶಿವಾಜಿಯ ದಿಗ್ವಿಜಯ:</strong> ಮೊಘಲರೊಂದಿಗಿನ ಸಂಘರ್ಷ ಮತ್ತು ಪಟ್ಟಾಭಿಷೇಕ</li>
  <li><strong>ಶಿವಾಜಿಯ ಆಡಳಿತ ಮತ್ತು ಉತ್ತರಾಧಿಕಾರಿಗಳು</strong></li>
  <li><strong>ಪೇಶ್ವೆಗಳ ಆಳ್ವಿಕೆ ಮತ್ತು ಮರಾಠಾ ಸಾಮ್ರಾಜ್ಯ</strong></li>
</ul>
""".strip(),
        notes_pdf_url='',

        mcqs=[
            MCQQuestion(
                question='ಶಿವಾಜಿ ರಾಜ್ಯಾಭಿಷೇಕ ಯಾವ ವರ್ಷ ನಡೆಯಿತು?',
                options=['1664', '1674', '1680', '1659'],
                answer=1,
                explanation='ಶಿವಾಜಿ 1674 ರಲ್ಲಿ ರಾಯಗಡದಲ್ಲಿ ಛತ್ರಪತಿಯಾಗಿ ಪಟ್ಟಾಭಿಷಿಕ್ತನಾದ.',
            ),
            MCQQuestion(
                question='ಶಿವಾಜಿ ಸ್ಥಾಪಿಸಿದ ಆಡಳಿತ ವ್ಯವಸ್ಥೆ ಯಾವುದು?',
                options=['ಜಮೀನ್ದಾರಿ', 'ಅಷ್ಟ ಪ್ರಧಾನ', 'ಮನ್ಸಬ್ದಾರಿ', 'ರಯ್ಯತ್ವಾರಿ'],
                answer=1,
                explanation='ಶಿವಾಜಿ ಅಷ್ಟ ಪ್ರಧಾನ (8 ಮಂತ್ರಿಗಳ ಸಮಿತಿ) ಆಧಾರಿತ ಆಡಳಿತ ಸ್ಥಾಪಿಸಿದ.',
            ),
            MCQQuestion(
                question='ಮರಾಠಾ ಸಾಮ್ರಾಜ್ಯದ ಪೇಶ್ವೆ ರಾಜಧಾನಿ ಎಲ್ಲಿತ್ತು?',
                options=['ರಾಯಗಡ', 'ಪುಣೆ', 'ಸತಾರ', 'ನಾಗ್ಪುರ'],
                answer=1,
                explanation='ಪೇಶ್ವೆಗಳ ರಾಜಧಾನಿ ಪುಣೆ (ಪೂನಾ) ಆಗಿತ್ತು.',
            ),
            MCQQuestion(
                question='ಶಿವಾಜಿ ಯಾವ ಮೊಘಲ್ ಸೇನಾಪತಿಯನ್ನು ಪ್ರತಾಪಗಡ ಯುದ್ಧದಲ್ಲಿ ಸೋಲಿಸಿದ?',
                options=['ಔರಂಗಜೇಬ್', 'ಮಿರ್ಝಾ ರಾಜ ಜಯಸಿಂಗ್', 'ಅಫ್ಜಲ್ ಖಾನ್', 'ಶಾಯಿಸ್ತಾ ಖಾನ್'],
                answer=2,
                explanation='ಶಿವಾಜಿ 1659 ರಲ್ಲಿ ಪ್ರತಾಪಗಡ ಯುದ್ಧದಲ್ಲಿ ಆದಿಲ್ ಶಾಹಿ ಸೇನಾಪತಿ ಅಫ್ಜಲ್ ಖಾನ್‌ನನ್ನು ಸೋಲಿಸಿ ಕೊಂದ.',
            ),
            MCQQuestion(
                question='ಮೂರನೇ ಪಾಣಿಪತ್ ಯುದ್ಧ (1761) ಮರಾಠರಿಗೆ ಏನು ಆಯಿತು?',
                options=['ಮರಾಠರು ಗೆದ್ದರು', 'ಮರಾಠರು ಸೋತರು', 'ಶಾಂತಿ ಒಪ್ಪಂದ ಆಯಿತು', 'ಯುದ್ಧ ಅನಿರ್ಣಯವಾಯಿತು'],
                answer=1,
                explanation='1761 ರ ಮೂರನೇ ಪಾಣಿಪತ್ ಯುದ್ಧದಲ್ಲಿ ಮರಾಠರು ಅಹ್ಮದ್ ಷಾ ಅಬ್ದಾಲಿಯಿಂದ ಸೋತರು.',
            ),
        ],

        descriptive_questions=[
            DescriptiveQuestion(
                question='ಶಿವಾಜಿಯ ಮಿಲಿಟರಿ ತಂತ್ರಗಳನ್ನು ವಿವರಿಸಿ.',
                answer='ಶಿವಾಜಿ ಗೆರಿಲ್ಲಾ ಯುದ್ಧ ತಂತ್ರ (ಗನಿಮಿ ಕಾವ) ಬಳಸಿದ. ಬೆಟ್ಟ ಪ್ರದೇಶ ಮತ್ತು ಕೋಟೆಗಳನ್ನು ಪರಿಣಾಮಕಾರಿಯಾಗಿ ಬಳಸಿದ. ನೌಕಾ ಸೇನೆ ನಿರ್ಮಿಸಿದ. ಬೇಹುಗಾರಿಕೆ ಜಾಲ (ಬಾತ್ಮಿದಾರ) ಸ್ಥಾಪಿಸಿದ.',
            ),
        ],

        audio_url='',
        full_video_url=video_url('session_07', 'session_07_full.mp4'),
        full_video_duration='',
        module_videos=[
            ModuleVideo(title='01 — ಮರಾಠರ ಉದಯ ಮತ್ತು ಶಿವಾಜಿಯ ಆರಂಭಿಕ ಜೀವನ',                           video_url=video_url('session_07', 'sections/01.mp4'), duration=''),
            ModuleVideo(title='02 — ಶಿವಾಜಿಯ ದಿಗ್ವಿಜಯಗಳು, ಮೊಘಲರೊಂದಿಗಿನ ಸಂಘರ್ಷ ಮತ್ತು ಪಟ್ಟಾಭಿಷೇಕ',        video_url=video_url('session_07', 'sections/02.mp4'), duration=''),
            ModuleVideo(title='03 — ಶಿವಾಜಿಯ ಆಡಳಿತ, ವ್ಯಕ್ತಿತ್ವ ಮತ್ತು ಉತ್ತರಾಧಿಕಾರಿಗಳು',                 video_url=video_url('session_07', 'sections/03.mp4'), duration=''),
            ModuleVideo(title='04 — ಪೇಶ್ವೆಗಳ ಆಳ್ವಿಕೆ ಮತ್ತು ಮರಾಠಾ ಸಾಮ್ರಾಜ್ಯ',                         video_url=video_url('session_07', 'sections/04.mp4'), duration=''),
        ],
        live_classes=[
            ExamLiveClass(
                title='Social Studies Session 7 — Live Doubt Clearing',
                description='Doubt clearing on Shivaji and the Maratha Empire.',
                date='2026-05-27', time='7:00 PM IST', join_url='',
            ),
        ],
    ),

    Session(
        title='ಸನಾತನ ಧರ್ಮ',
        locked=False,
        notes_locked=False, mcq_locked=False, descriptive_locked=False,
        audio_locked=False, video_locked=False, live_locked=False,

        notes_html="""
<h2>Session 8 — ಸನಾತನ ಧರ್ಮ</h2>
<ul>
  <li><strong>ಪರಿಚಯ:</strong> ಸನಾತನ ಧರ್ಮದ ಮೂಲ ಮತ್ತು ಅರ್ಥ</li>
  <li><strong>ಆಕರಗಳು:</strong> ಶೃತಿ, ಸ್ಮೃತಿ, ಧರ್ಮಸೂತ್ರ, ವೇದಾಂಗ</li>
  <li><strong>ಇತಿಹಾಸ ಮತ್ತು ಪುರಾಣಗಳು</strong></li>
  <li><strong>ದರ್ಶನಗಳು:</strong> ಭಾರತೀಯ ತತ್ವಶಾಸ್ತ್ರ</li>
  <li><strong>ವಿಗ್ರಹಾರಾಧನೆ, ಆಗಮ ಸಾಹಿತ್ಯ ಮತ್ತು ಸಾರ</strong></li>
</ul>
""".strip(),
        notes_pdf_url='',

        mcqs=[
            MCQQuestion(
                question='ವೇದಗಳ ಸಂಖ್ಯೆ ಎಷ್ಟು?',
                options=['2', '3', '4', '6'],
                answer=2,
                explanation='ನಾಲ್ಕು ವೇದಗಳು: ಋಗ್ವೇದ, ಯಜುರ್ವೇದ, ಸಾಮವೇದ ಮತ್ತು ಅಥರ್ವವೇದ.',
            ),
            MCQQuestion(
                question='ಉಪನಿಷತ್ತುಗಳು ಯಾವ ವರ್ಗಕ್ಕೆ ಸೇರುತ್ತವೆ?',
                options=['ಸ್ಮೃತಿ', 'ಶೃತಿ', 'ಪುರಾಣ', 'ಇತಿಹಾಸ'],
                answer=1,
                explanation='ಉಪನಿಷತ್ತುಗಳು ಶೃತಿ ಸಾಹಿತ್ಯಕ್ಕೆ ಸೇರುತ್ತವೆ (ವೇದಾಂತ ಭಾಗ).',
            ),
            MCQQuestion(
                question='ಭಾರತೀಯ ತತ್ವಶಾಸ್ತ್ರದ ಆಸ್ತಿಕ ದರ್ಶನಗಳ ಸಂಖ್ಯೆ ಎಷ್ಟು?',
                options=['4', '5', '6', '8'],
                answer=2,
                explanation='ಆರು ಆಸ್ತಿಕ ದರ್ಶನಗಳು (ಷಡ್ದರ್ಶನ): ಸಾಂಖ್ಯ, ಯೋಗ, ನ್ಯಾಯ, ವೈಶೇಷಿಕ, ಮೀಮಾಂಸ, ವೇದಾಂತ.',
            ),
            MCQQuestion(
                question='ಮಹಾಭಾರತ ಮತ್ತು ರಾಮಾಯಣ ಯಾವ ಸಾಹಿತ್ಯ ಪ್ರಕಾರಕ್ಕೆ ಸೇರುತ್ತವೆ?',
                options=['ಶೃತಿ', 'ಸ್ಮೃತಿ', 'ಇತಿಹಾಸ', 'ಪುರಾಣ'],
                answer=2,
                explanation='ಮಹಾಭಾರತ ಮತ್ತು ರಾಮಾಯಣ ಇತಿಹಾಸ ಪ್ರಕಾರಕ್ಕೆ ಸೇರುತ್ತವೆ.',
            ),
            MCQQuestion(
                question='ವೇದಾಂಗಗಳ ಸಂಖ್ಯೆ ಎಷ್ಟು?',
                options=['4', '5', '6', '8'],
                answer=2,
                explanation='ಆರು ವೇದಾಂಗಗಳು: ಶಿಕ್ಷಾ, ಕಲ್ಪ, ವ್ಯಾಕರಣ, ನಿರುಕ್ತ, ಛಂದಸ್ಸು, ಜ್ಯೋತಿಷ.',
            ),
        ],

        descriptive_questions=[
            DescriptiveQuestion(
                question='ಸನಾತನ ಧರ್ಮದ ಶೃತಿ ಮತ್ತು ಸ್ಮೃತಿ ಸಾಹಿತ್ಯದ ವ್ಯತ್ಯಾಸ ವಿವರಿಸಿ.',
                answer='ಶೃತಿ ಎಂದರೆ "ಕೇಳಿದ್ದು" — ವೇದ, ಬ್ರಾಹ್ಮಣ, ಅರಣ್ಯಕ, ಉಪನಿಷತ್ ಇವು ಶೃತಿ. ಇವು ಪರಮ ಪ್ರಮಾಣ. ಸ್ಮೃತಿ ಎಂದರೆ "ನೆನಪಿಸಿಕೊಂಡದ್ದು" — ಮನುಸ್ಮೃತಿ, ಧರ್ಮಸೂತ್ರ, ಮಹಾಭಾರತ, ರಾಮಾಯಣ, ಪುರಾಣಗಳು ಇವು ಸ್ಮೃತಿ. ಶೃತಿಗಿಂತ ಸ್ಮೃತಿ ದ್ವಿತೀಯ ಪ್ರಮಾಣ.',
            ),
        ],

        audio_url='',
        full_video_url=video_url('session_08', 'session_08_full.mp4'),
        full_video_duration='',
        module_videos=[
            ModuleVideo(title='01 — ಸನಾತನ ಧರ್ಮ: ಪರಿಚಯ',                        video_url=video_url('session_08', 'sections/01.mp4'), duration=''),
            ModuleVideo(title='02 — ಸನಾತನ ಧರ್ಮದ ಆಕರಗಳು: ಶೃತಿಗಳು',              video_url=video_url('session_08', 'sections/02.mp4'), duration=''),
            ModuleVideo(title='03 — ಸ್ಮೃತಿಗಳು ಮತ್ತು ಧರ್ಮಸೂತ್ರಗಳು',             video_url=video_url('session_08', 'sections/03.mp4'), duration=''),
            ModuleVideo(title='04 — ವೇದಾಂಗಗಳು',                                 video_url=video_url('session_08', 'sections/04.mp4'), duration=''),
            ModuleVideo(title='05 — ಇತಿಹಾಸ ಮತ್ತು ಪುರಾಣಗಳು',                    video_url=video_url('session_08', 'sections/05.mp4'), duration=''),
            ModuleVideo(title='06 — ದರ್ಶನಗಳು: ಭಾರತೀಯ ತತ್ವಶಾಸ್ತ್ರ',             video_url=video_url('session_08', 'sections/06.mp4'), duration=''),
            ModuleVideo(title='07 — ವಿಗ್ರಹಾರಾಧನೆ ಮತ್ತು ಆಗಮ ಸಾಹಿತ್ಯ',           video_url=video_url('session_08', 'sections/07.mp4'), duration=''),
            ModuleVideo(title='08 — ಸನಾತನ ಧರ್ಮದ ಆಶಯ',                          video_url=video_url('session_08', 'sections/08.mp4'), duration=''),
        ],
        live_classes=[
            ExamLiveClass(
                title='Social Studies Session 8 — Live Doubt Clearing',
                description='Doubt clearing on Sanatana Dharma — scriptures, philosophy and traditions.',
                date='2026-06-03', time='7:00 PM IST', join_url='',
            ),
        ],
    ),
]

# ── Subjects ───────────────────────────────────────────────────────────────────

subjects = [
    Subject(
        name='Social Studies / ಸಮಾಜ ವಿಜ್ಞಾನ',
        locked=False,
        sessions=social_sessions,
    ),
    Subject(
        name='Mathematics / ಗಣಿತ',
        locked=True,
        sessions=[],
    ),
    Subject(
        name='Science / ವಿಜ್ಞಾನ',
        locked=True,
        sessions=[],
    ),
    Subject(
        name='Pedagogy / ಶಿಕ್ಷಣಶಾಸ್ತ್ರ',
        locked=True,
        sessions=[],
    ),
    Subject(
        name='English / ಇಂಗ್ಲಿಷ್',
        locked=True,
        sessions=[],
    ),
    Subject(
        name='Kannada / ಕನ್ನಡ',
        locked=True,
        sessions=[],
    ),
]

# ── Create Exam ────────────────────────────────────────────────────────────────

exam = Exam(
    title='GPSTR 2026',
    exam_id=Exam.generate_exam_id('GPSTR 2026'),
    locked=False,
    full_form='Graduate Primary School Teacher Recruitment',
    description_en='Comprehensive preparation course for GPSTR 2026 — Graduate Primary School Teacher Recruitment. Covers Social Studies, Mathematics, Science, Pedagogy, English and Kannada for Class 1–5 teaching posts.',
    description_kn='ಜಿಪಿಎಸ್‌ಟಿಆರ್ 2026 — ಪದವೀಧರ ಪ್ರಾಥಮಿಕ ಶಾಲಾ ಶಿಕ್ಷಕ ನೇಮಕಾತಿ ಪರೀಕ್ಷೆಗೆ ಸಮಗ್ರ ತಯಾರಿ ಕೋರ್ಸ್. 1–5ನೇ ತರಗತಿ ಬೋಧನಾ ಹುದ್ದೆಗಳಿಗಾಗಿ ಸಮಾಜ ವಿಜ್ಞಾನ, ಗಣಿತ, ವಿಜ್ಞಾನ, ಶಿಕ್ಷಣಶಾಸ್ತ್ರ, ಇಂಗ್ಲಿಷ್ ಮತ್ತು ಕನ್ನಡ ಒಳಗೊಂಡಿದೆ.',
    thumbnail_url='',
    subjects=subjects,
)
exam.save()
print(f'Exam created: {exam.title} ({exam.exam_id})')
print(f'  Subjects: {len(exam.subjects)}')
print(f'  Total sessions (Social Studies): {len(social_sessions)}')

# ── Assessments ────────────────────────────────────────────────────────────────

assessments_data = [
    {
        'title': 'Social Studies Mock Test 1 — Medieval History',
        'subject_filter': 'Social Studies / ಸಮಾಜ ವಿಜ್ಞಾನ',
        'duration': 30,
        'questions': [
            ('ಪ್ರಥಮ ಪಾಣಿಪತ್ ಯುದ್ಧ ಯಾವ ವರ್ಷ ನಡೆಯಿತು?',
             ['1526', '1556', '1761', '1192'], 0,
             '1526 ರ ಪಾಣಿಪತ್ ಪ್ರಥಮ ಯುದ್ಧದಲ್ಲಿ ಬಾಬರ್ ಇಬ್ರಾಹಿಂ ಲೋಧಿಯನ್ನು ಸೋಲಿಸಿದ.'),
            ('ದೆಹಲಿ ಸುಲ್ತಾನಶಾಹಿಯ ಅಂತ್ಯ ಯಾವ ಯುದ್ಧದಿಂದ ಆಯಿತು?',
             ['ತರಾಯಿನ್ ಯುದ್ಧ', 'ಪಾಣಿಪತ್ ಮೊದಲ ಯುದ್ಧ', 'ಖಾನ್ವಾ ಯುದ್ಧ', 'ಬಕ್ಸರ್ ಯುದ್ಧ'], 1,
             '1526 ರ ಪಾಣಿಪತ್ ಮೊದಲ ಯುದ್ಧದಲ್ಲಿ ಇಬ್ರಾಹಿಂ ಲೋಧಿ ಸೋತು ದೆಹಲಿ ಸುಲ್ತಾನಶಾಹಿ ಅಂತ್ಯವಾಯಿತು.'),
            ('ಭಕ್ತಿ ಚಳುವಳಿ ಭಾರತದಲ್ಲಿ ಯಾವ ಶತಮಾನದಲ್ಲಿ ಉಚ್ಛ್ರಾಯಕ್ಕೆ ತಲುಪಿತು?',
             ['8–10ನೇ', '12–17ನೇ', '5–7ನೇ', '18–19ನೇ'], 1,
             'ಭಕ್ತಿ ಚಳುವಳಿ 12ರಿಂದ 17ನೇ ಶತಮಾನದ ನಡುವೆ ಉತ್ತುಂಗಕ್ಕೆ ತಲುಪಿತು.'),
            ('ಮೊಘಲ್ ಚಕ್ರವರ್ತಿ ಅಕ್ಬರ್‌ನ ಪ್ರಸಿದ್ಧ ನವರತ್ನಗಳಲ್ಲಿ ಒಬ್ಬ ಕವಿ ಯಾರು?',
             ['ತಾನ್ಸೇನ್', 'ತೋಡರ್‌ಮಲ್', 'ಅಬುಲ್ ಫಜಲ್', 'ಬೀರಬಲ್'], 3,
             'ಬೀರಬಲ್ ಅಕ್ಬರ್‌ನ ನವರತ್ನಗಳಲ್ಲಿ ಒಬ್ಬ ಪ್ರಸಿದ್ಧ ಕವಿ ಮತ್ತು ಬುದ್ಧಿಶಾಲಿ.'),
            ('ಶಿವಾಜಿ ಯಾವ ವರ್ಷ ನಿಧನರಾದರು?',
             ['1674', '1680', '1700', '1661'], 1,
             'ಶಿವಾಜಿ 1680 ರಲ್ಲಿ ರಾಯಗಡದಲ್ಲಿ ನಿಧನರಾದರು.'),
            ('ಗುಲಾಮ ಸಂತತಿಯ ಯಾವ ಸುಲ್ತಾನ "ಕೌಟಿಲ್ಯ ಆಫ್ ದೆಹಲಿ ಸುಲ್ತಾನಶಾಹಿ" ಎಂದು ಕರೆಯಲ್ಪಟ್ಟ?',
             ['ಕುತುಬ್ ಉದ್-ದೀನ್ ಐಬಕ್', 'ಇಲ್ಟುಟ್ಮಿಶ್', 'ಬಲ್ಬನ್', 'ರಜಿಯಾ'], 2,
             'ಬಲ್ಬನ್ ತನ್ನ ಕಟ್ಟುನಿಟ್ಟಿನ ಆಡಳಿತ ಮತ್ತು ಷಾಮ ದಾನ ದಂಡ ಭೇದ ನೀತಿಗಾಗಿ ಪ್ರಸಿದ್ಧ.'),
            ('ಸನಾತನ ಧರ್ಮದ "ಅಷ್ಟಾದಶ ಪುರಾಣ" ಗಳ ಸಂಖ್ಯೆ ಎಷ್ಟು?',
             ['12', '16', '18', '24'], 2,
             'ಅಷ್ಟಾದಶ ಎಂದರೆ 18 — 18 ಮಹಾಪುರಾಣಗಳಿವೆ.'),
            ('ಮೊಘಲ್ ಕಾಲದ ಅಧಿಕೃತ ಭಾಷೆ ಯಾವುದು?',
             ['ಅರಬ್ಬಿ', 'ಫಾರ್ಸಿ', 'ಉರ್ದು', 'ತುರ್ಕಿ'], 1,
             'ಮೊಘಲ್ ಆಸ್ಥಾನದ ಅಧಿಕೃತ ಭಾಷೆ ಫಾರ್ಸಿ (Persian) ಆಗಿತ್ತು.'),
            ('ಅಫ್ಜಲ್ ಖಾನ್ ಯಾವ ಸಾಮ್ರಾಜ್ಯದ ಸೇನಾಧಿಪತಿ?',
             ['ಮೊಘಲ್', 'ಆದಿಲ್ ಶಾಹಿ', 'ನಿಝಾಮ್ ಶಾಹಿ', 'ಕುತುಬ್ ಶಾಹಿ'], 1,
             'ಅಫ್ಜಲ್ ಖಾನ್ ಬಿಜಾಪುರದ ಆದಿಲ್ ಶಾಹಿ ಸಾಮ್ರಾಜ್ಯದ ಸೇನಾಧಿಪತಿ.'),
            ('ಕಬೀರ್ ಭಕ್ತ ಯಾರ ಶಿಷ್ಯ?',
             ['ಶಂಕರಾಚಾರ್ಯರು', 'ರಾಮಾನಂದ', 'ಮಧ್ವಾಚಾರ್ಯರು', 'ಗುರು ನಾನಕ್'], 1,
             'ಕಬೀರ್ ರಾಮಾನಂದರ ಶಿಷ್ಯ ಮತ್ತು ಹಿಂದೂ-ಮುಸ್ಲಿಂ ಐಕ್ಯತೆಯ ಭಕ್ತ ಕವಿ.'),
        ],
    },
    {
        'title': 'Social Studies Mock Test 2 — Full Length',
        'subject_filter': 'Social Studies / ಸಮಾಜ ವಿಜ್ಞಾನ',
        'duration': 45,
        'questions': [
            ('ರಜಪೂತ ವಂಶಗಳ ಪ್ರಮುಖ ಧರ್ಮ ಯಾವುದು?',
             ['ಬೌದ್ಧ', 'ಜೈನ', 'ಹಿಂದೂ', 'ಇಸ್ಲಾಂ'], 2,
             'ರಜಪೂತರು ಮುಖ್ಯವಾಗಿ ಹಿಂದೂ ಧರ್ಮ ಅನುಸರಿಸಿದರು.'),
            ('ಮಹಮ್ಮದ್ ಘಜ್ನಿ ಯಾವ ವಂಶಕ್ಕೆ ಸೇರಿದ?',
             ['ಘೋರಿ', 'ಗಜ್ನವಿದ್', 'ಸೆಲ್ಜುಕ್', 'ತೈಮೂರ್'], 1,
             'ಮಹಮ್ಮದ್ ಘಜ್ನಿ ಗಜ್ನವಿದ್ ವಂಶಕ್ಕೆ ಸೇರಿದ.'),
            ('ತಾಜ್ ಮಹಲ್ ಯಾವ ನಗರದಲ್ಲಿದೆ?',
             ['ದೆಹಲಿ', 'ಆಗ್ರಾ', 'ಲಾಹೋರ್', 'ಜೈಪುರ'], 1,
             'ತಾಜ್ ಮಹಲ್ ಉತ್ತರ ಪ್ರದೇಶದ ಆಗ್ರಾದಲ್ಲಿದೆ.'),
            ('ಗುರು ಗ್ರಂಥ ಸಾಹಿಬ್ ಯಾವ ಧರ್ಮದ ಪವಿತ್ರ ಗ್ರಂಥ?',
             ['ಹಿಂದೂ', 'ಬೌದ್ಧ', 'ಸಿಖ್', 'ಜೈನ'], 2,
             'ಗುರು ಗ್ರಂಥ ಸಾಹಿಬ್ ಸಿಖ್ ಧರ್ಮದ ಪವಿತ್ರ ಶಾಶ್ವತ ಗುರು ಮತ್ತು ಗ್ರಂಥ.'),
            ('ಪೇಶ್ವೆ ಬಾಜಿರಾವ್ I ಯಾವ ಶತಮಾನದಲ್ಲಿ ಮರಾಠಾ ಶಕ್ತಿ ವಿಸ್ತರಿಸಿದ?',
             ['16ನೇ', '17ನೇ', '18ನೇ', '19ನೇ'], 2,
             'ಬಾಜಿರಾವ್ I 18ನೇ ಶತಮಾನದಲ್ಲಿ (1720-1740) ಮರಾಠಾ ಸಾಮ್ರಾಜ್ಯ ವಿಸ್ತರಿಸಿದ.'),
        ],
    },
    {
        'title': 'GPSTR Full Mock Test',
        'subject_filter': '',
        'duration': 60,
        'questions': [
            ('ಪ್ರಾಥಮಿಕ ಶಾಲೆಯಲ್ಲಿ ಮಕ್ಕಳ ಕಲಿಕೆಯ ಮೌಲ್ಯಮಾಪನದ ಉದ್ದೇಶ ಯಾವುದು?',
             ['ಶ್ರೇಣಿ ನೀಡುವುದು', 'ಕಲಿಕೆಯ ಪ್ರಗತಿ ಗ್ರಹಿಸುವುದು', 'ಪರೀಕ್ಷೆ ಪಾಸ್ ಮಾಡಿಸುವುದು', 'ತರಗತಿ ಕೊಠಡಿ ನಿರ್ವಹಣೆ'], 1,
             'ಮೌಲ್ಯಮಾಪನದ ಮೂಲ ಉದ್ದೇಶ ಮಕ್ಕಳ ಕಲಿಕೆ ಮತ್ತು ಅಭಿವೃದ್ಧಿ ಅರ್ಥಮಾಡಿಕೊಳ್ಳುವುದು.'),
            ('2+3×4 = ?',
             ['20', '14', '24', '10'], 1,
             'BODMAS ನಿಯಮ: ಮೊದಲು 3×4=12, ನಂತರ 2+12=14.'),
            ('ಭೂಮಿಯ ಮೇಲ್ಮೈ ಶೇಕಡಾ ಎಷ್ಟು ಭಾಗ ನೀರಿನಿಂದ ಆವೃತ?',
             ['51%', '61%', '71%', '81%'], 2,
             'ಭೂಮಿಯ ಮೇಲ್ಮೈ ಸುಮಾರು 71% ನೀರಿನಿಂದ ಆವೃತ.'),
            ('ಕರ್ನಾಟಕ ಏಕೀಕರಣ ಯಾವ ದಿನ ಆಯಿತು?',
             ['ನವೆಂಬರ್ 1, 1956', 'ಜನವರಿ 26, 1950', 'ಆಗಸ್ಟ್ 15, 1947', 'ಮೇ 1, 1960'], 0,
             'ಕರ್ನಾಟಕ ಏಕೀಕರಣ ನವೆಂಬರ್ 1, 1956 ರಂದು ಆಯಿತು.'),
            ('ಮಕ್ಕಳ ಉಚಿತ ಮತ್ತು ಕಡ್ಡಾಯ ಶಿಕ್ಷಣ ಹಕ್ಕು ಕಾಯ್ದೆ ಯಾವ ವರ್ಷ ಜಾರಿಗೆ ಬಂತು?',
             ['2005', '2009', '2012', '2015'], 1,
             'ಆರ್‌ಟಿಇ ಕಾಯ್ದೆ 2009 ರಲ್ಲಿ ಜಾರಿಗೆ ಬಂತು, 2010 ರಿಂದ ಅನ್ವಯ.'),
        ],
    },
]

for ad in assessments_data:
    questions = []
    for q_text, opts, ans, expl in ad['questions']:
        questions.append(AssessmentQuestion(
            question=q_text, options=opts, answer=ans, explanation=expl,
        ))
    assessment = Assessment(
        exam=exam,
        title=ad['title'],
        subject_filter=ad['subject_filter'],
        duration_minutes=ad['duration'],
        questions=questions,
    )
    assessment.save()
    exam.update(push__assessments=assessment)
    print(f'  Assessment: {ad["title"]} ({len(questions)} questions, {ad["duration"]} min)')

print('\nDone! GPSTR exam seeded successfully.')
print(f'Subjects: {len(exam.subjects)}')
print(f'Assessments: {len(assessments_data)}')
print(f'\nNote: Audio URLs and thumbnail are empty — upload via admin panel.')
print(f'Video URLs point to CloudFront: {CF}')