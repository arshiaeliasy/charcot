# -*- coding: utf-8 -*-
"""
شارکوت | Charcot — ساخت ایندکس جستجوی سراسری متن
-------------------------------------------------
    python tools/make_search_index.py

خروجی: js/search-index.json
  {
    "generated": "...",
    "pages": {
      "clinical-notes.html": {
         "title": "یادداشت‌های بالینی",
         "sections": [
            {"id": "case-myositis", "title": "کیس ۱: ...", "text": "متن کامل برای جستجو"},
            ...
         ]
      }
    }
  }

قواعد:
  • محتوای آکاردئون‌ها به تفکیک هر بخش ایندکس می‌شود (لنگر = id آکاردئون).
  • صفحه‌های بدون آکاردئون بر اساس سرفصل‌هایشان (h2/h3/h4) بخش‌بندی می‌شوند.
  • متن ناوبری/فوتر/هدر/اسکریپت هرگز ایندکس نمی‌شود.
  • لنگرهای هدر صفحه با :::  از متن جدا می‌شوند و در جستجو نقش کمتری دارند.
"""

import glob
import io
import json
import os
import re
import sys
import time
import unicodedata

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

OUT = os.path.join("js", "search-index.json")
MAX_TEXT = 4000          # سقف متن هر بخش (کاراکتر) — جلوگیری از باد کردن فایل
MIN_TEXT = 40            # بخش‌های خیلی کوتاه نادیده گرفته می‌شوند

# ترتیب اهمیت صفحه‌ها در نتایج
# وزن کمتر = بالاتر در نتایج. صفحهٔ اصلی پایین‌ترین اولویت را دارد
# تا صفحهٔ تخصصی همان موضوع زودتر دیده شود.
PAGE_WEIGHT = {
    "index.html": 9,
    "basic-sciences.html": 1,
    "externship.html": 1,
    "clinical-notes.html": 1,
    "clinical-cases.html": 2,
    "pathophysiology.html": 2,
    "pre-internship.html": 2,
    "internship.html": 2,
}


def read(path):
    return io.open(path, encoding="utf-8", newline="").read()


def strip_chrome(html):
    """هدر، فوتر، منو، اسکریپت و استایل را حذف می‌کند."""
    s = html
    s = re.sub(r"(?s)<script.*?</script>", " ", s)
    s = re.sub(r"(?s)<style.*?</style>", " ", s)
    s = re.sub(r"(?s)<header.*?</header>", " ", s)
    s = re.sub(r"(?s)<nav.*?</nav>", " ", s)
    s = re.sub(r"(?s)<footer.*?</footer>", " ", s)
    s = re.sub(r"(?s)<div class=\"site-disclaimer\".*?</div>\s*</div>", " ", s)
    return s


def to_text(html):
    s = re.sub(r"(?s)<br\s*/?>", " ", html)
    s = re.sub(r"(?s)</(p|li|div|h1|h2|h3|h4|tr)>", " \n", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    s = s.replace("&quot;", '"').replace("&#39;", "'")
    s = s.replace("\u25bc", " ").replace("\u25b2", " ")   # فلش آکاردئون/FAQ
    s = re.sub(r"[ \t\u200c]+", " ", s)
    s = re.sub(r"\n\s*\n+", "\n", s)
    return s.strip()


def clean_title(html):
    html = re.sub(r'<span class="accordion-icon"[^>]*>.*?</span>', " ", html, flags=re.S)
    t = re.sub(r"<[^>]+>", "", html)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def page_title(html):
    m = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.S)
    if m:
        return clean_title(m.group(1))
    m = re.search(r"<title>(.*?)</title>", html, re.S)
    return clean_title(m.group(1)) if m else ""


def sections_from_accordions(body):
    """هر آکاردئون یک بخش."""
    out = []
    pattern = re.compile(
        r'<div class="accordion-item" id="([^"]+)">(.*?)(?=<div class="accordion-item" id="|</main>)',
        re.S,
    )
    for m in pattern.finditer(body):
        anchor, chunk = m.group(1), m.group(2)
        hm = re.search(r'<button class="accordion-header"[^>]*>(.*?)</button>', chunk, re.S)
        title = clean_title(hm.group(1)) if hm else anchor
        cm = re.search(r'<div class="accordion-content">(.*)', chunk, re.S)
        text = to_text(cm.group(1)) if cm else ""
        if len(text) >= MIN_TEXT:
            out.append({"id": anchor, "title": title, "text": text[:MAX_TEXT]})
    return out


def sections_from_headings(body):
    """صفحه‌های بدون آکاردئون: تقسیم بر اساس سرفصل‌ها."""
    out = []
    marks = []
    for m in re.finditer(r"<(h2|h3|h4)([^>]*)>(.*?)</\1>", body, re.S):
        marks.append((m.start(), m.end(), clean_title(m.group(3)), m.group(2)))
    if not marks:
        text = to_text(body)
        if len(text) >= MIN_TEXT:
            out.append({"id": "", "title": "", "text": text[:MAX_TEXT]})
        return out

    for i, (start, end, title, attrs) in enumerate(marks):
        stop = marks[i + 1][0] if i + 1 < len(marks) else len(body)
        chunk = body[end:stop]
        idm = re.search(r'id="([^"]+)"', attrs or "")
        anchor = idm.group(1) if idm else ""
        text = to_text(chunk)
        if len(text) >= MIN_TEXT:
            entry = {"id": anchor, "title": title, "text": text[:MAX_TEXT]}
            out.append(entry)
    return out


def main():
    pages = [p for p in sorted(glob.glob("*.html")) if not p.startswith("_")]
    data = {"generated": time.strftime("%Y-%m-%d"), "pages": {}}
    total_chars = 0

    for page in pages:
        html = read(page)
        body_all = re.search(r"(?s)<main.*?</main>", html)
        body = strip_chrome(body_all.group(0) if body_all else html)
        title = page_title(html) or page

        secs = sections_from_accordions(body)
        if not secs:
            secs = sections_from_headings(body)

        # در صفحهٔ اصلی، کارت‌های ناوبری نباید در جستجو بیایند؛
        # فقط بخش‌های توضیحی/پرسش‌های متداول ارزش جستجو دارند.
        if page == "index.html":
            secs = [x for x in secs if len(x["text"]) >= 250]

        # حذف تکراری‌ها
        seen = set()
        uniq = []
        for s in secs:
            key = (s["id"], s["title"])
            if key in seen:
                continue
            seen.add(key)
            uniq.append(s)

        # وزن نهایی: page اصلی پایین‌ترین اولویت را دارد (عدد بزرگ‌تر = دیرتر)
        weight = PAGE_WEIGHT.get(page, 3)
        data["pages"][page] = {
            "title": title,
            "weight": weight,
            "sections": uniq,
        }
        total_chars += sum(len(s["text"]) for s in uniq)
        print("%-24s بخش: %-3d  کاراکتر: %d" % (page, len(uniq), sum(len(s["text"]) for s in uniq)))

    os.makedirs("js", exist_ok=True)
    with io.open(OUT, "w", encoding="utf-8", newline="") as fh:
        json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))

    size = os.path.getsize(OUT)
    print("\n%s  |  %d بخش  |  %d کاراکتر  |  %.1f KB" % (
        OUT, sum(len(v["sections"]) for v in data["pages"].values()), total_chars, size / 1024.0))

    if size > 900 * 1024:
        print("هشدار: فایل ایندکس بزرگ‌تر از حد انتظار است.")
        return 1
    empty = [p for p, v in data["pages"].items() if not v["sections"]]
    if empty:
        print("هشدار: این صفحه‌ها هیچ بخشی برای جستجو ندارند:", empty)
        return 1
    print("ایندکس جستجو ساخته شد ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
