"""
SessionContent — one document per merge_code carrying the heavy
content (notes HTML, MCQs, descriptive questions). Lives in its own
collection so the Exam document stays under MongoDB's 16 MB limit.
"""

from datetime import datetime
from mongoengine import (
    Document, EmbeddedDocumentListField, StringField, DateTimeField,
)
from models.exam import MCQQuestion, DescriptiveQuestion


class SessionContent(Document):
    meta = {
        'collection': 'session_contents',
        'indexes': ['merge_code'],
    }

    merge_code            = StringField(required=True, unique=True)
    notes_html            = StringField(default='')
    mcqs                  = EmbeddedDocumentListField(MCQQuestion)
    descriptive_questions = EmbeddedDocumentListField(DescriptiveQuestion)
    updated_at            = DateTimeField(default=datetime.utcnow)
