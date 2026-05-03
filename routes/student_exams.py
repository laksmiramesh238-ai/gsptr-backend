from datetime import datetime
from flask import Blueprint, jsonify, request
from models.exam import Exam
from models.exam_enrollment import ExamEnrollment, EXAM_TIERS
from models.session_content import SessionContent
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


def _content_index(sessions):
    """Bulk-load SessionContent stats for the given sessions in a single
    Mongo aggregation. Computes counts/flags WITHOUT fetching the (heavy)
    notes_html / mcq / descriptive bodies."""
    codes = [s.merge_code for s in sessions if s.merge_code]
    if not codes:
        return {}
    coll = SessionContent._get_collection()
    pipeline = [
        {'$match': {'merge_code': {'$in': codes}}},
        {'$project': {
            '_id': 0,
            'merge_code': 1,
            'mcq_count':  {'$size': {'$ifNull': ['$mcqs', []]}},
            'desc_count': {'$size': {'$ifNull': ['$descriptive_questions', []]}},
            'has_notes':  {'$gt': [
                {'$strLenBytes': {'$ifNull': ['$notes_html', '']}}, 0
            ]},
        }},
    ]
    out = {}
    for doc in coll.aggregate(pipeline):
        out[doc['merge_code']] = {
            'mcq_count':  doc.get('mcq_count', 0),
            'desc_count': doc.get('desc_count', 0),
            'has_notes':  bool(doc.get('has_notes', False)),
        }
    return out


def _filter_session(sess, tier, content_idx=None):
    """Return session dict filtered by tier access. Preview sessions get full top-tier access."""
    if getattr(sess, 'preview', False):
        allowed = EXAM_TIERS[max(EXAM_TIERS.keys())]['includes']
    else:
        allowed = EXAM_TIERS.get(tier, {}).get('includes', []) if tier > 0 else []
    d = {'title': sess.title, 'preview': bool(getattr(sess, 'preview', False))}

    # Prefer external SessionContent stats if available.
    ext = (content_idx or {}).get(sess.merge_code) if sess.merge_code else None
    mcq_count    = ext['mcq_count']  if ext else len(sess.mcqs)
    desc_count   = ext['desc_count'] if ext else len(sess.descriptive_questions)
    has_notes    = ext['has_notes']  if ext else bool(sess.notes_html)
    has_notes    = has_notes or bool(sess.notes_pdf_url)

    if 'mcq' in allowed:
        d['mcq_count'] = mcq_count
    if 'descriptive' in allowed:
        d['descriptive_count'] = desc_count
    if 'notes' in allowed:
        d['has_notes'] = has_notes
    if 'audio' in allowed:
        d['has_audio'] = bool(sess.audio_url) or any(v.podcast_url for v in sess.module_videos)
    if 'videos' in allowed:
        d['has_video'] = bool(sess.full_video_url)
        d['module_video_count'] = len(sess.module_videos)
    if 'live_classes' in allowed:
        d['live_class_count'] = len(sess.live_classes)

    return d


# ── list exams ────────────────────────────────────────────────────────────────

@student_exams_bp.route('', methods=['GET'])
def list_exams():
    # Use raw mongo aggregation so we never pull subject/session content
    pipeline = [
        {'$project': {
            'exam_id': 1, 'title': 1, 'full_form': 1, 'description_en': 1,
            'thumbnail_url': 1, 'locked': 1,
            'subject_count': {'$size': {'$ifNull': ['$subjects', []]}},
            'session_count': {'$sum': {
                '$map': {
                    'input': {'$ifNull': ['$subjects', []]},
                    'as': 's',
                    'in': {'$size': {'$ifNull': ['$$s.sessions', []]}},
                }
            }},
        }},
    ]
    coll = Exam._get_collection()
    result = []
    for doc in coll.aggregate(pipeline):
        result.append({
            'id':             str(doc['_id']),
            'exam_id':        doc.get('exam_id', ''),
            'title':          doc.get('title', ''),
            'full_form':      doc.get('full_form', ''),
            'description_en': doc.get('description_en', ''),
            'thumbnail_url':  cdn_url(doc.get('thumbnail_url') or ''),
            'locked':         bool(doc.get('locked', False)),
            'subject_count':  doc.get('subject_count', 0),
            'session_count':  doc.get('session_count', 0),
        })
    return jsonify({'ok': True, 'exams': result})


# ── exam detail ───────────────────────────────────────────────────────────────

@student_exams_bp.route('/<exam_id>', methods=['GET'])
def exam_detail(exam_id):
    """Slim exam detail — only what the exam landing page renders.

    Returns subject summaries (name, lock state, counts), NOT the per-session
    list. The session list is loaded lazily from `/api/exams/<id>/subject/<idx>`
    when the user enters a subject.
    """
    exam = Exam.objects(exam_id=exam_id).first()
    if not exam:
        return jsonify({'ok': False, 'error': 'Exam not found'}), 404

    student = _get_student()
    tier = _get_tier(student, exam)

    subjects = []
    for sub in exam.subjects:
        sessions = sub.sessions or []
        preview_count = sum(1 for s in sessions if getattr(s, 'preview', False))
        locked_count  = sum(1 for s in sessions if s.locked)
        subjects.append({
            'name':           sub.name,
            'locked':         sub.locked,
            'session_count':  len(sessions),
            'preview_count':  preview_count,
            'locked_count':   locked_count,
        })

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

    content_idx = _content_index(sub.sessions)
    sessions = []
    for sess in sub.sessions:
        sd = _filter_session(sess, tier, content_idx)
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

    # Load external content keyed by merge_code (notes, MCQs, descriptive
    # questions live in SessionContent so the Exam doc stays under 16 MB).
    sc = SessionContent.objects(merge_code=sess.merge_code).first() if sess.merge_code else None
    mcqs_src   = sc.mcqs if sc else sess.mcqs
    descs_src  = sc.descriptive_questions if sc else sess.descriptive_questions
    notes_src  = (sc.notes_html if sc and sc.notes_html else sess.notes_html) or ''

    if 'mcq' in allowed and not sess.mcq_locked:
        d['mcqs'] = [{
            'question':        m.question,
            'options':         m.options,
            'answer':          m.answer,
            'explanation':     m.explanation,
            'option_feedback': list(m.option_feedback or []),
            'difficulty':      m.difficulty or '',
            'bloom_level':     m.bloom_level or '',
            'marks':           m.marks or 1,
        } for m in mcqs_src]

    if 'descriptive' in allowed and not sess.descriptive_locked:
        d['descriptive'] = [{
            'question':        dq.question,
            'answer':          dq.answer,
            'marks':           dq.marks or 0,
            'expected_answer': dq.expected_answer or '',
            'key_points':      list(dq.key_points or []),
            'common_traps':    list(dq.common_traps or []),
            'model_solution':  dq.model_solution or '',
            'marking_scheme':  [{'step': s.step, 'marks': s.marks, 'criterion': s.criterion}
                                for s in (dq.marking_scheme or [])],
        } for dq in descs_src]

    if 'notes' in allowed and not sess.notes_locked:
        d['notes_html'] = notes_src
        d['notes_pdf_url'] = cdn_url(sess.notes_pdf_url) if sess.notes_pdf_url else ''

    if 'audio' in allowed and not sess.audio_locked:
        d['audio_url'] = cdn_url(sess.audio_url) if sess.audio_url else ''
        # Per-module podcasts — surface them under audio so audio-tier users get them
        # even when videos aren't in their plan.
        d['audio_modules'] = [{
            'title': v.title,
            'podcast_url': cdn_url(v.podcast_url),
            'podcast_duration': v.podcast_duration,
        } for v in sess.module_videos if v.podcast_url]

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
