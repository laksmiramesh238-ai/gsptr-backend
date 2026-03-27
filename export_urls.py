"""
Export all courses + chapters with their S3 URLs to a CSV.
Run: python export_urls.py
Output: urls_export.csv
"""
import csv
import os
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId

load_dotenv()

NEW_URI = os.getenv("MONGO_URI")
NEW_DB  = os.getenv("DB_NAME", "course_platform")
db      = MongoClient(NEW_URI)[NEW_DB]

OUTPUT  = "urls_export.csv"

FIELDS  = [
    "course_name",
    "course_id",
    "course_thumbnail",
    "chapter_index",
    "chapter_type",
    "chapter_title",
    "chapter_demo",
    "video_url",
    "video_thumbnail",
    "pdf_url",
    "audio_url",
]

courses  = list(db["courses"].find())
chapters_map = {str(c["_id"]): c for c in db["chapters"].find()}

rows = []

for course in courses:
    cname     = course.get("name", "")
    cid       = course.get("course_id", str(course["_id"]))
    cthumb    = course.get("thumbnail_url", "")
    ch_refs   = course.get("chapters", [])

    if not ch_refs:
        # course with no chapters — still write one row
        rows.append({
            "course_name":      cname,
            "course_id":        cid,
            "course_thumbnail": cthumb,
            "chapter_index":    "",
            "chapter_type":     "",
            "chapter_title":    "",
            "chapter_demo":     "",
            "video_url":        "",
            "video_thumbnail":  "",
            "pdf_url":          "",
            "audio_url":        "",
        })
        continue

    for i, ref in enumerate(ch_refs, 1):
        ch_id = str(ref) if isinstance(ref, ObjectId) else str(ref.get("$id", ref))
        ch    = chapters_map.get(ch_id, {})

        ch_type  = ch.get("type", "")
        ch_demo  = ch.get("demo", False)

        video_url   = ""
        video_thumb = ""
        pdf_url     = ""
        audio_url   = ""
        title       = ""

        if ch_type == "video" and ch.get("video"):
            v           = ch["video"]
            title       = v.get("title", "")
            video_url   = v.get("video_url", "")
            video_thumb = v.get("thumbnail", "")

        elif ch_type == "pdf" and ch.get("pdf"):
            p       = ch["pdf"]
            title   = p.get("title", "")
            pdf_url = p.get("pdf_url", "")

        elif ch_type == "audio" and ch.get("audio"):
            a         = ch["audio"]
            title     = a.get("title", "")
            audio_url = a.get("audio_url", "")

        elif ch_type == "text" and ch.get("text"):
            title = ch["text"].get("title", "")

        elif ch_type == "live_class" and ch.get("live_class"):
            title = ch["live_class"].get("title", "")

        rows.append({
            "course_name":      cname,
            "course_id":        cid,
            "course_thumbnail": cthumb,
            "chapter_index":    i,
            "chapter_type":     ch_type,
            "chapter_title":    title,
            "chapter_demo":     ch_demo,
            "video_url":        video_url,
            "video_thumbnail":  video_thumb,
            "pdf_url":          pdf_url,
            "audio_url":        audio_url,
        })

with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)

print(f"✓ Exported {len(rows)} rows to {OUTPUT}")
print(f"  Courses : {len(courses)}")
print(f"  Chapters: {sum(1 for r in rows if r['chapter_type'])}")
