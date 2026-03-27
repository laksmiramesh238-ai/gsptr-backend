import os, hmac, hashlib, razorpay
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, render_template_string, redirect as flask_redirect
from models.exam import Exam
from models.exam_enrollment import ExamEnrollment, EXAM_TIERS
from routes.student_auth import student_from_token

exam_enrollment_bp = Blueprint('exam_enrollment', __name__)

RZP_KEY_ID     = os.getenv('RAZORPAY_KEY_ID', '')
RZP_KEY_SECRET = os.getenv('RAZORPAY_KEY_SECRET', '')
rzp = razorpay.Client(auth=(RZP_KEY_ID, RZP_KEY_SECRET))


def _get_student():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    return student_from_token(auth.split(' ', 1)[1])


# ── create order ──────────────────────────────────────────────────────────────

@exam_enrollment_bp.route('/create-order', methods=['POST'])
def create_order():
    student = _get_student()
    if not student:
        return jsonify({'ok': False, 'error': 'Unauthorized'}), 401

    data    = request.get_json(force=True)
    exam_id = data.get('exam_id', '')
    tier    = int(data.get('tier', 0))

    if tier not in EXAM_TIERS:
        return jsonify({'ok': False, 'error': 'Invalid tier'}), 400

    exam = Exam.objects(exam_id=exam_id).first()
    if not exam:
        return jsonify({'ok': False, 'error': 'Exam not found'}), 404

    existing = ExamEnrollment.objects(student=student, exam=exam, status='paid').first()
    if existing and existing.expires_at > datetime.utcnow():
        if existing.tier >= tier:
            return jsonify({'ok': False, 'error': 'Already enrolled at this tier or higher'}), 409
        price = EXAM_TIERS[tier]['price'] - EXAM_TIERS[existing.tier]['price']
    else:
        price = EXAM_TIERS[tier]['price']

    amount_paise = price * 100

    order = rzp.order.create({
        'amount':   amount_paise,
        'currency': 'INR',
        'receipt':  f"exam_{str(student.id)[:8]}_{exam_id[:8]}_t{tier}",
        'notes':    {'student_id': str(student.id), 'exam_id': exam_id, 'tier': str(tier)},
    })

    ExamEnrollment(
        student=student, exam=exam, tier=tier,
        order_id=order['id'], status='pending',
    ).save()

    return jsonify({
        'ok': True, 'order_id': order['id'],
        'amount': amount_paise, 'currency': 'INR', 'key': RZP_KEY_ID,
        'exam_title': exam.title, 'tier_label': EXAM_TIERS[tier]['label'],
    })


# ── pay page ──────────────────────────────────────────────────────────────────

CHECKOUT_HTML = """
<!DOCTYPE html>
<html><head>
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Payment</title>
  <style>
    body{font-family:-apple-system,sans-serif;display:flex;align-items:center;
    justify-content:center;min-height:100vh;margin:0;background:#f5f6fa}
    .wrap{text-align:center;padding:24px}.ok{color:#2ECC71;font-size:18px;font-weight:700}
  </style>
  <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
</head><body>
  <div class="wrap" id="status">
    <p style="font-size:18px;color:#333">Opening payment…</p>
    <button onclick="pay()" style="margin-top:12px;padding:12px 32px;background:#6C63FF;
      color:#fff;border:none;border-radius:8px;font-size:16px;font-weight:700">
      Pay ₹{{ amount_display }}
    </button>
  </div>
  <script>
    var CB="{{ callback_base }}";
    var opts={key:"{{ key }}",amount:"{{ amount }}",currency:"{{ currency }}",
      order_id:"{{ order_id }}",name:"Student Prep",
      description:"{{ exam_title }} — {{ tier_label }} Plan",
      prefill:{name:"{{ student_name }}",email:"{{ student_email }}"},
      theme:{color:"#6C63FF"},
      handler:function(r){
        document.getElementById("status").innerHTML="<p class=\\"ok\\">Payment successful! Redirecting…</p>";
        window.location.href=CB+"/callback?razorpay_payment_id="+encodeURIComponent(r.razorpay_payment_id)
          +"&razorpay_order_id="+encodeURIComponent(r.razorpay_order_id)
          +"&razorpay_signature="+encodeURIComponent(r.razorpay_signature)
          +"&scheme={{ scheme }}";
      },
      modal:{ondismiss:function(){window.location.href=CB+"/callback?cancelled=1&scheme={{ scheme }}"}}
    };
    function pay(){new Razorpay(opts).open()}
    setTimeout(pay,600);
  </script>
</body></html>
"""

@exam_enrollment_bp.route('/pay/<order_id>', methods=['GET'])
def pay_page(order_id):
    enrollment = ExamEnrollment.objects(order_id=order_id).first()
    if not enrollment:
        return "Order not found", 404

    exam    = enrollment.exam
    student = enrollment.student
    tier    = enrollment.tier

    existing = ExamEnrollment.objects(
        student=student, exam=exam, status='paid'
    ).order_by('-tier').first()
    if existing and existing.expires_at and existing.expires_at > datetime.utcnow() and existing.tier < tier:
        price = EXAM_TIERS[tier]['price'] - EXAM_TIERS[existing.tier]['price']
    else:
        price = EXAM_TIERS[tier]['price']

    scheme = request.args.get('scheme', 'studentprepapp')
    callback_base = request.host_url.rstrip('/') + '/api/exam-enroll'

    return render_template_string(CHECKOUT_HTML,
        key=RZP_KEY_ID, amount=price * 100, amount_display=str(price),
        currency='INR', order_id=order_id,
        exam_title=exam.title, tier_label=EXAM_TIERS[tier]['label'],
        student_name=student.name, student_email=student.email,
        scheme=scheme, callback_base=callback_base,
    )


# ── callback ──────────────────────────────────────────────────────────────────

@exam_enrollment_bp.route('/callback', methods=['GET'])
def payment_callback():
    scheme = request.args.get('scheme', 'studentprepapp')
    if request.args.get('cancelled'):
        return flask_redirect(f'{scheme}://payment-cancelled')

    payment_id = request.args.get('razorpay_payment_id', '')
    order_id   = request.args.get('razorpay_order_id', '')
    signature  = request.args.get('razorpay_signature', '')

    if not payment_id or not order_id or not signature:
        return flask_redirect(f'{scheme}://payment-failed')

    expected = hmac.new(RZP_KEY_SECRET.encode(),
                        f"{order_id}|{payment_id}".encode(),
                        hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, signature):
        return flask_redirect(f'{scheme}://payment-failed')

    enrollment = ExamEnrollment.objects(order_id=order_id).first()
    if enrollment and enrollment.status != 'paid':
        now = datetime.utcnow()
        enrollment.update(
            payment_id=payment_id, status='paid',
            enrolled_at=now, expires_at=now + timedelta(days=183),
        )
        # deactivate old lower-tier enrollment
        ExamEnrollment.objects(
            student=enrollment.student, exam=enrollment.exam,
            status='paid', tier__lt=enrollment.tier, id__ne=enrollment.id,
        ).update(set__status='upgraded')

    return flask_redirect(f'{scheme}://payment-success?order_id={order_id}')


# ── enrollment status ─────────────────────────────────────────────────────────

@exam_enrollment_bp.route('/status/<exam_id>', methods=['GET'])
def enrollment_status(exam_id):
    student = _get_student()
    if not student:
        return jsonify({'ok': True, 'enrolled': False, 'tier': 0})

    exam = Exam.objects(exam_id=exam_id).first()
    if not exam:
        return jsonify({'ok': True, 'enrolled': False, 'tier': 0})

    e = ExamEnrollment.objects(student=student, exam=exam, status='paid').order_by('-tier').first()
    if e and e.expires_at > datetime.utcnow():
        return jsonify({
            'ok': True, 'enrolled': True, 'tier': e.tier,
            'tier_label': EXAM_TIERS[e.tier]['label'],
            'expires_at': e.expires_at.strftime('%d %b %Y'),
        })
    return jsonify({'ok': True, 'enrolled': False, 'tier': 0})
