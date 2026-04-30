"""Admin-side user (student) listing & management."""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from models.student import Student
from models.enrollment import Enrollment
from models.exam_enrollment import ExamEnrollment

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
    student = Student.objects(id=student_id).first()
    if not student:
        flash('Student not found.', 'error')
        return redirect(url_for('admin_users.list_users'))

    course_enrolls = Enrollment.objects(student=student).order_by('-created_at')
    exam_enrolls   = ExamEnrollment.objects(student=student).order_by('-created_at')

    from models.exam_enrollment import EXAM_TIERS
    return render_template(
        'admin/user_detail.html',
        student=student,
        course_enrolls=course_enrolls,
        exam_enrolls=exam_enrolls,
        tiers=EXAM_TIERS,
    )


@admin_users_bp.route('/<student_id>/delete', methods=['POST'])
@login_required
def delete_user(student_id):
    s = Student.objects(id=student_id).first()
    if not s:
        flash('Student not found.', 'error')
        return redirect(url_for('admin_users.list_users'))
    Enrollment.objects(student=s).delete()
    ExamEnrollment.objects(student=s).delete()
    email = s.email
    s.delete()
    flash(f'Deleted {email} and all their enrollments.', 'success')
    return redirect(url_for('admin_users.list_users'))
