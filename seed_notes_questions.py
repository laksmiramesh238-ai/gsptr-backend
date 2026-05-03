"""
For every session that has a `merge_code`, replace its notes_html, mcqs,
and descriptive_questions with the content from the project's
notes/ and questions/ folders.

Usage:  python seed_notes_questions.py
"""

import os, sys, json
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from dotenv import load_dotenv
load_dotenv()

from mongoengine import connect
connect(db=os.getenv('DB_NAME', 'course_platform'), host=os.getenv('MONGO_URI'))

from datetime import datetime
from models.exam import Exam, MCQQuestion, DescriptiveQuestion, MarkingStep
from models.session_content import SessionContent

# Scan multiple folder pairs (notes + questions). Add more here as new
# subjects come online. First match wins per merge_code.
_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SOURCE_PAIRS = [
    (os.path.join(_root, 'notes'),         os.path.join(_root, 'questions')),
    (os.path.join(_root, 'notes_science'), os.path.join(_root, 'questions_science')),
]


def load_notes_html(merge_code: str) -> str | None:
    for notes_dir, _ in SOURCE_PAIRS:
        path = os.path.join(notes_dir, f'{merge_code}.html')
        if os.path.exists(path):
            with open(path, encoding='utf-8') as f:
                return f.read()
    return None


def load_questions(merge_code: str) -> dict | None:
    for _, q_dir in SOURCE_PAIRS:
        path = os.path.join(q_dir, f'{merge_code}.json')
        if os.path.exists(path):
            with open(path, encoding='utf-8') as f:
                return json.load(f)
    return None


def build_mcq(q: dict) -> MCQQuestion:
    options       = [opt.get('text', '') for opt in q.get('options', [])]
    feedback      = [opt.get('feedback', '') for opt in q.get('options', [])]
    correct_index = next((i for i, opt in enumerate(q.get('options', [])) if opt.get('is_correct')), 0)
    return MCQQuestion(
        question        = q.get('question', ''),
        options         = options,
        answer          = correct_index,
        explanation     = q.get('explanation', ''),
        option_feedback = feedback,
        difficulty      = q.get('difficulty', ''),
        bloom_level     = q.get('bloom_level', ''),
        marks           = int(q.get('marks') or 1),
        concept_id      = q.get('concept_id', ''),
        qid             = q.get('id', ''),
    )


def build_desc(q: dict) -> DescriptiveQuestion:
    steps = [
        MarkingStep(
            step      = int(s.get('step') or 0),
            marks     = float(s.get('marks') or 0),
            criterion = s.get('criterion', ''),
        )
        for s in q.get('marking_scheme', [])
    ]
    expected = q.get('expected_answer', '')
    model    = q.get('model_solution', '')
    return DescriptiveQuestion(
        question        = q.get('question', ''),
        answer          = model or expected,           # fallback for legacy UI
        marks           = int(q.get('marks') or 2),
        expected_answer = expected,
        key_points      = q.get('key_points', []) or [],
        marking_scheme  = steps,
        common_traps    = q.get('common_traps', []) or [],
        model_solution  = model,
        concept_id      = q.get('concept_id', ''),
        qid             = q.get('id', ''),
    )


def main():
    total_sessions     = 0
    sessions_with_code = 0
    notes_seeded       = 0
    notes_missing      = 0
    questions_seeded   = 0
    questions_missing  = 0
    total_mcqs         = 0
    total_descs        = 0
    missing_codes      = []

    # Collect every merge_code that exists in DB (across all exams)
    merge_codes = set()
    for exam in Exam.objects():
        for sub in exam.subjects:
            for sess in sub.sessions:
                total_sessions += 1
                if sess.merge_code:
                    merge_codes.add(sess.merge_code)
                    sessions_with_code += 1

    for mc in sorted(merge_codes):
        html  = load_notes_html(mc)
        qdata = load_questions(mc)

        if not html and not qdata:
            notes_missing += 1
            questions_missing += 1
            missing_codes.append(f'{mc} (both)')
            continue

        sc = SessionContent.objects(merge_code=mc).first() or SessionContent(merge_code=mc)
        sc.updated_at = datetime.utcnow()

        if html:
            sc.notes_html = html
            notes_seeded += 1
        else:
            notes_missing += 1
            missing_codes.append(f'{mc} (notes)')

        if qdata:
            new_mcqs  = [build_mcq(m) for m in qdata.get('mcqs', [])]
            new_descs = [build_desc(d) for d in qdata.get('descriptive', [])]
            sc.mcqs = new_mcqs
            sc.descriptive_questions = new_descs
            questions_seeded += 1
            total_mcqs  += len(new_mcqs)
            total_descs += len(new_descs)
        else:
            questions_missing += 1
            missing_codes.append(f'{mc} (questions)')

        sc.save()

    print()
    print(f"Total sessions:           {total_sessions}")
    print(f"  with merge_code:        {sessions_with_code}")
    print(f"Notes seeded:             {notes_seeded}    (missing files: {notes_missing})")
    print(f"Questions seeded:         {questions_seeded}    (missing files: {questions_missing})")
    print(f"  Total MCQs inserted:    {total_mcqs}")
    print(f"  Total descriptives:     {total_descs}")
    if missing_codes:
        print()
        print("Missing files:")
        for m in sorted(set(missing_codes)):
            print(f"  - {m}")


if __name__ == '__main__':
    main()
