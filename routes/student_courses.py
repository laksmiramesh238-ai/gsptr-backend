from datetime import datetime
from flask import Blueprint, jsonify, request
from models.course import Course
from models.enrollment import Enrollment
from routes.student_auth import student_from_token
from utils.cdn import cdn_url

student_courses_bp = Blueprint('student_courses', __name__)


def _chapter_title(ch) -> str:
    if ch.type == 'video'      and ch.video:      return ch.video.title
    if ch.type == 'pdf'        and ch.pdf:        return ch.pdf.title
    if ch.type == 'audio'      and ch.audio:      return ch.audio.title
    if ch.type == 'text'       and ch.text:       return ch.text.title
    if ch.type == 'live_class' and ch.live_class: return ch.live_class.title
    return 'Untitled'


def _chapter_to_dict(ch, include_media: bool) -> dict:
    d = {
        'id':    str(ch.id),
        'type':  ch.type,
        'demo':  ch.demo,
        'title': _chapter_title(ch),
    }
    if not include_media:
        return d

    if ch.type == 'video' and ch.video:
        d['video'] = {
            'video_url': cdn_url(ch.video.video_url),
            'thumbnail': cdn_url(ch.video.thumbnail or ''),
            'duration':  ch.video.duration,
            'professor': ch.video.professor,
            'notes':     ch.video.notes,
        }
    elif ch.type == 'pdf' and ch.pdf:
        d['pdf'] = {'pdf_url': cdn_url(ch.pdf.pdf_url)}
    elif ch.type == 'audio' and ch.audio:
        d['audio'] = {'audio_url': cdn_url(ch.audio.audio_url)}
    elif ch.type == 'text' and ch.text:
        d['text'] = {'text': ch.text.text}
    elif ch.type == 'live_class' and ch.live_class:
        lc = ch.live_class
        d['live_class'] = {
            'start_date': lc.start_date,
            'start_time': lc.start_time,
            'duration':   lc.duration,
            'link':       lc.link,
        }
    return d


# ── list all courses ──────────────────────────────────────────────────────────

@student_courses_bp.route('', methods=['GET'])
def list_courses():
    courses = Course.objects.all()
    result = []
    for c in courses:
        result.append({
            'id':             str(c.id),
            'course_id':      c.course_id,
            'name':           c.name,
            'thumbnail_url':  cdn_url(c.thumbnail_url or ''),
            'price':          str(c.price),
            'whole_duration': c.whole_duration,
            'topics':         c.topics,
            'professors':     c.professors,
            'chapter_count':  len(c.chapters),
        })
    return jsonify({'ok': True, 'courses': result})


# ── course detail with chapters ───────────────────────────────────────────────

@student_courses_bp.route('/<course_id>', methods=['GET'])
def course_detail(course_id):
    course = Course.objects(course_id=course_id).first()
    if not course:
        return jsonify({'ok': False, 'error': 'Course not found'}), 404

    # check enrollment — enrolled students get all media
    enrolled = False
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        student = student_from_token(auth.split(' ', 1)[1])
        if student:
            e = Enrollment.objects(student=student, course=course, status='paid').first()
            if e and e.expires_at > datetime.utcnow():
                enrolled = True

    chapters = []
    for ch in course.chapters:
        include_media = enrolled or ch.demo
        chapters.append(_chapter_to_dict(ch, include_media=include_media))

    return jsonify({
        'ok': True,
        'enrolled': enrolled,
        'course': {
            'id':             str(course.id),
            'course_id':      course.course_id,
            'name':           course.name,
            'thumbnail_url':  cdn_url(course.thumbnail_url or ''),
            'price':          str(course.price),
            'whole_duration': course.whole_duration,
            'topics':         course.topics,
            'professors':     course.professors,
            'chapters':       chapters,
        },
    })
