"""
List all unique domains found in URLs across chapters + courses in new DB.
Run: python list_domains.py
"""
import re, os
from urllib.parse import urlparse
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

db     = MongoClient(os.getenv("MONGO_URI"))[os.getenv("DB_NAME", "course_platform")]
URL_RE = re.compile(r'https?://[^\s"\'<>]+')

def all_strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from all_strings(v)
    elif isinstance(obj, list):
        for i in obj:
            yield from all_strings(i)

domains = set()

for col in ["chapters", "courses"]:
    for doc in db[col].find():
        for s in all_strings(doc):
            for url in URL_RE.findall(s):
                try:
                    domains.add(urlparse(url).netloc)
                except Exception:
                    pass

print(f"\n{len(domains)} unique domain(s):\n")
for d in sorted(domains):
    print(f"  {d}")
