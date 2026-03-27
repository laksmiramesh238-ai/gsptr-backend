from mongoengine import Document, ReferenceField, StringField, DateTimeField
from datetime import datetime
from models.student import Student
from models.course import Course


class Enrollment(Document):
    meta = {'collection': 'enrollments'}

    student     = ReferenceField(Student, required=True)
    course      = ReferenceField(Course,  required=True)
    order_id    = StringField(required=True)   # Razorpay order ID
    payment_id  = StringField(default='')      # Razorpay payment ID (set after success)
    status      = StringField(default='pending', choices=['pending', 'paid'])
    enrolled_at = DateTimeField()
    expires_at  = DateTimeField()              # enrolled_at + 6 months
    created_at  = DateTimeField(default=datetime.utcnow)
