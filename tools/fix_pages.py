# -*- coding: utf-8 -*-
"""
شارکوت | Charcot — اصلاح ساختار صفحات
--------------------------------------
یکبار اجرا کن (از ریشهٔ پروژه):

    python tools/fix_pages.py

چه میکند:
  ۱) <h1> جعلی هدر (نام سایت) را به <div class="brand-name"> تبدیل میکند
     تا هر صفحه فقط یک h1 معنادار داشته باشد.
  ۲) عنوان واقعی هر صفحه را به <h1> ارتقا میدهد (h2.page-title یا تیتر کیس).
  ۳) باکس «سلب مسئولیت آموزشی» را پیش از </footer> اضافه میکند (یکبار).
  ۴) داده ساختاریافته JSON-LD (WebSite/MedicalWebPage) را به <head> اضافه میکند.
  ۵) لینک «همین صفحه» و راهنمای چاپ را در هدر اضافه نمیکند؛ فقط متادیتا.

اجرای دوباره بیخطر است (idempotent).
"""

import glob
import io
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SITE = "شارکوت | Charcot"
BASE = "https://arshiaeliasy.github.io/charcot/"

DISCLAIMER_MARK = 'class="site-disclaimer"'
DISCLAIMER = """
            <div class="site-disclaimer" role="note">
                <span class="sd-icon" aria-hidden="true">i\uFE0F</span>
                <p><strong>یادآوری آموزشی:</strong> همهٔ مطالب این سایت با هدف <em>یادگیری و مرور</em> گردآوری شده است و جایگزین قضاوت بالینی، معاینهٔ بیمار یا دستور پزشک نیست. تصمیم درمانی تنها بر عهدهٔ کادر درمان و بر پایهٔ شرایط هر بیمار است.</p>
            </div>
"""

# توضیح کوتاه هر صفحه برای JSON-LD
PAGE_KIND = {
    "index.html": "WebSite",
    "about-us.html": "AboutPage",
}


def read(path):
    return io.open(path, encoding="utf-8", newline="").read()


def write(path, text):
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def fix_logo_h1(s):
    """h1 داخل .logo-text را به div تبدیل کن (بدون تغییر ظاهر)."""
    changed = False

    def repl(m):
        nonlocal changed
        changed = True
        return '<div class="brand-name">%s</div>' % m.group(1)

    s2 = re.sub(r'<h1>([^<]*شارکوت[^<]*)</h1>', repl, s, count=1)
    return s2, changed


def promote_title(s, page):
    """عنوان واقعی صفحه را h1 کن."""
    # حالت ۱: <h2 class="page-title">
    m = re.search(r'<h2 class="page-title">(.*?)</h2>', s, re.S)
    if m:
        return s.replace(m.group(0), '<h1 class="page-title">%s</h1>' % m.group(1), 1), m.group(1)

    # حالت ۲: صفحهٔ کیس → تیتر داخل کارت
    m = re.search(r'<h2>(کیس[^<]*)</h2>', s, re.S)
    if m:
        return s.replace(m.group(0), '<h1 class="case-title">%s</h1>' % m.group(1), 1), m.group(1)

    # حالت ۳: هیرو صفحهٔ اصلی
    if page == "index.html":
        m = re.search(r'<h2>(.*?)</h2>', s, re.S)
        if m:
            return s.replace(m.group(0), '<h1 class="hero-title">%s</h1>' % m.group(1), 1), m.group(1)

    # حالت ۴: about-us → اولین h2 داخل محتوا
    m = re.search(r'<h2>(.*?)</h2>', s, re.S)
    if m:
        return s.replace(m.group(0), '<h1 class="page-title">%s</h1>' % m.group(1), 1), m.group(1)

    return s, ""


def add_disclaimer(s):
    if DISCLAIMER_MARK in s:
        return s, False
    m = re.search(r'\n(\s*)<div class="footer-bottom">', s)
    if not m:
        return s, False
    return s[:m.start()] + "\n" + DISCLAIMER + s[m.start():], True


def add_jsonld(s, page, title):
    if 'application/ld+json' in s:
        return s, False
    url = BASE + page
    name = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", title)).strip()
    kind = PAGE_KIND.get(page, "MedicalWebPage")
    data = {
        "@context": "https://schema.org",
        "@type": kind,
        "name": name,
        "headline": name,
        "url": url,
        "inLanguage": "fa-IR",
        "isPartOf": {"@type": "WebSite", "name": SITE, "url": BASE},
        "publisher": {"@type": "Organization", "name": SITE, "url": BASE},
        "audience": {"@type": "EducationalAudience", "educationalRole": "student"},
        "about": "آموزش پزشکی",
    }
    if "og:image" in s:
        img = re.search(r'property="og:image" content="([^"]+)"', s)
        if img:
            data["image"] = img.group(1)
    desc = re.search(r'name="description" content="([^"]*)"', s)
    if desc:
        data["description"] = desc.group(1)
    block = (
        '    <script type="application/ld+json">\n'
        + json.dumps(data, ensure_ascii=False, indent=8).replace("\n", "\n    ")
        + "\n    </script>\n"
    )
    return s.replace("</head>", block + "</head>", 1), True


def main():
    pages = sorted(glob.glob("*.html"))
    if not pages:
        print("فایل HTML پیدا نشد؛ از ریشهٔ پروژه اجرا کن.")
        return 1

    report = []
    for page in pages:
        if page.startswith("_"):
            continue
        s = read(page)
        orig = s
        s, logo_fixed = fix_logo_h1(s)
        s, title = promote_title(s, page)
        s, disc_added = add_disclaimer(s)
        s, ld_added = add_jsonld(s, page, title)
        if s != orig:
            write(page, s)
        report.append((page, logo_fixed, bool(title), disc_added, ld_added, title))

    print("%-24s %-6s %-6s %-6s %-6s %s" % ("صفحه", "لوگو", "h1", "سلب", "JSON-LD", "عنوان"))
    for page, a, b, c, d, title in report:
        clean = re.sub(r"<[^>]+>", "", title)
        clean = re.sub(r"\s+", " ", clean).strip()[:44]
        print("%-24s %-6s %-6s %-6s %-6s %s" % (
            page,
            "✔" if a else "—",
            "✔" if b else "!",
            "✔" if c else "—",
            "✔" if d else "—",
            clean,
        ))
    missing = [p for p, a, b, c, d, t in report if not b]
    if missing:
        print("\nهشدار: برای این صفحهها عنوان h1 پیدا نشد:", missing)
        return 1
    print("\nهمهٔ %d صفحه اصلاح شد ✅" % len(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
