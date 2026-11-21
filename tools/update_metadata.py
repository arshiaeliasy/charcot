# -*- coding: utf-8 -*-
"""
شارکوت | Charcot — به‌روزرسانی متادیتای اشتراک‌گذاری هر صفحه
------------------------------------------------------------
    python tools/update_metadata.py

  • og:image / twitter:image هر صفحه را به تصویر اختصاصی خودش تغییر می‌دهد
    (img/og/<page>.jpg) و og:image:alt را با عنوان صفحه پر می‌کند.
  • ابعاد ۱۲۰۰×۶۳۰ و نوع تصویر را تضمین می‌کند.
  • ماژول JSON-LD را با تصویر جدید هم‌گام می‌کند.
  • اجرای دوباره بی‌خطر است.

اجرا پس از tools/make_og_images.py.
"""

import glob
import io
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

BASE = "https://arshiaeliasy.github.io/charcot/"


def read(path):
    return io.open(path, encoding="utf-8", newline="").read()


def write(path, text):
    with io.open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)


def page_title(s):
    m = re.search(r'<h1[^>]*>(.*?)</h1>', s, re.S)
    if not m:
        m = re.search(r"<title>(.*?)</title>", s, re.S)
    if not m:
        return ""
    t = re.sub(r"<[^>]+>", "", m.group(1))
    return re.sub(r"\s+", " ", t).strip()


def set_meta(s, kind, name, value):
    """محتوای یک متا را جایگزین می‌کند (یا اضافه می‌کند)."""
    attr = "property" if kind == "property" else "name"
    pat = re.compile(r'<meta %s="%s" content="[^"]*">' % (attr, re.escape(name)))
    if pat.search(s):
        return pat.sub('<meta %s="%s" content="%s">' % (attr, name, value), s, count=1), True
    anchor = '<meta name="twitter:card" content="summary_large_image">'
    if anchor in s:
        return s.replace(anchor, anchor + '\n    <meta %s="%s" content="%s">' % (attr, name, value), 1), True
    return s, False


def main():
    pages = [p for p in sorted(glob.glob("*.html")) if not p.startswith("_")]
    missing = []
    changed = []
    for page in pages:
        img_name = page.replace(".html", "") + ".jpg"
        rel = "img/og/" + img_name
        if not os.path.exists(rel):
            missing.append(page)
            continue
        url = BASE + rel
        s = read(page)
        orig = s
        title = page_title(s)

        s, _ = set_meta(s, "property", "og:image", url)
        s, _ = set_meta(s, "property", "og:image:width", "1200")
        s, _ = set_meta(s, "property", "og:image:height", "630")
        s, _ = set_meta(s, "property", "og:image:type", "image/jpeg")
        s, _ = set_meta(s, "property", "og:image:alt", title)
        s, _ = set_meta(s, "name", "twitter:image", url)
        s, _ = set_meta(s, "name", "twitter:image:alt", title)

        # هم‌گام‌سازی JSON-LD
        s = re.sub(r'("image":\s*")[^"]*(")', lambda m: m.group(1) + url + m.group(2), s)

        if s != orig:
            write(page, s)
            changed.append(page)

    print("صفحه‌های به‌روزشده: %d" % len(changed))
    for c in changed:
        print("  ✔", c, "->", "img/og/" + c.replace(".html", ".jpg"))
    if missing:
        print("\nهشدار: تصویر OG برای این صفحه‌ها ساخته نشده:")
        for m in missing:
            print("  -", m)
        print("اول tools/make_og_images.py را اجرا کن.")
        return 1
    print("\nمتادیتای اشتراک‌گذاری همهٔ صفحه‌ها به‌روز شد ✅")
    return 0


if __name__ == "__main__":
    sys.exit(main())
