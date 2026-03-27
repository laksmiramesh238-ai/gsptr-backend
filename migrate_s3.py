"""
1. Find all srinivas-ias-academy.s3.amazonaws.com URLs in new DB
2. Copy each file to deloai-mathquest (azad) bucket — original NOT deleted
3. Update URLs in DB to point to azad bucket

Run: python migrate_s3.py
"""
import re, os
from urllib.parse import urlparse, unquote
from pymongo import MongoClient
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError

load_dotenv()

# ── config ───────────────────────────────────────────────────────────────────

SRINIVAS_BUCKET = "srinivas-ias-academy"
SRINIVAS_DOMAIN = "srinivas-ias-academy.s3.amazonaws.com"

AZAD_BUCKET     = os.getenv("AWS_BUCKET", "deloai-mathquest")
AZAD_REGION     = os.getenv("AWS_REGION", "ap-south-1")
AZAD_DOMAIN     = f"{AZAD_BUCKET}.s3.amazonaws.com"

# same IAM creds can access both buckets
s3 = boto3.client(
    "s3",
    aws_access_key_id     = os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name           = AZAD_REGION,
)

db     = MongoClient(os.getenv("MONGO_URI"))[os.getenv("DB_NAME", "course_platform")]
URL_RE = re.compile(r'https?://[^\s"\'<>]+')

# ── collect all srinivas URLs from DB ─────────────────────────────────────────

def all_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from all_strings(v)
    elif isinstance(obj, list):
        for i in obj:
            yield from all_strings(i)

srinivas_urls = set()
for col in ["chapters", "courses"]:
    for doc in db[col].find():
        for s in all_strings(doc):
            for url in URL_RE.findall(s):
                if SRINIVAS_DOMAIN in url:
                    srinivas_urls.add(url)

print(f"Found {len(srinivas_urls)} unique srinivas URL(s) in DB\n")

if not srinivas_urls:
    print("Nothing to migrate.")
    exit(0)

# ── copy each file srinivas → azad ───────────────────────────────────────────

url_map = {}   # old_url → new_url
copied  = 0
skipped = 0
failed  = 0

for url in sorted(srinivas_urls):
    parsed      = urlparse(url)
    encoded_key = parsed.path.lstrip("/")   # keep encoded for building new URL
    key         = unquote(encoded_key)      # decode for S3 API calls

    new_url = f"https://{AZAD_DOMAIN}/{encoded_key}"
    url_map[url] = new_url

    # check if already exists in azad
    try:
        s3.head_object(Bucket=AZAD_BUCKET, Key=key)
        print(f"  ⏭  Already exists: {key}")
        skipped += 1
        continue
    except ClientError as e:
        if e.response["Error"]["Code"] != "404":
            print(f"  ✗  head_object error for {key}: {e}")
            failed += 1
            continue

    # copy
    try:
        s3.copy_object(
            CopySource = {"Bucket": SRINIVAS_BUCKET, "Key": key},
            Bucket     = AZAD_BUCKET,
            Key        = key,
        )
        print(f"  ✓  Copied: {key}")
        copied += 1
    except ClientError as e:
        print(f"  ✗  Failed to copy {key}: {e}")
        failed += 1
        url_map.pop(url)   # don't update DB if copy failed

print(f"\nCopy done — {copied} copied, {skipped} already existed, {failed} failed\n")

# ── update DB ────────────────────────────────────────────────────────────────

def replace_in_value(value, url_map):
    if isinstance(value, str):
        for old, new in url_map.items():
            value = value.replace(old, new)
        return value
    return value

def replace_in_doc(doc, url_map):
    changes = 0
    def walk(obj):
        nonlocal changes
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, str):
                    new_v = replace_in_value(v, url_map)
                    if new_v != v:
                        obj[k] = new_v
                        changes += 1
                else:
                    walk(v)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                if isinstance(item, str):
                    new_item = replace_in_value(item, url_map)
                    if new_item != item:
                        obj[i] = new_item
                        changes += 1
                else:
                    walk(item)
    walk(doc)
    return changes

db_updated = 0
db_changes = 0

for col_name in ["chapters", "courses"]:
    col  = db[col_name]
    docs = list(col.find())
    for doc in docs:
        n = replace_in_doc(doc, url_map)
        if n:
            col.replace_one({"_id": doc["_id"]}, doc)
            db_updated += 1
            db_changes += n

print(f"DB updated — {db_updated} document(s), {db_changes} URL(s) replaced")
print("\n✓ All done. Srinivas files untouched, DB now points to azad.")
