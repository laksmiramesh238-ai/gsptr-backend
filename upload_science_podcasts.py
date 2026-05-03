"""
Upload Science final_module.wav podcasts to S3 and link them onto each
ModuleVideo in DB.

Source layout:
  <AUDIO_ROOT>/<merge_code>/<module_id>/final_module.wav

S3 destination:
  science_podcasts/<merge_code>/<module_id>.wav

Behavior:
  • Skips files already present in S3 (head_object check) unless FORCE_UPLOAD=1
  • Uploads in parallel (8 workers by default) using boto3's TransferManager
  • After upload phase, updates each ModuleVideo.podcast_url + duration in DB

Re-running is safe: existing uploads are skipped, DB updates are idempotent.

Usage:
  python upload_science_podcasts.py
  FORCE_UPLOAD=1 python upload_science_podcasts.py    # re-upload all
"""

import os, sys, wave, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

try: sys.stdout.reconfigure(encoding='utf-8', line_buffering=True)
except Exception: pass

import boto3
from botocore.exceptions import ClientError
from boto3.s3.transfer import TransferConfig

from dotenv import load_dotenv; load_dotenv()
from mongoengine import connect
connect(db=os.getenv('DB_NAME', 'course_platform'), host=os.getenv('MONGO_URI'))

from models.exam import Exam

EXAM_TITLE = 'GPSTR 2026'
SUBJECT    = 'Science / ವಿಜ್ಞಾನ'

AUDIO_ROOT = Path('C:/Users/arkaa/Documents/gpstrhstr/maths/claude_works/audio_science')

BUCKET     = os.getenv('AWS_BUCKET', 'azad')
REGION     = os.getenv('AWS_REGION', 'us-east-1')
FORCE      = os.getenv('FORCE_UPLOAD', '').lower() in ('1', 'true', 'yes')
WORKERS    = int(os.getenv('UPLOAD_WORKERS', '8'))

s3 = boto3.client('s3', region_name=REGION)
transfer_cfg = TransferConfig(multipart_threshold=8*1024*1024, multipart_chunksize=8*1024*1024,
                              max_concurrency=4, use_threads=True)


def s3_url(key):
    return f'https://{BUCKET}.s3.{REGION}.amazonaws.com/{key}'


def s3_head_size(key):
    try:
        r = s3.head_object(Bucket=BUCKET, Key=key)
        return r['ContentLength']
    except ClientError as e:
        if e.response['Error']['Code'] in ('404', 'NoSuchKey', 'NotFound'):
            return None
        raise


def wav_duration_seconds(path):
    try:
        with wave.open(str(path), 'rb') as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:
        return 0.0


def fmt_duration(seconds):
    seconds = int(round(seconds))
    if seconds <= 0: return ''
    m, s = divmod(seconds, 60)
    if m >= 60:
        h, m = divmod(m, 60)
        return f'{h}h {m:02d}m'
    return f'{m}m {s:02d}s'


def discover_files():
    """Return list of (merge_code, module_id, local_path)."""
    out = []
    if not AUDIO_ROOT.exists():
        raise SystemExit(f"AUDIO_ROOT not found: {AUDIO_ROOT}")
    for ch_dir in sorted(AUDIO_ROOT.iterdir()):
        if not ch_dir.is_dir(): continue
        merge_code = ch_dir.name
        for mod_dir in sorted(ch_dir.iterdir()):
            if not mod_dir.is_dir(): continue
            module_id = mod_dir.name
            wav = mod_dir / 'final_module.wav'
            if wav.exists():
                out.append((merge_code, module_id, wav))
    return out


def upload_one(merge_code, module_id, local_path):
    key = f'science_podcasts/{merge_code}/{module_id}.wav'
    local_size = local_path.stat().st_size

    if not FORCE:
        existing = s3_head_size(key)
        if existing == local_size:
            return ('skip', merge_code, module_id, key, local_size, 0)

    t0 = time.time()
    s3.upload_file(
        str(local_path), BUCKET, key,
        ExtraArgs={'ContentType': 'audio/wav'},
        Config=transfer_cfg,
    )
    return ('upload', merge_code, module_id, key, local_size, time.time() - t0)


def main():
    files = discover_files()
    print(f'Discovered {len(files)} final_module.wav files')
    print(f'  S3 bucket: {BUCKET}    region: {REGION}    force: {FORCE}    workers: {WORKERS}')

    # ── Phase 1: upload in parallel ──────────────────────────────────────────
    uploaded = 0
    skipped  = 0
    durations = {}   # (merge_code, module_id) -> seconds
    keys      = {}   # (merge_code, module_id) -> s3_key
    total_bytes_uploaded = 0
    t_start = time.time()

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(upload_one, m, mid, p): (m, mid, p) for (m, mid, p) in files}
        for i, fut in enumerate(as_completed(futures), 1):
            try:
                status, m, mid, key, size, dt = fut.result()
            except Exception as e:
                m, mid, p = futures[fut]
                print(f'  [{i}/{len(files)}] FAIL  {m}/{mid}: {e}')
                continue

            keys[(m, mid)] = key
            durations[(m, mid)] = wav_duration_seconds(futures[fut][2])
            if status == 'upload':
                uploaded += 1
                total_bytes_uploaded += size
                print(f'  [{i}/{len(files)}] UP    {m}/{mid}  {size/1024/1024:.1f}MB in {dt:.1f}s')
            else:
                skipped += 1

    print()
    print(f'Phase 1 done in {time.time()-t_start:.0f}s')
    print(f'  Uploaded: {uploaded}  ({total_bytes_uploaded/1024/1024/1024:.2f} GB)')
    print(f'  Skipped (already in S3): {skipped}')

    # ── Phase 2: link into DB ────────────────────────────────────────────────
    exam = Exam.objects(title=EXAM_TITLE).first()
    sub  = next((s for s in exam.subjects if s.name == SUBJECT), None)
    if not sub:
        raise SystemExit('Science subject not found')

    linked = 0
    missing = 0
    for sess in sub.sessions:
        mc = sess.merge_code
        if not mc: continue
        # Modules are stored in same order as audio_science layout (sorted concept_1..N).
        # Use module index to derive module_id since ModuleVideo doesn't store it.
        for idx, mv in enumerate(sess.module_videos, start=1):
            module_id = f'{mc}_concept_{idx}'
            key = keys.get((mc, module_id))
            if not key:
                # File wasn't uploaded (didn't exist on disk)
                missing += 1
                continue
            url = s3_url(key)
            new_dur = fmt_duration(durations.get((mc, module_id), 0))
            if mv.podcast_url != url or (new_dur and mv.podcast_duration != new_dur):
                mv.podcast_url = url
                if new_dur: mv.podcast_duration = new_dur
                linked += 1

    exam.save()
    print()
    print(f'Phase 2 done')
    print(f'  Module podcast URLs linked/updated: {linked}')
    print(f'  Modules with no audio yet:          {missing}')


if __name__ == '__main__':
    main()
