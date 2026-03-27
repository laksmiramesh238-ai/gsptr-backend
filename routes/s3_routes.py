import uuid
import os
import boto3
from flask import Blueprint, request, jsonify
from flask_login import login_required

s3_bp = Blueprint('s3', __name__)

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION', 'ap-south-1')
AWS_BUCKET = os.getenv('AWS_BUCKET', 'deloai-mathquest')
CLOUDFRONT_DOMAIN = os.getenv('CLOUDFRONT_DOMAIN')

FOLDER_MAP = {
    'thumbnail':      'course-thumbnails',
    'video':          'course-videos',
    'pdf':            'course-pdfs',
    'audio':          'course-audio',
    'video_thumb':    'chapter-thumbnails',
    'exam_thumbnail': 'exam-thumbnails',
    'exam_pdf':       'exam-pdfs',
    'exam_audio':     'exam-audio',
    'exam_video':     'exam-videos',
}


def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )


@s3_bp.route('/presign', methods=['GET'])
@login_required
def presign():
    """
    Returns a presigned POST so the browser can upload directly to S3.
    Query params:
      - filename  : original filename (for extension)
      - folder    : one of thumbnail | video | pdf | audio | video_thumb
    """
    filename = request.args.get('filename', 'file')
    folder_key = request.args.get('folder', 'thumbnail')

    ext = os.path.splitext(filename)[1].lower()
    folder = FOLDER_MAP.get(folder_key, 'uploads')
    key = f"{folder}/{uuid.uuid4()}{ext}"

    s3 = get_s3_client()
    presigned = s3.generate_presigned_post(
        Bucket=AWS_BUCKET,
        Key=key,
        ExpiresIn=3600,
    )

    public_url = f"https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"

    return jsonify({
        'url':        presigned['url'],
        'fields':     presigned['fields'],
        'public_url': public_url,
        'key':        key,
    })
