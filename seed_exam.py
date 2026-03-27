"""
Seed script — creates a dummy exam with full content for testing.
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


# ── Sessions ──────────────────────────────────────────────────────────────────

def make_session(num, subject_name):
    return Session(
        title=f'{subject_name} — Session {num}: Core Concepts',
        locked=False,
        notes_locked=False, mcq_locked=False, descriptive_locked=False,
        audio_locked=False, video_locked=False, live_locked=False,

        notes_html=f"""
<h2>Session {num} Notes — {subject_name}</h2>
<p>This is a comprehensive study material covering the key concepts of session {num}.</p>
<ul>
  <li><strong>Topic A:</strong> Introduction and fundamentals</li>
  <li><strong>Topic B:</strong> Advanced principles and applications</li>
  <li><strong>Topic C:</strong> Case studies and real-world examples</li>
</ul>
<p>Make sure to revise these notes before attempting the MCQs and assessments.</p>
""".strip(),
        notes_pdf_url='',

        mcqs=[
            MCQQuestion(
                question=f'[{subject_name} S{num}] What is the capital of Karnataka?',
                options=['Mumbai', 'Bengaluru', 'Chennai', 'Hyderabad'],
                answer=1,
                explanation='Bengaluru (formerly Bangalore) is the capital city of Karnataka.',
            ),
            MCQQuestion(
                question=f'[{subject_name} S{num}] Which article of the Indian Constitution deals with Right to Equality?',
                options=['Article 12', 'Article 14', 'Article 19', 'Article 21'],
                answer=1,
                explanation='Article 14 guarantees equality before law and equal protection of laws.',
            ),
            MCQQuestion(
                question=f'[{subject_name} S{num}] The Vidhana Soudha is located in which city?',
                options=['Mysuru', 'Hubballi', 'Bengaluru', 'Mangaluru'],
                answer=2,
                explanation='Vidhana Soudha is the seat of the Karnataka state legislature in Bengaluru.',
            ),
            MCQQuestion(
                question=f'[{subject_name} S{num}] Who was the first Chief Minister of Karnataka?',
                options=['K. C. Reddy', 'Kengal Hanumanthaiah', 'S. Nijalingappa', 'Devaraj Urs'],
                answer=0,
                explanation='K. Chengalaraya Reddy was the first CM of Mysore State (now Karnataka).',
            ),
            MCQQuestion(
                question=f'[{subject_name} S{num}] Which river is known as the lifeline of Karnataka?',
                options=['Godavari', 'Krishna', 'Kaveri', 'Tungabhadra'],
                answer=2,
                explanation='The Kaveri (Cauvery) river is considered the lifeline of Karnataka.',
            ),
        ],

        descriptive_questions=[
            DescriptiveQuestion(
                question=f'[{subject_name} S{num}] Explain the significance of the 73rd Constitutional Amendment in strengthening local governance.',
                answer='The 73rd Constitutional Amendment Act (1992) gave constitutional status to Panchayati Raj institutions. It mandated the establishment of a three-tier system (village, intermediate, district), regular elections every 5 years, reservation of seats for SC/ST and women (1/3), and the creation of State Finance Commissions. This strengthened grassroots democracy and decentralized governance.',
            ),
            DescriptiveQuestion(
                question=f'[{subject_name} S{num}] Discuss the role of the Karnataka Administrative Service (KAS) in state governance.',
                answer='KAS officers form the backbone of state administration. They serve as Deputy Commissioners, CEO of Zilla Panchayats, and heads of various government departments. They implement government policies at the district level, coordinate between state and local bodies, manage revenue collection, maintain law and order, and oversee developmental programs. The KAS cadre is recruited through the KPSC examination.',
            ),
        ],

        audio_url='',
        full_video_url='',
        full_video_duration='45 min',
        module_videos=[
            ModuleVideo(title=f'Module 1: Introduction to {subject_name}', video_url='', duration='12 min'),
            ModuleVideo(title=f'Module 2: Key Concepts', video_url='', duration='15 min'),
            ModuleVideo(title=f'Module 3: Practice & Application', video_url='', duration='18 min'),
        ],

        live_classes=[
            ExamLiveClass(
                title=f'{subject_name} Session {num} — Live Doubt Clearing',
                description=f'Interactive session to clear all doubts from Session {num}. Bring your questions!',
                date='2026-04-15',
                time='7:00 PM IST',
                join_url='',
            ),
        ],
    )


# ── Subjects ──────────────────────────────────────────────────────────────────

subjects = [
    Subject(
        name='Indian Polity & Governance',
        locked=False,
        sessions=[make_session(i, 'Polity') for i in range(1, 4)],
    ),
    Subject(
        name='Karnataka History & Culture',
        locked=False,
        sessions=[make_session(i, 'KA History') for i in range(1, 4)],
    ),
    Subject(
        name='Indian Economy',
        locked=False,
        sessions=[make_session(i, 'Economy') for i in range(1, 3)],
    ),
    Subject(
        name='General Science & Technology',
        locked=True,  # locked subject for testing
        sessions=[make_session(1, 'Science')],
    ),
]


# ── Create Exam ───────────────────────────────────────────────────────────────

exam = Exam(
    title='KAS Prelims 2026',
    exam_id=Exam.generate_exam_id('KAS Prelims 2026'),
    locked=False,
    full_form='Karnataka Administrative Service — Preliminary Examination',
    description_en='Comprehensive preparation course for the KAS Prelims 2026 examination conducted by KPSC. Covers Indian Polity, Karnataka History, Economy, Science & Technology with notes, MCQs, video lectures, and mock tests.',
    description_kn='ಕೆಪಿಎಸ್‌ಸಿ ನಡೆಸುವ ಕೆಎಎಸ್ ಪ್ರಿಲಿಮ್ಸ್ 2026 ಪರೀಕ್ಷೆಗೆ ಸಮಗ್ರ ತಯಾರಿ ಕೋರ್ಸ್. ಭಾರತೀಯ ರಾಜಕೀಯ, ಕರ್ನಾಟಕ ಇತಿಹಾಸ, ಆರ್ಥಿಕತೆ, ವಿಜ್ಞಾನ ಮತ್ತು ತಂತ್ರಜ್ಞಾನವನ್ನು ಟಿಪ್ಪಣಿಗಳು, MCQ ಗಳು, ವೀಡಿಯೊ ಉಪನ್ಯಾಸಗಳು ಮತ್ತು ಮಾಕ್ ಪರೀಕ್ಷೆಗಳೊಂದಿಗೆ ಒಳಗೊಂಡಿದೆ.',
    thumbnail_url='',
    subjects=subjects,
)
exam.save()
print(f'Exam created: {exam.title} ({exam.exam_id})')
print(f'  Subjects: {len(exam.subjects)}')
print(f'  Total sessions: {sum(len(s.sessions) for s in exam.subjects)}')


# ── Assessments ───────────────────────────────────────────────────────────────

assessments_data = [
    {
        'title': 'Polity Mock Test 1',
        'subject_filter': 'Indian Polity & Governance',
        'duration': 30,
        'questions': [
            ('The Preamble of the Indian Constitution was amended by which amendment?',
             ['42nd', '44th', '52nd', '61st'], 0,
             'The 42nd Amendment (1976) added the words Socialist, Secular, and Integrity to the Preamble.'),
            ('Who is known as the Father of the Indian Constitution?',
             ['Mahatma Gandhi', 'Jawaharlal Nehru', 'B.R. Ambedkar', 'Sardar Patel'], 2,
             'Dr. B.R. Ambedkar was the chairman of the Drafting Committee and is regarded as the Father of the Indian Constitution.'),
            ('The Directive Principles of State Policy are enshrined in which part of the Constitution?',
             ['Part III', 'Part IV', 'Part V', 'Part VI'], 1,
             'Part IV (Articles 36-51) contains the Directive Principles of State Policy.'),
            ('What is the minimum age to become the President of India?',
             ['25 years', '30 years', '35 years', '40 years'], 2,
             'Article 58 prescribes that the President must have completed 35 years of age.'),
            ('Which schedule of the Constitution deals with the allocation of seats in the Rajya Sabha?',
             ['First Schedule', 'Second Schedule', 'Third Schedule', 'Fourth Schedule'], 3,
             'The Fourth Schedule deals with allocation of seats to states and UTs in the Rajya Sabha.'),
            ('The concept of Judicial Review in India is adopted from which country?',
             ['UK', 'USA', 'Canada', 'Australia'], 1,
             'Judicial Review was adopted from the Constitution of the United States of America.'),
            ('Article 370 was related to which state/UT?',
             ['Punjab', 'Jammu & Kashmir', 'Sikkim', 'Goa'], 1,
             'Article 370 granted special autonomous status to Jammu & Kashmir.'),
            ('How many Fundamental Rights are currently recognized by the Indian Constitution?',
             ['5', '6', '7', '8'], 1,
             'Originally 7 Fundamental Rights were listed; Right to Property was removed by the 44th Amendment, leaving 6.'),
            ('The Finance Commission is constituted under which article?',
             ['Article 280', 'Article 300', 'Article 312', 'Article 324'], 0,
             'Article 280 provides for the constitution of a Finance Commission.'),
            ('Who appoints the Governor of a state?',
             ['Chief Minister', 'President', 'Prime Minister', 'Chief Justice'], 1,
             'The Governor is appointed by the President of India under Article 155.'),
        ],
    },
    {
        'title': 'Karnataka History Quiz',
        'subject_filter': 'Karnataka History & Culture',
        'duration': 20,
        'questions': [
            ('The Hoysala Empire had its capital at:',
             ['Hampi', 'Halebidu', 'Badami', 'Mysuru'], 1,
             'Halebidu (formerly Dwarasamudra) was the regal capital of the Hoysala Empire.'),
            ('Hampi was the capital of which empire?',
             ['Chalukya', 'Rashtrakuta', 'Vijayanagara', 'Kadamba'], 2,
             'Hampi was the capital of the Vijayanagara Empire founded in 1336.'),
            ('The Kadamba dynasty was founded by:',
             ['Pulakeshin I', 'Mayurasharma', 'Krishna I', 'Vishnuvardhana'], 1,
             'Mayurasharma (also known as Mayurakeshi) founded the Kadamba dynasty in the 4th century.'),
            ('Which dance form is famous in Karnataka?',
             ['Bharatanatyam', 'Kathak', 'Yakshagana', 'Odissi'], 2,
             'Yakshagana is a traditional theatre form that combines dance, music, and dialogue, native to Karnataka.'),
            ('The Gol Gumbaz is located in:',
             ['Bidar', 'Bijapur', 'Gulbarga', 'Raichur'], 1,
             'Gol Gumbaz is in Bijapur (Vijayapura), built by Mohammed Adil Shah of the Adil Shahi dynasty.'),
        ],
    },
    {
        'title': 'Full Length Mock Test',
        'subject_filter': '',
        'duration': 60,
        'questions': [
            ('India is a member of which group of nations?',
             ['G7', 'G8', 'G20', 'G5'], 2,
             'India is a member of the G20 group of major economies.'),
            ('The largest district in Karnataka by area is:',
             ['Bengaluru Urban', 'Belagavi', 'Gulbarga', 'Tumkur'], 1,
             'Belagavi is the largest district in Karnataka by area.'),
            ('Who wrote the Indian national anthem?',
             ['Bankim Chandra', 'Rabindranath Tagore', 'Sarojini Naidu', 'Muhammad Iqbal'], 1,
             'Jana Gana Mana was written by Rabindranath Tagore.'),
            ('GDP stands for:',
             ['Gross Domestic Product', 'General Development Plan', 'Grand Domestic Price', 'Gross Development Product'], 0,
             'GDP = Gross Domestic Product, the total value of goods and services produced.'),
            ('Which planet is known as the Red Planet?',
             ['Venus', 'Mars', 'Jupiter', 'Saturn'], 1,
             'Mars appears reddish due to iron oxide on its surface.'),
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

print('\nDone! Exam seeded with full content.')
print('Subjects:', ', '.join(s.name for s in exam.subjects))
print(f'Assessments: {len(assessments_data)}')
print(f'\nNote: Audio/video URLs are empty — upload via admin panel.')
