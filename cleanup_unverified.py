"""
Deletes all student accounts that were created before the OTP-first fix
and never completed email verification.
"""
from dotenv import load_dotenv
load_dotenv()

import os
from mongoengine import connect
from models.student import Student

connect(db=os.getenv('DB_NAME', 'course_platform'), host=os.getenv('MONGO_URI'))

unverified = Student.objects(is_verified=False)
count = unverified.count()

if count == 0:
    print("No unverified students found. Nothing to clean up.")
else:
    print(f"Found {count} unverified student(s):")
    for s in unverified:
        print(f"  - {s.email}  (name: {s.name})")

    confirm = input(f"\nDelete all {count} unverified student(s)? [y/N]: ").strip().lower()
    if confirm == 'y':
        unverified.delete()
        print(f"Deleted {count} unverified student(s).")
    else:
        print("Aborted.")
