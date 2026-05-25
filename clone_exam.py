"""
Deep-clone an existing Exam document.

Copies:
  - the Exam doc (new _id, new exam_id, new title)
  - every session_contents doc referenced by the source exam's
    embedded sessions' merge_codes — with new merge_codes prefixed
    so HSTR and GPSTR are fully independent.

Usage:
    python clone_exam.py                                    # dry-run
    python clone_exam.py --commit                           # actually write
    python clone_exam.py --src "GPSTR 2026" --title HSTR --prefix HSTR    # custom

Env:
    MONGO_URI   — cluster URI
    DB_NAME     — defaults to course_platform
"""
import os
import sys
import argparse
import copy
import re
import uuid
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()


def slug_id(title: str) -> str:
    """Mimics Exam.generate_exam_id()."""
    s = re.sub(r'[^a-z0-9]+', '-', title.lower().strip()).strip('-')
    parts = [p for p in s.split('-') if p][:4]
    base = '-'.join(parts)
    return f'exam-{base}-{uuid.uuid4().hex[:6]}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src',    default='GPSTR 2026', help='source exam title to clone')
    ap.add_argument('--title',  default='HSTR',       help='new exam title')
    ap.add_argument('--prefix', default='HSTR',       help='merge_code prefix for clones')
    ap.add_argument('--full-form', default='Higher School Teacher Recruitment')
    ap.add_argument('--commit', action='store_true', help='write changes (else dry-run)')
    args = ap.parse_args()

    uri = os.getenv('MONGO_URI')
    if not uri:
        print('ERROR: MONGO_URI not set'); return

    db = MongoClient(uri)[os.getenv('DB_NAME', 'course_platform')]
    exams = db['exams']
    sc    = db['session_contents']

    src = exams.find_one({'title': args.src})
    if not src:
        print(f'ERROR: no exam found with title="{args.src}"'); return

    # Bail if a clone-by-title already exists, to avoid duplicate runs.
    if exams.find_one({'title': args.title}):
        print(f'ERROR: an exam with title="{args.title}" already exists. Refusing to clone again.'); return

    new_exam_id = slug_id(args.title)
    new_doc = copy.deepcopy(src)
    new_doc.pop('_id', None)
    new_doc['exam_id']     = new_exam_id
    new_doc['title']       = args.title
    new_doc['full_form']   = args.full_form
    new_doc['assessments'] = []  # references; do not carry old ones

    # Collect every merge_code in this exam's sessions and remap them.
    code_map = {}
    for subj in new_doc.get('subjects', []):
        for sess in subj.get('sessions', []):
            old = sess.get('merge_code') or ''
            if not old:
                continue
            if old not in code_map:
                code_map[old] = f'{args.prefix}-{old}'
            sess['merge_code'] = code_map[old]

    # Find which old merge_codes actually have content to clone
    present = {d['merge_code']: d for d in sc.find({'merge_code': {'$in': list(code_map.keys())}})}

    print(f'Source exam:    {args.src}  ({src.get("exam_id")})')
    print(f'Target exam:    {args.title}  ({new_exam_id})')
    print(f'Subjects:       {len(new_doc.get("subjects", []))}')
    print(f'Total sessions: {sum(len(s.get("sessions", [])) for s in new_doc.get("subjects", []))}')
    print(f'Merge codes:    {len(code_map)}  ({len(present)} have content to clone)')
    print(f'Mode:           {"COMMIT" if args.commit else "DRY-RUN"}')
    print('-' * 60)

    sample_codes = list(code_map.items())[:5]
    for old, new in sample_codes:
        has = 'YES' if old in present else 'no'
        print(f'  {old:<28} -> {new:<32}  (content: {has})')
    if len(code_map) > len(sample_codes):
        print(f'  ... and {len(code_map) - len(sample_codes)} more')

    if not args.commit:
        print('\nDRY-RUN. Re-run with --commit to write.')
        return

    # 1. Clone session_contents
    cloned_sc = []
    for old_code, doc in present.items():
        nd = copy.deepcopy(doc)
        nd.pop('_id', None)
        nd['merge_code'] = code_map[old_code]
        cloned_sc.append(nd)

    if cloned_sc:
        sc.insert_many(cloned_sc)
        print(f'\n[OK] Inserted {len(cloned_sc)} session_contents with prefix "{args.prefix}-"')

    # 2. Insert the exam clone
    result = exams.insert_one(new_doc)
    print(f'[OK] Inserted exam "{args.title}" (id={result.inserted_id}, exam_id={new_exam_id})')


if __name__ == '__main__':
    main()
