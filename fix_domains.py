"""
Replace all URLs with domain d1ytcm2rfo0yep.cloudfront.net
→ https://azad.s3.amazonaws.com  (path preserved)
Runs against the new DB (course_platform).

Run: python fix_domains.py
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

db = MongoClient(os.getenv("MONGO_URI"))[os.getenv("DB_NAME", "course_platform")]

OLD_DOMAIN = "https://d1ytcm2rfo0yep.cloudfront.net"
NEW_DOMAIN = "https://azad.s3.amazonaws.com"


def swap(value):
    if isinstance(value, str) and OLD_DOMAIN in value:
        return value.replace(OLD_DOMAIN, NEW_DOMAIN)
    return value


def fix_doc(doc: dict) -> tuple[dict, int]:
    """Return (updated_doc, count_of_changes)."""
    changes = 0

    # ── chapters collection fields ──────────────────────────────────────────
    for embedded, url_fields in {
        "video":      ["video_url", "thumbnail"],
        "pdf":        ["pdf_url"],
        "audio":      ["audio_url"],
    }.items():
        block = doc.get(embedded)
        if not isinstance(block, dict):
            continue
        for field in url_fields:
            old = block.get(field, "")
            new = swap(old)
            if new != old:
                doc[embedded][field] = new
                changes += 1

    # ── courses collection fields ───────────────────────────────────────────
    old = doc.get("thumbnail_url", "")
    new = swap(old)
    if new != old:
        doc["thumbnail_url"] = new
        changes += 1

    return doc, changes


def process_collection(col_name: str):
    col = db[col_name]
    docs = list(col.find())
    updated = 0
    total_changes = 0

    for doc in docs:
        fixed, changes = fix_doc(doc)
        if changes:
            col.replace_one({"_id": doc["_id"]}, fixed)
            updated += 1
            total_changes += changes

    print(f"  {col_name}: {updated} docs updated, {total_changes} URL(s) replaced")


print(f"Replacing  {OLD_DOMAIN}")
print(f"      with {NEW_DOMAIN}\n")

process_collection("chapters")
process_collection("courses")

print("\n✓ Done.")
