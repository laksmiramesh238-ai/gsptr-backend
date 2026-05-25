from flask import (
    Blueprint, render_template, request, jsonify, redirect,
    url_for, flash
)
from flask_login import login_required
from datetime import datetime, timedelta
from bson import ObjectId
import json

from mongoengine.connection import get_db
from models.test import Test, QuestionDetail
from models.student import Student

admin_tests_bp = Blueprint('admin_tests', __name__)


def _parse_dt(date_str, time_str):
    """Parse 'YYYY-MM-DDTHH:MM' or just 'YYYY-MM-DD' + 'HH:MM AM' loosely."""
    if not date_str:
        return None
    # Accept 'YYYY-MM-DDTHH:MM' from <input type="datetime-local">
    try:
        return datetime.fromisoformat(date_str)
    except Exception:
        pass
    try:
        return datetime.strptime(date_str, '%Y-%m-%d')
    except Exception:
        return None


def _build_questions(payload):
    out = []
    for q in payload:
        opt = lambda o: {
            'text':      (o or {}).get('text', ''),
            'image_url': (o or {}).get('image_url') or None,
        }
        out.append(QuestionDetail(
            id              = q.get('id') or str(ObjectId()),
            question        = q.get('question', ''),
            question_image  = q.get('question_image') or None,
            option_a        = opt(q.get('option_a')),
            option_b        = opt(q.get('option_b')),
            option_c        = opt(q.get('option_c')),
            option_d        = opt(q.get('option_d')),
            correct_option  = int(q.get('correct_option', 0)),
            crt_ans_score   = float(q.get('crt_ans_score', 3.0)),
            wrong_ans_score = float(q.get('wrong_ans_score', -0.25)),
        ))
    return out


# ── list ──────────────────────────────────────────────────────────────────────

@admin_tests_bp.route('/')
@login_required
def list_tests():
    """List page — uses an aggregation so we don't pull all questions over the wire."""
    pipeline = [
        {'$project': {
            '_id': 1,
            'name': 1,
            'start_date': 1,
            'start_time': 1,
            'end_date': 1,
            'end_time': 1,
            'duration': 1,
            'order_index': 1,
            'questions_count': {'$size': {'$ifNull': ['$questions', []]}},
            'enrolled_count':  {'$size': {'$ifNull': ['$students_enrolled', []]}},
            'submitted_count': {
                '$size': {
                    '$filter': {
                        'input': {'$ifNull': ['$results', []]},
                        'as':    'r',
                        'cond':  {'$eq': ['$$r.status', 1]},
                    }
                }
            },
            'total_max_score': {
                '$sum': {
                    '$map': {
                        'input': {'$ifNull': ['$questions', []]},
                        'as':    'q',
                        'in':    {'$ifNull': ['$$q.crt_ans_score', 0]},
                    }
                }
            },
        }},
        {'$sort': {'order_index': 1, 'start_date': -1}},
    ]
    tests = list(get_db()['tests'].aggregate(pipeline))
    return render_template('admin/tests/list.html', tests=tests, now=datetime.utcnow())


# ── add ───────────────────────────────────────────────────────────────────────

@admin_tests_bp.route('/add', methods=['GET'])
@login_required
def add_test():
    return render_template('admin/tests/form.html', test=None, questions_json='[]')


@admin_tests_bp.route('/add', methods=['POST'])
@login_required
def add_test_post():
    try:
        data = request.get_json(force=True)

        start_dt = _parse_dt(data.get('start_date'), data.get('start_time'))
        if not start_dt:
            return jsonify({'ok': False, 'error': 'Invalid start date'}), 400
        duration = int(data.get('duration', 60))
        end_dt   = start_dt + timedelta(minutes=duration)

        # Determine min order_index so newest goes to top
        existing = list(Test.objects.only('order_index'))
        min_order = min((t.order_index for t in existing), default=0) - 1

        questions = _build_questions(data.get('questions', []))

        t = Test(
            name        = data.get('name', '').strip(),
            start_date  = start_dt,
            start_time  = data.get('start_time') or start_dt.strftime('%I:%M %p'),
            duration    = duration,
            end_date    = end_dt,
            end_time    = end_dt.strftime('%I:%M %p'),
            questions   = questions,
            results     = [],
            order_index = data.get('order_index') if data.get('order_index') is not None else min_order,
        )
        t.save()
        return jsonify({'ok': True, 'id': str(t.id)})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


# ── edit ──────────────────────────────────────────────────────────────────────

@admin_tests_bp.route('/<test_id>/edit', methods=['GET'])
@login_required
def edit_test(test_id):
    t = Test.objects(id=test_id).first()
    if not t:
        flash('Test not found', 'error'); return redirect(url_for('admin_tests.list_tests'))

    qjson = json.dumps([{
        'id':              q.id,
        'question':        q.question,
        'question_image':  q.question_image,
        'option_a':        q.option_a,
        'option_b':        q.option_b,
        'option_c':        q.option_c,
        'option_d':        q.option_d,
        'correct_option':  q.correct_option,
        'crt_ans_score':   q.crt_ans_score,
        'wrong_ans_score': q.wrong_ans_score,
    } for q in t.questions], default=str)

    return render_template('admin/tests/form.html', test=t, questions_json=qjson)


@admin_tests_bp.route('/<test_id>/edit', methods=['POST'])
@login_required
def edit_test_post(test_id):
    try:
        t = Test.objects(id=test_id).first()
        if not t:
            return jsonify({'ok': False, 'error': 'Not found'}), 404

        data = request.get_json(force=True)
        start_dt = _parse_dt(data.get('start_date'), data.get('start_time')) or t.start_date
        duration = int(data.get('duration', t.duration))
        end_dt   = start_dt + timedelta(minutes=duration)

        questions = _build_questions(data.get('questions', []))

        t.update(
            name        = data.get('name', t.name).strip(),
            start_date  = start_dt,
            start_time  = data.get('start_time') or t.start_time,
            duration    = duration,
            end_date    = end_dt,
            end_time    = end_dt.strftime('%I:%M %p'),
            questions   = questions,
            order_index = data.get('order_index', t.order_index),
        )
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


# ── delete ────────────────────────────────────────────────────────────────────

@admin_tests_bp.route('/<test_id>/delete', methods=['POST'])
@login_required
def delete_test(test_id):
    t = Test.objects(id=test_id).first()
    if t:
        t.delete()
        flash('Test deleted.', 'success')
    return redirect(url_for('admin_tests.list_tests'))


# ── enrollment ────────────────────────────────────────────────────────────────

@admin_tests_bp.route('/<test_id>/enrollments', methods=['GET'])
@login_required
def manage_enrollments(test_id):
    t = Test.objects(id=test_id).first()
    if not t:
        flash('Test not found', 'error'); return redirect(url_for('admin_tests.list_tests'))

    enrolled_ids = {str(s.id) for s in t.students_enrolled if s}
    enrolled = [s for s in t.students_enrolled if s]
    all_students = Student.objects().order_by('name')
    available = [s for s in all_students if str(s.id) not in enrolled_ids]
    return render_template(
        'admin/tests/enrollments.html',
        test=t, enrolled=enrolled, available=available,
    )


@admin_tests_bp.route('/<test_id>/enrollments/add', methods=['POST'])
@login_required
def enroll_one(test_id):
    t = Test.objects(id=test_id).first()
    if not t:
        flash('Test not found', 'error'); return redirect(url_for('admin_tests.list_tests'))

    student_id = request.form.get('student_id', '').strip()
    s = Student.objects(id=student_id).first()
    if not s:
        flash('Student not found', 'error')
    else:
        t.enroll(s)
        flash(f'Enrolled {s.name}.', 'success')
    return redirect(url_for('admin_tests.manage_enrollments', test_id=test_id))


@admin_tests_bp.route('/<test_id>/enrollments/bulk', methods=['POST'])
@login_required
def enroll_bulk(test_id):
    t = Test.objects(id=test_id).first()
    if not t:
        return jsonify({'ok': False, 'error': 'Not found'}), 404
    data = request.get_json(force=True)
    added = 0
    for sid in data.get('student_ids', []):
        s = Student.objects(id=sid).first()
        if s and not t.is_student_enrolled(s):
            t.students_enrolled.append(s)
            added += 1
    if added:
        t.save()
    return jsonify({'ok': True, 'added': added})


@admin_tests_bp.route('/<test_id>/enrollments/remove', methods=['POST'])
@login_required
def unenroll_one(test_id):
    t = Test.objects(id=test_id).first()
    if not t:
        flash('Test not found', 'error'); return redirect(url_for('admin_tests.list_tests'))

    student_id = request.form.get('student_id', '').strip()
    s = Student.objects(id=student_id).first()
    if s:
        t.unenroll(s)
        flash(f'Unenrolled {s.name}.', 'success')
    return redirect(url_for('admin_tests.manage_enrollments', test_id=test_id))


# ── reorder ──────────────────────────────────────────────────────────────────

@admin_tests_bp.route('/<test_id>/move', methods=['POST'])
@login_required
def move_test(test_id):
    """Swap order_index with the neighbour above/below.

    POST body: form-encoded `direction=up|down` (or JSON).
    """
    direction = (request.form.get('direction')
                 or (request.get_json(silent=True) or {}).get('direction', ''))
    if direction not in ('up', 'down'):
        return jsonify({'ok': False, 'error': 'direction must be up or down'}), 400

    t = Test.objects(id=test_id).first()
    if not t:
        return jsonify({'ok': False, 'error': 'Test not found'}), 404

    # Same sort as the list page: order_index ASC, then -start_date
    ordered = list(Test.objects.order_by('order_index', '-start_date'))
    try:
        idx = next(i for i, x in enumerate(ordered) if str(x.id) == str(t.id))
    except StopIteration:
        return jsonify({'ok': False, 'error': 'Test not found in list'}), 404

    swap_idx = idx - 1 if direction == 'up' else idx + 1
    if swap_idx < 0 or swap_idx >= len(ordered):
        return redirect(url_for('admin_tests.list_tests'))  # at boundary, no-op

    neighbour = ordered[swap_idx]

    # If both have the same order_index, just bump theirs by ±1 so they actually swap.
    if t.order_index == neighbour.order_index:
        if direction == 'up':
            t.order_index = neighbour.order_index - 1
        else:
            t.order_index = neighbour.order_index + 1
        t.save()
    else:
        t.order_index, neighbour.order_index = neighbour.order_index, t.order_index
        t.save(); neighbour.save()

    return redirect(url_for('admin_tests.list_tests'))


@admin_tests_bp.route('/reorder', methods=['POST'])
@login_required
def bulk_reorder():
    """Set order_index for a list of test IDs.

    JSON body: { "new_order": ["test_id_1", "test_id_2", ...] }
    """
    data = request.get_json(force=True)
    new_order = data.get('new_order', [])
    for idx, tid in enumerate(new_order):
        Test.objects(id=tid).update(set__order_index=idx)
    return jsonify({'ok': True, 'count': len(new_order)})


# ── results browser ──────────────────────────────────────────────────────────

@admin_tests_bp.route('/<test_id>/results', methods=['GET'])
@login_required
def view_results(test_id):
    t = Test.objects(id=test_id).first()
    if not t:
        flash('Test not found', 'error'); return redirect(url_for('admin_tests.list_tests'))

    sid_to_student = {str(s.id): s for s in Student.objects(id__in=[r.student_id for r in t.results])}
    rows = []
    for r in t.results:
        s = sid_to_student.get(r.student_id)
        rows.append({
            'student_name':  s.name  if s else '(deleted)',
            'student_email': s.email if s else r.student_id,
            'score':         r.score,
            'status':        'Submitted' if r.status == 1 else 'In progress',
            'submitted_at':  r.submitted_at,
            'responses':     len(r.responses),
        })
    return render_template(
        'admin/tests/results.html',
        test=t, rows=rows, max_score=t.get_total_max_score(),
    )
