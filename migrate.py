"""
Migration: azad-db  →  course_platform
Run once: python migrate.py
"""
import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId
from mongoengine import connect

load_dotenv()

# ── connections ──────────────────────────────────────────────────────────────

OLD_URI = "mongodb+srv://user:user@cluster0.rgocxdb.mongodb.net/azad-db"
NEW_URI = os.getenv("MONGO_URI")
NEW_DB  = os.getenv("DB_NAME", "course_platform")

old_client = MongoClient(OLD_URI)
old_db     = old_client["azad-db"]

# mongoengine connects to new DB for model saves
connect(db=NEW_DB, host=NEW_URI, alias="default")

from models.chapter import (
    Chapter, PDFChapter, AudioChapter, TextChapter, VideoChapter, LiveClass
)
from models.course import Course

# ── helpers ──────────────────────────────────────────────────────────────────

def g(doc, *keys, default=""):
    """Get first matching key from a dict (handles old/new field name variants)."""
    for k in keys:
        if k in doc and doc[k] not in (None, ""):
            return doc[k]
    return default


def migrate_chapter(raw: dict) -> Chapter:
    ch_type = g(raw, "type", default="video")

    chapter = Chapter(
        type=ch_type,
        demo=bool(raw.get("demo", False)),
    )

    if ch_type == "video":
        v = raw.get("video") or {}
        chapter.video = VideoChapter(
            title    = g(v, "title", default="Untitled"),
            video_url= g(v, "video_url", "videoUrl", "url"),
            thumbnail= g(v, "thumbnail", "thumbnail_url", default=""),
            duration = g(v, "duration", default=""),
            professor= g(v, "professor", default=""),
            notes    = g(v, "notes", default=""),
        )

    elif ch_type == "pdf":
        p = raw.get("pdf") or {}
        chapter.pdf = PDFChapter(
            title  = g(p, "title", default="Untitled"),
            pdf_url= g(p, "pdf_url", "pdfUrl", "url"),
        )

    elif ch_type == "audio":
        a = raw.get("audio") or {}
        chapter.audio = AudioChapter(
            title    = g(a, "title", default="Untitled"),
            audio_url= g(a, "audio_url", "audioUrl", "url"),
        )

    elif ch_type == "text":
        t = raw.get("text") or {}
        chapter.text = TextChapter(
            title= g(t, "title", default="Untitled"),
            text = g(t, "text", "content", default=""),
        )

    elif ch_type == "live_class":
        lc = raw.get("live_class") or {}
        chapter.live_class = LiveClass(
            title     = g(lc, "title", default="Untitled"),
            start_date= g(lc, "start_date", "startDate", "date", default=""),
            start_time= g(lc, "start_time", "startTime", "time", default=""),
            duration  = g(lc, "duration", default=""),
            link      = g(lc, "link", "url", "meeting_url", default=""),
        )

    return chapter


def resolve_chapters(raw_course: dict) -> list:
    """
    Old DB may store chapters as:
      - embedded docs in the course document
      - ObjectId references to a 'chapters' collection
    Handle both.
    """
    raw_chapters = raw_course.get("chapters", [])
    resolved = []

    for item in raw_chapters:
        if isinstance(item, dict):
            # already embedded
            resolved.append(item)
        elif isinstance(item, ObjectId):
            # reference — fetch from chapters collection
            doc = old_db["chapters"].find_one({"_id": item})
            if doc:
                resolved.append(doc)
            else:
                print(f"  ⚠  Chapter {item} not found in old DB, skipping.")
        else:
            print(f"  ⚠  Unknown chapter format: {type(item)}, skipping.")

    return resolved


def migrate_course(raw: dict) -> Course:
    topics     = raw.get("topics") or []
    professors = raw.get("professors") or []

    # some old schemas store as comma strings
    if isinstance(topics, str):
        topics = [t.strip() for t in topics.split(",") if t.strip()]
    if isinstance(professors, str):
        professors = [p.strip() for p in professors.split(",") if p.strip()]

    raw_chapters = resolve_chapters(raw)
    saved_chapters = []
    for i, rc in enumerate(raw_chapters, 1):
        try:
            ch = migrate_chapter(rc)
            ch.save()
            saved_chapters.append(ch)
        except Exception as e:
            print(f"  ✗  Chapter {i} failed: {e}")

    course = Course(
        name          = g(raw, "name", "title", default="Untitled Course"),
        course_id     = g(raw, "course_id", "courseId", "id",
                          default=str(raw["_id"])),
        price         = float(raw.get("price") or 0),
        whole_duration= str(g(raw, "whole_duration", "duration", "wholeDuration", default="0")),
        topics        = topics,
        professors    = professors,
        thumbnail_url = g(raw, "thumbnail_url", "thumbnailUrl", "thumbnail", default=""),
        chapters      = saved_chapters,
    )
    return course


# ── run ──────────────────────────────────────────────────────────────────────

def main():
    old_courses = list(old_db["courses"].find())
    print(f"Found {len(old_courses)} course(s) in azad-db\n")

    ok = 0
    fail = 0

    for raw in old_courses:
        name = raw.get("name") or raw.get("title") or str(raw["_id"])
        print(f"Migrating: {name}")

        # skip if already migrated (same course_id)
        cid = str(raw.get("course_id") or raw.get("courseId") or raw["_id"])
        if Course.objects(course_id=cid).first():
            print(f"  ⏭  Already exists, skipping.\n")
            continue

        try:
            course = migrate_course(raw)
            course.save()
            print(f"  ✓  Saved → {course.id}  ({len(course.chapters)} chapters)\n")
            ok += 1
        except Exception as e:
            print(f"  ✗  Failed: {e}\n")
            fail += 1

    print(f"Done. {ok} migrated, {fail} failed.")


if __name__ == "__main__":
    main()
