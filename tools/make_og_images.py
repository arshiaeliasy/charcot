# -*- coding: utf-8 -*-
"""
شارکوت | Charcot — ساخت تصویر پیشنمایش (og:image) اختصاصی هر صفحه
------------------------------------------------------------------
اجرا از ریشهٔ پروژه:

    python tools/make_og_images.py            # ساخت همه
    python tools/make_og_images.py --selftest # بررسی خروجیها

خروجی: img/og/<page>.jpg  (۱۲۰۰×۶۳۰)

ویژگیها:
  • پسزمینهٔ گرادیانی روشن→تیره با خط تأکید (بهجای تصویر تقریباً سیاه قبلی)
  • عنوان فارسی با شکلسازی درست (tools/fa_text.py) و RTL واقعی
  • هر صفحه تصویر خودش را دارد؛ اگر عنوان طولانی باشد خودکار کوچک میشود
"""

import glob
import io
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fa_text import shape_fa, strip_tags  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

W, H = 1200, 630
OUT_DIR = os.path.join("img", "og")

FONT_BOLD = os.path.join("fonts", "vazirmatn-arabic-800-normal.woff2")
FONT_MED = os.path.join("fonts", "vazirmatn-arabic-700-normal.woff2")
FONT_LAT = os.path.join("fonts", "vazirmatn-latin-800-normal.woff2")

# رنگها — همخوان با تم سایت
C_BG_TOP = (232, 244, 248)
C_BG_BOT = (255, 255, 255)
C_TEAL = (13, 148, 136)
C_BLUE = (2, 132, 199)
C_TEXT = (13, 27, 42)
C_MUTED = (71, 85, 105)

# عنوان کوتاه و خوانا برای هر صفحه
OG_TITLE = {
    "index.html": "پلتفرم یادگیری دانشجویان پزشکی",
    "basic-sciences.html": "دروس و منابع علوم پایه",
    "pathophysiology.html": "فیزیوپاتولوژی",
    "externship.html": "استاجری — کورس‌های بالینی",
    "pre-internship.html": "پره‌انترنی",
    "internship.html": "اینترنی",
    "clinical-cases.html": "بانک کیس‌های بالینی",
    "clinical-notes.html": "یادداشت‌های بالینی",
    "case-stroke.html": "کیس: سکته مغزی حاد",
    "case-acs.html": "کیس: سندرم حاد کرونری",
    "case-sepsis.html": "کیس: شوک سپتیک",
    "about-us.html": "درباره شارکوت",
}

OG_KICKER = {
    "index.html": "از علوم پایه تا کارورزی بالینی",
    "basic-sciences.html": "۱۹ درس با سرفصل و نکتهٔ مطالعه",
    "pathophysiology.html": "پایهٔ درک بیماری‌ها",
    "externship.html": "۱۴ کورس بالینی با راهنمای بخش",
    "pre-internship.html": "آمادگی برای امتحان جامع",
    "internship.html": "نخستین سال طبابت",
    "clinical-cases.html": "کیس‌های واقعی بیمارستانی",
    "clinical-notes.html": "جمع‌بندی کانال تلگرام",
    "case-stroke.html": "شرح‌حال، برخورد و نکات",
    "case-acs.html": "شرح‌حال، برخورد و نکات",
    "case-sepsis.html": "شرح‌حال، برخورد و نکات",
    "about-us.html": "درباره ما",
}


def find_font(preferred, size):
    """فونت را از میان مسیرهای ممکن پیدا می‌کند."""
    candidates = [
        preferred,
        os.path.join("fonts", "vazirmatn-arabic-800-normal.woff2"),
        os.path.join("fonts", "vazirmatn-arabic-700-normal.woff2"),
        os.path.join("fonts", "vazirmatn-latin-800-normal.woff2"),
        "C:/Windows/Fonts/tahoma.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def gradient():
    """پس‌زمینهٔ روشن با هالهٔ ملایم فیروزه‌ای در گوشهٔ راست-پایین."""
    img = Image.new("RGB", (W, H), C_BG_TOP)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / float(H - 1)
        col = tuple(int(C_BG_TOP[i] + (C_BG_BOT[i] - C_BG_TOP[i]) * t) for i in range(3))
        d.line([(0, y), (W, y)], fill=col)

    # هالهٔ فیروزه‌ای ملایم (افزودنی، تا تصویر تخت نشود)
    glow = Image.new("RGB", (W, H), (255, 255, 255))
    gd = ImageDraw.Draw(glow)
    cx, cy = int(W * 0.86), int(H * 1.02)
    for i in range(80, 0, -1):
        r = i * 11
        strength = (1 - i / 80.0)
        col = (
            int(255 - (255 - C_TEAL[0]) * 0.30 * strength),
            int(255 - (255 - C_TEAL[1]) * 0.30 * strength),
            int(255 - (255 - C_TEAL[2]) * 0.30 * strength),
        )
        gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)
    img = Image.blend(img, glow, 0.5)
    return img


def wrap_fa(text, font, max_w, draw):
    """شکستن متن به خطوط با احترام به عرض."""
    words = text.split()
    lines, cur = [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        w = draw.textlength(shape_fa(trial), font=font)
        if w <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def build(page, title, kicker):
    img = gradient()
    d = ImageDraw.Draw(img)

    # نوار تأکید سمت راست + نوار باریک بالای کارت
    d.rectangle([W - 14, 0, W, H], fill=C_TEAL)
    d.rectangle([W - 14, 0, W, int(H * 0.42)], fill=C_BLUE)

    # لوگو در گوشهٔ راست-بالا (سایت راست‌به‌چپ است)
    LOGO_S = 112
    LOGO_X = W - 92 - LOGO_S
    LOGO_Y = 78
    logo_path = os.path.join("img", "logo-96.png")
    if os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA").resize((LOGO_S, LOGO_S), Image.LANCZOS)
            img.paste(logo, (LOGO_X, LOGO_Y), logo)
        except Exception:
            pass

    # برند: نام سایت + نام فارسی، بلافاصله سمت چپ لوگو
    f_brand = find_font(FONT_LAT, 42)
    brand_txt = "Charcot"
    bw = d.textlength(brand_txt, font=f_brand)
    d.text((LOGO_X - 26 - bw, LOGO_Y + 6), brand_txt, font=f_brand, fill=C_TEAL)

    f_fa = find_font(FONT_BOLD, 28)
    fa_txt = shape_fa("شارکوت | مرجع دانشجویان پزشکی")
    fw = d.textlength(fa_txt, font=f_fa)
    d.text((LOGO_X - 26 - fw, LOGO_Y + 62), fa_txt, font=f_fa, fill=C_MUTED)

    # عنوان اصلی — اندازهٔ خودکار
    max_w = W - 200
    size = 78
    while size > 40:
        f = find_font(FONT_BOLD, size)
        lines = wrap_fa(title, f, max_w, d)
        widest = max(d.textlength(shape_fa(l), font=f) for l in lines)
        if len(lines) <= 2 and widest <= max_w:
            break
        size -= 4

    f_title = find_font(FONT_BOLD, size)
    lines = wrap_fa(title, f_title, max_w, d)
    line_h = int(size * 1.45)
    total = len(lines) * line_h
    y = int(H * 0.55 - total / 2) + 40
    for line in lines:
        s = shape_fa(line)
        w = d.textlength(s, font=f_title)
        d.text((W - 100 - w, y), s, font=f_title, fill=C_TEXT)
        y += line_h

    # خط جداکنندهٔ کوتاه، زیر عنوان و راست‌چین
    y += 26
    d.rectangle([W - 190, y, W - 100, y + 8], fill=C_BLUE)

    # زیرعنوان
    f_kick = find_font(FONT_MED, 30)
    ks = shape_fa(kicker)
    kw = d.textlength(ks, font=f_kick)
    d.text((W - 100 - kw, y + 30), ks, font=f_kick, fill=C_TEAL)

    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, page.replace(".html", "") + ".jpg")
    img.save(path, "JPEG", quality=88, optimize=True, progressive=True)
    return path


def page_title(page):
    """اگر OG_TITLE نداشت، از خود صفحه بردار."""
    s = io.open(page, encoding="utf-8").read()
    m = re.search(r'<h1[^>]*>(.*?)</h1>', s, re.S)
    if m:
        return strip_tags(m.group(1))
    m = re.search(r"<title>(.*?)</title>", s, re.S)
    return strip_tags(m.group(1)) if m else page


def main(argv):
    pages = [p for p in sorted(glob.glob("*.html")) if not p.startswith("_")]
    if not pages:
        print("صفحه‌ای پیدا نشد؛ از ریشهٔ پروژه اجرا کن.")
        return 1

    made = []
    for page in pages:
        title = OG_TITLE.get(page) or page_title(page)
        kicker = OG_KICKER.get(page, "شارکوت | Charcot")
        path = build(page, title, kicker)
        made.append((page, path, os.path.getsize(path), title))

    print("%-24s %-22s %8s  %s" % ("صفحه", "فایل", "حجم", "عنوان"))
    for page, path, size, title in made:
        print("%-24s %-22s %7.1fKB  %s" % (page, os.path.basename(path), size / 1024.0, title))

    if "--selftest" in argv:
        bad = []
        for page, path, size, _t in made:
            im = Image.open(path)
            if im.size != (W, H):
                bad.append("%s: اندازهٔ نادرست %s" % (path, im.size))
            if size < 8000:
                bad.append("%s: حجم مشکوک (%.1fKB)" % (path, size / 1024.0))
            g = im.convert("L")
            hist = g.histogram()
            total = sum(hist)
            # پس‌زمینه باید روشن باشد (تصویر تیره در تلگرام خوانده نمی‌شود)
            light_share = sum(hist[150:]) / float(total)
            # متن باید سهم معناداری از پیکسل‌ها را تیره کند
            ink_share = sum(hist[:110]) / float(total)
            mean = sum(i * hist[i] for i in range(256)) / float(total)
            if light_share < 0.80:
                bad.append("%s: پس‌زمینه به‌قدر کافی روشن نیست (%.1f%%)" % (path, light_share * 100))
            if ink_share < 0.015:
                bad.append("%s: متن کافی ندارد (شاخص جوهر %.1f%%)" % (path, ink_share * 100))
            if mean < 150:
                bad.append("%s: میانگین روشنایی پایین است (%.0f/255)" % (path, mean))
        if bad:
            print("\nایرادها:")
            for b in bad:
                print("  -", b)
            return 1
        print("\nSELFTEST: PASS ✅  (%d تصویر روشن و خوانا)" % len(made))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
