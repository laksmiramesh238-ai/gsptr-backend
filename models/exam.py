from mongoengine import (
    Document, EmbeddedDocument, EmbeddedDocumentField, EmbeddedDocumentListField,
    StringField, ListField, ReferenceField, IntField, BooleanField, FloatField
)
import re, uuid


# ── Embedded docs for Session content ────────────────────────────────────────

class MCQQuestion(EmbeddedDocument):
    question        = StringField(required=True)
    options         = ListField(StringField(), required=True)   # 4 option texts
    answer          = IntField(required=True)                   # 0-based index of correct option
    explanation     = StringField(default='')
    # Rich metadata from the new question generator
    option_feedback = ListField(StringField(), default=list)    # parallel array to options (per-option feedback)
    difficulty      = StringField(default='')                   # basic / intermediate / advanced
    bloom_level     = StringField(default='')                   # remember / understand / apply / analyze / ...
    marks           = IntField(default=1)
    concept_id      = StringField(default='')                   # links MCQ to a concept in notes
    qid             = StringField(default='')                   # source-side question id


class MarkingStep(EmbeddedDocument):
    step      = IntField(default=0)
    marks     = FloatField(default=0)
    criterion = StringField(default='')


class DescriptiveQuestion(EmbeddedDocument):
    question         = StringField(required=True)
    answer           = StringField(default='')                  # legacy single-string answer (back-compat)
    # Rich fields from the new question generator
    marks            = IntField(default=2)
    expected_answer  = StringField(default='')
    key_points       = ListField(StringField(), default=list)
    marking_scheme   = EmbeddedDocumentListField(MarkingStep)
    common_traps     = ListField(StringField(), default=list)
    model_solution   = StringField(default='')                  # full step-by-step model answer (markdown)
    concept_id       = StringField(default='')
    qid              = StringField(default='')


class ModuleVideo(EmbeddedDocument):
    title            = StringField(required=True)
    video_url        = StringField(required=True)
    duration         = StringField(default='')
    podcast_url      = StringField(default='')
    podcast_duration = StringField(default='')
    slides_count     = IntField(default=0)


class ExamLiveClass(EmbeddedDocument):
    title       = StringField(required=True)
    description = StringField(default='')
    date        = StringField(required=True)      # "2026-04-15"
    time        = StringField(required=True)      # "10:00 AM IST"
    join_url    = StringField(default='')


# ── Session ──────────────────────────────────────────────────────────────────

class Session(EmbeddedDocument):
    title  = StringField(required=True)
    merge_code = StringField(default='')          # links to source notes/questions e.g. "ALG-EXP-1"
    locked = BooleanField(default=False)          # lock entire session
    preview = BooleanField(default=False)         # if True, all content is open even without subscription
    # Per-content locks
    notes_locked       = BooleanField(default=False)
    mcq_locked         = BooleanField(default=False)
    descriptive_locked = BooleanField(default=False)
    audio_locked       = BooleanField(default=False)
    video_locked       = BooleanField(default=False)
    live_locked        = BooleanField(default=False)
    # Notes (HTML pasted or PDF)
    notes_html    = StringField(default='')
    notes_pdf_url = StringField(default='')
    # Questions
    mcqs                  = EmbeddedDocumentListField(MCQQuestion)
    descriptive_questions = EmbeddedDocumentListField(DescriptiveQuestion)
    # Audio revision
    audio_url = StringField(default='')
    # Videos
    full_video_url      = StringField(default='')
    full_video_duration = StringField(default='')
    module_videos       = EmbeddedDocumentListField(ModuleVideo)
    # Live classes
    live_classes = EmbeddedDocumentListField(ExamLiveClass)


# ── Subject ──────────────────────────────────────────────────────────────────

class Subject(EmbeddedDocument):
    name     = StringField(required=True)
    locked   = BooleanField(default=False)
    sessions = EmbeddedDocumentListField(Session)


# ── Exam ─────────────────────────────────────────────────────────────────────

class Exam(Document):
    meta = {'collection': 'exams'}

    exam_id        = StringField(unique=True, required=True)
    title          = StringField(required=True)
    locked         = BooleanField(default=False)
    full_form      = StringField(default='')
    description_en = StringField(default='')
    description_kn = StringField(default='')
    thumbnail_url  = StringField(default='')
    subjects       = EmbeddedDocumentListField(Subject)
    assessments    = ListField(ReferenceField('Assessment'))

    @staticmethod
    def generate_exam_id(title: str) -> str:
        slug = re.sub(r'[^a-z0-9]+', '-', title.lower().strip()).strip('-')
        parts = [p for p in slug.split('-') if p][:4]
        base = '-'.join(parts)
        suffix = uuid.uuid4().hex[:6]
        candidate = f"exam-{base}-{suffix}"
        while Exam.objects(exam_id=candidate).first():
            candidate = f"exam-{base}-{uuid.uuid4().hex[:6]}"
        return candidate
