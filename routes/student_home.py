"""
Curated home-screen payload — featured exam(s), top courses, quick stats.
One round-trip for everything the home tab needs.

Cached server-side (3 min) to avoid hammering Mongo.
"""

import time
from threading import Lock
from flask import Blueprint, jsonify

from models.exam import Exam
from models.course import Course
from utils.cdn import cdn_url

student_home_bp = Blueprint('student_home', __name__)

_cache = {}
_lock = Lock()
_TTL = 180  # 3 minutes


def _cache_get(key):
    with _lock:
        e = _cache.get(key)
    if not e: return None
    if time.time() - e[1] > _TTL: return None
    return e[0]


def _cache_put(key, value):
    with _lock:
        _cache[key] = (value, time.time())


@student_home_bp.route('', methods=['GET'])
def home():
    cached = _cache_get('home')
    if cached is not None:
        return jsonify(cached)

    # ── Featured exam (the newest / first) ───────────────────────────────────
    exam_coll = Exam._get_collection()
    exams_pipeline = [
        {'$project': {
            'exam_id': 1, 'title': 1, 'full_form': 1,
            'description_en': 1, 'thumbnail_url': 1, 'locked': 1,
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
    exams_raw = list(exam_coll.aggregate(exams_pipeline))
    exams = []
    for e in exams_raw:
        exams.append({
            'id':             str(e['_id']),
            'exam_id':        e.get('exam_id', ''),
            'title':          e.get('title', ''),
            'full_form':      e.get('full_form', ''),
            'description_en': e.get('description_en', ''),
            'thumbnail_url':  cdn_url(e.get('thumbnail_url') or ''),
            'locked':         bool(e.get('locked', False)),
            'subject_count':  e.get('subject_count', 0),
            'session_count':  e.get('session_count', 0),
        })
    featured_exam = exams[0] if exams else None

    # ── Top courses (first 2) ────────────────────────────────────────────────
    course_coll = Course._get_collection()
    courses_raw = list(course_coll.find(
        {},
        {'course_id': 1, 'name': 1, 'thumbnail_url': 1, 'price': 1,
         'whole_duration': 1, 'topics': 1, 'professors': 1, 'chapters': 1},
    ).limit(2))
    courses = []
    for c in courses_raw:
        courses.append({
            'id':             str(c['_id']),
            'course_id':      c.get('course_id', ''),
            'name':           c.get('name', ''),
            'thumbnail_url':  cdn_url(c.get('thumbnail_url') or ''),
            'price':          str(c.get('price', '')),
            'whole_duration': c.get('whole_duration', ''),
            'topics':         (c.get('topics') or [])[:3],
            'professors':     c.get('professors', []),
            'chapter_count':  len(c.get('chapters') or []),
        })

    # ── Quick stats ──────────────────────────────────────────────────────────
    stats = {
        'exam_count':    len(exams),
        'course_count':  course_coll.count_documents({}),
        'subject_count': sum(e.get('subject_count', 0) for e in exams_raw),
        'session_count': sum(e.get('session_count', 0) for e in exams_raw),
    }

    payload = {
        'ok': True,
        'featured_exam': featured_exam,
        'exams':         exams[:3],
        'courses':       courses,
        'stats':         stats,
        'academy': {
            'name':       'Srinivas IAS Academy',
            'tagline':    'Bengaluru · Coaching for Government Exams',
        },
    }
    _cache_put('home', payload)
    return jsonify(payload)
