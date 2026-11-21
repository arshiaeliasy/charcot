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
    // رنگ نوار مرورگر موبایل/دسکتاپ باید همیشه با تم جاری یکی باشد
    // (پیشتر فقط در لحظهٔ بارگذاری و با متغیر محلی اسکریپت هد ست میشد).
    // رنگ نوار مرورگر مستقیماً از متغیر CSS خوانده می‌شود تا تک‌منبع بماند

    function themeColorValue(fallback) {
        const fromCss = getComputedStyle(document.documentElement).getPropertyValue('--theme-color');
        return fromCss && fromCss.trim() ? fromCss.trim() : fallback;
    }

    function applyThemeColor(theme) {
        const color = themeColorValue(theme === 'light' ? '#F1F7F9' : '#07161B');
        let meta = document.querySelector('meta[name="theme-color"]');
        if (!meta) {
            meta = document.createElement('meta');
            meta.setAttribute('name', 'theme-color');
            document.head.appendChild(meta);
        }
        meta.setAttribute('content', color);
    }

    function applyTheme(theme) {
        theme = theme === 'light' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', theme);
        applyThemeColor(theme);
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
        { title: 'داخلی (Internal Medicine)', cat: 'استاجری', url: 'externship.html#internal-medicine', icon: '🩺', sub: 'کورس ماژور' },
        { title: 'جراحی عمومی (General Surgery)', cat: 'استاجری', url: 'externship.html#general-surgery', icon: '🔪', sub: 'کورس ماژور' },
        { title: 'کودکان (Pediatrics)', cat: 'استاجری', url: 'externship.html#pediatrics', icon: '👶', sub: 'کورس ماژور' },
        { title: 'زنان و زایمان (Obstetrics & Gyn)', cat: 'استاجری', url: 'externship.html#obgyn', icon: '🤰', sub: 'کورس ماژور' },
        { title: 'مغز و اعصاب (Neurology)', cat: 'استاجری', url: 'externship.html#neurology', icon: '🧠', sub: 'کورس مینور' },
        { title: 'قلب و عروق (Cardiology)', cat: 'استاجری', url: 'externship.html#cardiology', icon: '🫀', sub: 'کورس مینور' },
        { title: 'بیماری‌های عفونی (Infectious Diseases)', cat: 'استاجری', url: 'externship.html#infectious-diseases', icon: '🦠', sub: 'کورس مینور' },
        { title: 'روان‌پزشکی (Psychiatry)', cat: 'استاجری', url: 'externship.html#psychiatry', icon: '🧠', sub: 'کورس مینور' },
        { title: 'ارتوپدی (Orthopedics)', cat: 'استاجری', url: 'externship.html#orthopedics', icon: '🦴', sub: 'کورس مینور' },
        { title: 'چشم‌پزشکی (Ophthalmology)', cat: 'استاجری', url: 'externship.html#ophthalmology', icon: '👁️', sub: 'کورس مینور' },
        { title: 'گوش و حلق و بینی (ENT)', cat: 'استاجری', url: 'externship.html#ent', icon: '👂', sub: 'کورس مینور' },
        { title: 'پوست (Dermatology)', cat: 'استاجری', url: 'externship.html#dermatology', icon: '🔬', sub: 'کورس مینور' },
        { title: 'اورولوژی (Urology)', cat: 'استاجری', url: 'externship.html#urology', icon: '🩺', sub: 'کورس مینور' },
        { title: 'بیهوشی و طب اورژانس', cat: 'استاجری', url: 'externship.html#anesthesia-emergency', icon: '🚑', sub: 'کورس مینور' },
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
        /* --- یادداشت‌های بالینی --- */
        { title: 'یادداشت‌های بالینی کانال', cat: 'مقطع', url: 'clinical-notes.html', icon: '📝', sub: 'کیس‌ها، روماتولوژی، گوارش و علوم پایه' },
        { title: 'کیس میوزیت پست‌وایرال', cat: 'یادداشت', url: 'clinical-notes.html#case-myositis', icon: '💪', sub: 'ضعف عضلانی پس از سرماخوردگی در کودک' },
        { title: 'کیس تورم دور چشم', cat: 'یادداشت', url: 'clinical-notes.html#case-orbital', icon: '👁️', sub: 'سلولیت پری‌سپتال در مقابل حساسیت' },
        { title: 'کیس اسپلنومگالی کودک', cat: 'یادداشت', url: 'clinical-notes.html#case-splenomegaly', icon: '🩸', sub: 'درد شکم و بزرگی طحال و کبد' },
        { title: 'کیس سیانوز نوزاد', cat: 'یادداشت', url: 'clinical-notes.html#case-neonatal-cyanosis', icon: '👶', sub: 'هایپراکسی تست و بیماری‌های قلبی سیانوتیک' },
        { title: 'کیس یرقان کودک', cat: 'یادداشت', url: 'clinical-notes.html#case-cholestasis', icon: '🟡', sub: 'تفسیر بیلی‌روبین و آنزیم‌های کبدی' },
        { title: 'داستان لوپوس (SLE)', cat: 'یادداشت', url: 'clinical-notes.html#sle', icon: '🦋', sub: 'پاتوژنز، تشخیص و درمان' },
        { title: 'اسپوندیلیت آنکیلوزان', cat: 'یادداشت', url: 'clinical-notes.html#ankylosing', icon: '🦴', sub: 'HLA-B27 و ستون فقرات بامبویی' },
        { title: 'پرپورا هنوخ-شونلاین', cat: 'یادداشت', url: 'clinical-notes.html#hsp', icon: '🟣', sub: 'پرپورای لمس‌پذیر و درگیری کلیه' },
        { title: 'درد مفصلی در مقابل غیرمفصلی', cat: 'یادداشت', url: 'clinical-notes.html#articular-pain', icon: '🔀', sub: 'آرتروز در مقابل فیبرومیالژیا' },
        { title: 'آزمایش‌های روماتولوژی', cat: 'یادداشت', url: 'clinical-notes.html#rheum-tests', icon: '🧪', sub: 'ANA، Anti-dsDNA، Anti-CCP، کمپلمان' },
        { title: 'سندرم اتصالی مختلط (MCTD)', cat: 'یادداشت', url: 'clinical-notes.html#mctd', icon: '🧬', sub: 'لوپوس + اسکلرودرمی + میوزیت' },
        { title: 'تست‌های چهارگزینه‌ای روماتولوژی', cat: 'یادداشت', url: 'clinical-notes.html#rheum-quiz', icon: '❓', sub: 'پسوریاتیک و فیبرومیالژی' },
        { title: 'اسهال حاد (هاریسون)', cat: 'یادداشت', url: 'clinical-notes.html#diarrhea', icon: '💧', sub: 'الگوریتم ارزیابی و درمان' },
        { title: 'سندرم روده تحریک‌پذیر (IBS)', cat: 'یادداشت', url: 'clinical-notes.html#ibs', icon: '🌀', sub: 'Rome IV و درمان زیرگروه‌ها' },
        { title: 'بیماری کرون و کولیت اولسراتیو', cat: 'یادداشت', url: 'clinical-notes.html#ibd', icon: '🩹', sub: 'مقایسه IBD بر اساس هاریسون' },
        { title: 'ایسکمی روده', cat: 'یادداشت', url: 'clinical-notes.html#mesenteric-ischemia', icon: '🫀', sub: 'AOMI، NOMI و کولیت ایسکمیک' },
        { title: 'پانکراتیت حاد و مزمن', cat: 'یادداشت', url: 'clinical-notes.html#pancreatitis', icon: '🔥', sub: 'معیار تشخیصی ۲ از ۳' },
        { title: 'یبوست حاد', cat: 'یادداشت', url: 'clinical-notes.html#constipation', icon: '⛔', sub: 'علائم هشدار و ارزیابی' },
        { title: 'کولیک صفراوی', cat: 'یادداشت', url: 'clinical-notes.html#biliary-colic', icon: '🟠', sub: 'سنگ صفرا و درد RUQ' },
        { title: 'GERD (ریفلاکس)', cat: 'یادداشت', url: 'clinical-notes.html#gerd', icon: '🫗', sub: 'اندیکاسیون آندوسکوپی و پایش pH' },
        { title: 'الگوهای آسیب کبدی و R Factor', cat: 'یادداشت', url: 'clinical-notes.html#liver-enzymes', icon: '🫘', sub: 'هپاتوسلولار در مقابل کلستاتیک' },
        { title: 'نلسون و نارسایی آدرنال', cat: 'یادداشت', url: 'clinical-notes.html#nelson', icon: '⚕️', sub: 'سندرم پس از آدرنال‌کتومی' },
        { title: 'داستان بروسلا (تب مالت)', cat: 'یادداشت', url: 'clinical-notes.html#brucella', icon: '🥛', sub: 'تب مواج و درمان ترکیبی' },
        { title: 'جدول واکولیت‌ها', cat: 'یادداشت', url: 'clinical-notes.html#vasculitis-mnemonics', icon: '🩸', sub: 'تاکایاسو، تمپورال، GPA، PAN' },
        { title: 'ریشه‌های عصبی کمری L2-S1', cat: 'یادداشت', url: 'clinical-notes.html#myotomes', icon: '🦶', sub: 'نقشه حرکات عضلانی' },
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

    /* ------------------------------------------------------
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
            const label = header.textContent.replace(/\s+/g, ' ').trim();
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
    let searchBuilt = false;
    let searchOverlay = null;
    let searchInput = null;
    let searchResults = null;
    /* --- جستجوی سراسری متن (ایندکس در js/search-index.json) --- */
    let textIndex = null;
    let textIndexLoading = false;
    let lastQuery = '';
    const MIN_FULLTEXT = 3;   // کمتر از این تعداد حرف، جستجو فقط روی عنوان انجام می‌شود

    function loadTextIndex() {
        if (textIndex || textIndexLoading) return;
        textIndexLoading = true;
        fetch('js/search-index.json', { cache: 'force-cache' })
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (data) {
                textIndex = data && data.pages ? data.pages : {};
                textIndexLoading = false;
                if (lastQuery) renderSearchResults(lastQuery);
            })
            .catch(function () {
                textIndex = {};
                textIndexLoading = false;
            });
    }
    // ریشه‌یابی سبک فارسی: «ها/های/هایی» و «تر/ترین» را نادیده می‌گیرد

    function stem(word) {
        let w = word;
        if (w.length > 4) w = w.replace(/(هایی|های|ها)$/, '');
        if (w.length > 4) w = w.replace(/(ترین|تر)$/, '');
        return w;
    }

    function queryTerms(q) {
        return normalize(q).split(' ').filter(function (t) { return t.length > 0; });
    }
    // امتیازدهی یک بخش: عنوان وزن بیشتری از متن دارد

    function scoreSection(sec, pageTitle, terms) {
        const title = normalize(sec.title || '');
        const body = normalize(sec.text || '');
        const page = normalize(pageTitle || '');
        let score = 0;
        for (let i = 0; i < terms.length; i++) {
            const t = terms[i];
            const st = stem(t);
            let hit = 0;
            if (title.indexOf(t) !== -1) hit += 12;
            else if (st !== t && title.indexOf(st) !== -1) hit += 8;
            if (page.indexOf(t) !== -1) hit += 2;
            if (body.indexOf(t) !== -1) hit += 5;
            else if (st !== t && body.indexOf(st) !== -1) hit += 3;
            if (hit === 0) return 0;   // همهٔ واژه‌ها باید جایی در بخش باشند
            score += hit;
        }
        if (sec.title) score += 1;
        return score;
    }

    function snippetAround(text, term, len) {
        len = len || 130;
        if (!term) return '';
        const norm = normalize(text);
        let needle = term;
        let pos = norm.indexOf(needle);
        if (pos === -1 && term.length > 4) {
            needle = stem(term);
            pos = norm.indexOf(needle);
        }
        if (pos === -1) return '';
        const start = Math.max(0, pos - Math.floor(len / 3));
        let frag = text.substr(start, len);
        if (start > 0) frag = '… ' + frag;
        if (start + len < text.length) frag = frag + ' …';
        return frag;
    }

    function highlight(frag, terms) {
        let safe = escapeHtml(frag);
        for (let i = 0; i < terms.length; i++) {
            const t = terms[i];
            if (t.length < 2) continue;
            const esc = t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            safe = safe.replace(new RegExp('(' + esc + ')', 'gi'), '<mark>$1</mark>');
        }
        return safe;
    }

    function currentPage() {
        const p = (window.location.pathname || '').split('/').pop();
        return p && p.indexOf('.html') !== -1 ? p : 'index.html';
    }

    function searchFullText(terms) {
        if (!textIndex) return [];
        const here = currentPage();
        const out = [];
        const pages = Object.keys(textIndex);
        for (let p = 0; p < pages.length; p++) {
            const page = pages[p];
            const info = textIndex[page] || {};
            const secs = info.sections || [];
            for (let i = 0; i < secs.length; i++) {
                const seg = secs[i];
                const sc = scoreSection(seg, info.title, terms);
                if (sc > 0) {
                    out.push({
                        page: page,
                        pageTitle: info.title || page,
                        weight: typeof info.weight === 'number' ? info.weight : 3,
                        sec: seg,
                        score: sc + (page === here ? 3 : 0)
                    });
                }
            }
        }
        out.sort(function (a, b) {
            if (b.score !== a.score) return b.score - a.score;
            return a.weight - b.weight;
        });
        return out;
    }

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
        lastQuery = query;
        if (!q) {
            searchResults.innerHTML = '<div class="search-empty">شروع به تایپ کنید... مثلاً «قلب»، «کودکان»، «اسهال» یا «آناتومی»</div>';
            return;
        }
        // بخش ۱ — عنوان‌ها و فهرست راهنما (آنی، بدون نیاز به دانلود ایندکس)
        const titleMatches = SEARCH_INDEX.filter(function (item) {
            return normalize(item.title + ' ' + item.cat + ' ' + (item.sub || '')).indexOf(q) !== -1;
        });
        // بخش ۲ — متن کامل، از سه حرف به بالا
        let fullMatches = [];
        const compact = q.replace(/\s/g, '');
        if (compact.length >= MIN_FULLTEXT) {
            if (!textIndex) loadTextIndex();
            fullMatches = searchFullText(queryTerms(q));
        }
        // نتایج تکراری حذف شوند
        const seen = {};
        titleMatches.forEach(function (it) { seen[normalize(it.title)] = true; });
        const filteredFull = fullMatches.filter(function (m) {
            return !seen[normalize(m.sec.title || '')];
        });
        if (!titleMatches.length && !filteredFull.length) {
            searchResults.innerHTML = '<div class="search-empty">نتیجه‌ای پیدا نشد. عبارت دیگری امتحان کنید.</div>';
            return;
        }
        titleMatches.sort(function (a, b) {
            const aStart = normalize(a.title).indexOf(q) === 0 ? 0 : 1;
            const bStart = normalize(b.title).indexOf(q) === 0 ? 0 : 1;
            return aStart - bStart;
        });
        const terms = queryTerms(q);
        let html = titleMatches.slice(0, 8).map(function (item) {
            return '<a class="search-result" href="' + item.url + '">' +
                        '<span class="r-title">' + item.icon + ' ' + escapeHtml(item.title) +
                            (item.sub ? '<span class="r-sub">' + escapeHtml(item.sub) + '</span>' : '') +
                        '</span>' +
                        '<span class="r-cat">' + escapeHtml(item.cat) + '</span>' +
                    '</a>';
        }).join('');
        html += filteredFull.slice(0, 22).map(function (m) {
            const url = m.page + (m.sec.id ? '#' + m.sec.id : '#top');
            const frag = snippetAround(m.sec.text, terms[0]);
            return '<a class="search-result" href="' + url + '">' +
                        '<span class="r-title">' + escapeHtml(m.sec.title || m.pageTitle) +
                            '<span class="r-sub">' + escapeHtml(m.pageTitle) + '</span>' +
                        '</span>' +
                        (frag ? '<span class="r-hit">' + highlight(frag, terms) + '</span>' : '') +
                        '<span class="r-cat">در متن</span>' +
                    '</a>';
        }).join('');
        if (!textIndex && compact.length >= MIN_FULLTEXT) {
            html += '<div class="search-source">در حال جستجو در متن کامل…</div>';
        } else if (filteredFull.length) {
            html += '<div class="search-source">' + filteredFull.length + ' بخش در متن صفحات پیدا شد</div>';
        }
        searchResults.innerHTML = html;
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
        buildToc();
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