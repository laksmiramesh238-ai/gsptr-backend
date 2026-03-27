from mongoengine import Document, ReferenceField, StringField, DateTimeField, IntField
from datetime import datetime
from models.student import Student
from models.exam import Exam


EXAM_TIERS = {
    1: {'price': 1500,  'label': 'Basic',   'includes': ['mcq', 'descriptive', 'assessments']},
    2: {'price': 2500,  'label': 'Notes',   'includes': ['mcq', 'descriptive', 'assessments', 'notes']},
    3: {'price': 4000,  'label': 'Audio',   'includes': ['mcq', 'descriptive', 'assessments', 'notes', 'audio']},
    4: {'price': 8000,  'label': 'Video',   'includes': ['mcq', 'descriptive', 'assessments', 'notes', 'audio', 'videos']},
    5: {'price': 15000, 'label': 'Premium', 'includes': ['mcq', 'descriptive', 'assessments', 'notes', 'audio', 'videos', 'live_classes', 'offline']},
}


class ExamEnrollment(Document):
    meta = {'collection': 'exam_enrollments'}

    student     = ReferenceField(Student, required=True)
    exam        = ReferenceField(Exam, required=True)
    tier        = IntField(required=True, min_value=1, max_value=5)
    order_id    = StringField(required=True)
    payment_id  = StringField(default='')
    status      = StringField(default='pending', choices=['pending', 'paid'])
    enrolled_at = DateTimeField()
    expires_at  = DateTimeField()
    created_at  = DateTimeField(default=datetime.utcnow)
