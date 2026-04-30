"""
Admin-side manual enrollment.

Lets the admin grant a student access to a course or an exam (any tier)
without going through Razorpay. Used while the payment gateway is offline,
or for comp / promo enrollments.
"""

from datetime import datetime, timedelta
import uuid

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from models.student import Student
from models.course import Course
from models.exam import Exam
from models.enrollment import Enrollment
from models.exam_enrollment import ExamEnrollment, EXAM_TIERS

admin_enroll_bp = Blueprint('admin_enroll', __name__)

DEFAULT_DAYS = 183  # ~6 months, matches paid enrollments


def _find_student(identifier: str):
    identifier = (identifier or '').strip().lower()
    if not identifier:
        return None
    return (
        Student.objects(email=identifier).first()
        or Student.objects(phone=identifier).first()
    )


@admin_enroll_bp.route('/', methods=['GET'])
@login_required
def manual_enroll_page():
    courses = Course.objects().order_by('name')
    exams   = Exam.objects().order_by('title')

    students = Student.objects().order_by('-created_at').limit(50)

    # Recent manual enrollments for the activity panel
    recent_course = Enrollment.objects(payment_id__startswith='admin-').order_by('-created_at').limit(10)
    recent_exam   = ExamEnrollment.objects(payment_id__startswith='admin-').order_by('-created_at').limit(10)

    return render_template(
        'admin/manual_enroll.html',
        courses=courses,
        exams=exams,
        students=students,
        tiers=EXAM_TIERS,
        recent_course=recent_course,
        recent_exam=recent_exam,
    )


@admin_enroll_bp.route('/course', methods=['POST'])
@login_required
def enroll_course():
    student = _find_student(request.form.get('student'))
    course_id = request.form.get('course_id')
    days = int(request.form.get('days') or DEFAULT_DAYS)

    if not student:
        flash('Student not found. Use email or phone.', 'error')
        return redirect(url_for('admin_enroll.manual_enroll_page'))
    course = Course.objects(id=course_id).first()
    if not course:
        flash('Course not found.', 'error')
        return redirect(url_for('admin_enroll.manual_enroll_page'))

    now = datetime.utcnow()
    existing = Enrollment.objects(student=student, course=course, status='paid').first()
    if existing and existing.expires_at and existing.expires_at > now:
        existing.expires_at = now + timedelta(days=days)
        existing.save()
        flash(f"Extended {student.email} → {course.name} until {existing.expires_at:%d %b %Y}.", 'success')
    else:
        Enrollment(
            student=student,
            course=course,
            order_id=f"admin-{uuid.uuid4().hex[:10]}",
            payment_id=f"admin-manual-{uuid.uuid4().hex[:8]}",
            status='paid',
            enrolled_at=now,
            expires_at=now + timedelta(days=days),
        ).save()
        flash(f"Enrolled {student.email} in {course.name} for {days} days.", 'success')

    return redirect(url_for('admin_enroll.manual_enroll_page'))


@admin_enroll_bp.route('/exam', methods=['POST'])
@login_required
def enroll_exam():
    student = _find_student(request.form.get('student'))
    exam_id = request.form.get('exam_id')
    try:
        tier = int(request.form.get('tier') or 0)
    except ValueError:
        tier = 0
    days = int(request.form.get('days') or DEFAULT_DAYS)

    if not student:
        flash('Student not found. Use email or phone.', 'error')
        return redirect(url_for('admin_enroll.manual_enroll_page'))
    exam = Exam.objects(id=exam_id).first()
    if not exam:
        flash('Exam not found.', 'error')
        return redirect(url_for('admin_enroll.manual_enroll_page'))
    if tier not in EXAM_TIERS:
        flash('Invalid tier.', 'error')
        return redirect(url_for('admin_enroll.manual_enroll_page'))

    now = datetime.utcnow()
    existing = ExamEnrollment.objects(student=student, exam=exam, status='paid').order_by('-tier').first()
    if existing and existing.expires_at and existing.expires_at > now:
        existing.tier = max(existing.tier, tier)
        existing.expires_at = now + timedelta(days=days)
        existing.save()
        flash(
            f"Updated {student.email} → {exam.title} to tier {existing.tier} "
            f"({EXAM_TIERS[existing.tier]['label']}) until {existing.expires_at:%d %b %Y}.",
            'success',
        )
    else:
        ExamEnrollment(
            student=student,
            exam=exam,
            tier=tier,
            order_id=f"admin-{uuid.uuid4().hex[:10]}",
            payment_id=f"admin-manual-{uuid.uuid4().hex[:8]}",
            status='paid',
            enrolled_at=now,
            expires_at=now + timedelta(days=days),
        ).save()
        flash(
            f"Enrolled {student.email} in {exam.title} at tier {tier} "
            f"({EXAM_TIERS[tier]['label']}) for {days} days.",
            'success',
        )

    return redirect(url_for('admin_enroll.manual_enroll_page'))


@admin_enroll_bp.route('/revoke/course/<enrollment_id>', methods=['POST'])
@login_required
def revoke_course(enrollment_id):
    e = Enrollment.objects(id=enrollment_id).first()
    if e:
        e.delete()
        flash('Course enrollment revoked.', 'success')
    return redirect(url_for('admin_enroll.manual_enroll_page'))


@admin_enroll_bp.route('/revoke/exam/<enrollment_id>', methods=['POST'])
@login_required
def revoke_exam(enrollment_id):
    e = ExamEnrollment.objects(id=enrollment_id).first()
    if e:
        e.delete()
        flash('Exam enrollment revoked.', 'success')
    return redirect(url_for('admin_enroll.manual_enroll_page'))
