# -*- coding: utf-8 -*-
"""
شارکوت | Charcot — بررسی «قالب مشترک» بین همهٔ صفحه‌ها
------------------------------------------------------
    python tools/check_template.py

هدف: مطمئن شویم هر ۱۲ صفحه از یک قالب واحد ساخته شده‌اند و کسی
(یا ابزاری) هدر/فوتر/سلب مسئولیت/داده ساختاریافته را ناقص نگذاشته است.

بررسی‌ها:
  ۱) هدر: اسکلت یکی است؛ فقط نام صفحه و آیتم فعال منو تفاوت دارد
  ۲) فوتر: کاملاً یکسان
  ۳) سلب مسئولیت آموزشی: کاملاً یکسان و در همهٔ صفحه‌ها
  ۴) JSON-LD: همان ۱۲ کلید و مقادیر معتبر
  ۵) منوی اصلی: همان ۸ لینک در همهٔ صفحه‌ها
  ۶) اکشن‌های هدر: جستجو/تم/منو در همهٔ صفحه‌ها
  ۷) پنجرهٔ جستجو و عناصر مشترک جاوااسکریپت
"""

import glob
import hashlib
import io
import json
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PROBLEMS = []
NOTES = []
pages = sorted(p for p in glob.glob("*.html") if not p.startswith("_"))


def read(p):
    return io.open(p, encoding="utf-8", newline="").read()


def block(s, start, end):
    i = s.find(start)
    j = s.find(end, i)
    return s[i:j] if i != -1 and j != -1 else ""


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r">\s*<", "><", s)).strip()


def header_skeleton(h):
    """نام صفحه، آیتم فعال منو و aria-current را حذف می‌کند."""
    h = re.sub(
        r'(<div class="logo-text">\s*<div class="brand-name">.*?</div>\s*<span>).*?(</span>)',
        r"\1SKEL\2", h, flags=re.S)
    h = re.sub(r"\s(?:class=\"[^\"]*\bactive\b[^\"]*\"|aria-current=\"page\")", "", h)
    return norm(h)


# ---------- ۱) هدر ----------
groups = {}
for f in pages:
    h = block(read(f), "<header", "</header>")
    if not h:
        PROBLEMS.append("%s: تگ <header> پیدا نشد" % f)
        continue
    groups.setdefault(hashlib.md5(header_skeleton(h).encode()).hexdigest()[:8], []).append(f)
if len(groups) != 1:
    PROBLEMS.append("هدر صفحه‌ها یکسان نیست: %d گونه" % len(groups))
    for k, v in groups.items():
        NOTES.append("   گونهٔ %s -> %s" % (k, ", ".join(v)))
else:
    NOTES.append("هدر: %d صفحه با اسکلت یکسان" % len(pages))

# ---------- ۲) فوتر ----------
foots = {hashlib.md5(norm(block(read(f), "<footer", "</footer>")).encode()).hexdigest()
         for f in pages}
if len(foots) != 1:
    PROBLEMS.append("فوتر صفحه‌ها یکسان نیست (%d گونه)" % len(foots))
else:
    NOTES.append("فوتر: کاملاً یکسان در %d صفحه" % len(pages))

# ---------- ۳) سلب مسئولیت ----------
disc = {hashlib.md5(norm(block(read(f), '<div class="site-disclaimer"', "</section>")).encode()).hexdigest()
        for f in pages}
if len(disc) != 1:
    PROBLEMS.append("باکس سلب مسئولیت یکسان نیست (%d گونه)" % len(disc))
else:
    NOTES.append("سلب مسئولیت آموزشی: یکسان در %d صفحه" % len(pages))

# ---------- ۴) JSON-LD ----------
KEYS = {"@context", "@type", "name", "headline", "description", "url", "inLanguage",
        "isPartOf", "publisher", "audience", "image", "about"}
types = {}
for f in pages:
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', read(f), re.S)
    if not m:
        PROBLEMS.append("%s: JSON-LD ندارد" % f)
        continue
    try:
        obj = json.loads(m.group(1))
    except Exception as exc:
        PROBLEMS.append("%s: JSON-LD نامعتبر (%s)" % (f, exc))
        continue
    missing = KEYS - set(obj)
    if missing:
        PROBLEMS.append("%s: کلیدهای JSON-LD ناقص -> %s" % (f, sorted(missing)))
    if obj.get("@context") != "https://schema.org":
        PROBLEMS.append("%s: @context نادرست" % f)
    if obj.get("inLanguage") != "fa-IR":
        PROBLEMS.append("%s: inLanguage باید fa-IR باشد" % f)
    if obj.get("url") != "https://arshiaeliasy.github.io/charcot/" + f:
        PROBLEMS.append("%s: url در JSON-LD با canonical یکی نیست" % f)
    if obj.get("image") != "https://arshiaeliasy.github.io/charcot/img/og/" + f.replace(".html", ".jpg"):
        PROBLEMS.append("%s: image در JSON-LD با og:image یکی نیست" % f)
    types[obj.get("@type")] = types.get(obj.get("@type"), 0) + 1
NOTES.append("JSON-LD: %s" % ", ".join("%s×%d" % (k, v) for k, v in sorted(types.items())))

# ---------- ۵) منوی اصلی ----------
NAV = ["basic-sciences.html", "pathophysiology.html", "externship.html", "pre-internship.html",
       "internship.html", "clinical-cases.html", "clinical-notes.html", "about-us.html"]
for f in pages:
    nav = block(read(f), 'class="main-nav"', "</nav>")
    hrefs = re.findall(r'href="([^"]+)"', nav)
    if hrefs != NAV:
        PROBLEMS.append("%s: منوی اصلی ناقص/نامرتب -> %s" % (f, hrefs))

# ---------- ۶) اکشن‌های هدر ----------
for f in pages:
    s = read(f)
    for eid in ("searchBtn", "themeBtn", "menuBtn"):
        if 'id="%s"' % eid not in s:
            PROBLEMS.append("%s: دکمهٔ %s در هدر نیست" % (f, eid))

# ---------- ۷) عناصر مشترک جاوااسکریپت ----------
# این عناصر در زمان اجرا ساخته می‌شوند، پس وجودشان در js/main.js بررسی می‌شود
RUNTIME = {
    "پنجرهٔ جستجو": "searchOverlay = document.createElement",
    "نوار پیشرفت مطالعه": "'scroll-progress'",
    "دکمهٔ بازگشت به بالا": "'back-to-top'",
    "ظرف Toast": "'toastContainer'",
    "فهرست چسبان بخش‌ها": "function buildToc",
}
main_js = read("js/main.js")
for label, needle in RUNTIME.items():
    if needle not in main_js:
        PROBLEMS.append("js/main.js: %s ساخته نمی‌شود (%s)" % (label, needle))

for f in pages:
    s = read(f)
    if 'href="css/style.css"' not in s:
        PROBLEMS.append("%s: استایل مشترک لینک نشده" % f)
    if 'src="js/main.js"' not in s:
        PROBLEMS.append("%s: js/main.js لینک نشده" % f)
    if s.count("<h1") != 1:
        PROBLEMS.append("%s: باید دقیقاً یک h1 داشته باشد" % f)
    if 'class="site-header"' not in s:
        PROBLEMS.append("%s: هدر مشترک نیست" % f)
    # صفحهٔ اصلی breadcrumb ندارد (خودش ریشه است)؛ بقیه باید داشته باشند
    if f != "index.html" and 'class="crumbs"' not in s:
        PROBLEMS.append("%s: مسیر صفحه (breadcrumb) ندارد" % f)
NOTES.append("عناصر زمان اجرا در js/main.js: %d مورد بررسی شد" % len(RUNTIME))

# ---------- گزارش ----------
print("صفحه‌های بررسی‌شده: %d" % len(pages))
for n in NOTES:
    print(n)
if PROBLEMS:
    print("\nایرادهای قالب مشترک (%d):" % len(PROBLEMS))
    for p in PROBLEMS:
        print("  -", p)
    sys.exit(1)
print("\nقالب مشترک: همهٔ صفحه‌ها هم‌ساخت هستند ✅")
