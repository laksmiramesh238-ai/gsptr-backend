from mongoengine import Document, StringField, DateTimeField, BooleanField
from datetime import datetime


class OTP(Document):
    meta = {'collection': 'otps'}

    email      = StringField(required=True)
    code       = StringField(required=True)
    expires_at = DateTimeField(required=True)
    used       = BooleanField(default=False)
    created_at = DateTimeField(default=datetime.utcnow)
    # stored only for signup flow — empty for login/forgot
    pending_name  = StringField(default='')
    pending_phone = StringField(default='')
