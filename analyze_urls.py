"""
Scan all chapters in azad-db, extract every URL field,
and print unique domains with counts.
Run: python analyze_urls.py
"""
import re
from urllib.parse import urlparse
from collections import defaultdict
from pymongo import MongoClient

OLD_URI = "mongodb+srv://user:user@cluster0.rgocxdb.mongodb.net/azad-db"
old_db  = MongoClient(OLD_URI)["azad-dbto doanaylse for new mogodb db"]

# Regex to catch any http/https URL inside a string value
URL_RE = re.compile(r'https?://[^\s"\'<>]+')

domain_counts  = defaultdict(int)   # domain → total URLs
domain_fields  = defaultdict(set)   # domain → which fields it appeared in
domain_samples = defaultdict(set)   # domain → sample URLs (max 3)


def extract_urls_from_value(value):
    """Return all URLs found in a string value."""
    if not isinstance(value, str):
        return []
    return URL_RE.findall(value)


def scan_doc(doc, path=""):
    """Recursively walk a document and yield (field_path, url)."""
    if isinstance(doc, dict):
        for k, v in doc.items():
            yield from scan_doc(v, path=f"{path}.{k}" if path else k)
    elif isinstance(doc, list):
        for i, item in enumerate(doc):
            yield from scan_doc(item, path=f"{path}[{i}]")
    elif isinstance(doc, str):
        for url in extract_urls_from_value(doc):
            yield path, url


def domain_of(url):
    try:
        return urlparse(url).netloc
    except Exception:
        return "invalid"


# ── scan chapters collection ─────────────────────────────────────────────────

chapters = list(old_db["chapters"].find())
print(f"Scanning {len(chapters)} chapter(s)...\n")

total_urls = 0

for ch in chapters:
    for field_path, url in scan_doc(ch):
        domain = domain_of(url)
        domain_counts[domain] += 1
        domain_fields[domain].add(field_path)
        if len(domain_samples[domain]) < 3:
            domain_samples[domain].add(url)
        total_urls += 1

# ── also scan courses for thumbnail_url ──────────────────────────────────────

courses = list(old_db["courses"].find())
print(f"Scanning {len(courses)} course(s) for thumbnail/top-level URLs...\n")

for c in courses:
    for field_path, url in scan_doc(c):
        # skip _id and non-url noise
        if "chapter" in field_path.lower():
            continue
        domain = domain_of(url)
        domain_counts[domain] += 1
        domain_fields[domain].add(f"[course] {field_path}")
        if len(domain_samples[domain]) < 3:
            domain_samples[domain].add(url)
        total_urls += 1

# ── report ───────────────────────────────────────────────────────────────────

print("=" * 70)
print(f"{'DOMAIN':<45} {'COUNT':>6}  FIELDS")
print("=" * 70)

for domain, count in sorted(domain_counts.items(), key=lambda x: -x[1]):
    fields = ", ".join(sorted(domain_fields[domain]))
    print(f"{domain:<45} {count:>6}  {fields}")

print("=" * 70)
print(f"Total URLs found: {total_urls}")
print(f"Unique domains  : {len(domain_counts)}\n")

print("Sample URLs per domain:")
print("-" * 70)
for domain, count in sorted(domain_counts.items(), key=lambda x: -x[1]):
    print(f"\n  {domain} ({count} URLs)")
    for s in list(domain_samples[domain])[:3]:
        print(f"    {s[:100]}")
