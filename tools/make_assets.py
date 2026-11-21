#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
شارکوت | Charcot — تولید دارایی‌های تصویری سایت
--------------------------------------------------
از تصویر منبع 10990.jpg این فایل‌ها ساخته می‌شوند:
    img/favicon-32.png     آیکون مرورگر (۳۲×۳۲)
    img/favicon-180.png    آیکون اپل/اندروید (۱۸۰×۱۸۰)
    favicon.ico            آیکون قدیمی مرورگر (۱۶/۳۲/۴۸)
    img/logo-96.png        لوگوی هدر و فوتر (۹۶×۹۶، برای نمایش ۴۶px)
    img/og-image.png       تصویر پیش‌نمایش شبکه‌های اجتماعی (۱۲۰۰×۶۳۰)

اجرا (با پایتون همراه با Pillow):
    python tools/make_assets.py
"""

import os

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "10990.jpg")
OUT_DIR = os.path.join(ROOT, "img")

BG_DARK = (7, 22, 27)        # --bg-main تم تیره
TEXT_MAIN = (240, 253, 244)  # --text-main تم تیره
ACCENT_TEAL = (45, 212, 191)  # --accent-teal تم تیره
TEXT_MUTED = (148, 163, 184)  # --text-muted تم تیره
GLOW = (14, 165, 233)        # --accent-primary تم تیره

LATIN_BOLD = r"C:\Windows\Fonts\segoeuib.ttf"
LATIN_REGULAR = r"C:\Windows\Fonts\segoeui.ttf"


def load_logo():
    img = Image.open(SRC)
    if img.mode != "RGB":
        img = img.convert("RGB")
    return img


def rounded(img, radius):
    """گوشه‌های گرد روی یک تصویر RGBA."""
    img = img.convert("RGBA")
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [0, 0, img.size[0] - 1, img.size[1] - 1], radius=radius, fill=255
    )
    img.putalpha(mask)
    return img


def save_png(img, path, colors):
    """PNG کم‌حجم با پالت محدود (لوگو عکس‌گونه است و PNG تمام‌رنگ سنگین می‌شود)."""
    img.convert("RGB").quantize(colors=colors, method=Image.MEDIANCUT).save(
        path, optimize=True
    )


def build_icons(logo):
    save_png(logo.resize((96, 96), Image.LANCZOS), os.path.join(OUT_DIR, "logo-96.png"), 128)
    save_png(logo.resize((32, 32), Image.LANCZOS), os.path.join(OUT_DIR, "favicon-32.png"), 64)
    save_png(logo.resize((180, 180), Image.LANCZOS), os.path.join(OUT_DIR, "favicon-180.png"), 128)
    save_png(logo.resize((48, 48), Image.LANCZOS), os.path.join(ROOT, "favicon.tmp.png"), 64)
    with Image.open(os.path.join(ROOT, "favicon.tmp.png")) as tmp:
        tmp.convert("RGB").save(
            os.path.join(ROOT, "favicon.ico"),
            sizes=[(16, 16), (32, 32), (48, 48)],
        )
    os.remove(os.path.join(ROOT, "favicon.tmp.png"))


def build_og(logo):
    """کارت ۱۲۰۰×۶۳۰ برای og:image — بدون متن فارسی (شکل‌دهی حروف در Pillow نیست)."""
    W, H = 1200, 630
    card = Image.new("RGB", (W, H), BG_DARK)

    # هالهٔ نرم آبی-فیروزه‌ای در گوشهٔ بالا-راست
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    cx, cy, R = int(W * 0.82), int(H * 0.18), 560
    steps = 90
    for i in range(steps, 0, -1):
        r = int(R * i / steps)
        a = int(46 * (1 - i / steps) ** 1.6)
        gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GLOW + (a,))
    card = Image.alpha_composite(card.convert("RGBA"), glow).convert("RGB")

    # نوار باریک فیروزه‌ای پایین کارت
    ImageDraw.Draw(card).rectangle([0, H - 14, W, H], fill=ACCENT_TEAL)

    badge = rounded(logo.resize((250, 250), Image.LANCZOS), radius=44)
    card.paste(badge, (96, (H - 250) // 2 - 7), badge)

    draw = ImageDraw.Draw(card)
    f_title = ImageFont.truetype(LATIN_BOLD, 96)
    f_sub = ImageFont.truetype(LATIN_REGULAR, 40)
    f_url = ImageFont.truetype(LATIN_REGULAR, 30)

    x = 400
    draw.text((x, 190), "Charcot", font=f_title, fill=TEXT_MAIN)
    draw.text((x, 320), "Medical Learning & Research Platform", font=f_sub, fill=ACCENT_TEAL)
    draw.text((x, 392), "arshiaeliasy.github.io/charcot", font=f_url, fill=TEXT_MUTED)

    card.save(os.path.join(OUT_DIR, "og-image.jpg"), quality=86, optimize=True, progressive=True)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    logo = load_logo()
    print("source:", SRC, logo.size, logo.mode)
    build_icons(logo)
    build_og(logo)
    for name in ("logo-96.png", "favicon-32.png", "favicon-180.png", "og-image.jpg"):
        p = os.path.join(OUT_DIR, name)
        with Image.open(p) as im:
            print(f"{name:18} {im.size} {os.path.getsize(p):>7} bytes")
    p = os.path.join(ROOT, "favicon.ico")
    print(f"{'favicon.ico':18} {os.path.getsize(p):>7} bytes")


if __name__ == "__main__":
    main()
