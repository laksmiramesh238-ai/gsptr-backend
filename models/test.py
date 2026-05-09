from mongoengine import (
    Document, EmbeddedDocument, EmbeddedDocumentField, EmbeddedDocumentListField,
    StringField, IntField, FloatField, ListField, ReferenceField,
    DateTimeField, DictField,
)
from datetime import datetime
from models.student import Student


class QuestionDetail(EmbeddedDocument):
    """One MCQ inside a test. Same shape as the old project for migration."""
    id              = StringField(required=True)              # unique within test
    question        = StringField(required=True)
    question_image  = StringField(default=None)
    option_a        = DictField(required=True)                # {text, image_url}
    option_b        = DictField(required=True)
    option_c        = DictField(required=True)
    option_d        = DictField(required=True)
    correct_option  = IntField(required=True, min_value=0, max_value=3)
    crt_ans_score   = FloatField(default=3.0)
    wrong_ans_score = FloatField(default=-0.25)

    def to_json(self, include_correct=True):
        data = {
            'id':             str(self.id),
            'question':       self.question,
            'question_image': self.question_image,
            'options': {
                'A': self.option_a,
                'B': self.option_b,
                'C': self.option_c,
                'D': self.option_d,
            },
            'crt_ans_score':   self.crt_ans_score,
            'wrong_ans_score': self.wrong_ans_score,
        }
        if include_correct:
            data['correct_option'] = self.correct_option
        return data


class Response(EmbeddedDocument):
    question_id = StringField(required=True)
    answer      = StringField(required=True)   # "A" | "B" | "C" | "D" | "NA"


class Result(EmbeddedDocument):
    student_id = StringField(required=True)
    responses  = EmbeddedDocumentListField(Response)
    score      = FloatField(default=0)
    status     = IntField(default=-1)          # -1 = in_progress, 1 = submitted
    submitted_at = DateTimeField()

    def to_json(self):
        return {
            'student_id': self.student_id,
            'responses':  [{'question_id': r.question_id, 'answer': r.answer} for r in self.responses],
            'score':      self.score,
            'status':     self.status,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
        }


class Test(Document):
    meta = {'collection': 'tests'}

    name              = StringField(required=True)
    start_date        = DateTimeField(required=True)
    start_time        = StringField(required=True)
    duration          = IntField(required=True)               # minutes
    end_date          = DateTimeField(required=True)
    end_time          = StringField(required=True)
    students_enrolled = ListField(ReferenceField(Student))
    questions         = EmbeddedDocumentListField(QuestionDetail)
    results           = EmbeddedDocumentListField(Result)
    order_index       = IntField(default=0)

    # ── helpers ──
    def get_total_max_score(self):
        return sum(q.crt_ans_score for q in self.questions)

    def get_student_result(self, student_id):
        sid = str(student_id)
        for r in self.results:
            if r.student_id == sid:
                return r
        return None

    def is_student_enrolled(self, student):
        if not student:
            return False
        return any(s and str(s.id) == str(student.id) for s in self.students_enrolled)

    # ── enroll / unenroll ──
    def enroll(self, student):
        if not self.is_student_enrolled(student):
            self.students_enrolled.append(student)
            self.save()
            return True
        return False

    def unenroll(self, student):
        sid = str(student.id)
        self.students_enrolled = [s for s in self.students_enrolled if not (s and str(s.id) == sid)]
        self.results = [r for r in self.results if r.student_id != sid]
        self.save()

    # ── attempt lifecycle ──
    def start_attempt(self, student_id):
        sid = str(student_id)
        existing = self.get_student_result(sid)
        if existing:
            return existing
        r = Result(student_id=sid, responses=[], score=0, status=-1)
        self.results.append(r)
        self.save()
        return r

    def record_result(self, student_id, responses):
        """responses: [{'question_id': '...', 'answer': 'A'|'B'|'C'|'D'|'NA'}, ...]"""
        sid = str(student_id)
        score = 0.0
        rdocs = []
        opt_letter = ['A', 'B', 'C', 'D']
        for r in responses:
            qid = r.get('question_id')
            ans = r.get('answer', 'NA')
            q = next((qq for qq in self.questions if qq.id == qid), None)
            if q:
                if ans == 'NA':
                    pass
                elif ans == opt_letter[q.correct_option]:
                    score += q.crt_ans_score
                else:
                    score += q.wrong_ans_score
            rdocs.append(Response(question_id=qid, answer=ans))

        existing = self.get_student_result(sid)
        if existing:
            existing.responses    = rdocs
            existing.score        = score
            existing.status       = 1
            existing.submitted_at = datetime.utcnow()
        else:
            self.results.append(Result(
                student_id=sid, responses=rdocs, score=score,
                status=1, submitted_at=datetime.utcnow(),
            ))
        self.save()
        return self.get_student_result(sid)

    # ── serializers ──
    def to_json_admin(self):
        return {
            'id':              str(self.id),
            'name':            self.name,
            'start_date':      self.start_date.isoformat() if self.start_date else None,
            'start_time':      self.start_time,
            'duration':        self.duration,
            'end_date':        self.end_date.isoformat() if self.end_date else None,
            'end_time':        self.end_time,
            'enrolled_count':  len(self.students_enrolled),
            'questions_count': len(self.questions),
            'results_count':   sum(1 for r in self.results if r.status == 1),
            'total_max_score': self.get_total_max_score(),
            'order_index':     self.order_index,
        }

    def to_json_secure(self, student_id):
        """For students attempting — without correct answers, with their result if any."""
        result = self.get_student_result(student_id)
        return {
            'id':              str(self.id),
            'name':            self.name,
            'start_date':      self.start_date.isoformat() if self.start_date else None,
            'start_time':      self.start_time,
            'duration':        self.duration,
            'end_date':        self.end_date.isoformat() if self.end_date else None,
            'end_time':        self.end_time,
            'total_questions': len(self.questions),
            'total_max_score': self.get_total_max_score(),
            'questions':       [q.to_json(include_correct=False) for q in self.questions],
            'result':          result.to_json() if result else None,
        }

    def to_json_review(self, student_id):
        """For result/report — includes correct answers and student's responses."""
        result = self.get_student_result(student_id)
        return {
            'id':              str(self.id),
            'name':            self.name,
            'duration':        self.duration,
            'total_questions': len(self.questions),
            'total_max_score': self.get_total_max_score(),
            'questions':       [q.to_json(include_correct=True) for q in self.questions],
            'result':          result.to_json() if result else None,
        }

    def to_json_list(self, student_id=None):
        """Lightweight card data for list screen."""
        result = self.get_student_result(student_id) if student_id else None
        if result and result.status == 1:
            status = 'done'
        elif result and result.status == -1:
            status = 'in_progress'
        else:
            status = 'open'

        now = datetime.utcnow()
        if self.end_date and self.end_date < now:
            window = 'ended'
        elif self.start_date and self.start_date > now:
            window = 'upcoming'
        else:
            window = 'live'

        return {
            'id':              str(self.id),
            'name':            self.name,
            'start_date':      self.start_date.isoformat() if self.start_date else None,
            'start_time':      self.start_time,
            'duration':        self.duration,
            'end_date':        self.end_date.isoformat() if self.end_date else None,
            'end_time':        self.end_time,
            'total_questions': len(self.questions),
            'total_max_score': self.get_total_max_score(),
            'order_index':     self.order_index,
            'status':          status,
            'window':          window,
            'score':           result.score if result and result.status == 1 else None,
        }
