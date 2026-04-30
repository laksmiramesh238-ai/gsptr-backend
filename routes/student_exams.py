from datetime import datetime
from flask import Blueprint, jsonify, request
from models.exam import Exam
from models.exam_enrollment import ExamEnrollment, EXAM_TIERS
from routes.student_auth import student_from_token
from utils.cdn import cdn_url

student_exams_bp = Blueprint('student_exams', __name__)


def _get_student():
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    return student_from_token(auth.split(' ', 1)[1])


def _get_tier(student, exam):
    if not student:
        return 0
    e = ExamEnrollment.objects(student=student, exam=exam, status='paid').first()
    if e and e.expires_at > datetime.utcnow():
        return e.tier
    return 0


def _filter_session(sess, tier):
    """Return session dict filtered by tier access. Preview sessions get full top-tier access."""
    if getattr(sess, 'preview', False):
        allowed = EXAM_TIERS[max(EXAM_TIERS.keys())]['includes']
    else:
        allowed = EXAM_TIERS.get(tier, {}).get('includes', []) if tier > 0 else []
    d = {'title': sess.title, 'preview': bool(getattr(sess, 'preview', False))}

    if 'mcq' in allowed:
        d['mcq_count'] = len(sess.mcqs)
    if 'descriptive' in allowed:
        d['descriptive_count'] = len(sess.descriptive_questions)
    if 'notes' in allowed:
        d['has_notes'] = bool(sess.notes_html or sess.notes_pdf_url)
    if 'audio' in allowed:
        d['has_audio'] = bool(sess.audio_url)
    if 'videos' in allowed:
        d['has_video'] = bool(sess.full_video_url)
        d['module_video_count'] = len(sess.module_videos)
    if 'live_classes' in allowed:
        d['live_class_count'] = len(sess.live_classes)

    return d


# ── list exams ────────────────────────────────────────────────────────────────

@student_exams_bp.route('', methods=['GET'])
def list_exams():
    exams = Exam.objects.all()
    result = []
    for e in exams:
        subject_count = len(e.subjects)
        session_count = sum(len(s.sessions) for s in e.subjects)
        result.append({
            'id':             str(e.id),
            'exam_id':        e.exam_id,
            'title':          e.title,
            'full_form':      e.full_form,
            'description_en': e.description_en,
            'thumbnail_url':  cdn_url(e.thumbnail_url or ''),
            'locked':         e.locked,
            'subject_count':  subject_count,
            'session_count':  session_count,
        })
    return jsonify({'ok': True, 'exams': result})


# ── exam detail ───────────────────────────────────────────────────────────────

@student_exams_bp.route('/<exam_id>', methods=['GET'])
def exam_detail(exam_id):
    exam = Exam.objects(exam_id=exam_id).first()
    if not exam:
        return jsonify({'ok': False, 'error': 'Exam not found'}), 404

    student = _get_student()
    tier = _get_tier(student, exam)

    subjects = []
    for sub in exam.subjects:
        sessions = []
        for sess in sub.sessions:
            sd = _filter_session(sess, tier)
            sd['locked'] = sess.locked
            sd['preview'] = bool(getattr(sess, 'preview', False))
            sd['notes_locked'] = sess.notes_locked
            sd['mcq_locked'] = sess.mcq_locked
            sd['descriptive_locked'] = sess.descriptive_locked
            sd['audio_locked'] = sess.audio_locked
            sd['video_locked'] = sess.video_locked
            sd['live_locked'] = sess.live_locked
            sessions.append(sd)
        subjects.append({'name': sub.name, 'locked': sub.locked, 'sessions': sessions})

    assessments = []
    for a in exam.assessments:
        assessments.append({
            'id':             str(a.id),
            'title':          a.title,
            'subject_filter': a.subject_filter,
            'topic_filter':   a.topic_filter,
            'session_filter': a.session_filter,
            'question_count': len(a.questions),
            'duration':       a.duration_minutes,
        })

    return jsonify({
        'ok': True,
        'tier': tier,
        'tiers': EXAM_TIERS,
        'exam': {
            'id':             str(exam.id),
            'exam_id':        exam.exam_id,
            'title':          exam.title,
            'locked':         exam.locked,
            'full_form':      exam.full_form,
            'description_en': exam.description_en,
            'description_kn': exam.description_kn,
            'thumbnail_url':  cdn_url(exam.thumbnail_url or ''),
            'subjects':       subjects,
            'assessments':    assessments,
        },
    })


# ── one subject's session list (lightweight; for subject page) ────────────────

@student_exams_bp.route('/<exam_id>/subject/<int:sub_idx>', methods=['GET'])
def subject_detail(exam_id, sub_idx):
    exam = Exam.objects(exam_id=exam_id).first()
    if not exam:
        return jsonify({'ok': False, 'error': 'Exam not found'}), 404
    if sub_idx >= len(exam.subjects):
        return jsonify({'ok': False, 'error': 'Subject not found'}), 404

    student = _get_student()
    tier = _get_tier(student, exam)
    sub = exam.subjects[sub_idx]

    sessions = []
    for sess in sub.sessions:
        sd = _filter_session(sess, tier)
        sd['locked'] = sess.locked
        sd['preview'] = bool(getattr(sess, 'preview', False))
        sessions.append(sd)

    return jsonify({
        'ok': True,
        'tier': tier,
        'subject': {'name': sub.name, 'locked': sub.locked, 'sessions': sessions},
    })


# ── session content (full data for enrolled students) ─────────────────────────

@student_exams_bp.route('/<exam_id>/subject/<int:sub_idx>/session/<int:sess_idx>', methods=['GET'])
def session_content(exam_id, sub_idx, sess_idx):
    exam = Exam.objects(exam_id=exam_id).first()
    if not exam:
        return jsonify({'ok': False, 'error': 'Exam not found'}), 404

    student = _get_student()
    tier = _get_tier(student, exam)

    if sub_idx >= len(exam.subjects):
        return jsonify({'ok': False, 'error': 'Subject not found'}), 404
    sub = exam.subjects[sub_idx]
    if sess_idx >= len(sub.sessions):
        return jsonify({'ok': False, 'error': 'Session not found'}), 404
    sess = sub.sessions[sess_idx]

    is_preview = bool(getattr(sess, 'preview', False))

    if not is_preview and tier == 0:
        return jsonify({'ok': False, 'error': 'Not enrolled'}), 403

    if sub.locked or sess.locked:
        return jsonify({'ok': False, 'error': 'This content is locked'}), 403

    if is_preview:
        allowed = EXAM_TIERS[max(EXAM_TIERS.keys())]['includes']
    else:
        allowed = EXAM_TIERS[tier]['includes']
    d = {
        'title': sess.title, 'subject': sub.name,
        'preview': is_preview,
        'notes_locked': sess.notes_locked,
        'mcq_locked': sess.mcq_locked,
        'descriptive_locked': sess.descriptive_locked,
        'audio_locked': sess.audio_locked,
        'video_locked': sess.video_locked,
        'live_locked': sess.live_locked,
    }

    if 'mcq' in allowed and not sess.mcq_locked:
        d['mcqs'] = [{'question': m.question, 'options': m.options,
                       'answer': m.answer, 'explanation': m.explanation}
                      for m in sess.mcqs]

    if 'descriptive' in allowed and not sess.descriptive_locked:
        d['descriptive'] = [{'question': dq.question, 'answer': dq.answer}
                            for dq in sess.descriptive_questions]

    if 'notes' in allowed and not sess.notes_locked:
        d['notes_html'] = sess.notes_html
        d['notes_pdf_url'] = cdn_url(sess.notes_pdf_url) if sess.notes_pdf_url else ''

    if 'audio' in allowed and not sess.audio_locked:
        d['audio_url'] = cdn_url(sess.audio_url) if sess.audio_url else ''

    if 'videos' in allowed and not sess.video_locked:
        d['full_video_url'] = cdn_url(sess.full_video_url) if sess.full_video_url else ''
        d['full_video_duration'] = sess.full_video_duration
        d['module_videos'] = [{
            'title': v.title,
            'video_url': cdn_url(v.video_url),
            'duration': v.duration,
            'podcast_url': cdn_url(v.podcast_url) if v.podcast_url else '',
            'podcast_duration': v.podcast_duration,
            'slides_count': v.slides_count,
        } for v in sess.module_videos]

    if 'live_classes' in allowed and not sess.live_locked:
        d['live_classes'] = [{'title': lc.title, 'description': lc.description,
                              'date': lc.date, 'time': lc.time,
                              'join_url': lc.join_url} for lc in sess.live_classes]

    return jsonify({'ok': True, 'session': d, 'tier': tier, 'allowed': allowed})
