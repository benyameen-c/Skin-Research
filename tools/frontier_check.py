#!/usr/bin/env python3
"""Check content/frontier-scan.md: every quoted string must appear in a saved
source named in the same paragraph (PMID, NCT, GEO accession or the search log).

Usage: python3 tools/frontier_check.py [excerpts_dir]
Exit 1 if any quote cannot be matched.
"""
import re, sys, os, glob

PAGE = 'content/frontier-scan.md'
DIR = sys.argv[1] if len(sys.argv) > 1 else '/mnt/project-files/papers/excerpts/'

def norm(s):
    return re.sub(r'\s+', ' ', s.replace('−', '-')).strip()

def load(name):
    for p in (os.path.join(DIR, name), name):
        if os.path.exists(p):
            return norm(open(p, errors='replace').read())
    return None

text = open(PAGE).read()
paras = [p for p in text.split('\n\n')]
fails, checked = [], 0
for para in paras:
    if para.lstrip().startswith('<p>') or para.lstrip().startswith('| ID |'):
        continue
    ids = []
    for m in re.findall(r'PMID (\d{4,9})', para):
        ids.append('pmid_%s.txt' % m)
    for m in re.findall(r'(NCT\d{8})', para):
        ids.append('%s.api.json' % m.lower())
    if re.search(r'GSE\d+|geo_frontier', para):
        ids.append('geo_frontier_summaries.txt')
    if 'search log' in para or 'search_log' in para:
        ids.append('data/search_log.csv')
    for m in re.findall(r'ledger id (\w+)|ledger as (\w+)', para):
        for g in m:
            if g:
                ids.append('%s.txt' % g)
    bodies = [(n, load(n)) for n in ids]
    bodies = [(n, b) for n, b in bodies if b]
    # quoted spans: straight double quotes, taken in pairs on one line
    for line in para.split('\n'):
        for q in re.findall(r'"([^"\n]{3,})"', line):
            qn = norm(q)
            checked += 1
            if not any(qn in b for _, b in bodies):
                fails.append((qn[:70], [n for n, _ in bodies]))

print('quotes checked: %d' % checked)
for q, src in fails:
    print('FAIL: "%s" not found in %s' % (q, src or 'no source named in paragraph'))
print('fails: %d' % len(fails))
sys.exit(1 if fails else 0)
