from mongoengine import (
    Document, EmbeddedDocument, StringField, BooleanField,
    URLField, EmbeddedDocumentField
)


class PDFChapter(EmbeddedDocument):
    title = StringField(required=True)
    pdf_url = URLField(required=True)


class AudioChapter(EmbeddedDocument):
    title = StringField(required=True)
    audio_url = URLField(required=True)


class TextChapter(EmbeddedDocument):
    title = StringField(required=True)
    text = StringField(required=True)


class VideoChapter(EmbeddedDocument):
    video_url = URLField(required=True)
    # default=None (not '') — MongoEngine's URLField validates any non-None
    # value, so an empty string fails "Invalid scheme in URL" even though
    # this field is optional. None skips validation entirely.
    thumbnail = URLField(required=False, default=None)
    title = StringField(required=True)
    duration = StringField(required=True, default='')
    professor = StringField(required=False, default='')
    notes = StringField(default='')


class LiveClass(EmbeddedDocument):
    title = StringField(required=True)
    start_date = StringField(required=True)
    start_time = StringField(required=True)
    duration = StringField(required=True)
    link = StringField(default='')


class Chapter(Document):
    meta = {'collection': 'chapters'}

    type = StringField(required=True, choices=['pdf', 'text', 'video', 'live_class', 'audio'])
    pdf = EmbeddedDocumentField(PDFChapter)
    audio = EmbeddedDocumentField(AudioChapter)
    text = EmbeddedDocumentField(TextChapter)
    video = EmbeddedDocumentField(VideoChapter)
    demo = BooleanField(default=False)
    live_class = EmbeddedDocumentField(LiveClass)
