/* ============================================================
   شارکوت | Charcot - اسکریپت مشترک همه صفحات
   شامل: تم روز/شب، منوی موبایل، جستجوی سریع، Toast، آکاردئون
   ============================================================ */
(function () {
    'use strict';

    /* ------------------------------------------------------
       ۱) تم روز / شب
       ------------------------------------------------------ */
    const THEME_KEY = 'charcot-theme';

    function applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        const btn = document.getElementById('themeBtn');
        if (btn) {
            btn.textContent = theme === 'light' ? '🌙' : '☀️';
            btn.setAttribute('aria-label', theme === 'light' ? 'فعال‌سازی حالت تیره' : 'فعال‌سازی حالت روشن');
            btn.setAttribute('title', theme === 'light' ? 'حالت تیره' : 'حالت روشن');
        }
    }

    function initTheme() {
        let saved = null;
        try { saved = localStorage.getItem(THEME_KEY); } catch (e) { /* ignore */ }
        const prefersLight = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches;
        applyTheme(saved || (prefersLight ? 'light' : 'dark'));
    }

    function toggleTheme() {
        const current = document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
        const next = current === 'light' ? 'dark' : 'light';
        applyTheme(next);
        try { localStorage.setItem(THEME_KEY, next); } catch (e) { /* ignore */ }
    }

    /* ------------------------------------------------------
       ۲) Toast (جایگزین alert)
       ------------------------------------------------------ */
    function ensureToastContainer() {
        let container = document.getElementById('toastContainer');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toastContainer';
            container.setAttribute('role', 'status');
            container.setAttribute('aria-live', 'polite');
            document.body.appendChild(container);
        }
        return container;
    }

    function showToast(message, type) {
        type = type || 'info';
        const container = ensureToastContainer();
        const toast = document.createElement('div');
        toast.className = 'toast ' + type;
        const icons = { success: '✅', error: '⚠️', info: 'ℹ️' };
        toast.innerHTML = '<span>' + (icons[type] || 'ℹ️') + '</span><span>' + escapeHtml(message) + '</span>';
        container.appendChild(toast);
        setTimeout(function () {
            toast.classList.add('hide');
            setTimeout(function () { toast.remove(); }, 320);
        }, 4200);
    }

    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    window.showToast = showToast;

    /* ------------------------------------------------------
       ۳) منوی موبایل
       ------------------------------------------------------ */
    function initMobileMenu() {
        const menuBtn = document.getElementById('menuBtn');
        const nav = document.getElementById('mainNav');
        if (!menuBtn || !nav) return;

        menuBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            const isOpen = nav.classList.toggle('open');
            menuBtn.setAttribute('aria-expanded', String(isOpen));
            menuBtn.textContent = isOpen ? '✕' : '☰';
        });

        document.addEventListener('click', function (e) {
            if (!nav.classList.contains('open')) return;
            if (!nav.contains(e.target) && e.target !== menuBtn) {
                nav.classList.remove('open');
                menuBtn.setAttribute('aria-expanded', 'false');
                menuBtn.textContent = '☰';
            }
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && nav.classList.contains('open')) {
                nav.classList.remove('open');
                menuBtn.setAttribute('aria-expanded', 'false');
                menuBtn.textContent = '☰';
            }
        });
    }

    /* ------------------------------------------------------
       ۴) هایلایت لینک صفحهٔ جاری
       ------------------------------------------------------ */
    function initActiveNav() {
        let file = window.location.pathname.split('/').pop() || 'index.html';
        if (file === '') file = 'index.html';
        // صفحات جزئیات کیس، زیرمجموعه صفحه «کیس‌های بالینی» هستند
        const navFile = file.indexOf('case-') === 0 ? 'clinical-cases.html' : file;
        document.querySelectorAll('#mainNav a').forEach(function (link) {
            const href = (link.getAttribute('href') || '').split('/').pop();
            if (href === navFile) link.classList.add('active');
        });
    }

    /* ------------------------------------------------------
       ۵) آکاردئون (به‌جای onclick درون‌خطی)
       ------------------------------------------------------ */
    function initAccordion() {
        document.querySelectorAll('.accordion-header').forEach(function (header) {
            header.addEventListener('click', function () {
                const item = header.parentElement;
                document.querySelectorAll('.accordion-item').forEach(function (el) {
                    if (el !== item) {
                        el.classList.remove('active');
                        const h = el.querySelector('.accordion-header');
                        if (h) h.setAttribute('aria-expanded', 'false');
                    }
                });
                const isActive = item.classList.toggle('active');
                header.setAttribute('aria-expanded', String(isActive));
            });
        });

        // باز کردن آیتم مورد نظر با لینک مستقیم (مثلاً basic-sciences.html#physiology)
        function openFromHash() {
            const id = decodeURIComponent((window.location.hash || '').slice(1));
            if (!id) return;
            const target = document.getElementById(id);
            if (target && target.classList.contains('accordion-item')) {
                document.querySelectorAll('.accordion-item').forEach(function (el) {
                    el.classList.remove('active');
                    const h = el.querySelector('.accordion-header');
                    if (h) h.setAttribute('aria-expanded', 'false');
                });
                target.classList.add('active');
                const header = target.querySelector('.accordion-header');
                if (header) header.setAttribute('aria-expanded', 'true');
                target.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }
        openFromHash();
        window.addEventListener('hashchange', openFromHash);
    }

    /* ------------------------------------------------------
       ۶) جستجوی سریع
       ------------------------------------------------------ */
    const SEARCH_INDEX = [
        /* --- علوم پایه --- */
        { title: 'فیزیولوژی', cat: 'علوم پایه', url: 'basic-sciences.html#physiology', icon: '🧪' },
        { title: 'بیوشیمی', cat: 'علوم پایه', url: 'basic-sciences.html#biochemistry', icon: '⚗️' },
        { title: 'باکتری‌شناسی', cat: 'علوم پایه', url: 'basic-sciences.html#bacteriology', icon: '🧫' },
        { title: 'انگل‌شناسی', cat: 'علوم پایه', url: 'basic-sciences.html#parasitology', icon: '🐛' },
        { title: 'قارچ‌شناسی', cat: 'علوم پایه', url: 'basic-sciences.html#mycology', icon: '🍄' },
        { title: 'حشره‌شناسی', cat: 'علوم پایه', url: 'basic-sciences.html#entomology', icon: '🪲' },
        { title: 'ویروس‌شناسی', cat: 'علوم پایه', url: 'basic-sciences.html#virology', icon: '🦠' },
        { title: 'آناتومی', cat: 'علوم پایه', url: 'basic-sciences.html#anatomy', icon: '💀' },
        { title: 'بافت‌شناسی', cat: 'علوم پایه', url: 'basic-sciences.html#histology', icon: '🔬' },
        { title: 'جنین‌شناسی', cat: 'علوم پایه', url: 'basic-sciences.html#embryology', icon: '👶' },
        { title: 'اصول خدمات سلامت', cat: 'علوم پایه', url: 'basic-sciences.html#health-services', icon: '🏥' },
        { title: 'اپیدمیولوژی', cat: 'علوم پایه', url: 'basic-sciences.html#epidemiology', icon: '📊' },
        { title: 'ایمونولوژی', cat: 'علوم پایه', url: 'basic-sciences.html#immunology', icon: '🛡️' },
        { title: 'زبان انگلیسی', cat: 'علوم پایه', url: 'basic-sciences.html#english', icon: '📖' },
        { title: 'ژنتیک پزشکی', cat: 'علوم پایه', url: 'basic-sciences.html#genetics', icon: '🧬' },
        { title: 'پاتولوژی', cat: 'علوم پایه', url: 'basic-sciences.html#pathology', icon: '🔬' },
        { title: 'اصول تغذیه', cat: 'علوم پایه', url: 'basic-sciences.html#nutrition', icon: '🥗' },
        { title: 'انقلاب و اندیشه اسلامی', cat: 'علوم پایه', url: 'basic-sciences.html#islamic-thought', icon: '📚' },
        { title: 'فیزیک پزشکی', cat: 'علوم پایه', url: 'basic-sciences.html#medical-physics', icon: '⚛️' },

        /* --- فیزیوپاتولوژی --- */
        { title: 'فیزیوپاتولوژی', cat: 'مقطع', url: 'pathophysiology.html', icon: '🔬', sub: 'مکانیسم بیماری‌ها به تفکیک اندام' },
        { title: 'فیزیوپاتولوژی قلب و عروق', cat: 'فیزیوپاتولوژی', url: 'pathophysiology.html', icon: '🫀' },
        { title: 'فیزیوپاتولوژی ریه', cat: 'فیزیوپاتولوژی', url: 'pathophysiology.html', icon: '🫁' },
        { title: 'فیزیوپاتولوژی کلیه', cat: 'فیزیوپاتولوژی', url: 'pathophysiology.html', icon: '🫘' },
        { title: 'اختلالات اسید و باز', cat: 'فیزیوپاتولوژی', url: 'pathophysiology.html', icon: '⚗️' },
        { title: 'شوک (Shock)', cat: 'فیزیوپاتولوژی', url: 'pathophysiology.html', icon: '📉' },

        /* --- استاجری --- */
        { title: 'داخلی (Internal Medicine)', cat: 'استاجری', url: 'externship.html', icon: '🩺', sub: 'کورس ماژور' },
        { title: 'جراحی عمومی (General Surgery)', cat: 'استاجری', url: 'externship.html', icon: '🔪', sub: 'کورس ماژور' },
        { title: 'کودکان (Pediatrics)', cat: 'استاجری', url: 'externship.html', icon: '👶', sub: 'کورس ماژور' },
        { title: 'زنان و زایمان (Obstetrics & Gyn)', cat: 'استاجری', url: 'externship.html', icon: '🤰', sub: 'کورس ماژور' },
        { title: 'مغز و اعصاب (Neurology)', cat: 'استاجری', url: 'externship.html', icon: '🧠', sub: 'کورس مینور' },
        { title: 'قلب و عروق (Cardiology)', cat: 'استاجری', url: 'externship.html', icon: '🫀', sub: 'کورس مینور' },
        { title: 'بیماری‌های عفونی (Infectious Diseases)', cat: 'استاجری', url: 'externship.html', icon: '🦠', sub: 'کورس مینور' },
        { title: 'روان‌پزشکی (Psychiatry)', cat: 'استاجری', url: 'externship.html', icon: '🧠', sub: 'کورس مینور' },
        { title: 'ارتوپدی (Orthopedics)', cat: 'استاجری', url: 'externship.html', icon: '🦴', sub: 'کورس مینور' },
        { title: 'چشم‌پزشکی (Ophthalmology)', cat: 'استاجری', url: 'externship.html', icon: '👁️', sub: 'کورس مینور' },
        { title: 'گوش و حلق و بینی (ENT)', cat: 'استاجری', url: 'externship.html', icon: '👂', sub: 'کورس مینور' },
        { title: 'پوست (Dermatology)', cat: 'استاجری', url: 'externship.html', icon: '🔬', sub: 'کورس مینور' },
        { title: 'اورولوژی (Urology)', cat: 'استاجری', url: 'externship.html', icon: '🩺', sub: 'کورس مینور' },
        { title: 'بیهوشی و طب اورژانس', cat: 'استاجری', url: 'externship.html', icon: '🚑', sub: 'کورس مینور' },

        /* --- پره انترنی / اینترنی --- */
        { title: 'پره انترنی', cat: 'مقطع', url: 'pre-internship.html', icon: '📝', sub: 'راهنمای آمادگی، چک‌لیست و منابع' },
        { title: 'اینترنی', cat: 'مقطع', url: 'internship.html', icon: '🩺', sub: 'انتخاب‌های بالینی و برنامه روزانه' },
        { title: 'منابع پره انترنی', cat: 'پره انترنی', url: 'pre-internship.html', icon: '📚' },
        { title: 'انتخاب‌های اینترنی', cat: 'اینترنی', url: 'internship.html', icon: '🏥' },

        /* --- کیس‌های بالینی --- */
        { title: 'کیس سکته مغزی حاد (Stroke)', cat: 'کیس بالینی', url: 'case-stroke.html', icon: '🧠', sub: 'فلج حاد اندام‌ها و افت هوشیاری' },
        { title: 'کیس درد قفسه سینه (ACS)', cat: 'کیس بالینی', url: 'case-acs.html', icon: '🫀', sub: 'سندرم حاد کرونری و تفسیر ECG' },
        { title: 'کیس شوک سپتیک', cat: 'کیس بالینی', url: 'case-sepsis.html', icon: '🌡️', sub: 'تب، لرز و افت فشار خون مقاوم' },
        { title: 'سکته مغزی ایسکمیک و ترومبولیز', cat: 'کیس بالینی', url: 'case-stroke.html', icon: '⏱️', sub: 'پنجره زمانی ۴.۵ ساعته' },
        { title: 'سندرم حاد کرونری (ACS)', cat: 'کیس بالینی', url: 'case-acs.html', icon: '📈', sub: 'STEMI و NON-STEMI' },
        { title: 'شوک سپتیک و سرکوب واکنش التهابی', cat: 'کیس بالینی', url: 'case-sepsis.html', icon: '🧫', sub: 'گایدلاین Surviving Sepsis' },

        /* --- صفحات --- */
        { title: 'صفحه اصلی', cat: 'صفحه', url: 'index.html', icon: '🏠' },
        { title: 'درباره ما', cat: 'صفحه', url: 'about-us.html', icon: 'ℹ️' },
        { title: 'ورود و ثبت‌نام', cat: 'صفحه', url: 'index.html#auth', icon: '🔐' }
    ];

    function normalize(text) {
        return String(text)
            .toLowerCase()
            .replace(/ي/g, 'ی')
            .replace(/ك/g, 'ک')
            .replace(/\u200c/g, ' ')
            .replace(/[ًٌٍَُِّْ]/g, '')
            .replace(/\s+/g, ' ')
            .trim();
    }

    let searchBuilt = false;
    let searchOverlay = null;
    let searchInput = null;
    let searchResults = null;

    function buildSearchModal() {
        if (searchBuilt) return;
        searchBuilt = true;

        searchOverlay = document.createElement('div');
        searchOverlay.className = 'search-overlay';
        searchOverlay.setAttribute('role', 'dialog');
        searchOverlay.setAttribute('aria-modal', 'true');
        searchOverlay.setAttribute('aria-label', 'جستجو در شارکوت');
        searchOverlay.innerHTML =
            '<div class="search-panel">' +
                '<div class="search-input-row">' +
                    '<span class="search-icon">🔍</span>' +
                    '<input type="text" id="searchInput" placeholder="جستجوی درس، بخش یا کیس بالینی..." autocomplete="off" />' +
                    '<button class="search-close" type="button">ESC</button>' +
                '</div>' +
                '<div class="search-results" id="searchResults"></div>' +
                '<div class="search-hint">' +
                    '<span>برای بستن ESC را بزنید</span>' +
                    '<span>Ctrl + K برای جستجوی سریع</span>' +
                '</div>' +
            '</div>';

        document.body.appendChild(searchOverlay);
        searchInput = searchOverlay.querySelector('#searchInput');
        searchResults = searchOverlay.querySelector('#searchResults');

        searchOverlay.addEventListener('click', function (e) {
            if (e.target === searchOverlay) closeSearch();
        });
        searchOverlay.querySelector('.search-close').addEventListener('click', closeSearch);

        searchInput.addEventListener('input', function () {
            renderSearchResults(searchInput.value);
        });

        searchInput.addEventListener('keydown', function (e) {
            const items = Array.prototype.slice.call(searchResults.querySelectorAll('.search-result'));
            if (!items.length) return;

            let idx = items.findIndex(function (el) { return el.classList.contains('selected'); });

            if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
                e.preventDefault();
                if (idx > -1) items[idx].classList.remove('selected');
                idx = e.key === 'ArrowDown'
                    ? (idx + 1) % items.length
                    : (idx <= 0 ? items.length - 1 : idx - 1);
                items[idx].classList.add('selected');
                items[idx].scrollIntoView({ block: 'nearest' });
            } else if (e.key === 'Enter') {
                e.preventDefault();
                const target = idx > -1 ? items[idx] : items[0];
                window.location.href = target.getAttribute('href');
            }
        });
    }

    function renderSearchResults(query) {
        const q = normalize(query);
        if (!q) {
            searchResults.innerHTML = '<div class="search-empty">شروع به تایپ کنید... مثلاً «قلب»، «کودکان» یا «آناتومی»</div>';
            return;
        }

        const matches = SEARCH_INDEX.filter(function (item) {
            return normalize(item.title + ' ' + item.cat + ' ' + (item.sub || '')).indexOf(q) !== -1;
        });

        if (!matches.length) {
            searchResults.innerHTML = '<div class="search-empty">نتیجه‌ای پیدا نشد. عبارت دیگری امتحان کنید.</div>';
            return;
        }

        // مرتب‌سازی: عنوان‌هایی که با عبارت شروع می‌شوند اول
        matches.sort(function (a, b) {
            const aStart = normalize(a.title).indexOf(q) === 0 ? 0 : 1;
            const bStart = normalize(b.title).indexOf(q) === 0 ? 0 : 1;
            return aStart - bStart;
        });

        searchResults.innerHTML = matches.slice(0, 30).map(function (item) {
            return '<a class="search-result" href="' + item.url + '">' +
                        '<span class="r-title">' + item.icon + ' ' + escapeHtml(item.title) +
                            (item.sub ? '<span class="r-sub">' + escapeHtml(item.sub) + '</span>' : '') +
                        '</span>' +
                        '<span class="r-cat">' + escapeHtml(item.cat) + '</span>' +
                    '</a>';
        }).join('');
    }

    function openSearch(e) {
        if (e) e.preventDefault();
        buildSearchModal();
        searchOverlay.style.display = 'flex';
        document.body.style.overflow = 'hidden';
        searchInput.value = '';
        renderSearchResults('');
        setTimeout(function () { searchInput.focus(); }, 30);
    }

    function closeSearch() {
        if (!searchOverlay) return;
        searchOverlay.style.display = 'none';
        document.body.style.overflow = '';
    }

    function initSearch() {
        const btn = document.getElementById('searchBtn');
        if (btn) btn.addEventListener('click', openSearch);

        document.addEventListener('keydown', function (e) {
            if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')) {
                openSearch(e);
            } else if (e.key === '/' && document.activeElement === document.body) {
                openSearch(e);
            } else if (e.key === 'Escape') {
                closeSearch();
            }
        });
    }

    /* ------------------------------------------------------
       ۷) نوار پیشرفت اسکرول + دکمه بازگشت به بالا
       ------------------------------------------------------ */
    function initScrollTools() {
        const bar = document.createElement('div');
        bar.className = 'scroll-progress';
        bar.setAttribute('aria-hidden', 'true');
        document.body.appendChild(bar);

        const topBtn = document.createElement('button');
        topBtn.className = 'back-to-top';
        topBtn.type = 'button';
        topBtn.setAttribute('aria-label', 'بازگشت به بالای صفحه');
        topBtn.textContent = '↑';
        topBtn.addEventListener('click', function () {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });
        document.body.appendChild(topBtn);

        let ticking = false;
        function update() {
            const doc = document.documentElement;
            const max = doc.scrollHeight - doc.clientHeight;
            const pct = max > 0 ? (doc.scrollTop || document.body.scrollTop) / max * 100 : 0;
            bar.style.width = pct + '%';
            topBtn.classList.toggle('show', (doc.scrollTop || document.body.scrollTop) > 450);
            ticking = false;
        }

        window.addEventListener('scroll', function () {
            if (!ticking) {
                window.requestAnimationFrame(update);
                ticking = true;
            }
        }, { passive: true });
        update();
    }

    /* ------------------------------------------------------
       ۸) ظهور تدریجی بخش‌ها هنگام اسکرول
       ------------------------------------------------------ */
    function initReveal() {
        const targets = document.querySelectorAll('.reveal');
        if (!targets.length) return;

        const reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (reduced || !('IntersectionObserver' in window)) {
            targets.forEach(function (el) { el.classList.add('revealed'); });
            return;
        }

        document.documentElement.classList.add('js-reveal');
        const io = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('revealed');
                    io.unobserve(entry.target);
                }
            });
        }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

        targets.forEach(function (el) { io.observe(el); });
    }

    /* ------------------------------------------------------
       راه‌اندازی
       ------------------------------------------------------ */
    function init() {
        initTheme();
        const themeBtn = document.getElementById('themeBtn');
        if (themeBtn) themeBtn.addEventListener('click', toggleTheme);

        initMobileMenu();
        initActiveNav();
        initAccordion();
        initSearch();
        initScrollTools();
        initReveal();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
