from mongoengine import (
    Document, StringField, ListField, DecimalField, ReferenceField
)


class Course(Document):
    meta = {'collection': 'courses'}

    name = StringField(required=True)
    course_id = StringField(unique=True, required=True)
    topics = ListField(StringField())
    professors = ListField(StringField())
    price = DecimalField(precision=2, required=True)
    whole_duration = StringField(default='0')
    chapters = ListField(ReferenceField('Chapter'))
    thumbnail_url = StringField(default='')
