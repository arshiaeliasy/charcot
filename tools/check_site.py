#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
شارکوت | Charcot — بررسی سلامت سایت (بدون وابستگی بیرونی)
-----------------------------------------------------------
قبل از push اجرا کن:

    python tools/check_site.py

بررسی می‌کند:
  • متعادل بودن تگ‌های HTML و نبود شناسهٔ تکراری
  • وجود همهٔ فایل‌های محلی ارجاع‌شده (لینک شکسته / تصویر گم‌شده)
  • بودن canonical، og:image، twitter:card، آیکون‌ها و theme-color در هر صفحه
  • نبود تصویر بدون alt و نبود onclick درون‌خطی
  • تطابق آدرس‌های sitemap.xml با فایل‌های واقعی

خروج با کد ۱ اگر ایرادی پیدا شود.
"""

import glob
import io
import os
import re
import sys
from html.parser import HTMLParser
from xml.etree import ElementTree

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}
REQUIRED_META = {
    'rel="canonical"': "canonical",
    '"og:image"': "og:image",
    '"twitter:card"': "twitter:card",
    'name="theme-color"': "theme-color",
    "img/favicon-32.png": "favicon 32",
    "favicon.ico": "favicon.ico",
    "apple-touch-icon": "apple-touch-icon",
}


class TagBalance(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self, convert_charrefs=True)
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append("تگ بستهٔ اضافه </%s> خط %d" % (tag, self.getpos()[0]))
            return
        if self.stack[-1][0] != tag:
            self.errors.append("عدم تطابق: انتظار </%s> (خط %d) اما </%s> در خط %d"
                               % (self.stack[-1][0], self.stack[-1][1], tag, self.getpos()[0]))
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i][0] == tag:
                    del self.stack[i:]
                    return
        else:
            self.stack.pop()


def read(path):
    return io.open(path, encoding="utf-8", newline="").read()


def main():
    problems = []
    pages = sorted(glob.glob("*.html"))
    if not pages:
        print("هیچ فایل HTML پیدا نشد؛ از ریشهٔ پروژه اجرا کن.")
        return 1

    for page in pages:
        s = read(page)
        parser = TagBalance()
        parser.feed(s)
        for err in parser.errors:
            problems.append("%s: %s" % (page, err))
        for tag, line in parser.stack:
            problems.append("%s: تگ باز مانده <%s> خط %d" % (page, tag, line))

        ids = re.findall(r'id="([A-Za-z0-9_-]+)"', s)
        for dup in sorted({i for i in ids if ids.count(i) > 1}):
            problems.append('%s: شناسهٔ تکراری id="%s"' % (page, dup))

        for match in re.finditer(r'(?:href|src)="([^"]+)"', s):
            url = match.group(1)
            if re.match(r"^(https?:|mailto:|tel:|#|data:|javascript:)", url):
                continue
            path = url.split("#")[0]
            if path and not os.path.exists(path):
                problems.append("%s: فایل موجود نیست -> %s" % (page, url))

        for needle, label in REQUIRED_META.items():
            if needle not in s:
                problems.append("%s: %s ندارد" % (page, label))

        for match in re.finditer(r"<img(?![^>]*\balt=)[^>]*>", s):
            problems.append("%s: تصویر بدون alt -> %s" % (page, match.group()[:60]))
        if re.search(r"\son(click|change|submit|input)=", s):
            problems.append("%s: هندلر درون‌خطی onclick/onchange باقی مانده" % page)

    if os.path.exists("sitemap.xml"):
        tree = ElementTree.parse("sitemap.xml")
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        for loc in tree.getroot().findall(".//s:loc", ns):
            url = (loc.text or "").strip()
            name = url.rsplit("/", 1)[-1] or "index.html"
            if not os.path.exists(name):
                problems.append("sitemap.xml: آدرس بدون فایل -> %s" % url)
    else:
        problems.append("sitemap.xml پیدا نشد")

    print("صفحات بررسی‌شده: %d" % len(pages))
    if problems:
        print("\nایرادها (%d):" % len(problems))
        for p in problems:
            print("  - " + p)
        return 1
    print("همه‌چیز سالم است ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
