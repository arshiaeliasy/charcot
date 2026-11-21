# -*- coding: utf-8 -*-
"""
شارکوت | Charcot — راستی‌آزمایی نهایی سایت
------------------------------------------
    python tools/verify_changes.py

بررسی می‌کند (پس از هر تغییر اجرا کن):
  ۱) هر صفحه دقیقاً یک <h1> دارد و آن عنوان خودِ صفحه است (نه نام سایت)
  ۲) canonical / og:image اختصاصی / twitter / theme-color در هر صفحه
  ۳) باکس سلب مسئولیت آموزشی و JSON-LD در هر صفحه
  ۴) فرم‌ها و شناسه‌های احراز هویت در index.html
  ۵) آکاردئون‌های استاجری و تطابق با ایندکس جستجو و فهرست بالای صفحه
  ۶) درستی ایندکس جستجوی متن (js/search-index.json)
  ۷) متغیرهای رنگ تم (کنتراست‌محور) و توکن‌های جدید
  ۸) نبود آیکون شکسته و تصویر بدون alt
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

problems = []
notes = []


def read(path):
    return io.open(path, encoding="utf-8", newline="").read()


pages = sorted(p for p in glob.glob("*.html") if not p.startswith("_"))
if not pages:
    print("فایل HTML پیدا نشد؛ از ریشهٔ پروژه اجرا کن.")
    sys.exit(1)

BASE = "https://arshiaeliasy.github.io/charcot/"

# ---------- ۱) ساختار هدینگ ----------
for f in pages:
    s = read(f)
    h1s = re.findall(r"<h1[^>]*>(.*?)</h1>", s, re.S)
    if len(h1s) != 1:
        problems.append("%s: باید دقیقاً یک <h1> داشته باشد (یافت شد: %d)" % (f, len(h1s)))
        continue
    h1 = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", h1s[0])).strip()
    # آیکون‌ها و نشانه‌های ابتدای عنوان را برای مقایسه حذف کن
    h1_word = re.sub(r"^[^\w\u0600-\u06FF]+", "", h1).strip()
    if h1_word == "شارکوت | Charcot" or h1_word.startswith("شارکوت | Charcot"):
        problems.append("%s: <h1> هنوز نام سایت است، نه عنوان صفحه -> %s" % (f, h1))
    if len(h1_word) < 4:
        problems.append("%s: عنوان <h1> بسیار کوتاه است -> %s" % (f, h1))
    if '<div class="brand-name">' not in s:
        problems.append("%s: نام سایت باید در div.brand-name باشد (نه h1)" % f)

# ---------- ۲) متادیتا ----------
for f in pages:
    s = read(f)
    for needle in ('rel="canonical"', 'property="og:url"', 'name="theme-color"',
                   'getPropertyValue(\'--theme-color\')', 'application/ld+json',
                   'class="site-disclaimer"'):
        if needle not in s:
            problems.append("%s: ندارد -> %s" % (f, needle))
    m = re.search(r'property="og:image" content="([^"]+)"', s)
    expected = BASE + "img/og/" + f.replace(".html", ".jpg")
    if not m:
        problems.append("%s: og:image پیدا نشد" % f)
    elif m.group(1) != expected:
        problems.append("%s: og:image اختصاصی نیست -> %s" % (f, m.group(1)))
    else:
        rel = m.group(1).replace(BASE, "")
        if not os.path.exists(rel):
            problems.append("%s: فایل og:image وجود ندارد -> %s" % (f, rel))
    if 'property="og:image:alt"' not in s:
        problems.append("%s: og:image:alt ندارد" % f)

# ---------- ۳) فرم‌های احراز هویت ----------
idx = read("index.html")
for fid in ("loginForm", "registerForm", "forgotPasswordForm", "resetPasswordForm",
            "newPassword", "newPassword2", "resetBtn", "authNotice", "userProfile"):
    if 'id="%s"' % fid not in idx:
        problems.append("index.html: فرم/فیلد %s پیدا نشد" % fid)

# ---------- ۴) آکاردئون‌های استاجری ----------
ext = read("externship.html")
ext_ids = re.findall(r'<div class="accordion-item" id="([^"]+)"', ext)
main = read("js/main.js")
search_anchors = re.findall(r"url: 'externship\.html#([a-z-]+)'", main)

expected = ["internal-medicine", "general-surgery", "pediatrics", "obgyn", "neurology",
            "cardiology", "infectious-diseases", "psychiatry", "orthopedics", "ophthalmology",
            "ent", "dermatology", "urology", "anesthesia-emergency"]
if ext_ids != expected:
    problems.append("externship.html: آیدی‌ها مطابق انتظار نیست -> %s" % ext_ids)
if sorted(search_anchors) != sorted(expected):
    problems.append("main.js: لنگرهای جستجوی استاجری ناقص است -> %s" % search_anchors)
toc = re.findall(r'<li><a href="#([a-z-]+)"', ext)
if sorted(toc) != sorted(expected):
    problems.append("externship.html: فهرست بالای صفحه کامل نیست -> %s" % toc)
for h in re.findall(r'<button class="accordion-header"[^>]*>(.*?)</button>', ext, re.S):
    if h.count("<span") != 2 or "accordion-icon" not in h:
        problems.append("externship.html: سرتیتر نامعتبر -> %s" % h[:70].replace("\n", " "))

# ---------- ۵) ایندکس جستجوی متن ----------
if not os.path.exists("js/search-index.json"):
    problems.append("js/search-index.json وجود ندارد (tools/make_search_index.py را اجرا کن)")
else:
    try:
        data = json.loads(read("js/search-index.json"))
    except Exception as exc:
        problems.append("js/search-index.json قابل خواندن نیست: %s" % exc)
        data = None
    if data:
        indexed = set(data.get("pages", {}))
        if indexed != set(pages):
            problems.append("ایندکس جستجو با صفحه‌ها هم‌خوان نیست: %s" %
                            sorted(set(pages) ^ indexed))
        total = 0
        for page, info in data["pages"].items():
            secs = info.get("sections", [])
            total += len(secs)
            if not secs:
                problems.append("ایندکس جستجو: صفحهٔ %s هیچ بخشی ندارد" % page)
            for sec in secs:
                if sec.get("id"):
                    anchor = 'id="%s"' % sec["id"]
                    if anchor not in read(page):
                        problems.append("ایندکس جستجو: لنگر %s در %s نیست" % (sec["id"], page))
                if "\u25bc" in sec.get("text", ""):
                    problems.append("ایندکس جستجو: فلش آکاردئون در متن %s#%s" % (page, sec.get("id")))
        notes.append("بخش‌های ایندکس جستجو: %d" % total)
        # صفحهٔ اصلی نباید در جستجوی متن سنگین باشد
        if len(data["pages"].get("index.html", {}).get("sections", [])) > 6:
            problems.append("ایندکس جستجو: بخش‌های ناوبری صفحهٔ اصلی فیلتر نشده‌اند")

# ---------- ۶) تم و رنگ‌ها ----------
css = read("css/style.css")
if css.count("--theme-color:") != 2:
    problems.append("style.css: --theme-color باید دو بار (تیره/روشن) تعریف شود")
for token in ("--danger: #ef4444", "--danger: #DC2626",
              "--accent-ink: #2DD4BF", "--accent-ink: #0B6E66",
              "--danger-ink: #F87171", "--danger-ink: #B91C1C"):
    if token not in css:
        problems.append("style.css: توکن رنگ %s پیدا نشد" % token)
for token in (".site-disclaimer", ".toc-nav", ".page-layout", "@media print",
              ".search-result .r-hit"):
    if token not in css:
        problems.append("style.css: استایل %s تعریف نشده" % token)

# ---------- ۷) آیکون شکسته و alt ----------
for f in pages + ["js/main.js"]:
    s = read(f)
    if "i\uFE0F" in s:
        problems.append("%s: آیکون شکستهٔ 'i' + U+FE0F باقی مانده" % f)
    if "\u2139\uFE0F" not in s and f in ("about-us.html", "index.html", "js/main.js"):
        problems.append("%s: آیکون اطلاعات ندارد" % f)
for f in pages:
    s = read(f)
    for m in re.finditer(r"<img(?![^>]*\balt=)[^>]*>", s):
        problems.append("%s: تصویر بدون alt -> %s" % (f, m.group()[:60]))

# ---------- گزارش ----------
print("صفحات بررسی‌شده: %d" % len(pages))
print("آکاردئون‌های استاجری: %d" % len(ext_ids))
print("لنگرهای جستجوی استاجری: %d" % len(search_anchors))
for n in notes:
    print(n)
if problems:
    print("\nایرادها (%d):" % len(problems))
    for p in problems:
        print("  -", p)
    sys.exit(1)
print("\nراستی‌آزمایی: همه‌چیز درست است ✅")
