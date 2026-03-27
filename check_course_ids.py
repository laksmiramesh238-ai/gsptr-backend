import os
from dotenv import load_dotenv
from pymongo import MongoClient
load_dotenv()

db = MongoClient(os.getenv("MONGO_URI"))[os.getenv("DB_NAME", "course_platform")]
courses = list(db["courses"].find({}, {"course_id": 1, "name": 1}))
print(f"{len(courses)} course(s):\n")
for c in courses:
    print(f"  name: {c.get('name',''):<40}  course_id: {c.get('course_id','')}")
