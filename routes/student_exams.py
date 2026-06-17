from datetime import datetime
import time
from threading import Lock
from flask import Blueprint, jsonify, request
from models.exam import Exam
from models.exam_enrollment import ExamEnrollment, EXAM_TIERS
from models.session_content import SessionContent
from routes.student_auth import student_from_token
from utils.cdn import cdn_url


# ── Server-side TTL cache ────────────────────────────────────────────────────
# Cache hot read endpoints in-process so we avoid hammering Mongo from
# Railway every time. Per-process — fine for our single-worker setup.
# Bust via _bust_cache(prefix) when content changes.

_cache: dict = {}
_cache_lock = Lock()

def _cache_get(key, max_age_s):
    with _cache_lock:
        e = _cache.get(key)
    if not e: return None
    if time.time() - e[1] > max_age_s: return None
    return e[0]

def _cache_put(key, value):
    with _cache_lock:
        _cache[key] = (value, time.time())

def _bust_cache(prefix=None):
    with _cache_lock:
        if prefix is None:
            _cache.clear()
        else:
            for k in list(_cache.keys()):
                if k.startswith(prefix):
                    _cache.pop(k, None)

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
    cached = _cache_get('list_exams', 300)
    if cached is not None:
        return jsonify(cached)
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
    payload = {'ok': True, 'exams': result}
    _cache_put('list_exams', payload)
    return jsonify(payload)


# ── exam detail ───────────────────────────────────────────────────────────────

@student_exams_bp.route('/<exam_id>', methods=['GET'])
def exam_detail(exam_id):
    """Slim exam detail — only what the exam landing page renders.

    Subject summaries are computed via Mongo aggregation so we never pull
    the heavy embedded session arrays across the network. The exam-level
    payload is cached server-side; per-user `tier` is added on top.
    """
    cache_key = f'exam_detail:{exam_id}'
    cached = _cache_get(cache_key, 300)
    if cached is not None:
        student = _get_student()
        tier = _get_tier(student, Exam(id=cached['_exam_oid'])) if student else 0
        out = {**cached['payload']}
        out['tier'] = tier
        return jsonify(out)

    coll = Exam._get_collection()
    pipeline = [
        {'$match': {'exam_id': exam_id}},
        {'$project': {
            'exam_id': 1, 'title': 1, 'full_form': 1,
            'description_en': 1, 'description_kn': 1,
            'thumbnail_url': 1, 'locked': 1,
            'subjects': {
                '$map': {
                    'input': {'$ifNull': ['$subjects', []]},
                    'as': 's',
                    'in': {
                        'name':   '$$s.name',
                        'locked': '$$s.locked',
                        'session_count': {'$size': {'$ifNull': ['$$s.sessions', []]}},
                        'preview_count': {'$size': {
                            '$filter': {
                                'input': {'$ifNull': ['$$s.sessions', []]},
                                'as': 'x',
                                'cond': {'$eq': ['$$x.preview', True]},
                            }
                        }},
                        'locked_count': {'$size': {
                            '$filter': {
                                'input': {'$ifNull': ['$$s.sessions', []]},
                                'as': 'x',
                                'cond': {'$eq': ['$$x.locked', True]},
                            }
                        }},
                    },
                }
            },
            'assessments': 1,   # ObjectId refs only — small
        }},
    ]
    docs = list(coll.aggregate(pipeline))
    if not docs:
        return jsonify({'ok': False, 'error': 'Exam not found'}), 404
    doc = docs[0]

    # Tier requires a real Exam ref for the enrollment query
    student = _get_student()
    if student:
        e_ref = Exam(id=doc['_id'])
        tier = _get_tier(student, e_ref)
    else:
        tier = 0

    # Resolve assessment refs only when needed (small projection)
    assessments = []
    a_ids = doc.get('assessments') or []
    if a_ids:
        from models.assessment import Assessment
        a_coll = Assessment._get_collection()
        for a in a_coll.find(
            {'_id': {'$in': a_ids}},
            {'title': 1, 'subject_filter': 1, 'topic_filter': 1,
             'session_filter': 1, 'questions': 1, 'duration_minutes': 1},
        ):
            assessments.append({
                'id':             str(a['_id']),
                'title':          a.get('title', ''),
                'subject_filter': a.get('subject_filter', ''),
                'topic_filter':   a.get('topic_filter', ''),
                'session_filter': a.get('session_filter', ''),
                'question_count': len(a.get('questions') or []),
                'duration':       a.get('duration_minutes', 0),
            })

    subjects = doc.get('subjects', [])

    payload = {
        'ok': True,
        'tier': tier,            # overwritten on cache hits with the user's actual tier
        'tiers': EXAM_TIERS,
        'exam': {
            'id':             str(doc['_id']),
            'exam_id':        doc.get('exam_id', ''),
            'title':          doc.get('title', ''),
            'locked':         bool(doc.get('locked', False)),
            'full_form':      doc.get('full_form', ''),
            'description_en': doc.get('description_en', ''),
            'description_kn': doc.get('description_kn', ''),
            'thumbnail_url':  cdn_url(doc.get('thumbnail_url') or ''),
            'subjects':       subjects,
            'assessments':    assessments,
        },
    }
    _cache_put(cache_key, {'_exam_oid': doc['_id'], 'payload': payload})
    return jsonify(payload)


# ── one subject's session list (lightweight; for subject page) ────────────────

@student_exams_bp.route('/<exam_id>/subject/<int:sub_idx>', methods=['GET'])
def subject_detail(exam_id, sub_idx):
    """Slice a single subject out of the exam at the Mongo level so we never
    transfer the other subjects' sessions across the network. Cached per
    (exam, subject_idx, tier)."""
    student = _get_student()
    # Resolve tier without a fresh Mongo query when possible
    tier_key_cache = _cache_get(f'tier:{exam_id}:{student.id if student else "anon"}', 60)
    if tier_key_cache is not None:
        tier = tier_key_cache
    else:
        # Need exam id from cache or fetch later; defer
        tier = None

    cache_key = f'subject:{exam_id}:{sub_idx}:t{tier if tier is not None else "?"}'
    if tier is not None:
        cached = _cache_get(cache_key, 180)
        if cached is not None:
            return jsonify(cached)

    coll = Exam._get_collection()
    pipeline = [
        {'$match': {'exam_id': exam_id}},
        {'$project': {
            '_id': 1,
            'subjects_count': {'$size': {'$ifNull': ['$subjects', []]}},
            'subject': {'$arrayElemAt': [{'$ifNull': ['$subjects', []]}, sub_idx]},
        }},
    ]
    docs = list(coll.aggregate(pipeline))
    if not docs:
        return jsonify({'ok': False, 'error': 'Exam not found'}), 404
    doc = docs[0]
    sub = doc.get('subject')
    if not sub:
        return jsonify({'ok': False, 'error': 'Subject not found'}), 404

    # Tier needs an Exam ref (id only is enough for the enrollment query)
    if tier is None:
        tier = _get_tier(student, Exam(id=doc['_id'])) if student else 0
        _cache_put(f'tier:{exam_id}:{student.id if student else "anon"}', tier)
        # Re-key the cache and check (in case a parallel request filled it)
        cache_key = f'subject:{exam_id}:{sub_idx}:t{tier}'
        cached = _cache_get(cache_key, 180)
        if cached is not None:
            return jsonify(cached)

    raw_sessions = sub.get('sessions') or []

    # Build content_idx via aggregation (counts only, no body data)
    merge_codes = [s.get('merge_code') for s in raw_sessions if s.get('merge_code')]
    content_idx = _bulk_session_content_stats(merge_codes) if merge_codes else {}

    allowed_for_tier = EXAM_TIERS.get(tier, {}).get('includes', []) if tier > 0 else []
    top_includes = EXAM_TIERS[max(EXAM_TIERS.keys())]['includes']

    sessions = []
    for s in raw_sessions:
        is_preview = bool(s.get('preview', False))
        allowed = top_includes if is_preview else allowed_for_tier
        ext = content_idx.get(s.get('merge_code'))
        mcq_count  = ext['mcq_count']  if ext else len(s.get('mcqs') or [])
        desc_count = ext['desc_count'] if ext else len(s.get('descriptive_questions') or [])
        has_notes  = (ext['has_notes'] if ext else bool(s.get('notes_html'))) or bool(s.get('notes_pdf_url'))
        d: dict = {
            'title':   s.get('title', ''),
            'preview': is_preview,
            'locked':  bool(s.get('locked', False)),
        }
        if 'mcq' in allowed:         d['mcq_count']         = mcq_count
        if 'descriptive' in allowed: d['descriptive_count'] = desc_count
        if 'notes' in allowed:       d['has_notes']         = has_notes
        if 'audio' in allowed:
            d['has_audio'] = bool(s.get('audio_url')) or any(
                v.get('podcast_url') for v in (s.get('module_videos') or [])
            )
        if 'videos' in allowed:
            d['has_video']           = bool(s.get('full_video_url'))
            d['module_video_count']  = len(s.get('module_videos') or [])
        if 'live_classes' in allowed:
            d['live_class_count'] = len(s.get('live_classes') or [])
        sessions.append(d)

    payload = {
        'ok': True,
        'tier': tier,
        'subject': {
            'name':     sub.get('name', ''),
            'locked':   bool(sub.get('locked', False)),
            'sessions': sessions,
        },
    }
    _cache_put(cache_key, payload)
    return jsonify(payload)


def _bulk_session_content_stats(codes):
    """Same as _content_index but takes a list of codes directly."""
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
    for d in coll.aggregate(pipeline):
        out[d['merge_code']] = {
            'mcq_count':  d.get('mcq_count', 0),
            'desc_count': d.get('desc_count', 0),
            'has_notes':  bool(d.get('has_notes', False)),
        }
    return out


# ── session content (full data for enrolled students) ─────────────────────────

@student_exams_bp.route('/<exam_id>/subject/<int:sub_idx>/session/<int:sess_idx>', methods=['GET'])
def session_content(exam_id, sub_idx, sess_idx):
    """Use aggregation to fetch only one session — never pull the 700KB exam doc."""
    from mongoengine.connection import get_db
    pipeline = [
        {'$match': {'exam_id': exam_id}},
        {'$project': {
            '_id': 1,
            'subject': {'$arrayElemAt': ['$subjects', sub_idx]},
            'sub_count': {'$size': {'$ifNull': ['$subjects', []]}},
        }},
        {'$project': {
            '_id': 1,
            'sub_count': 1,
            'subject_name':   '$subject.name',
            'subject_locked': '$subject.locked',
            'sess_count':     {'$size': {'$ifNull': ['$subject.sessions', []]}},
            'session':        {'$arrayElemAt': ['$subject.sessions', sess_idx]},
        }},
    ]
    rows = list(get_db()['exams'].aggregate(pipeline))
    if not rows:
        return jsonify({'ok': False, 'error': 'Exam not found'}), 404
    row = rows[0]
    if sub_idx >= row.get('sub_count', 0) or row.get('subject_name') is None:
        return jsonify({'ok': False, 'error': 'Subject not found'}), 404
    if sess_idx >= row.get('sess_count', 0) or not row.get('session'):
        return jsonify({'ok': False, 'error': 'Session not found'}), 404

    sess = row['session']
    sub_locked   = row.get('subject_locked', False)
    subject_name = row['subject_name']
    exam_oid     = row['_id']

    student = _get_student()
    # Tier lookup: query ExamEnrollment by raw ObjectId (avoids loading Exam doc).
    tier = 0
    if student:
        e = ExamEnrollment.objects(student=student, exam=exam_oid, status='paid').first()
        if e and e.expires_at > datetime.utcnow():
            tier = e.tier

    is_preview = bool(sess.get('preview', False))

    if not is_preview and tier == 0:
        return jsonify({'ok': False, 'error': 'Not enrolled'}), 403

    if sub_locked or sess.get('locked'):
        return jsonify({'ok': False, 'error': 'This content is locked'}), 403

    if is_preview:
        allowed = EXAM_TIERS[max(EXAM_TIERS.keys())]['includes']
    else:
        allowed = EXAM_TIERS[tier]['includes']

    d = {
        'title':              sess.get('title', ''),
        'subject':            subject_name,
        'preview':            is_preview,
        'notes_locked':       sess.get('notes_locked', False),
        'mcq_locked':         sess.get('mcq_locked', False),
        'descriptive_locked': sess.get('descriptive_locked', False),
        'audio_locked':       sess.get('audio_locked', False),
        'video_locked':       sess.get('video_locked', False),
        'live_locked':        sess.get('live_locked', False),
    }

    merge_code = sess.get('merge_code') or ''
    sc = SessionContent.objects(merge_code=merge_code).first() if merge_code else None
    mcqs_src  = (sc.mcqs if sc else sess.get('mcqs') or [])
    descs_src = (sc.descriptive_questions if sc else sess.get('descriptive_questions') or [])
    notes_src = (sc.notes_html if sc and sc.notes_html else sess.get('notes_html')) or ''

    def _attr(o, k, default=None):
        # MCQs/descriptive can come from SessionContent (mongoengine objects) or raw dicts.
        return getattr(o, k, default) if not isinstance(o, dict) else o.get(k, default)

    if 'mcq' in allowed and not d['mcq_locked']:
        d['mcqs'] = [{
            'question':        _attr(m, 'question'),
            'options':         _attr(m, 'options'),
            'answer':          _attr(m, 'answer'),
            'explanation':     _attr(m, 'explanation'),
            'option_feedback': list(_attr(m, 'option_feedback') or []),
            'difficulty':      _attr(m, 'difficulty') or '',
            'bloom_level':     _attr(m, 'bloom_level') or '',
            'marks':           _attr(m, 'marks') or 1,
        } for m in mcqs_src]

    if 'descriptive' in allowed and not d['descriptive_locked']:
        d['descriptive'] = [{
            'question':        _attr(dq, 'question'),
            'answer':          _attr(dq, 'answer'),
            'marks':           _attr(dq, 'marks') or 0,
            'expected_answer': _attr(dq, 'expected_answer') or '',
            'key_points':      list(_attr(dq, 'key_points') or []),
            'common_traps':    list(_attr(dq, 'common_traps') or []),
            'model_solution':  _attr(dq, 'model_solution') or '',
            'marking_scheme':  [{
                'step':      _attr(s, 'step'),
                'marks':     _attr(s, 'marks'),
                'criterion': _attr(s, 'criterion'),
            } for s in (_attr(dq, 'marking_scheme') or [])],
        } for dq in descs_src]

    if 'notes' in allowed and not d['notes_locked']:
        d['notes_html']    = notes_src
        d['notes_pdf_url'] = cdn_url(sess.get('notes_pdf_url')) if sess.get('notes_pdf_url') else ''

    if 'audio' in allowed and not d['audio_locked']:
        d['audio_url'] = cdn_url(sess.get('audio_url')) if sess.get('audio_url') else ''
        d['audio_modules'] = [{
            'title':            v.get('title'),
            'podcast_url':      cdn_url(v.get('podcast_url')),
            'podcast_duration': v.get('podcast_duration'),
        } for v in (sess.get('module_videos') or []) if v.get('podcast_url')]

    if 'videos' in allowed and not d['video_locked']:
        d['full_video_url']      = cdn_url(sess.get('full_video_url')) if sess.get('full_video_url') else ''
        d['full_video_duration'] = sess.get('full_video_duration')
        d['module_videos'] = [{
            'title':            v.get('title'),
            'video_url':        cdn_url(v.get('video_url')),
            'duration':         v.get('duration'),
            'podcast_url':      cdn_url(v.get('podcast_url')) if v.get('podcast_url') else '',
            'podcast_duration': v.get('podcast_duration'),
            'slides_count':     v.get('slides_count'),
        } for v in (sess.get('module_videos') or [])]

    if 'live_classes' in allowed and not d['live_locked']:
        d['live_classes'] = [{
            'title':       lc.get('title'),
            'description': lc.get('description'),
            'date':        lc.get('date'),
            'time':        lc.get('time'),
            'join_url':    lc.get('join_url'),
        } for lc in (sess.get('live_classes') or [])]

    # Offline download is a tier-5 perk ('offline' in includes) and is only
    # granted to genuinely paid enrollments — never for free preview sessions.
    offline_allowed = ('offline' in allowed) and tier >= 1

    return jsonify({
        'ok': True, 'session': d, 'tier': tier,
        'allowed': allowed, 'offline_allowed': offline_allowed,
    })
