#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
شارکوت | Charcot — تولید QR محلی (بدون سرویس بیرونی)
------------------------------------------------------
خروجی: img/qr.svg  (کد QR آدرس سایت، برداری و سبک)

چرا؟ قبلاً تصویر QR از api.qrserver.com لود می‌شد؛ یعنی یک وابستگی بیرونی
که IP بازدیدکننده را به سرویس سوم می‌داد و در صورت قطعی، جای خالی می‌ماند.

پیاده‌سازی خودکفا: حالت byte، سطح تصحیح خطا M، انتخاب خودکار نسخه،
Reed-Solomon روی GF(256) با چندجملهٔ مولد 0x11D، انتخاب ماسک با قواعد
جریمهٔ استاندارد. صحت با سه آزمون در همین فایل بررسی می‌شود (--selftest).

اجرا:
    python tools/make_qr.py
    python tools/make_qr.py --selftest
"""

import os
import sys

try:  # کنسول ویندوز ممکن است cp1252 باشد
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

URL = "https://arshiaeliasy.github.io/charcot/index.html"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "img", "qr.svg")

# ---------------------------------------------------------------- GF(256)
EXP = [0] * 512
LOG = [0] * 256


def _init_tables():
    x = 1
    for i in range(255):
        EXP[i] = x
        LOG[x] = i
        x <<= 1
        if x & 0x100:
            x ^= 0x11D  # چندجملهٔ مولد QR
    for i in range(255, 512):
        EXP[i] = EXP[i - 255]


_init_tables()


def gf_mul(a, b):
    if a == 0 or b == 0:
        return 0
    return EXP[LOG[a] + LOG[b]]


def rs_generator(n):
    poly = [1]
    for i in range(n):
        poly.append(0)
        for j in range(len(poly) - 1, 0, -1):
            poly[j] = poly[j] ^ gf_mul(poly[j - 1], EXP[i])
    return poly


def rs_encode(data, n_ec):
    """کدواژه‌های تصحیح خطا برای یک بلوک داده."""
    gen = rs_generator(n_ec)
    res = list(data) + [0] * n_ec
    for i in range(len(data)):
        coef = res[i]
        if coef:
            for j in range(1, len(gen)):
                res[i + j] ^= gf_mul(gen[j], coef)
    return res[len(data):]


# ------------------------------------------------- جدول ظرفیت و بلوک‌ها
# نسخه‌های ۱ تا ۱۰، سطح M : (تعداد کدواژه داده، ec_per_block، تعداد بلوک‌ها)
ECC_M = {
    1: (16, 10, 1),
    2: (28, 16, 1),
    3: (44, 26, 1),
    4: (64, 18, 2),
    5: (86, 24, 2),
    6: (108, 16, 4),
    7: (124, 18, 4),
    8: (154, 22, 2),
    9: (182, 22, 3),
    10: (216, 26, 4),
}
TOTAL_CODEWORDS = {1: 26, 2: 44, 3: 70, 4: 100, 5: 134, 6: 172, 7: 196, 8: 242, 9: 292, 10: 346}
REMAINDER_BITS = {1: 0, 2: 7, 3: 7, 4: 7, 5: 7, 6: 7, 7: 0, 8: 0, 9: 0, 10: 0}
ALIGN_CENTERS = {
    1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30],
    6: [6, 34], 7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46], 10: [6, 28, 50],
}


def pick_version(n_bytes):
    for v in range(1, 11):
        data_cw, _, _ = ECC_M[v]
        # ۴ بیت مود + ۸ بیت طول (نسخه‌های <۱۰) → ۲ بایت سربار
        if n_bytes + 2 <= data_cw:
            return v
    raise ValueError("متن برای نسخه‌های پشتیبانی‌شده بلند است")


# ------------------------------------------------------------ کدگذاری
def encode_data(text, version):
    data_cw, ec_per_block, n_blocks = ECC_M[version]
    payload = text.encode("utf-8")
    bits = []

    def put(value, length):
        for i in range(length - 1, -1, -1):
            bits.append((value >> i) & 1)

    put(0b0100, 4)               # حالت byte
    put(len(payload), 8)         # طول (نسخه < ۱۰)
    for b in payload:
        put(b, 8)

    capacity_bits = data_cw * 8
    bits += [0] * min(4, capacity_bits - len(bits))       # ترمینیتور
    while len(bits) % 8:
        bits.append(0)
    codewords = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
    pad = [0xEC, 0x11]
    k = 0
    while len(codewords) < data_cw:
        codewords.append(pad[k % 2])
        k += 1

    # تقسیم به بلوک‌ها و ساخت کدواژه‌های EC
    per_block = data_cw // n_blocks
    blocks = [codewords[i * per_block:(i + 1) * per_block] for i in range(n_blocks)]
    ec_blocks = [rs_encode(b, ec_per_block) for b in blocks]

    # درهم‌بافی (interleave)
    out = []
    for i in range(per_block):
        for b in blocks:
            out.append(b[i])
    for i in range(ec_per_block):
        for e in ec_blocks:
            out.append(e[i])
    assert len(out) == TOTAL_CODEWORDS[version], (len(out), TOTAL_CODEWORDS[version])
    return out


# ------------------------------------------------------------- ماتریس
def new_matrix(size):
    return [[None] * size for _ in range(size)]


def place_function_patterns(m, version):
    size = len(m)

    def finder(r0, c0):
        for r in range(-1, 8):
            for c in range(-1, 8):
                rr, cc = r0 + r, c0 + c
                if not (0 <= rr < size and 0 <= cc < size):
                    continue
                if 0 <= r <= 6 and 0 <= c <= 6:
                    edge = r in (0, 6) or c in (0, 6)
                    core = 2 <= r <= 4 and 2 <= c <= 4
                    m[rr][cc] = 1 if (edge or core) else 0
                else:
                    m[rr][cc] = 0  # جداکننده

    finder(0, 0)
    finder(0, size - 7)
    finder(size - 7, 0)

    for i in range(8, size - 8):        # الگوهای زمان‌بندی
        v = 1 if i % 2 == 0 else 0
        if m[6][i] is None:
            m[6][i] = v
        if m[i][6] is None:
            m[i][6] = v

    centers = ALIGN_CENTERS[version]
    for r in centers:
        for c in centers:
            if (r < 9 and c < 9) or (r < 9 and c > size - 10) or (r > size - 10 and c < 9):
                continue
            for dr in range(-2, 3):
                for dc in range(-2, 3):
                    m[r + dr][c + dc] = 1 if max(abs(dr), abs(dc)) != 1 else 0

    m[size - 8][8] = 1                  # ماژول تیره

    for i in range(9):                  # ناحیهٔ رزرو اطلاعات قالب
        if m[8][i] is None:
            m[8][i] = 0
        if m[i][8] is None:
            m[i][8] = 0
    for i in range(8):
        if m[8][size - 1 - i] is None:
            m[8][size - 1 - i] = 0
        if m[size - 1 - i][8] is None:
            m[size - 1 - i][8] = 0


def reserved_mask(version):
    """خانه‌هایی که داده در آن‌ها قرار نمی‌گیرد."""
    size = 4 * version + 17
    m = new_matrix(size)
    place_function_patterns(m, version)
    return [[m[r][c] is not None for c in range(size)] for r in range(size)]


def place_data(m, codewords, version):
    size = len(m)
    fixed = reserved_mask(version)
    bits = []
    for cw in codewords:
        for i in range(7, -1, -1):
            bits.append((cw >> i) & 1)
    bits += [0] * REMAINDER_BITS[version]

    idx = 0
    col = size - 1
    upward = True
    while col > 0:
        if col == 6:
            col -= 1
        for i in range(size):
            row = (size - 1 - i) if upward else i
            for c in (col, col - 1):
                if not fixed[row][c]:
                    m[row][c] = bits[idx] if idx < len(bits) else 0
                    idx += 1
        col -= 2
        upward = not upward
    return idx


MASK_FN = [
    lambda i, j: (i + j) % 2 == 0,
    lambda i, j: i % 2 == 0,
    lambda i, j: j % 3 == 0,
    lambda i, j: (i + j) % 3 == 0,
    lambda i, j: (i // 2 + j // 3) % 2 == 0,
    lambda i, j: (i * j) % 2 + (i * j) % 3 == 0,
    lambda i, j: ((i * j) % 2 + (i * j) % 3) % 2 == 0,
    lambda i, j: ((i + j) % 2 + (i * j) % 3) % 2 == 0,
]


def apply_mask(m, version, mask_id):
    fixed = reserved_mask(version)
    size = len(m)
    fn = MASK_FN[mask_id]
    out = [row[:] for row in m]
    for r in range(size):
        for c in range(size):
            if not fixed[r][c] and fn(r, c):
                out[r][c] ^= 1
    return out


def format_bits(ecc_bits, mask_id):
    """۵ بیت اطلاعات قالب + ۱۰ بیت BCH، XOR با 0x5412."""
    data = (ecc_bits << 3) | mask_id
    rem = data << 10
    for i in range(4, -1, -1):
        if rem & (1 << (i + 10)):
            rem ^= 0x537 << i
    return ((data << 10) | rem) ^ 0x5412


def place_format(m, version, fmt):
    """۱۵ بیت اطلاعات قالب در دو نسخه: دور فایندر بالا-چپ و (بالا-راست + پایین-چپ).

    نکته: خانهٔ (4*version+9, 8) ماژول تیره است و هرگز بازنویسی نمی‌شود؛
    به همین دلیل نسخهٔ دوم ۸ بیت بالا-راست و ۷ بیت پایین-چپ دارد.
    """
    size = len(m)
    bit = lambda i: (fmt >> (14 - i)) & 1
    for i in range(6):
        m[8][i] = bit(i)
    m[8][7] = bit(6)
    m[8][8] = bit(7)
    m[7][8] = bit(8)
    for i in range(9, 15):
        m[14 - i][8] = bit(i)
    for i in range(7):                     # پایین-چپ: بیت‌های ۰ تا ۶
        m[size - 1 - i][8] = bit(i)
    for i in range(7, 15):                 # بالا-راست: بیت‌های ۷ تا ۱۴
        m[8][size - 15 + i] = bit(i)
    return m


def read_format(m, version):
    """خواندن اطلاعات قالب از هر دو نسخه و بررسی هم‌خوانی آن‌ها."""
    size = len(m)
    a = 0
    for i in range(6):
        a |= m[8][i] << (14 - i)
    a |= m[8][7] << 8
    a |= m[8][8] << 7
    a |= m[7][8] << 6
    for i in range(9, 15):
        a |= m[14 - i][8] << (14 - i)

    b = 0
    for i in range(7):
        b |= m[size - 1 - i][8] << (14 - i)
    for i in range(7, 15):
        b |= m[8][size - 15 + i] << (14 - i)

    assert a == b, "دو نسخهٔ اطلاعات قالب یکسان نیستند"
    data = (a ^ 0x5412) >> 10          # ۵ بیت بالا: ۲ بیت ECC + ۳ بیت ماسک
    return (data >> 3) & 0b11, data & 0b111


def penalty(m):
    size = len(m)
    score = 0
    # قاعده ۱: ردیف/ستون‌های هم‌رنگ ۵تایی و بیشتر
    for line in list(m) + [[m[r][c] for r in range(size)] for c in range(size)]:
        run = 1
        for i in range(1, size):
            if line[i] == line[i - 1]:
                run += 1
            else:
                if run >= 5:
                    score += 3 + (run - 5)
                run = 1
        if run >= 5:
            score += 3 + (run - 5)
    # قاعده ۲: بلوک‌های ۲×۲ هم‌رنگ
    for r in range(size - 1):
        for c in range(size - 1):
            v = m[r][c]
            if v == m[r][c + 1] == m[r + 1][c] == m[r + 1][c + 1]:
                score += 3
    # قاعده ۳: الگوی شبه‌فایندر
    p1 = [1, 0, 1, 1, 1, 0, 1, 0, 0, 0, 0]
    p2 = [0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 1]
    for line in list(m) + [[m[r][c] for r in range(size)] for c in range(size)]:
        for i in range(size - 10):
            seg = line[i:i + 11]
            if seg == p1 or seg == p2:
                score += 40
    # قاعده ۴: انحراف نسبت ماژول‌های تیره از ۵۰٪
    dark = sum(sum(row) for row in m)
    pct = dark * 100 / (size * size)
    score += 10 * (abs(pct - 50) // 5)
    return score


def build(text):
    version = pick_version(len(text.encode("utf-8")))
    codewords = encode_data(text, version)
    size = 4 * version + 17
    m = new_matrix(size)
    place_function_patterns(m, version)
    place_data(m, codewords, version)

    best, best_score = None, None
    for mask_id in range(8):
        cand = apply_mask(m, version, mask_id)
        place_format(cand, version, format_bits(0b00, mask_id))  # M = 00
        s = penalty(cand)
        if best_score is None or s < best_score:
            best, best_score = cand, s
    return version, best


# ------------------------------------------------------------- بازخوانی
def decode(matrix, version):
    """بازخوانی مستقل ماتریس تولیدشده: قالب، ماسک، درهم‌بافی و صحت RS."""
    size = len(matrix)
    ecc, mask_id = read_format(matrix, version)
    assert ecc == 0b00, "سطح ECC باید M باشد"
    assert matrix[4 * version + 9][8] == 1, "ماژول تیره باید همیشه تیره باشد"

    fixed = reserved_mask(version)
    fn = MASK_FN[mask_id]
    unmasked = [row[:] for row in matrix]
    for r in range(size):
        for c in range(size):
            if not fixed[r][c] and fn(r, c):
                unmasked[r][c] ^= 1

    bits = []
    col = size - 1
    upward = True
    while col > 0:
        if col == 6:
            col -= 1
        for i in range(size):
            row = (size - 1 - i) if upward else i
            for c in (col, col - 1):
                if not fixed[row][c]:
                    bits.append(unmasked[row][c])
        col -= 2
        upward = not upward
    total = TOTAL_CODEWORDS[version]
    cws = [int("".join(map(str, bits[i * 8:i * 8 + 8])), 2) for i in range(total)]

    data_cw, ec_per_block, n_blocks = ECC_M[version]
    per_block = data_cw // n_blocks
    blocks = [[] for _ in range(n_blocks)]
    for i in range(per_block):
        for b in range(n_blocks):
            blocks[b].append(cws[i * n_blocks + b])
    ec_start = data_cw
    ecs = [[] for _ in range(n_blocks)]
    for i in range(ec_per_block):
        for b in range(n_blocks):
            ecs[b].append(cws[ec_start + i * n_blocks + b])

    for b in range(n_blocks):
        assert rs_encode(blocks[b], ec_per_block) == ecs[b], f"syndrome بلوک {b} صفر نیست"
    flat = [cw for b in blocks for cw in b]

    mode = flat[0] >> 4
    assert mode == 0b0100, "حالت باید byte باشد"
    length = ((flat[0] & 0x0F) << 4) | (flat[1] >> 4)
    payload = []
    bitstream = []
    for cw in flat:
        for i in range(7, -1, -1):
            bitstream.append((cw >> i) & 1)
    for k in range(length):
        start = 12 + k * 8
        payload.append(int("".join(map(str, bitstream[start:start + 8])), 2))
    return bytes(payload).decode("utf-8")


def to_png(matrix, path, scale=10, quiet=4):
    """نسخهٔ PNG (برای چاپ یا اسکن از روی صفحه) — فقط اگر Pillow نصب باشد."""
    try:
        from PIL import Image
    except ImportError:
        return False
    size = len(matrix)
    dim = (size + quiet * 2) * scale
    img = Image.new("L", (dim, dim), 255)
    px = img.load()
    for r in range(size):
        for c in range(size):
            if matrix[r][c]:
                x0 = (c + quiet) * scale
                y0 = (r + quiet) * scale
                for y in range(y0, y0 + scale):
                    for x in range(x0, x0 + scale):
                        px[x, y] = 0
    img.save(path, optimize=True)
    return True


def to_svg(matrix, scale=8, quiet=4):
    size = len(matrix)
    dim = (size + quiet * 2) * scale
    parts = []
    for r in range(size):
        c = 0
        while c < size:
            if matrix[r][c]:
                run = 1
                while c + run < size and matrix[r][c + run]:
                    run += 1
                x = (c + quiet) * scale
                y = (r + quiet) * scale
                parts.append(f"M{x} {y}h{run * scale}v{scale}h-{run * scale}z")
                c += run
            else:
                c += 1
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{dim}" height="{dim}" '
        f'viewBox="0 0 {dim} {dim}" role="img" aria-label="کد QR شارکوت">\n'
        f'  <rect width="{dim}" height="{dim}" fill="#ffffff"/>\n'
        f'  <path d="{" ".join(parts)}" fill="#07161B" shape-rendering="crispEdges"/>\n'
        f'</svg>\n'
    )


def selftest():
    ok = True
    # ۱) بردار آزمون استاندارد: "HELLO WORLD" نسخه ۱ سطح M
    data = [32, 91, 11, 120, 209, 114, 220, 77, 67, 64, 236, 17, 236, 17, 236, 17]
    expected_ec = [196, 35, 39, 119, 235, 215, 231, 226, 93, 23]
    got = rs_encode(data, 10)
    print("RS vector :", "OK" if got == expected_ec else f"FAIL {got}")
    ok &= got == expected_ec

    # ۲) اطلاعات قالب: (M,mask0) باید 0x5412 و (L,mask0) باید 0x77C4 باشد
    f_m0 = format_bits(0b00, 0)
    f_l0 = format_bits(0b01, 0)
    print(f"format M/0:", hex(f_m0), "OK" if f_m0 == 0x5412 else "FAIL")
    print(f"format L/0:", hex(f_l0), "OK" if f_l0 == 0x77C4 else "FAIL")
    ok &= f_m0 == 0x5412 and f_l0 == 0x77C4

    # ۳) رفت‌وبرگشت کامل روی آدرس سایت
    version, m = build(URL)
    back = decode(m, version)
    print(f"roundtrip : version={version} size={len(m)} -> {'OK' if back == URL else 'FAIL: ' + back}")
    ok &= back == URL
    print("SELFTEST:", "PASS" if ok else "FAIL")
    return ok


def main():
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    version, m = build(URL)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    svg = to_svg(m)
    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(svg)
    png = os.path.join(os.path.dirname(OUT), "qr.png")
    made_png = to_png(m, png)
    print(f"URL      : {URL}")
    print(f"version  : {version} ({len(m)}x{len(m)} ماژول، سطح M)")
    print(f"written  : {OUT} ({len(svg.encode('utf-8'))} bytes)")
    if made_png:
        print(f"written  : {png} ({os.path.getsize(png)} bytes)")
    assert decode(m, version) == URL


if __name__ == "__main__":
    main()
