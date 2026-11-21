# -*- coding: utf-8 -*-
"""
شارکوت | Charcot — ساخت sitemap.xml از روی صفحه‌های واقعی
--------------------------------------------------------
    python tools/make_sitemap.py
    python tools/make_sitemap.py --selftest

* هر ۱۲ صفحه با اولویت و changefreq مناسب ثبت می‌شود.
* تاریخ آخرین تغییر از mtime خود فایل خوانده می‌شود (نه تاریخ دستی).
* ترتیب بر اساس اولویت (نزولی) است تا خزندهٔ گوگل مهم‌ترین صفحه را اول ببیند.
"""

import glob
import io
import os
import sys
from datetime import datetime, timezone

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE = "https://arshiaeliasy.github.io/charcot/"
OUT = "sitemap.xml"

# اولویت و بازهٔ بازبینی هر صفحه
PLAN = {
    "index.html":          ("1.0", "weekly"),
    "basic-sciences.html": ("0.9", "weekly"),
    "externship.html":     ("0.9", "weekly"),
    "clinical-notes.html": ("0.9", "weekly"),
    "clinical-cases.html": ("0.9", "weekly"),
    "pre-internship.html": ("0.8", "weekly"),
    "internship.html":     ("0.8", "weekly"),
    "pathophysiology.html": ("0.8", "weekly"),
    "case-stroke.html":    ("0.7", "monthly"),
    "case-acs.html":       ("0.7", "monthly"),
    "case-sepsis.html":    ("0.7", "monthly"),
    "about-us.html":       ("0.6", "monthly"),
}


def lastmod(path):
    ts = os.path.getmtime(path)
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")


def build():
    rows = []
    for page in sorted(PLAN, key=lambda p: (-float(PLAN[p][0]), p)):
        if not os.path.exists(page):
            print("هشدار: صفحه وجود ندارد -> %s" % page)
            continue
        priority, freq = PLAN[page]
        rows.append((BASE + page, lastmod(page), freq, priority))

    extra = [p for p in glob.glob("*.html") if p not in PLAN and not p.startswith("_")]
    if extra:
        print("توجه: این صفحه‌ها در sitemap نیستند -> %s" % extra)

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, mod, freq, prio in rows:
        lines += [
            "    <url>",
            "        <loc>%s</loc>" % loc,
            "        <lastmod>%s</lastmod>" % mod,
            "        <changefreq>%s</changefreq>" % freq,
            "        <priority>%s</priority>" % prio,
            "    </url>",
        ]
    lines.append("</urlset>")
    lines.append("")

    with io.open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines))

    print("%s | %d آدرس | آخرین تغییرها %s..%s" % (
        OUT, len(rows), rows[-1][1], rows[0][1]))
    return rows


def selftest(rows):
    import re

    problems = []
    s = io.open(OUT, encoding="utf-8").read()
    if s.count("<url>") != len(rows):
        problems.append("تعداد url با ورودی‌ها یکی نیست")
    for loc, mod, freq, prio in rows:
        block = re.search(r"<url>\s*<loc>%s</loc>(.*?)</url>" % re.escape(loc), s, re.S)
        if not block:
            problems.append("بلوک url پیدا نشد: %s" % loc)
            continue
        body = block.group(1)
        if "<lastmod>%s</lastmod>" % mod not in body:
            problems.append("lastmod نادرست در %s" % loc)
        if "<changefreq>%s</changefreq>" % freq not in body:
            problems.append("changefreq نادرست در %s" % loc)
        if "<priority>%s</priority>" % prio not in body:
            problems.append("priority نادرست در %s" % loc)
        if not loc.startswith(BASE):
            problems.append("آدرس اشتباه: %s" % loc)
        # وجود واقعی تصویر og هر صفحه
        img = "img/og/" + loc.rsplit("/", 1)[-1].replace(".html", ".jpg")
        if not os.path.exists(img):
            problems.append("تصویر og وجود ندارد: %s" % img)
    if "index.html" not in s:
        problems.append("صفحهٔ اصلی در sitemap نیست")
    if not s.endswith("</urlset>\n"):
        problems.append("پایان فایل XML نادرست است")
    print("SITEMAP SELFTEST: %s (%d آدرس)" % ("PASS ✅" if not problems else "FAIL ❌", len(rows)))
    for p in problems:
        print("  -", p)
    return 0 if not problems else 1


if __name__ == "__main__":
    rows = build()
    if "--selftest" in sys.argv:
        sys.exit(selftest(rows))
