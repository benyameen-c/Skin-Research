#!/usr/bin/env python3
"""Check content/photo-methods-review.md: every quoted string must appear in a
saved source text named in the same '## ' section (a `<file>.txt` in backticks).

Quotes are spans in straight double quotes on one line. A quote in a section
that names no source counts as a failure. Whitespace is collapsed and the
Unicode minus is read as a hyphen on both sides before matching.

Usage: python3 tools/photo_methods_check.py [excerpts_dir]
Default excerpts_dir: /mnt/project-files/papers/excerpts/
Exit 1 if any quote cannot be matched or a named source is missing.
"""
import os
import re
import sys

PAGE = 'content/photo-methods-review.md'
DIR = sys.argv[1] if len(sys.argv) > 1 else '/mnt/project-files/papers/excerpts/'
SOURCE_RE = re.compile(r'`([A-Za-z0-9_]+\.txt)`')
QUOTE_RE = re.compile(r'"([^"\n]{3,})"')


def norm(s):
    return re.sub(r'\s+', ' ', s.replace('−', '-')).strip()


def main():
    text = open(PAGE, encoding='utf-8').read()
    sections = re.split(r'\n(?=## )', text)
    checked, fails = 0, []
    for sec in sections:
        title = sec.split('\n', 1)[0]
        names = sorted(set(SOURCE_RE.findall(sec)))
        bodies = []
        for n in names:
            path = os.path.join(DIR, n)
            if not os.path.exists(path):
                fails.append((title, n, 'source file missing'))
                continue
            bodies.append(norm(open(path, encoding='utf-8', errors='replace').read()))
        for line in sec.split('\n'):
            for q in QUOTE_RE.findall(line):
                checked += 1
                qn = norm(q)
                if not any(qn in b for b in bodies):
                    fails.append((title, qn[:70], 'not found in ' + (', '.join(names) or 'no source named')))
    print('quotes checked: %d' % checked)
    for t, q, why in fails:
        print('FAIL [%s] "%s": %s' % (t[:40], q, why))
    print('fails: %d' % len(fails))
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
