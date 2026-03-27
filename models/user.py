from mongoengine import Document, StringField, BooleanField, DateTimeField, ListField
from flask_login import UserMixin
from datetime import datetime


class User(UserMixin, Document):
    meta = {'collection': 'users'}

    name = StringField(required=True, max_length=100)
    email = StringField(required=True, unique=True, max_length=200)
    password = StringField(required=True)
    role = StringField(default='student', choices=['student', 'instructor', 'admin'])
    is_active = BooleanField(default=True)
    enrolled_courses = ListField(StringField())  # list of Course ids
    created_at = DateTimeField(default=datetime.utcnow)

    def get_id(self):
        return str(self.id)
