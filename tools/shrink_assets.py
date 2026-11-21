# -*- coding: utf-8 -*-
"""کوچک‌سازی دارایی‌های تصویری: لوگوی هدر/فوتر و favicon.ico"""
import io, os, sys
from PIL import Image
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.abspath("tools/make_assets.py"))
SRC = Image.open("10990.jpg").convert("RGB")

def save_png(img, path, colors):
    img.convert("RGB").quantize(colors=colors, method=Image.MEDIANCUT).save(path, optimize=True)
    return os.path.getsize(path)

before = {p: os.path.getsize(p) for p in ("img/logo-96.png", "favicon.ico", "img/favicon-32.png", "img/favicon-180.png")}

# لوگو: ۶۴px جاي ۹۶px (در هدر ۴۶px و در فوتر ۳۸px نمايش داده مى‌شود)
save_png(SRC.resize((64, 64), Image.LANCZOS), "img/logo-96.png", 96)
save_png(SRC.resize((32, 32), Image.LANCZOS), "img/favicon-32.png", 32)
save_png(SRC.resize((180, 180), Image.LANCZOS), "img/favicon-180.png", 96)

# favicon.ico فقط با دو اندازهٔ ضروری
tmp = "favicon.tmp.png"
save_png(SRC.resize((32, 32), Image.LANCZOS), tmp, 32)
with Image.open(tmp) as im:
    im.convert("RGB").save("favicon.ico", sizes=[(16, 16), (32, 32)])
os.remove(tmp)

for p, b in before.items():
    print("%-20s %7d -> %7d bytes" % (p, b, os.path.getsize(p)))

# بررسی اینکه متن‌های فارسی همه UTF-8 معتبرند (نمایش مو‌بیکه در کنسول ویندوز طبیعی است)
for f in ("img/qr.svg", "js/main.js", "js/vendor/supabase.js", "externship.html"):
    raw = open(f, "rb").read()
    try:
        raw.decode("utf-8")
        print("%-26s UTF-8 OK (%d bytes)" % (f, len(raw)))
    except UnicodeDecodeError as e:
        print("%-26s NOT UTF-8: %s" % (f, e))
