"""
Migrate `tests` collection from azad-db → course_platform.

Field names match 1:1 (we kept the old schema), so this is mostly a
copy with two cleanups:
  - drop students_enrolled (old Student IDs don't exist in new DB)
  - drop results          (same reason)

Usage:
    python migrate_tests.py             # dry-run, just reports
    python migrate_tests.py --commit    # actually copies them over
    python migrate_tests.py --commit --wipe   # wipe new tests first

Env (.env):
    MONGO_URI     — current cluster URI
    OLD_DB_NAME   — defaults to 'azad-db'
    DB_NAME       — defaults to 'course_platform'
"""
import os
import sys
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

URI    = os.getenv('MONGO_URI')
OLD_DB = os.getenv('OLD_DB_NAME', 'azad-db')
NEW_DB = os.getenv('DB_NAME', 'course_platform')

COMMIT = '--commit' in sys.argv
WIPE   = '--wipe'   in sys.argv


def main():
    if not URI:
        print('ERROR: MONGO_URI not set'); return

    print(f'Source:      {OLD_DB}.tests')
    print(f'Destination: {NEW_DB}.tests')
    print(f'Mode:        {"COMMIT" if COMMIT else "DRY-RUN"}{"  +WIPE" if WIPE else ""}')
    print('-' * 60)

    client = MongoClient(URI)
    src = client[OLD_DB]['tests']
    dst = client[NEW_DB]['tests']

    docs = list(src.find({}))
    total_qs = sum(len(d.get('questions', [])) for d in docs)
    print(f'Found {len(docs)} tests with {total_qs} questions in {OLD_DB}.tests')
    print(f'Existing in {NEW_DB}.tests: {dst.count_documents({})}')
    print()

    to_insert = []
    skipped = 0
    for d in docs:
        if not d.get('name'):
            skipped += 1
            continue

        new_doc = {
            'name':              d.get('name'),
            'start_date':        d.get('start_date'),
            'start_time':        d.get('start_time') or '',
            'duration':          d.get('duration', 60),
            'end_date':          d.get('end_date'),
            'end_time':          d.get('end_time') or '',
            'students_enrolled': [],
            'questions':         d.get('questions', []),
            'results':           [],
            'order_index':       d.get('order_index', 0),
        }
        to_insert.append(new_doc)

    print(f'Ready to insert: {len(to_insert)}   Skipped (no name): {skipped}')
    if to_insert:
        print(f'Sample: "{to_insert[0]["name"]}" — {len(to_insert[0]["questions"])} questions')

    if not COMMIT:
        print('\nDRY-RUN — nothing written. Run with --commit to apply.')
        return

    if WIPE:
        n = dst.count_documents({})
        dst.delete_many({})
        print(f'\nWiped {n} existing docs from {NEW_DB}.tests')

    if to_insert:
        dst.insert_many(to_insert)
        print(f'\n[OK] Inserted {len(to_insert)} tests into {NEW_DB}.tests')
        print(f'  ({sum(len(d["questions"]) for d in to_insert)} questions total)')
        print(f'  (enrollments + results NOT carried over — admin enrolls students manually)')


if __name__ == '__main__':
    main()
