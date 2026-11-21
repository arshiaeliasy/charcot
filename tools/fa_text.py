# -*- coding: utf-8 -*-
"""
شکلسازی متن فارسی/عربی برای رندر با Pillow (بدون وابستگی بیرونی)
-----------------------------------------------------------------
Pillow متن را «بدون اتصال حروف» و «چپبهراست» میچیند. این ماژول:
  ۱) حروف را به شکل درست (آغازین/میانی/پایانی/تنها) تبدیل میکند
  ۲) ترتیب گلیفها را برای نمایش راستبهچپ برمیگرداند
  ۳) نیمفاصله و اعداد فارسی را درست نگه میدارد

استفاده:
    from fa_text import shape_fa
    shaped = shape_fa("استاجری و کورسهای بالینی")
"""

import re
import unicodedata

# ---------- جدول اشکال حروف عربی/فارسی ----------
# هر مدخل: [تنها، پایانی، آغازین، میانی]
_FORMS = {
    "\u0621": ["\u0621"],                                        # ء
    "\u0622": ["\u0622", "\uFE81", "\uFE81", "\uFE82"],           # آ
    "\u0623": ["\u0623", "\uFE83", "\uFE83", "\uFE84"],           # أ
    "\u0624": ["\u0624", "\uFE85", "\uFE85", "\uFE86"],           # ؤ
    "\u0625": ["\u0625", "\uFE87", "\uFE87", "\uFE88"],           # إ
    "\u0626": ["\u0626", "\uFE89", "\uFE89", "\uFE8A", "\uFE8B", "\uFE8C"],  # ئ
    "\u0627": ["\u0627", "\uFE8D", "\uFE8D", "\uFE8E"],           # ا
    "\u0628": ["\u0628", "\uFE8F", "\uFE90", "\uFE91", "\uFE92"],  # ب
    "\u0629": ["\u0629", "\uFE93", "\uFE93", "\uFE94"],           # ة
    "\u062A": ["\u062A", "\uFE95", "\uFE96", "\uFE97", "\uFE98"],  # ت
    "\u062B": ["\u062B", "\uFE99", "\uFE9A", "\uFE9B", "\uFE9C"],  # ث
    "\u062C": ["\u062C", "\uFE9D", "\uFE9E", "\uFE9F", "\uFEA0"],  # ج
    "\u062D": ["\u062D", "\uFEA1", "\uFEA2", "\uFEA3", "\uFEA4"],  # ح
    "\u062E": ["\u062E", "\uFEA5", "\uFEA6", "\uFEA7", "\uFEA8"],  # خ
    "\u062F": ["\u062F", "\uFEA9", "\uFEA9", "\uFEAA"],           # د
    "\u0630": ["\u0630", "\uFEAB", "\uFEAB", "\uFEAC"],           # ذ
    "\u0631": ["\u0631", "\uFEAD", "\uFEAD", "\uFEAE"],           # ر
    "\u0632": ["\u0632", "\uFEAF", "\uFEAF", "\uFEB0"],           # ز
    "\u0633": ["\u0633", "\uFEB1", "\uFEB2", "\uFEB3", "\uFEB4"],  # س
    "\u0634": ["\u0634", "\uFEB5", "\uFEB6", "\uFEB7", "\uFEB8"],  # ش
    "\u0635": ["\u0635", "\uFEB9", "\uFEBA", "\uFEBB", "\uFEBC"],  # ص
    "\u0636": ["\u0636", "\uFEBD", "\uFEBE", "\uFEBF", "\uFEC0"],  # ض
    "\u0637": ["\u0637", "\uFEC1", "\uFEC2", "\uFEC3", "\uFEC4"],  # ط
    "\u0638": ["\u0638", "\uFEC5", "\uFEC6", "\uFEC7", "\uFEC8"],  # ظ
    "\u0639": ["\u0639", "\uFEC9", "\uFECA", "\uFECB", "\uFECC"],  # ع
    "\u063A": ["\u063A", "\uFECD", "\uFECE", "\uFECF", "\uFED0"],  # غ
    "\u0640": ["\u0640", "\u0640", "\u0640", "\u0640"],           # ـ کشیده
    "\u0641": ["\u0641", "\uFED1", "\uFED2", "\uFED3", "\uFED4"],  # ف
    "\u0642": ["\u0642", "\uFED5", "\uFED6", "\uFED7", "\uFED8"],  # ق
    "\u0643": ["\u0643", "\uFED9", "\uFEDA", "\uFEDB", "\uFEDC"],  # ك
    "\u0644": ["\u0644", "\uFEDD", "\uFEDE", "\uFEDF", "\uFEE0"],  # ل
    "\u0645": ["\u0645", "\uFEE1", "\uFEE2", "\uFEE3", "\uFEE4"],  # م
    "\u0646": ["\u0646", "\uFEE5", "\uFEE6", "\uFEE7", "\uFEE8"],  # ن
    "\u0647": ["\u0647", "\uFEE9", "\uFEEA", "\uFEEB", "\uFEEC"],  # ه
    "\u0648": ["\u0648", "\uFEED", "\uFEED", "\uFEEE"],           # و
    "\u0649": ["\u0649", "\uFEEF", "\uFEEF", "\uFEF0"],           # ى
    "\u064A": ["\u064A", "\uFEF1", "\uFEF2", "\uFEF3", "\uFEF4"],  # ي
    "\u0671": ["\u0671", "\uFB50", "\uFB50", "\uFB51"],           # ٱ
    "\u067E": ["\u067E", "\uFB56", "\uFB57", "\uFB58", "\uFB59"],  # پ
    "\u0686": ["\u0686", "\uFB7A", "\uFB7B", "\uFB7C", "\uFB7D"],  # چ
    "\u0698": ["\u0698", "\uFB8A", "\uFB8A", "\uFB8B"],           # ژ
    "\u06A9": ["\u06A9", "\uFB8E", "\uFB8F", "\uFB90", "\uFB91"],  # ک
    "\u06AF": ["\u06AF", "\uFB92", "\uFB93", "\uFB94", "\uFB95"],  # گ
    "\u06CC": ["\u06CC", "\uFBFC", "\uFBFD", "\uFBFE", "\uFBFF"],  # ی
}

# حروفی که به حرف بعدی (سمت چپ در متن منطقی) نمیچسبند
_NON_JOINING_NEXT = set("\u0621\u0622\u0623\u0624\u0625\u0627\u062F\u0630\u0631\u0632\u0698\u0648\u0649\u0671")

# علامتهای اعراب و نیمفاصله که اتصال را نمیشکنند
_TRANSPARENT = set("\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652\u0653\u0654\u0655\u0670\u200C\u200F\u200E")

# ---------- اعداد و علائم لاتین که باید چپبهراست بمانند ----------
_LTR_CHARS = set(
    "0123456789"
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    ".:%+-/#&()[]{}<>|=_*'\"@!?$,;"
)

_AR_RANGE = (
    (0x0600, 0x06FF),
    (0x0750, 0x077F),
    (0x08A0, 0x08FF),
    (0xFB50, 0xFDFF),
    (0xFE70, 0xFEFF),
)


def _is_arabic(ch):
    cp = ord(ch)
    return any(lo <= cp <= hi for lo, hi in _AR_RANGE)


def _is_transparent(ch):
    return ch in _TRANSPARENT or unicodedata.combining(ch) != 0


def _connectable(ch):
    """آیا حرف شکل آغازین/میانی دارد؟"""
    forms = _FORMS.get(ch)
    return bool(forms and len(forms) >= 4)


def _can_join_next(ch):
    return _connectable(ch) and ch not in _NON_JOINING_NEXT


def shape_fa(text, base_dir="rtl"):
    """متن را به گلیفهای متصل و آمادهٔ رندر تبدیل میکند."""
    out = []
    buf = []  # کاراکترهای خنثیِ معلق (فاصله، علائم)

    def flush_buf():
        # خنثیها به ترتیب منطقی برمیگردند؛ جای خودشان در معکوسسازی درست میشود
        for c in buf:
            out.append(c)
        del buf[:]

    chars = list(text)

    # ---- مرحلهٔ ۱: انتخاب شکل هر حرف ----
    shaped = []
    for i, ch in enumerate(chars):
        if not _is_arabic(ch) or ch not in _FORMS:
            shaped.append(ch)
            continue

        prev = None
        for j in range(i - 1, -1, -1):
            if _is_transparent(chars[j]):
                continue
            prev = chars[j]
            break

        nxt = None
        for j in range(i + 1, len(chars)):
            if _is_transparent(chars[j]):
                continue
            nxt = chars[j]
            break

        connects_prev = prev is not None and _is_arabic(prev) and _can_join_next(prev)
        connects_next = nxt is not None and _is_arabic(nxt)

        forms = _FORMS[ch]
        if len(forms) == 1:
            shaped.append(forms[0])
            continue

        if connects_prev and connects_next:
            shaped.append(forms[3] if len(forms) > 4 else forms[1])
        elif connects_prev:
            shaped.append(forms[1])
        elif connects_next:
            shaped.append(forms[2])
        else:
            shaped.append(forms[0])

    # ---- مرحلهٔ ۲: چیدمان دوجهته (RTL پایه) ----
    tokens = _tokenize(shaped)

    if base_dir != "rtl":
        return "".join(chunk for _kind, chunk in tokens)

    out = []
    for kind, chunk in reversed(tokens):
        if kind == "ltr":
            # واژههای لاتین حفظ میشوند، ترتیبشان برمیگردد
            words = chunk.split(" ")
            out.append(" ".join(reversed(words)))
        elif kind == "neutral":
            out.append(_mirror(chunk))
        else:
            out.append(chunk)
    return "".join(out)


_MIRROR = {"(": ")", ")": "(", "[": "]", "]": "[", "{": "}", "}": "{",
           "<": ">", ">": "<", "\u00AB": "\u00BB", "\u00BB": "\u00AB"}


def _mirror(chunk):
    return "".join(_MIRROR.get(c, c) for c in chunk)


def _tokenize(chars):
    """به توکنهای ltr / rtl / neutral تبدیل میکند."""
    tokens = []
    i = 0
    n = len(chars)
    while i < n:
        ch = chars[i]
        if ch in _LTR_CHARS:
            j = i
            while j < n and chars[j] in _LTR_CHARS:
                j += 1
            tokens.append(("ltr", "".join(chars[i:j])))
            i = j
        elif _is_arabic(ch):
            j = i
            while j < n and _is_arabic(chars[j]):
                j += 1
            tokens.append(("rtl", "".join(chars[i:j])))
            i = j
        else:
            j = i
            while j < n and chars[j] not in _LTR_CHARS and not _is_arabic(chars[j]):
                j += 1
            tokens.append(("neutral", "".join(chars[i:j])))
            i = j
    return tokens


def strip_tags(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()


if __name__ == "__main__":
    import sys

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    samples = [
        "استاجری و کورسهای بالینی",
        "علوم پایه پزشکی",
        "Charcot | شارکوت",
        "۱۲ کورس بالینی برای دانشجویان پزشکی",
        "بیماریهای عفونی (Infectious Diseases)",
    ]
    for s in samples:
        print(s)
        print("  ->", shape_fa(s))
        print("  codepoints:", " ".join("%04X" % ord(c) for c in shape_fa(s)))
        print()
