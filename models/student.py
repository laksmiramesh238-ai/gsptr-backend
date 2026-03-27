from mongoengine import Document, StringField, BooleanField, DateTimeField
from datetime import datetime


class Student(Document):
    meta = {'collection': 'students'}

    name       = StringField(required=True)
    email      = StringField(required=True, unique=True)
    phone      = StringField(default='')
    is_verified = BooleanField(default=False)
    created_at  = DateTimeField(default=datetime.utcnow)
