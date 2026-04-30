"""
One-shot cleanup:
  • deletes ALL assessments
  • deletes ALL course enrollments
  • deletes ALL exam enrollments
  • removes assessment references attached to exams (exam.assessments)

Usage:  python cleanup_db.py
"""

import os, sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from dotenv import load_dotenv
load_dotenv()

from mongoengine import connect
connect(db=os.getenv('DB_NAME', 'course_platform'), host=os.getenv('MONGO_URI'))

from models.assessment import Assessment
from models.assessment_attempt import AssessmentAttempt
from models.enrollment import Enrollment
from models.exam_enrollment import ExamEnrollment
from models.exam import Exam


def main():
    a_count = Assessment.objects.count()
    aa_count = AssessmentAttempt.objects.count()
    e_count  = Enrollment.objects.count()
    ee_count = ExamEnrollment.objects.count()

    print(f"Before cleanup:")
    print(f"  Assessments:        {a_count}")
    print(f"  Assessment attempts: {aa_count}")
    print(f"  Course enrollments: {e_count}")
    print(f"  Exam enrollments:   {ee_count}")

    AssessmentAttempt.objects.delete()
    Assessment.objects.delete()
    Enrollment.objects.delete()
    ExamEnrollment.objects.delete()

    # also clear the exam.assessments reference list
    cleared_exams = 0
    for exam in Exam.objects():
        if exam.assessments:
            exam.assessments = []
            exam.save()
            cleared_exams += 1

    print()
    print(f"After cleanup:")
    print(f"  Assessments:        {Assessment.objects.count()}")
    print(f"  Assessment attempts: {AssessmentAttempt.objects.count()}")
    print(f"  Course enrollments: {Enrollment.objects.count()}")
    print(f"  Exam enrollments:   {ExamEnrollment.objects.count()}")
    print(f"  Exams cleared of assessment refs: {cleared_exams}")
    print()
    print("Done.")


if __name__ == '__main__':
    main()
