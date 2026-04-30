import json
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, abort
from flask_login import login_required
from models.exam import (
    Exam, Subject, Session, MCQQuestion, DescriptiveQuestion,
    ModuleVideo, ExamLiveClass,
)
from models.assessment import Assessment, AssessmentQuestion

exam_admin_bp = Blueprint('exam_admin', __name__)


# ── helpers ──────────────────────────────────────────────────────────────────

def _build_session(sd):
    sess = Session(title=sd.get('title', 'Untitled'))
    sess.locked = bool(sd.get('locked', False))
    sess.preview = bool(sd.get('preview', False))
    sess.notes_locked = bool(sd.get('notes_locked', False))
    sess.mcq_locked = bool(sd.get('mcq_locked', False))
    sess.descriptive_locked = bool(sd.get('descriptive_locked', False))
    sess.audio_locked = bool(sd.get('audio_locked', False))
    sess.video_locked = bool(sd.get('video_locked', False))
    sess.live_locked = bool(sd.get('live_locked', False))
    sess.notes_html = sd.get('notes_html', '')
    sess.notes_pdf_url = sd.get('notes_pdf_url', '')
    sess.audio_url = sd.get('audio_url', '')
    sess.full_video_url = sd.get('full_video_url', '')
    sess.full_video_duration = sd.get('full_video_duration', '')

    for m in sd.get('mcqs', []):
        sess.mcqs.append(MCQQuestion(
            question=m['question'], options=m.get('options', []),
            answer=int(m.get('answer', 0)), explanation=m.get('explanation', ''),
        ))
    for d in sd.get('descriptive_questions', []):
        sess.descriptive_questions.append(DescriptiveQuestion(
            question=d['question'], answer=d['answer'],
        ))
    for v in sd.get('module_videos', []):
        sess.module_videos.append(ModuleVideo(
            title=v['title'], video_url=v['video_url'], duration=v.get('duration', ''),
        ))
    for lc in sd.get('live_classes', []):
        sess.live_classes.append(ExamLiveClass(
            title=lc['title'], description=lc.get('description', ''),
            date=lc['date'], time=lc['time'], join_url=lc.get('join_url', ''),
        ))
    return sess


def _build_subjects(subjects_data):
    subjects = []
    for sd in subjects_data:
        sub = Subject(name=sd['name'], locked=bool(sd.get('locked', False)))
        for sess_data in sd.get('sessions', []):
            sub.sessions.append(_build_session(sess_data))
        subjects.append(sub)
    return subjects


def _exam_to_json(exam):
    subjects = []
    for sub in exam.subjects:
        sessions = []
        for sess in sub.sessions:
            sessions.append({
                'title': sess.title,
                'locked': sess.locked,
                'notes_locked': sess.notes_locked,
                'mcq_locked': sess.mcq_locked,
                'descriptive_locked': sess.descriptive_locked,
                'audio_locked': sess.audio_locked,
                'video_locked': sess.video_locked,
                'live_locked': sess.live_locked,
                'notes_html': sess.notes_html,
                'notes_pdf_url': sess.notes_pdf_url,
                'audio_url': sess.audio_url,
                'full_video_url': sess.full_video_url,
                'full_video_duration': sess.full_video_duration,
                'mcqs': [{'question': m.question, 'options': m.options,
                          'answer': m.answer, 'explanation': m.explanation} for m in sess.mcqs],
                'descriptive_questions': [{'question': d.question, 'answer': d.answer}
                                          for d in sess.descriptive_questions],
                'module_videos': [{'title': v.title, 'video_url': v.video_url, 'duration': v.duration}
                                   for v in sess.module_videos],
                'live_classes': [{'title': lc.title, 'description': lc.description,
                                  'date': lc.date, 'time': lc.time, 'join_url': lc.join_url}
                                  for lc in sess.live_classes],
            })
        subjects.append({'name': sub.name, 'locked': sub.locked, 'sessions': sessions})
    return subjects


# ── list ─────────────────────────────────────────────────────────────────────

def _session_to_json(sess):
    return {
        'title': sess.title,
        'locked': sess.locked,
        'preview': sess.preview,
        'notes_locked': sess.notes_locked,
        'mcq_locked': sess.mcq_locked,
        'descriptive_locked': sess.descriptive_locked,
        'audio_locked': sess.audio_locked,
        'video_locked': sess.video_locked,
        'live_locked': sess.live_locked,
        'notes_html': sess.notes_html,
        'notes_pdf_url': sess.notes_pdf_url,
        'audio_url': sess.audio_url,
        'full_video_url': sess.full_video_url,
        'full_video_duration': sess.full_video_duration,
        'mcqs': [{'question': m.question, 'options': m.options,
                  'answer': m.answer, 'explanation': m.explanation} for m in sess.mcqs],
        'descriptive_questions': [{'question': d.question, 'answer': d.answer}
                                  for d in sess.descriptive_questions],
        'module_videos': [{'title': v.title, 'video_url': v.video_url, 'duration': v.duration}
                           for v in sess.module_videos],
        'live_classes': [{'title': lc.title, 'description': lc.description,
                          'date': lc.date, 'time': lc.time, 'join_url': lc.join_url}
                          for lc in sess.live_classes],
    }


@exam_admin_bp.route('/')
@login_required
def list_exams():
    exams = Exam.objects.all()
    return render_template('admin/exams/list.html', exams=exams)


# ── add ──────────────────────────────────────────────────────────────────────

@exam_admin_bp.route('/add', methods=['GET'])
@login_required
def add_exam():
    return render_template('admin/exams/form.html', exam=None, subjects_json='[]')


@exam_admin_bp.route('/add', methods=['POST'])
@login_required
def add_exam_post():
    try:
        data = request.get_json(force=True)
        subjects = _build_subjects(data.get('subjects', []))

        exam = Exam(
            title=data['title'],
            exam_id=Exam.generate_exam_id(data['title']),
            locked=bool(data.get('locked', False)),
            full_form=data.get('full_form', ''),
            description_en=data.get('description_en', ''),
            description_kn=data.get('description_kn', ''),
            thumbnail_url=data.get('thumbnail_url', ''),
            subjects=subjects,
        )
        exam.save()
        return jsonify({'ok': True, 'id': str(exam.id)})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


# ── edit ─────────────────────────────────────────────────────────────────────

@exam_admin_bp.route('/<exam_id>/edit', methods=['GET'])
@login_required
def edit_exam(exam_id):
    exam = Exam.objects(id=exam_id).first()
    if not exam:
        abort(404)
    subjects_json = json.dumps(_exam_to_json(exam))
    return render_template('admin/exams/form.html', exam=exam, subjects_json=subjects_json)


@exam_admin_bp.route('/<exam_id>/edit', methods=['POST'])
@login_required
def edit_exam_post(exam_id):
    try:
        exam = Exam.objects(id=exam_id).first()
        if not exam:
            return jsonify({'ok': False, 'error': 'Not found'}), 404
        data = request.get_json(force=True)
        subjects = _build_subjects(data.get('subjects', []))

        exam.update(
            title=data['title'],
            locked=bool(data.get('locked', False)),
            full_form=data.get('full_form', ''),
            description_en=data.get('description_en', ''),
            description_kn=data.get('description_kn', ''),
            thumbnail_url=data.get('thumbnail_url', ''),
            subjects=subjects,
        )
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


# ── delete ───────────────────────────────────────────────────────────────────

@exam_admin_bp.route('/<exam_id>/delete', methods=['POST'])
@login_required
def delete_exam(exam_id):
    exam = Exam.objects(id=exam_id).first()
    if not exam:
        abort(404)
    Assessment.objects(exam=exam).delete()
    exam.delete()
    flash('Exam deleted.', 'success')
    return redirect(url_for('exam_admin.list_exams'))


# ── assessment CRUD ──────────────────────────────────────────────────────────

@exam_admin_bp.route('/<exam_id>/assessments')
@login_required
def list_assessments(exam_id):
    exam = Exam.objects(id=exam_id).first()
    if not exam:
        abort(404)
    assessments = Assessment.objects(exam=exam)
    return render_template('admin/exams/assessments/list.html', exam=exam, assessments=assessments)


@exam_admin_bp.route('/<exam_id>/assessments/add', methods=['GET'])
@login_required
def add_assessment(exam_id):
    exam = Exam.objects(id=exam_id).first()
    if not exam:
        abort(404)
    return render_template('admin/exams/assessments/form.html', exam=exam, assessment=None, questions_json='[]')


@exam_admin_bp.route('/<exam_id>/assessments/add', methods=['POST'])
@login_required
def add_assessment_post(exam_id):
    try:
        exam = Exam.objects(id=exam_id).first()
        if not exam:
            return jsonify({'ok': False, 'error': 'Exam not found'}), 404
        data = request.get_json(force=True)

        questions = []
        for q in data.get('questions', []):
            questions.append(AssessmentQuestion(
                question=q['question'], options=q.get('options', []),
                answer=int(q.get('answer', 0)), explanation=q.get('explanation', ''),
            ))

        assessment = Assessment(
            exam=exam,
            title=data['title'],
            subject_filter=data.get('subject_filter', ''),
            topic_filter=data.get('topic_filter', ''),
            session_filter=data.get('session_filter', ''),
            duration_minutes=int(data.get('duration_minutes', 60)),
            questions=questions,
        )
        assessment.save()

        exam.update(push__assessments=assessment)
        return jsonify({'ok': True, 'id': str(assessment.id)})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


@exam_admin_bp.route('/<exam_id>/assessments/<assessment_id>/edit', methods=['GET'])
@login_required
def edit_assessment(exam_id, assessment_id):
    exam = Exam.objects(id=exam_id).first()
    if not exam:
        abort(404)
    assessment = Assessment.objects(id=assessment_id).first()
    if not assessment:
        abort(404)
    questions_json = json.dumps([{
        'question': q.question, 'options': q.options,
        'answer': q.answer, 'explanation': q.explanation,
    } for q in assessment.questions])
    return render_template('admin/exams/assessments/form.html', exam=exam, assessment=assessment, questions_json=questions_json)


@exam_admin_bp.route('/<exam_id>/assessments/<assessment_id>/edit', methods=['POST'])
@login_required
def edit_assessment_post(exam_id, assessment_id):
    try:
        assessment = Assessment.objects(id=assessment_id).first()
        if not assessment:
            return jsonify({'ok': False, 'error': 'Not found'}), 404
        data = request.get_json(force=True)

        questions = []
        for q in data.get('questions', []):
            questions.append(AssessmentQuestion(
                question=q['question'], options=q.get('options', []),
                answer=int(q.get('answer', 0)), explanation=q.get('explanation', ''),
            ))

        assessment.update(
            title=data['title'],
            subject_filter=data.get('subject_filter', ''),
            topic_filter=data.get('topic_filter', ''),
            session_filter=data.get('session_filter', ''),
            duration_minutes=int(data.get('duration_minutes', 60)),
            questions=questions,
        )
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


@exam_admin_bp.route('/<exam_id>/assessments/<assessment_id>/delete', methods=['POST'])
@login_required
def delete_assessment(exam_id, assessment_id):
    exam = Exam.objects(id=exam_id).first()
    assessment = Assessment.objects(id=assessment_id).first()
    if assessment:
        exam.update(pull__assessments=assessment)
        assessment.delete()
    flash('Assessment deleted.', 'success')
    return redirect(url_for('exam_admin.list_assessments', exam_id=exam_id))


# ── session CRUD ─────────────────────────────────────────────────────────────

@exam_admin_bp.route('/<exam_id>/subjects/<int:sub_idx>/sessions')
@login_required
def list_sessions(exam_id, sub_idx):
    exam = Exam.objects(id=exam_id).first()
    if not exam or sub_idx >= len(exam.subjects):
        abort(404)
    subject = exam.subjects[sub_idx]
    return render_template('admin/exams/sessions/list.html',
                           exam=exam, subject=subject, sub_idx=sub_idx)


@exam_admin_bp.route('/<exam_id>/subjects/<int:sub_idx>/sessions/add', methods=['GET'])
@login_required
def add_session_page(exam_id, sub_idx):
    exam = Exam.objects(id=exam_id).first()
    if not exam or sub_idx >= len(exam.subjects):
        abort(404)
    return render_template('admin/exams/sessions/form.html',
                           exam=exam, sub_idx=sub_idx,
                           sess_idx=None, session_json='{}')


@exam_admin_bp.route('/<exam_id>/subjects/<int:sub_idx>/sessions/add', methods=['POST'])
@login_required
def add_session_post(exam_id, sub_idx):
    try:
        exam = Exam.objects(id=exam_id).first()
        if not exam or sub_idx >= len(exam.subjects):
            return jsonify({'ok': False, 'error': 'Not found'}), 404
        data = request.get_json(force=True)
        sess = _build_session(data)
        exam.subjects[sub_idx].sessions.append(sess)
        exam.save()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


@exam_admin_bp.route('/<exam_id>/subjects/<int:sub_idx>/sessions/<int:sess_idx>/edit', methods=['GET'])
@login_required
def edit_session_page(exam_id, sub_idx, sess_idx):
    exam = Exam.objects(id=exam_id).first()
    if not exam or sub_idx >= len(exam.subjects):
        abort(404)
    sub = exam.subjects[sub_idx]
    if sess_idx >= len(sub.sessions):
        abort(404)
    return render_template('admin/exams/sessions/form.html',
                           exam=exam, sub_idx=sub_idx, sess_idx=sess_idx,
                           session_json=json.dumps(_session_to_json(sub.sessions[sess_idx])))


@exam_admin_bp.route('/<exam_id>/subjects/<int:sub_idx>/sessions/<int:sess_idx>/edit', methods=['POST'])
@login_required
def edit_session_post(exam_id, sub_idx, sess_idx):
    try:
        exam = Exam.objects(id=exam_id).first()
        if not exam or sub_idx >= len(exam.subjects):
            return jsonify({'ok': False, 'error': 'Not found'}), 404
        sub = exam.subjects[sub_idx]
        if sess_idx >= len(sub.sessions):
            return jsonify({'ok': False, 'error': 'Session not found'}), 404
        data = request.get_json(force=True)
        exam.subjects[sub_idx].sessions[sess_idx] = _build_session(data)
        exam.save()
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 400


@exam_admin_bp.route('/<exam_id>/subjects/<int:sub_idx>/sessions/<int:sess_idx>/delete', methods=['POST'])
@login_required
def delete_session(exam_id, sub_idx, sess_idx):
    exam = Exam.objects(id=exam_id).first()
    if not exam or sub_idx >= len(exam.subjects):
        abort(404)
    sub = exam.subjects[sub_idx]
    if sess_idx >= len(sub.sessions):
        abort(404)
    del exam.subjects[sub_idx].sessions[sess_idx]
    exam.save()
    flash('Session deleted.', 'success')
    return redirect(url_for('exam_admin.list_sessions', exam_id=exam_id, sub_idx=sub_idx))
