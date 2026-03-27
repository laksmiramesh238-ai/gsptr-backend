import os
import hmac
import hashlib
import razorpay
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify, render_template_string, redirect as flask_redirect
from models.course import Course
from models.enrollment import Enrollment
from routes.student_auth import student_from_token

enrollment_bp = Blueprint('enrollment', __name__)

RZP_KEY_ID     = os.getenv('RAZORPAY_KEY_ID', '')
RZP_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', '')

rzp = razorpay.Client(auth=(RZP_KEY_ID, RZP_KEY_SECRET))


def _get_student():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    return student_from_token(auth.split(' ', 1)[1])


# ── create order ─────────────────────────────────────────────────────────────

@enrollment_bp.route('/create-order', methods=['POST'])
def create_order():
    student = _get_student()
    if not student:
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401

    data      = request.get_json(force=True)
    course_id = data.get('course_id', '')

    course = Course.objects(course_id=course_id).first()
    if not course:
        return jsonify({'ok': False, 'error': 'Course not found'}), 404

    # check already enrolled and active
    existing = Enrollment.objects(student=student, course=course, status='paid').first()
    if existing and existing.expires_at > datetime.utcnow():
        return jsonify({'ok': False, 'error': 'Already enrolled'}), 409

    amount_paise = int(float(str(course.price)) * 100)  # Razorpay expects paise

    order = rzp.order.create({
        'amount':   amount_paise,
        'currency': 'INR',
        'receipt':  f"enroll_{str(student.id)[:8]}_{course_id[:8]}",
        'notes': {
            'student_id': str(student.id),
            'course_id':  course_id,
        },
    })

    # save pending enrollment
    Enrollment(
        student=student,
        course=course,
        order_id=order['id'],
        status='pending',
    ).save()

    return jsonify({
        'ok':       True,
        'order_id': order['id'],
        'amount':   amount_paise,
        'currency': 'INR',
        'key':      RZP_KEY_ID,
        'course_name': course.name,
    })


# ── checkout page (serves Razorpay checkout.js for WebBrowser flow) ───────────

CHECKOUT_HTML = """
<!DOCTYPE html>
<html><head>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Payment</title>
  <style>
    body { font-family: -apple-system, sans-serif; display:flex; align-items:center;
           justify-content:center; min-height:100vh; margin:0; background:#f5f6fa; }
    .wrap { text-align:center; padding:24px; }
    .msg  { font-size:18px; color:#333; margin-bottom:16px; }
    .sub  { font-size:14px; color:#888; }
    .ok   { color:#2ECC71; font-size:18px; font-weight:700; }
  </style>
  <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
</head><body>
  <div class="wrap" id="status">
    <p class="msg">Opening payment…</p>
    <p class="sub">If nothing happens, tap the button below.</p>
    <button onclick="pay()" style="margin-top:12px;padding:12px 32px;background:#6C63FF;
      color:#fff;border:none;border-radius:8px;font-size:16px;font-weight:700;cursor:pointer;">
      Pay ₹{{ amount_display }}
    </button>
  </div>
  <script>
    var CALLBACK = "{{ callback_base }}";
    var options = {
      key:         "{{ key }}",
      amount:      "{{ amount }}",
      currency:    "{{ currency }}",
      order_id:    "{{ order_id }}",
      name:        "Student Prep",
      description: "{{ course_name }}",
      prefill:     { name: "{{ student_name }}", email: "{{ student_email }}" },
      theme:       { color: "#6C63FF" },
      handler: function(resp) {
        document.getElementById("status").innerHTML = '<p class="ok">Payment successful! Redirecting…</p>';
        // go through backend callback which does a proper HTTP 302 redirect to app
        window.location.href = CALLBACK + "/callback"
          + "?razorpay_payment_id=" + encodeURIComponent(resp.razorpay_payment_id)
          + "&razorpay_order_id="   + encodeURIComponent(resp.razorpay_order_id)
          + "&razorpay_signature="  + encodeURIComponent(resp.razorpay_signature)
          + "&scheme={{ scheme }}";
      },
      modal: {
        ondismiss: function() {
          window.location.href = CALLBACK + "/callback?cancelled=1&scheme={{ scheme }}";
        }
      }
    };
    function pay() { new Razorpay(options).open(); }
    setTimeout(pay, 600);
  </script>
</body></html>
"""

@enrollment_bp.route('/pay/<order_id>', methods=['GET'])
def pay_page(order_id):
    enrollment = Enrollment.objects(order_id=order_id).first()
    if not enrollment:
        return "Order not found", 404

    course  = enrollment.course
    student = enrollment.student
    amount  = int(float(str(course.price)) * 100)
    scheme  = request.args.get('scheme', 'studentprepapp')

    # build the callback base URL from the current request
    callback_base = request.host_url.rstrip('/') + '/api/enroll'

    return render_template_string(CHECKOUT_HTML,
        key=RZP_KEY_ID,
        amount=amount,
        amount_display=str(course.price),
        currency='INR',
        order_id=order_id,
        course_name=course.name,
        student_name=student.name,
        student_email=student.email,
        scheme=scheme,
        callback_base=callback_base,
    )


# ── payment callback (browser → backend → 302 redirect to app scheme) ────────

@enrollment_bp.route('/callback', methods=['GET'])
def payment_callback():
    scheme     = request.args.get('scheme', 'studentprepapp')
    cancelled  = request.args.get('cancelled', '')

    if cancelled:
        return flask_redirect(f'{scheme}://payment-cancelled')

    payment_id = request.args.get('razorpay_payment_id', '')
    order_id   = request.args.get('razorpay_order_id', '')
    signature  = request.args.get('razorpay_signature', '')

    if not payment_id or not order_id or not signature:
        return flask_redirect(f'{scheme}://payment-failed')

    # verify signature
    expected = hmac.new(
        RZP_KEY_SECRET.encode(),
        f"{order_id}|{payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        return flask_redirect(f'{scheme}://payment-failed')

    # mark enrollment as paid
    enrollment = Enrollment.objects(order_id=order_id).first()
    if enrollment and enrollment.status != 'paid':
        now = datetime.utcnow()
        enrollment.update(
            payment_id=payment_id,
            status='paid',
            enrolled_at=now,
            expires_at=now + timedelta(days=183),
        )

    return flask_redirect(f'{scheme}://payment-success?order_id={order_id}')


# ── verify payment ────────────────────────────────────────────────────────────

@enrollment_bp.route('/verify-payment', methods=['POST'])
def verify_payment():
    data       = request.get_json(force=True)
    order_id   = data.get('razorpay_order_id', '')
    payment_id = data.get('razorpay_payment_id', '')
    signature  = data.get('razorpay_signature', '')

    # verify HMAC signature — proves payment is genuine from Razorpay
    expected = hmac.new(
        RZP_KEY_SECRET.encode(),
        f"{order_id}|{payment_id}".encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        return jsonify({'ok': False, 'error': 'Invalid payment signature'}), 400

    enrollment = Enrollment.objects(order_id=order_id).first()
    if not enrollment:
        return jsonify({'ok': False, 'error': 'Order not found'}), 404

    if enrollment.status == 'paid':
        return jsonify({'ok': True, 'message': 'Already verified.'})

    now = datetime.utcnow()
    enrollment.update(
        payment_id=payment_id,
        status='paid',
        enrolled_at=now,
        expires_at=now + timedelta(days=183),
    )

    return jsonify({'ok': True, 'message': 'Enrollment successful! Access valid for 6 months.'})


# ── enrollment status ─────────────────────────────────────────────────────────

@enrollment_bp.route('/status/<course_id>', methods=['GET'])
def enrollment_status(course_id):
    student = _get_student()
    if not student:
        return jsonify({'ok': True, 'enrolled': False})

    course = Course.objects(course_id=course_id).first()
    if not course:
        return jsonify({'ok': True, 'enrolled': False})

    enrollment = Enrollment.objects(student=student, course=course, status='paid').first()
    if enrollment and enrollment.expires_at > datetime.utcnow():
        return jsonify({
            'ok':         True,
            'enrolled':   True,
            'expires_at': enrollment.expires_at.strftime('%d %b %Y'),
        })

    return jsonify({'ok': True, 'enrolled': False})


# ── my courses ────────────────────────────────────────────────────────────────

@enrollment_bp.route('/my-courses', methods=['GET'])
def my_courses():
    student = _get_student()
    if not student:
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401

    now         = datetime.utcnow()
    enrollments = Enrollment.objects(student=student, status='paid')
    result      = []

    for e in enrollments:
        c = e.course
        result.append({
            'course_id':    c.course_id,
            'name':         c.name,
            'thumbnail_url': c.thumbnail_url or '',
            'expires_at':   e.expires_at.strftime('%d %b %Y'),
            'active':       e.expires_at > now,
        })

    return jsonify({'ok': True, 'enrollments': result})
