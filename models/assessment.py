from mongoengine import (
    Document, EmbeddedDocument, EmbeddedDocumentListField,
    StringField, ListField, ReferenceField, IntField
)


class AssessmentQuestion(EmbeddedDocument):
    question    = StringField(required=True)
    options     = ListField(StringField(), required=True)
    answer      = IntField(required=True)   # 0-based
    explanation = StringField(default='')


class Assessment(Document):
    meta = {'collection': 'assessments'}

    exam             = ReferenceField('Exam', required=True)
    title            = StringField(required=True)
    subject_filter   = StringField(default='')
    topic_filter     = StringField(default='')
    session_filter   = StringField(default='')
    questions        = EmbeddedDocumentListField(AssessmentQuestion)
    duration_minutes = IntField(default=60)
