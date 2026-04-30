"""Merge per-subject Kannada title JSONs into titles_export_kn.csv."""

import csv, json, os, sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE = os.path.dirname(__file__)
SRC  = os.path.join(BASE, 'titles_export.csv')
OUT  = os.path.join(BASE, 'titles_export_kn.csv')

with open(os.path.join(BASE, 'kn_maths.json'),   encoding='utf-8') as f: kn_maths   = json.load(f)
with open(os.path.join(BASE, 'kn_science.json'), encoding='utf-8') as f: kn_science = json.load(f)
with open(os.path.join(BASE, 'kn_social.json'),  encoding='utf-8') as f: kn_social  = json.load(f)

LOOKUP = {
    'Mathematics / ಗಣಿತ':           kn_maths,
    'Science / ವಿಜ್ಞಾನ':              kn_science,
    'Social Studies / ಸಮಾಜ ವಿಜ್ಞಾನ': kn_social,
}

with open(SRC, encoding='utf-8-sig') as f, open(OUT, 'w', newline='', encoding='utf-8-sig') as g:
    r = csv.DictReader(f)
    fieldnames = r.fieldnames + ['session_title_kn']
    w = csv.DictWriter(g, fieldnames=fieldnames)
    w.writeheader()
    missing = 0
    for row in r:
        kn = LOOKUP.get(row['subject'], {}).get(row['session_no'], '')
        if not kn:
            missing += 1
        row['session_title_kn'] = kn
        w.writerow(row)

print(f"Wrote {OUT}")
if missing:
    print(f"WARNING: {missing} rows had no Kannada match")
