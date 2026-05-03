import os
import random
import string
import jwt
import resend
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from models.student import Student
from models.otp import OTP

student_auth = Blueprint('student_auth', __name__)

resend.api_key = os.getenv('RESEND_API_KEY')
SECRET         = os.getenv('SECRET_KEY', 'dev-secret')
FROM_EMAIL     = os.getenv('RESEND_FROM', 'onboarding@resend.dev')
OTP_EXPIRY_MIN = 10


# ── helpers ──────────────────────────────────────────────────────────────────

def gen_otp():
    return ''.join(random.choices(string.digits, k=6))


def send_otp_email(email: str, code: str, name: str = ''):
    resend.Emails.send({
        'from':    FROM_EMAIL,
        'to':      email,
        'subject': 'Your verification code',
        'html':    f"""
            <div style="font-family:sans-serif;max-width:480px;margin:auto">
              <h2 style="color:#6c63ff">Your OTP Code</h2>
              <p>Hi {name or 'there'},</p>
              <p>Use the code below to verify your account. It expires in {OTP_EXPIRY_MIN} minutes.</p>
              <div style="font-size:36px;font-weight:700;letter-spacing:12px;
                          color:#1a1a2e;background:#f0efff;padding:20px;
                          text-align:center;border-radius:10px;margin:20px 0">
                {code}
              </div>
              <p style="color:#888;font-size:13px">If you didn't request this, ignore this email.</p>
            </div>
        """,
    })


def make_token(student: Student) -> str:
    payload = {
        'sub':   str(student.id),
        'email': student.email,
        'exp':   datetime.utcnow() + timedelta(days=30),
    }
    return jwt.encode(payload, SECRET, algorithm='HS256')


def student_from_token(token: str):
    try:
        data = jwt.decode(token, SECRET, algorithms=['HS256'])
        return Student.objects(id=data['sub']).first()
    except Exception:
        return None


# ── signup ────────────────────────────────────────────────────────────────────

@student_auth.route('/signup', methods=['POST'])
def signup():
    data  = request.get_json(force=True)
    name  = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()

    if not name or not email:
        return jsonify({'ok': False, 'error': 'Name and email are required'}), 400

    if Student.objects(email=email).first():
        return jsonify({'ok': False, 'error': 'Email already registered'}), 409

    code = gen_otp()
    OTP(email=email, code=code,
        expires_at=datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MIN),
        pending_name=name, pending_phone=phone).save()
    send_otp_email(email, code, name)

    return jsonify({'ok': True, 'message': 'OTP sent'})


# ── send otp (login / forgot) ─────────────────────────────────────────────────

@student_auth.route('/send-otp', methods=['POST'])
def send_otp():
    data  = request.get_json(force=True)
    email = data.get('email', '').strip().lower()

    if not email:
        return jsonify({'ok': False, 'error': 'Email is required'}), 400

    student = Student.objects(email=email).first()
    if not student:
        return jsonify({'ok': False, 'error': 'No account found with this email'}), 404

    code = gen_otp()
    OTP(email=email, code=code,
        expires_at=datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MIN)).save()
    send_otp_email(email, code, student.name)

    return jsonify({'ok': True, 'message': 'OTP sent'})


# ── verify otp ────────────────────────────────────────────────────────────────

@student_auth.route('/verify-otp', methods=['POST'])
def verify_otp():
    data  = request.get_json(force=True)
    email = data.get('email', '').strip().lower()
    code  = data.get('code', '').strip()
    device_id    = (data.get('device_id') or '').strip()
    device_label = (data.get('device_label') or '').strip()[:120]

    if not email or not code:
        return jsonify({'ok': False, 'error': 'Email and code are required'}), 400

    otp = OTP.objects(
        email=email, code=code, used=False
    ).order_by('-created_at').first()

    if not otp:
        return jsonify({'ok': False, 'error': 'Invalid OTP'}), 401

    if datetime.utcnow() > otp.expires_at:
        return jsonify({'ok': False, 'error': 'OTP expired'}), 401

    student = Student.objects(email=email).first()
    is_signup = student is None

    # ── Device-lock check (only enforced for existing accounts) ──────────────
    if student and student.device_id and device_id and student.device_id != device_id:
        # Don't burn the OTP — let the user retry on the right device.
        return jsonify({
            'ok':           False,
            'error':        'This account is already signed in on another device. '
                            'Ask the admin to reset your device, then try again.',
            'code':         'DEVICE_MISMATCH',
            'bound_device': student.device_label or 'another device',
        }), 403

    otp.update(used=True)

    if is_signup:
        if not otp.pending_name:
            return jsonify({'ok': False, 'error': 'Account not found'}), 404
        student = Student(
            name=otp.pending_name,
            email=email,
            phone=otp.pending_phone,
            is_verified=True,
        )
        student.save()
    elif not student.is_verified:
        student.update(is_verified=True)

    # Bind device on first successful verify (or rebind if cleared by admin).
    if device_id and not student.device_id:
        student.device_id       = device_id
        student.device_label    = device_label
        student.device_bound_at = datetime.utcnow()
        student.save()

    token = make_token(student)

    return jsonify({
        'ok':    True,
        'token': token,
        'student': {
            'id':    str(student.id),
            'name':  student.name,
            'email': student.email,
            'phone': student.phone,
        },
    })


# ── me (get profile) ──────────────────────────────────────────────────────────

@student_auth.route('/me', methods=['GET'])
def me():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401

    student = student_from_token(auth.split(' ', 1)[1])
    if not student:
        return jsonify({'ok': False, 'error': 'Invalid token'}), 401

    return jsonify({
        'ok': True,
        'student': {
            'id':    str(student.id),
            'name':  student.name,
            'email': student.email,
            'phone': student.phone,
        },
    })


# ── My enrollments (courses + exams) ─────────────────────────────────────────

@student_auth.route('/me/enrollments', methods=['GET'])
def my_enrollments():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401
    student = student_from_token(auth.split(' ', 1)[1])
    if not student:
        return jsonify({'ok': False, 'error': 'Invalid token'}), 401

    from datetime import datetime
    from models.enrollment import Enrollment
    from models.exam_enrollment import ExamEnrollment, EXAM_TIERS
    from utils.cdn import cdn_url

    now = datetime.utcnow()

    courses = []
    for e in Enrollment.objects(student=student, status='paid').order_by('-enrolled_at'):
        try:
            c = e.course
            if not c: continue
            courses.append({
                'enrollment_id': str(e.id),
                'course_id':     c.course_id,
                'name':          c.name,
                'thumbnail_url': cdn_url(c.thumbnail_url or ''),
                'enrolled_at':   e.enrolled_at.strftime('%d %b %Y') if e.enrolled_at else '',
                'expires_at':    e.expires_at.strftime('%d %b %Y') if e.expires_at else '',
                'active':        bool(e.expires_at and e.expires_at > now),
                'days_left':     max(0, (e.expires_at - now).days) if e.expires_at else 0,
            })
        except Exception:
            continue

    exams = []
    for e in ExamEnrollment.objects(student=student, status='paid').order_by('-enrolled_at'):
        try:
            x = e.exam
            if not x: continue
            tier_info = EXAM_TIERS.get(e.tier, {})
            exams.append({
                'enrollment_id': str(e.id),
                'exam_id':       x.exam_id,
                'title':         x.title,
                'thumbnail_url': cdn_url(x.thumbnail_url or ''),
                'tier':          e.tier,
                'tier_label':    tier_info.get('label', ''),
                'enrolled_at':   e.enrolled_at.strftime('%d %b %Y') if e.enrolled_at else '',
                'expires_at':    e.expires_at.strftime('%d %b %Y') if e.expires_at else '',
                'active':        bool(e.expires_at and e.expires_at > now),
                'days_left':     max(0, (e.expires_at - now).days) if e.expires_at else 0,
            })
        except Exception:
            continue

    return jsonify({'ok': True, 'courses': courses, 'exams': exams})
