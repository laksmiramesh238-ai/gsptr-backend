import json
import re
import uuid
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, abort
from flask_login import login_required
from models.course import Course
from models.chapter import (
    Chapter, PDFChapter, AudioChapter, TextChapter, VideoChapter, LiveClass
)
from utils.cdn import cdn_url

courses_bp = Blueprint('courses', __name__)


def generate_course_id(name: str) -> str:
    """
    Generate a unique course_id from the course name.
    Pattern: slug of first 4 words + 6-char unique suffix
    e.g. "Advanced Indian History" → "advanced-indian-history-a3f9k2"
    """
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower().strip()).strip('-')
    # keep max 4 words worth
    parts = [p for p in slug.split('-') if p][:4]
    base  = '-'.join(parts)
    suffix = uuid.uuid4().hex[:6]
    candidate = f"{base}-{suffix}"
    # ensure uniqueness (extremely unlikely to collide but safe)
    while Course.objects(course_id=candidate).first():
        candidate = f"{base}-{uuid.uuid4().hex[:6]}"
    return candidate


# ── helpers ─────────────────────────────────────────────────────────────────

def build_chapter(ch_data: dict) -> Chapter:
    ch_type = ch_data.get('type')
    demo = ch_data.get('demo', False)
    chapter = Chapter(type=ch_type, demo=demo)

    if ch_type == 'video':
        v = ch_data.get('video', {})
        chapter.video = VideoChapter(
            title=v['title'],
            video_url=v['video_url'],
            thumbnail=v.get('thumbnail', ''),
            duration=v.get('duration', ''),
            professor=v.get('professor', ''),
            notes=v.get('notes', ''),
        )
    elif ch_type == 'pdf':
        p = ch_data.get('pdf', {})
        chapter.pdf = PDFChapter(title=p['title'], pdf_url=p['pdf_url'])

    elif ch_type == 'audio':
        a = ch_data.get('audio', {})
        chapter.audio = AudioChapter(title=a['title'], audio_url=a['audio_url'])

    elif ch_type == 'text':
        t = ch_data.get('text', {})
        chapter.text = TextChapter(title=t['title'], text=t['text'])

    elif ch_type == 'live_class':
        lc = ch_data.get('live_class', {})
        chapter.live_class = LiveClass(
            title=lc['title'],
            start_date=lc['start_date'],
            start_time=lc['start_time'],
            duration=lc['duration'],
            link=lc.get('link', ''),
        )

    return chapter


def chapter_to_dict(ch: Chapter) -> dict:
    d = {'id': str(ch.id), 'type': ch.type, 'demo': ch.demo}
    if ch.type == 'video' and ch.video:
        d['video'] = {
            'title': ch.video.title,
            'video_url': cdn_url(ch.video.video_url),
            'thumbnail': cdn_url(ch.video.thumbnail or ''),
            'duration': ch.video.duration,
            'professor': ch.video.professor,
            'notes': ch.video.notes,
        }
    elif ch.type == 'pdf' and ch.pdf:
        d['pdf'] = {'title': ch.pdf.title, 'pdf_url': cdn_url(ch.pdf.pdf_url)}
    elif ch.type == 'audio' and ch.audio:
        d['audio'] = {'title': ch.audio.title, 'audio_url': cdn_url(ch.audio.audio_url)}
    elif ch.type == 'text' and ch.text:
        d['text'] = {'title': ch.text.title, 'text': ch.text.text}
    elif ch.type == 'live_class' and ch.live_class:
        lc = ch.live_class
        d['live_class'] = {
            'title': lc.title, 'start_date': lc.start_date,
            'start_time': lc.start_time, 'duration': lc.duration, 'link': lc.link,
        }
    return d


# ── list ────────────────────────────────────────────────────────────────────

@courses_bp.route('/')
@login_required
def list_courses():
    courses = Course.objects.all()
    return render_template('admin/courses/list.html', courses=courses)


# ── add ─────────────────────────────────────────────────────────────────────

@courses_bp.route('/add', methods=['GET'])
@login_required
def add_course():
    return render_template('admin/courses/form.html', course=None, chapters_json='[]')


@courses_bp.route('/add', methods=['POST'])
@login_required
def add_course_post():
    try:
        data = request.get_json(force=True)

        # build + save chapters first
        saved_chapters = []
        for ch_data in data.get('chapters', []):
            ch = build_chapter(ch_data)
            ch.save()
            saved_chapters.append(ch)

        topics = [t.strip() for t in data.get('topics', '').split(',') if t.strip()]
        professors = [p.strip() for p in data.get('professors', '').split(',') if p.strip()]

        course = Course(
            name=data['name'],
            course_id=generate_course_id(data['name']),
            price=data['price'],
            whole_duration=data.get('whole_duration', '0'),
            topics=topics,
            professors=professors,
            thumbnail_url=data.get('thumbnail_url', ''),
            chapters=saved_chapters,
        )
        course.save()
        return jsonify({'ok': True, 'id': str(course.id)})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


# ── edit ────────────────────────────────────────────────────────────────────

@courses_bp.route('/<course_id>/edit', methods=['GET'])
@login_required
def edit_course(course_id):
    course = Course.objects(id=course_id).first()
    if not course:
        abort(404)
    chapters = [chapter_to_dict(c) for c in course.chapters]
    return render_template(
        'admin/courses/form.html',
        course=course,
        chapters_json=json.dumps(chapters),
    )


@courses_bp.route('/<course_id>/edit', methods=['POST'])
@login_required
def edit_course_post(course_id):
    try:
        course = Course.objects(id=course_id).first()
        if not course:
            return jsonify({'ok': False, 'error': 'Course not found'}), 404
        data = request.get_json(force=True)

        # delete old chapters, replace with new
        for old_ch in course.chapters:
            old_ch.delete()

        saved_chapters = []
        for ch_data in data.get('chapters', []):
            ch = build_chapter(ch_data)
            ch.save()
            saved_chapters.append(ch)

        topics = [t.strip() for t in data.get('topics', '').split(',') if t.strip()]
        professors = [p.strip() for p in data.get('professors', '').split(',') if p.strip()]

        course.update(
            name=data['name'],
            course_id=data['course_id'],
            price=data['price'],
            whole_duration=data.get('whole_duration', '0'),
            topics=topics,
            professors=professors,
            thumbnail_url=data.get('thumbnail_url', ''),
            chapters=saved_chapters,
        )
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


# ── delete ──────────────────────────────────────────────────────────────────

@courses_bp.route('/<course_id>/delete', methods=['POST'])
@login_required
def delete_course(course_id):
    course = Course.objects(id=course_id).first()
    if not course:
        abort(404)
    for ch in course.chapters:
        ch.delete()
    course.delete()
    flash('Course deleted.', 'success')
    return redirect(url_for('courses.list_courses'))
