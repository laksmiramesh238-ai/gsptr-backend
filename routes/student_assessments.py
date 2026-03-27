from datetime import datetime
from flask import Blueprint, request, jsonify
from models.assessment import Assessment
from models.assessment_attempt import AssessmentAttempt, AttemptAnswer
from models.exam_enrollment import ExamEnrollment
from routes.student_auth import student_from_token

student_assessments_bp = Blueprint('student_assessments', __name__)


def _get_student():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    return student_from_token(auth.split(' ', 1)[1])


# ── start assessment ──────────────────────────────────────────────────────────

@student_assessments_bp.route('/start', methods=['POST'])
def start_assessment():
    student = _get_student()
    if not student:
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401

    data = request.get_json(force=True)
    assessment_id = data.get('assessment_id', '')

    assessment = Assessment.objects(id=assessment_id).first()
    if not assessment:
        return jsonify({'ok': False, 'error': 'Assessment not found'}), 404

    # check enrollment (assessments need at least tier 1)
    enrollment = ExamEnrollment.objects(
        student=student, exam=assessment.exam, status='paid'
    ).first()
    if not enrollment or enrollment.expires_at < datetime.utcnow():
        return jsonify({'ok': False, 'error': 'Not enrolled'}), 403

    # create attempt
    attempt = AssessmentAttempt(
        student=student,
        assessment=assessment,
        total=len(assessment.questions),
    )
    attempt.save()

    # return questions WITHOUT answers
    questions = []
    for i, q in enumerate(assessment.questions):
        questions.append({
            'index': i,
            'question': q.question,
            'options': q.options,
        })

    return jsonify({
        'ok': True,
        'attempt_id': str(attempt.id),
        'duration_minutes': assessment.duration_minutes,
        'questions': questions,
    })


# ── submit assessment ─────────────────────────────────────────────────────────

@student_assessments_bp.route('/submit', methods=['POST'])
def submit_assessment():
    student = _get_student()
    if not student:
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401

    data       = request.get_json(force=True)
    attempt_id = data.get('attempt_id', '')
    answers    = data.get('answers', [])  # [{question_index, selected}]

    attempt = AssessmentAttempt.objects(id=attempt_id, student=student).first()
    if not attempt:
        return jsonify({'ok': False, 'error': 'Attempt not found'}), 404

    if attempt.status == 'submitted':
        return jsonify({'ok': False, 'error': 'Already submitted'}), 400

    assessment = attempt.assessment

    # score it
    saved_answers = []
    score = 0
    for ans in answers:
        idx = ans.get('question_index', -1)
        sel = ans.get('selected', -1)
        saved_answers.append(AttemptAnswer(question_index=idx, selected=sel))
        if 0 <= idx < len(assessment.questions):
            if sel == assessment.questions[idx].answer:
                score += 1

    attempt.update(
        answers=saved_answers,
        score=score,
        status='submitted',
        submitted_at=datetime.utcnow(),
    )

    # build report
    report = []
    for i, q in enumerate(assessment.questions):
        # find student's answer for this question
        student_ans = -1
        for a in answers:
            if a.get('question_index') == i:
                student_ans = a.get('selected', -1)
                break
        report.append({
            'question': q.question,
            'options': q.options,
            'correct_answer': q.answer,
            'selected': student_ans,
            'is_correct': student_ans == q.answer,
            'explanation': q.explanation,
        })

    return jsonify({
        'ok': True,
        'score': score,
        'total': len(assessment.questions),
        'percentage': round(score / len(assessment.questions) * 100) if assessment.questions else 0,
        'report': report,
    })


# ── get attempt report ────────────────────────────────────────────────────────

@student_assessments_bp.route('/attempt/<attempt_id>', methods=['GET'])
def get_attempt(attempt_id):
    student = _get_student()
    if not student:
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401

    attempt = AssessmentAttempt.objects(id=attempt_id, student=student).first()
    if not attempt:
        return jsonify({'ok': False, 'error': 'Attempt not found'}), 404

    assessment = attempt.assessment

    report = []
    if attempt.status == 'submitted':
        for i, q in enumerate(assessment.questions):
            student_ans = -1
            for a in attempt.answers:
                if a.question_index == i:
                    student_ans = a.selected
                    break
            report.append({
                'question': q.question,
                'options': q.options,
                'correct_answer': q.answer,
                'selected': student_ans,
                'is_correct': student_ans == q.answer,
                'explanation': q.explanation,
            })

    return jsonify({
        'ok': True,
        'status': attempt.status,
        'score': attempt.score,
        'total': attempt.total,
        'percentage': round(attempt.score / attempt.total * 100) if attempt.total else 0,
        'report': report,
    })
