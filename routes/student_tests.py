from flask import Blueprint, request, jsonify
from datetime import datetime
from models.test import Test
from routes.student_auth import student_from_token

student_tests_bp = Blueprint('student_tests', __name__)


def _get_student():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    return student_from_token(auth.split(' ', 1)[1])


# ── list (only tests the student is enrolled in) ─────────────────────────────

@student_tests_bp.route('/', methods=['GET'])
def list_tests():
    student = _get_student()
    if not student:
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401

    qs = Test.objects(students_enrolled=student).order_by('-start_date')
    return jsonify({
        'ok': True,
        'tests': [t.to_json_list(student_id=str(student.id)) for t in qs],
    })


# ── secure get (no answers) — used during attempt ────────────────────────────

@student_tests_bp.route('/<test_id>/secure', methods=['GET'])
def get_test_secure(test_id):
    student = _get_student()
    if not student:
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401

    t = Test.objects(id=test_id).first()
    if not t:
        return jsonify({'ok': False, 'error': 'Test not found'}), 404
    if not t.is_student_enrolled(student):
        return jsonify({'ok': False, 'error': 'Not enrolled'}), 403

    # Window check
    now = datetime.utcnow()
    if t.end_date and t.end_date < now:
        return jsonify({'ok': False, 'error': 'Test window has ended'}), 403
    if t.start_date and t.start_date > now:
        return jsonify({'ok': False, 'error': 'Test has not started yet'}), 403

    return jsonify({'ok': True, **t.to_json_secure(str(student.id))})


# ── start attempt (initialize result with status=-1) ─────────────────────────

@student_tests_bp.route('/<test_id>/start', methods=['POST'])
def start_test(test_id):
    student = _get_student()
    if not student:
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401

    t = Test.objects(id=test_id).first()
    if not t:
        return jsonify({'ok': False, 'error': 'Test not found'}), 404
    if not t.is_student_enrolled(student):
        return jsonify({'ok': False, 'error': 'Not enrolled'}), 403

    r = t.start_attempt(str(student.id))
    if r.status == 1:
        return jsonify({'ok': False, 'error': 'Already submitted'}), 400
    return jsonify({'ok': True, 'started_at': datetime.utcnow().isoformat()})


# ── submit ───────────────────────────────────────────────────────────────────

@student_tests_bp.route('/<test_id>/submit', methods=['POST'])
def submit_test(test_id):
    student = _get_student()
    if not student:
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401

    t = Test.objects(id=test_id).first()
    if not t:
        return jsonify({'ok': False, 'error': 'Test not found'}), 404
    if not t.is_student_enrolled(student):
        return jsonify({'ok': False, 'error': 'Not enrolled'}), 403

    existing = t.get_student_result(str(student.id))
    if existing and existing.status == 1:
        return jsonify({'ok': False, 'error': 'Already submitted'}), 400

    data = request.get_json(force=True)
    responses = data.get('responses', [])
    result = t.record_result(str(student.id), responses)
    return jsonify({
        'ok': True,
        'score':           result.score,
        'total_max_score': t.get_total_max_score(),
    })


# ── result / review ──────────────────────────────────────────────────────────

@student_tests_bp.route('/<test_id>/result', methods=['GET'])
def get_result(test_id):
    student = _get_student()
    if not student:
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401

    t = Test.objects(id=test_id).first()
    if not t:
        return jsonify({'ok': False, 'error': 'Test not found'}), 404
    if not t.is_student_enrolled(student):
        return jsonify({'ok': False, 'error': 'Not enrolled'}), 403

    return jsonify({'ok': True, **t.to_json_review(str(student.id))})
