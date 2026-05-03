"""Admin-side user (student) listing & management."""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from bson import ObjectId
from bson.errors import InvalidId
from mongoengine.errors import ValidationError, DoesNotExist

from models.student import Student
from models.enrollment import Enrollment
from models.exam_enrollment import ExamEnrollment


def _safe_get_student(student_id):
    try:
        return Student.objects(id=ObjectId(student_id)).first()
    except (InvalidId, ValidationError, DoesNotExist):
        return None

admin_users_bp = Blueprint('admin_users', __name__)


@admin_users_bp.route('/', methods=['GET'])
@login_required
def list_users():
    q = (request.args.get('q') or '').strip().lower()
    qs = Student.objects()
    if q:
        qs = qs.filter(__raw__={
            '$or': [
                {'email': {'$regex': q, '$options': 'i'}},
                {'phone': {'$regex': q, '$options': 'i'}},
                {'name':  {'$regex': q, '$options': 'i'}},
            ]
        })

    students = list(qs.order_by('-created_at').limit(500))

    course_counts = {}
    exam_counts   = {}
    for s in students:
        course_counts[str(s.id)] = Enrollment.objects(student=s, status='paid').count()
        exam_counts[str(s.id)]   = ExamEnrollment.objects(student=s, status='paid').count()

    return render_template(
        'admin/users_list.html',
        students=students,
        course_counts=course_counts,
        exam_counts=exam_counts,
        q=q,
        total=Student.objects().count(),
    )


@admin_users_bp.route('/<student_id>', methods=['GET'])
@login_required
def user_detail(student_id):
    student = _safe_get_student(student_id)
    if not student:
        flash('Student not found.', 'error')
        return redirect(url_for('admin_users.list_users'))

    # Wrap each enrollment with a safe label so template never dereferences
    # a missing course/exam (which can throw DoesNotExist).
    course_enrolls = []
    for e in Enrollment.objects(student=student).order_by('-created_at'):
        try:
            label = e.course.name if e.course else '— deleted —'
        except Exception:
            label = '— deleted —'
        course_enrolls.append({'e': e, 'label': label})

    exam_enrolls = []
    for e in ExamEnrollment.objects(student=student).order_by('-created_at'):
        try:
            label = e.exam.title if e.exam else '— deleted —'
        except Exception:
            label = '— deleted —'
        exam_enrolls.append({'e': e, 'label': label})

    from models.exam_enrollment import EXAM_TIERS
    return render_template(
        'admin/user_detail.html',
        student=student,
        course_enrolls=course_enrolls,
        exam_enrolls=exam_enrolls,
        tiers=EXAM_TIERS,
    )


@admin_users_bp.route('/<student_id>/reset-device', methods=['POST'])
@login_required
def reset_device(student_id):
    s = _safe_get_student(student_id)
    if not s:
        flash('Student not found.', 'error')
        return redirect(url_for('admin_users.list_users'))
    s.device_id = ''
    s.device_label = ''
    s.device_bound_at = None
    s.save()
    flash(f'Device reset for {s.email}. They can sign in on a new device now.', 'success')
    return redirect(url_for('admin_users.user_detail', student_id=student_id))


@admin_users_bp.route('/<student_id>/delete', methods=['POST'])
@login_required
def delete_user(student_id):
    s = _safe_get_student(student_id)
    if not s:
        flash('Student not found.', 'error')
        return redirect(url_for('admin_users.list_users'))
    Enrollment.objects(student=s).delete()
    ExamEnrollment.objects(student=s).delete()
    email = s.email
    s.delete()
    flash(f'Deleted {email} and all their enrollments.', 'success')
    return redirect(url_for('admin_users.list_users'))
