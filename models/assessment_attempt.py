from mongoengine import (
    Document, ReferenceField, StringField, IntField,
    DateTimeField, EmbeddedDocument, EmbeddedDocumentListField
)
from datetime import datetime
from models.student import Student
from models.assessment import Assessment


class AttemptAnswer(EmbeddedDocument):
    question_index = IntField(required=True)
    selected       = IntField(default=-1)  # -1 = unanswered


class AssessmentAttempt(Document):
    meta = {'collection': 'assessment_attempts'}

    student      = ReferenceField(Student, required=True)
    assessment   = ReferenceField(Assessment, required=True)
    answers      = EmbeddedDocumentListField(AttemptAnswer)
    score        = IntField(default=0)
    total        = IntField(default=0)
    started_at   = DateTimeField(default=datetime.utcnow)
    submitted_at = DateTimeField()
    status       = StringField(default='in_progress', choices=['in_progress', 'submitted'])
