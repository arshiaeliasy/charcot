# -*- coding: utf-8 -*-
"""
inject_features.py — افزودن «فهرست چسبان بخش‌ها» به js/main.js
اجرا از ریشهٔ پروژه:  python tools/inject_features.py
"""

import io
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

PATH = "js/main.js"

TOC = u"""    /* ------------------------------------------------------
       ۶.۵) فهرست چسبان کنار صفحه + هایلایت بخش جاری
       ------------------------------------------------------ */
    function buildToc() {
        const items = document.querySelectorAll('.accordion-item');
        if (items.length < 6) return;   // صفحه‌های کم‌بخش نیازی به فهرست ندارند

        const main = document.querySelector('main');
        if (!main) return;

        const container = main.querySelector('.content-container') || main;
        if (!container.parentElement) return;

        const links = [];
        const ol = document.createElement('ol');

        items.forEach(function (item) {
            const header = item.querySelector('.accordion-header');
            if (!header || !item.id) return;
            const label = header.textContent.replace(/\\s+/g, ' ').trim();
            if (!label) return;

            const li = document.createElement('li');
            const a = document.createElement('a');
            a.href = '#' + item.id;
            a.textContent = label;
            li.appendChild(a);
            ol.appendChild(li);
            links.push({ id: item.id, a: a, el: item });
        });

        if (links.length < 6) return;

        const nav = document.createElement('nav');
        nav.className = 'toc-nav';
        nav.setAttribute('aria-label', 'فهرست بخش‌های این صفحه');
        const heading = document.createElement('h2');
        heading.textContent = '📑 فهرست بخش‌ها';
        nav.appendChild(heading);
        nav.appendChild(ol);

        const layout = document.createElement('div');
        layout.className = 'page-layout has-toc';
        container.parentElement.insertBefore(layout, container);
        layout.appendChild(container);
        layout.appendChild(nav);
        document.documentElement.classList.add('has-toc-layout');

        // هایلایت بخش جاری هنگام اسکرول
        let ticking = false;
        function updateActive() {
            ticking = false;
            const offset = 150;
            let current = null;
            for (let i = 0; i < links.length; i++) {
                const rect = links[i].el.getBoundingClientRect();
                if (rect.top <= offset) current = links[i];
                else break;
            }
            if (!current && links.length) current = links[0];
            links.forEach(function (l) {
                l.a.classList.toggle('active', current === l);
            });
        }

        window.addEventListener('scroll', function () {
            if (!ticking) {
                ticking = true;
                window.requestAnimationFrame(updateActive);
            }
        }, { passive: true });

        // کلیک روی فهرست، آکاردئون همان بخش را هم باز کند
        nav.addEventListener('click', function (e) {
            const a = e.target.closest ? e.target.closest('a') : null;
            if (!a) return;
            const id = (a.getAttribute('href') || '').slice(1);
            const item = id ? document.getElementById(id) : null;
            if (item && item.classList.contains('accordion-item')) {
                document.querySelectorAll('.accordion-item').forEach(function (el) {
                    if (el !== item) {
                        el.classList.remove('active');
                        const h = el.querySelector('.accordion-header');
                        if (h) h.setAttribute('aria-expanded', 'false');
                    }
                });
                item.classList.add('active');
                const h = item.querySelector('.accordion-header');
                if (h) h.setAttribute('aria-expanded', 'true');
            }
        });

        updateActive();
    }

"""


def main():
    s = io.open(PATH, encoding="utf-8", newline="").read()
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r"\n{3,}", "\n\n", s)

    if "function buildToc()" in s:
        print("buildToc از قبل وجود دارد؛ فقط فراخوانی بررسی می‌شود.")
    else:
        m = re.search(
            r"(\n\s*openFromHash\(\);\n+)(\s*window\.addEventListener\('hashchange', openFromHash\);\n+)",
            s,
        )
        if not m:
            print("!! لنگر آکاردئون پیدا نشد")
            return 1
        # پایان تابع initAccordion
        close = s.find("\n    }\n", m.end())
        if close == -1:
            print("!! پایان تابع آکاردئون پیدا نشد")
            return 1
        insert_at = close + len("\n    }\n")
        s = s[:insert_at] + "\n" + TOC + s[insert_at:]
        print("buildToc اضافه شد.")

    if "buildToc();" not in s:
        m = re.search(r"(\n\s*initAccordion\(\);\n+)", s)
        if not m:
            print("!! فراخوانی initAccordion پیدا نشد")
            return 1
        s = s[:m.end()] + "        buildToc();\n" + s[m.end():]
        print("فراخوانی buildToc اضافه شد.")

    with io.open(PATH, "w", encoding="utf-8", newline="") as fh:
        fh.write(s.replace("\n", "\r\n"))
    print("js/main.js ذخیره شد. خطوط:", s.count("\n") + 1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
