"""
Find every video stored as .mpg/.mpeg (across course chapters AND exam
session videos), transcode each to .mp4 (H.264/AAC, +faststart), upload
the result to S3 under the same folder convention as normal admin
uploads, and repoint the DB record at the new file.

Safety:
  - Without --apply, only lists what would be converted (dry run).
  - The original .mpg file is NEVER deleted — it's left in S3 as a
    backup. The DB URL is only updated after the new .mp4 is uploaded
    and verified (has a valid video stream + duration) to succeed.
  - Each item is handled in its own try/except so one failure doesn't
    abort the batch.

Requires ffmpeg + ffprobe on PATH.

Usage:
  python convert_mpg_to_mp4.py            # dry run — just lists them
  python convert_mpg_to_mp4.py --apply    # actually convert + upload + update DB
"""
import os, sys, json, uuid, subprocess, tempfile, shutil
import urllib.request

try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass

from dotenv import load_dotenv; load_dotenv()
from mongoengine import connect
connect(db=os.getenv('DB_NAME', 'course_platform'), host=os.getenv('MONGO_URI'))

import boto3
from models.course import Course
from models.chapter import Chapter
from models.exam import Exam

AWS_ACCESS_KEY_ID     = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION            = os.getenv('AWS_REGION', 'us-east-1')
AWS_BUCKET            = os.getenv('AWS_BUCKET', 'azad')

FOLDER = {'course': 'course-videos', 'exam': 'exam-videos'}


def is_mpg(url: str) -> bool:
    if not url:
        return False
    path = url.split('?')[0].lower()
    return path.endswith('.mpg') or path.endswith('.mpeg')


def s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
    )


def public_s3_url(key: str) -> str:
    return f'https://{AWS_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}'


# ── discovery ────────────────────────────────────────────────────────────────

def find_targets():
    """Returns a list of dicts describing every .mpg/.mpeg video found."""
    targets = []

    course_by_chapter = {}
    for co in Course.objects():
        for ch in co.chapters:
            course_by_chapter[ch.id] = co.name

    for ch in Chapter.objects(type='video'):
        if ch.video and is_mpg(ch.video.video_url):
            targets.append({
                'kind': 'course_chapter',
                'label': f'{course_by_chapter.get(ch.id, "(orphaned)")} -> {ch.video.title}',
                'url': ch.video.video_url,
                'chapter_id': str(ch.id),
            })

    for ex in Exam.objects():
        for si, sub in enumerate(ex.subjects):
            for ssi, sess in enumerate(sub.sessions):
                if is_mpg(sess.full_video_url):
                    targets.append({
                        'kind': 'exam_full_video',
                        'label': f'{ex.title} -> {sub.name} -> {sess.title} (full video)',
                        'url': sess.full_video_url,
                        'exam_id': ex.exam_id, 'sub_idx': si, 'sess_idx': ssi,
                    })
                for mi, mv in enumerate(sess.module_videos):
                    if is_mpg(mv.video_url):
                        targets.append({
                            'kind': 'exam_module_video',
                            'label': f'{ex.title} -> {sub.name} -> {sess.title} -> {mv.title}',
                            'url': mv.video_url,
                            'exam_id': ex.exam_id, 'sub_idx': si, 'sess_idx': ssi, 'mod_idx': mi,
                        })

    return targets


# ── conversion ───────────────────────────────────────────────────────────────

def download(url: str, dest: str):
    req = urllib.request.Request(url, headers={'User-Agent': 'mpg-to-mp4-migration/1.0'})
    with urllib.request.urlopen(req, timeout=120) as r, open(dest, 'wb') as f:
        shutil.copyfileobj(r, f)


def transcode(src: str, dest: str):
    subprocess.run(
        ['ffmpeg', '-y', '-i', src,
         '-c:v', 'libx264', '-preset', 'medium', '-crf', '20',
         '-c:a', 'aac', '-b:a', '128k',
         '-movflags', '+faststart',
         dest],
        check=True, capture_output=True, text=True,
    )


def probe_ok(path: str) -> bool:
    """Sanity check: the output has a video stream and non-zero duration."""
    try:
        out = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-show_entries', 'stream=codec_type', '-of', 'json', path],
            check=True, capture_output=True, text=True,
        ).stdout
        data = json.loads(out)
        has_video = any(s.get('codec_type') == 'video' for s in data.get('streams', []))
        duration = float(data.get('format', {}).get('duration', 0) or 0)
        return has_video and duration > 0
    except Exception:
        return False


def upload(local_path: str, folder_key: str) -> str:
    key = f'{FOLDER[folder_key]}/{uuid.uuid4()}.mp4'
    s3_client().upload_file(local_path, AWS_BUCKET, key, ExtraArgs={'ContentType': 'video/mp4'})
    return public_s3_url(key)


# ── main ─────────────────────────────────────────────────────────────────────

def process_one(t: dict, apply: bool):
    print(f'\n--- [{t["kind"]}] {t["label"]}')
    print(f'    source: {t["url"]}')

    if not apply:
        print('    (dry run — would convert)')
        return 'dry-run'

    tmp = tempfile.mkdtemp(prefix='mpg2mp4_')
    src_path = os.path.join(tmp, 'source.mpg')
    dst_path = os.path.join(tmp, 'converted.mp4')
    try:
        print('    downloading...')
        download(t['url'], src_path)

        print('    transcoding...')
        transcode(src_path, dst_path)

        if not probe_ok(dst_path):
            print('    FAILED: converted file failed validation (no video stream / zero duration)')
            return 'failed'

        folder_key = 'course' if t['kind'] == 'course_chapter' else 'exam'
        print('    uploading...')
        new_url = upload(dst_path, folder_key)
        print(f'    new url: {new_url}')

        # Only now, after a verified upload, repoint the DB.
        if t['kind'] == 'course_chapter':
            ch = Chapter.objects(id=t['chapter_id']).first()
            if not ch or not ch.video:
                print('    FAILED: chapter disappeared before DB update')
                return 'failed'
            ch.video.video_url = new_url
            ch.save()
        else:
            ex = Exam.objects(exam_id=t['exam_id']).first()
            if not ex:
                print('    FAILED: exam disappeared before DB update')
                return 'failed'
            sess = ex.subjects[t['sub_idx']].sessions[t['sess_idx']]
            if t['kind'] == 'exam_full_video':
                sess.full_video_url = new_url
            else:
                sess.module_videos[t['mod_idx']].video_url = new_url
            ex.save()

        print('    DB updated. Original .mpg left in place as backup.')
        return 'converted'
    except subprocess.CalledProcessError as e:
        print('    FAILED (ffmpeg/ffprobe error):', e.stderr[-500:] if e.stderr else e)
        return 'failed'
    except Exception as e:
        print('    FAILED:', repr(e))
        return 'failed'
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    apply = '--apply' in sys.argv
    targets = find_targets()
    print(f'Found {len(targets)} .mpg/.mpeg video(s).')
    if not targets:
        return

    counts = {}
    for t in targets:
        status = process_one(t, apply)
        counts[status] = counts.get(status, 0) + 1

    print('\n=== SUMMARY ===')
    for k, v in counts.items():
        print(f'  {k}: {v}')
    if not apply:
        print('\nThis was a dry run. Re-run with --apply to actually convert and update the DB.')


if __name__ == '__main__':
    main()
