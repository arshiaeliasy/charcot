/* ============================================================
   شارکوت | Charcot — تست رفتار واقعی js/main.js روی DOM حداقلی
   ------------------------------------------------------------
   اجرا:  node tools/runtime_test.mjs
   پوشش:
     • آکاردئون: باز شدن با هش، بستن آیتم قبلی، aria-expanded
     • تم: تغییر theme-color از متغیر CSS و ذخیره در localStorage
     • ابزار اسکرول: نوار پیشرفت + دکمهٔ بازگشت به بالا
     • فهرست چسبان بخش‌ها (buildToc) و کلیک روی آن
     • جستجوی سراسری متن از js/search-index.json
   ============================================================ */
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';

const ROOT = process.cwd() + path.sep;
const html = fs.readFileSync(ROOT + 'externship.html', 'utf8');
const searchIndex = JSON.parse(fs.readFileSync(ROOT + 'js/search-index.json', 'utf8'));

/* ---------- DOM حداقلی ---------- */
class ClassList {
    constructor() { this.set = new Set(); }
    add(c) { this.set.add(c); }
    remove(c) { this.set.delete(c); }
    contains(c) { return this.set.has(c); }
    toggle(c, force) {
        const on = force === undefined ? !this.set.has(c) : !!force;
        if (on) this.set.add(c); else this.set.delete(c);
        return on;
    }
    toString() { return [...this.set].join(' '); }
}

class El {
    constructor(tag) {
        this.tagName = (tag || 'div').toUpperCase();
        this.children = [];
        this.parentElement = null;
        this.classList = new ClassList();
        this.attributes = {};
        this.style = {};
        this.dataset = {};
        this.listeners = {};
        this._text = '';
        this.id = '';
    }
    get className() { return this.classList.toString(); }
    set className(v) { this.classList = new ClassList(); String(v).split(/\s+/).filter(Boolean).forEach(c => this.classList.add(c)); }
    get textContent() { return this._text || this.children.map(c => c.textContent).join(''); }
    set textContent(v) { this._text = String(v); this.children = []; }
    get innerHTML() { return this._html || ''; }
    set innerHTML(v) { this._html = String(v); this.children = []; parseInto(this, String(v)); }
    appendChild(c) { c.parentElement = this; this.children.push(c); return c; }
    insertBefore(node, ref) {
        node.parentElement = this;
        const i = this.children.indexOf(ref);
        if (i === -1) this.children.push(node);
        else this.children.splice(i, 0, node);
        return node;
    }
    scrollIntoView() {}
    focus() { document.activeElement = this; }
    closest(sel) {
        let n = this;
        while (n) {
            if (n.matches && n.matches(sel)) return n;
            n = n.parentElement;
        }
        return null;
    }
    remove() { if (this.parentElement) this.parentElement.children = this.parentElement.children.filter(x => x !== this); }
    setAttribute(k, v) { this.attributes[k] = String(v); if (k === 'id') this.id = String(v); if (k === 'class') this.className = v; if (k === 'href') this.href = String(v); }
    getAttribute(k) { return k in this.attributes ? this.attributes[k] : (k === 'href' && this.href ? this.href : null); }
    removeAttribute(k) { delete this.attributes[k]; }
    addEventListener(t, fn) { (this.listeners[t] = this.listeners[t] || []).push(fn); }
    removeEventListener() {}
    dispatch(t, extra) {
        const ev = Object.assign({ type: t, target: this, currentTarget: this, stopPropagation() {}, preventDefault() {} }, extra || {});
        let node = this;
        while (node) {
            ev.currentTarget = node;
            (node.listeners[t] || []).forEach(fn => fn.call(node, ev));
            node = node.parentElement;
        }
    }
    click() { this.dispatch('click'); }
    getBoundingClientRect() { return { top: (this._top || 0), left: 0, width: 100, height: 40, bottom: 0, right: 0 }; }
    matches(sel) {
        if (sel.startsWith('#')) return this.id === sel.slice(1);
        if (sel.indexOf('.') !== -1 && !sel.startsWith('[')) {
            const parts = sel.split('.').filter(Boolean);
            return parts.every(p => this.classList.contains(p));
        }
        if (sel.startsWith('.')) return this.classList.contains(sel.slice(1));
        return this.tagName === sel.toUpperCase();
    }
    querySelector(sel) { const r = this.querySelectorAll(sel); return r.length ? r[0] : null; }
    querySelectorAll(sel) {
        const parts = sel.trim().split(/\s+/);
        const out = [];
        const walk = (node, idx) => {
            node.children.forEach(ch => {
                if (ch.matches(parts[idx])) {
                    if (idx === parts.length - 1) out.push(ch);
                    else walk(ch, idx + 1);
                }
                walk(ch, idx);
            });
        };
        walk(this, 0);
        if (parts.length === 1 && this.matches(parts[0])) out.unshift(this);
        return out;
    }
}

const registry = new Map();
const docEl = new El('html');
const head = new El('head');
const body = new El('body');
const main = new El('main');
const container = new El('div');
container.classList.add('content-container');
main.appendChild(container);
body.appendChild(main);

/* ---------- تجزیهٔ سادهٔ innerHTML (فقط تگ‌های بدون تودرتویی عمیق) ---------- */
function parseInto(parent, htmlStr) {
    const re = /<(\w+)([^>]*)>([^<]*)/g;
    let m;
    while ((m = re.exec(htmlStr))) {
        const tag = m[1];
        const attrs = m[2] || '';
        const text = m[3] || '';
        const el = new El(tag);
        const idm = /id="([^"]+)"/.exec(attrs);
        if (idm) { el.id = idm[1]; registry.set(idm[1], el); }
        const cm = /class="([^"]+)"/.exec(attrs);
        if (cm) el.className = cm[1];
        const hm = /href="([^"]+)"/.exec(attrs);
        if (hm) el.href = hm[1];
        if (/type="([^"]+)"/.test(attrs)) el.setAttribute('type', /type="([^"]+)"/.exec(attrs)[1]);
        if (text.trim()) el.textContent = text.trim();
        parent.appendChild(el);
    }
}

/* آکاردئون‌های واقعی از externship.html */
function buildAccordions(src) {
    const re = /<div class="accordion-item" id="([^"]+)">([\s\S]*?)<\/div>\s*<\/div>/g;
    let m;
    let n = 0;
    while ((m = re.exec(src))) {
        const id = m[1];
        const item = new El('div');
        item.classList.add('accordion-item');
        item.id = id;
        item._top = 100 + n * 300;
        const header = new El('button');
        header.classList.add('accordion-header');
        header.setAttribute('aria-expanded', 'false');
        header.textContent = 'بخش ' + id;
        item.appendChild(header);
        const content = new El('div');
        content.classList.add('accordion-content');
        item.appendChild(content);
        container.appendChild(item);
        registry.set(id, item);
        n++;
    }
    return n;
}
const accordionCount = buildAccordions(html);

const themeBtn = new El('button'); themeBtn.id = 'themeBtn'; registry.set('themeBtn', themeBtn); body.appendChild(themeBtn);
const searchBtn = new El('button'); searchBtn.id = 'searchBtn'; registry.set('searchBtn', searchBtn); body.appendChild(searchBtn);
const menuBtn = new El('button'); menuBtn.id = 'menuBtn'; registry.set('menuBtn', menuBtn); body.appendChild(menuBtn);
const mainNav = new El('nav'); mainNav.id = 'mainNav'; registry.set('mainNav', mainNav); body.appendChild(mainNav);

const themeMeta = new El('meta');
themeMeta.setAttribute('name', 'theme-color');
themeMeta.setAttribute('content', '#07161B');
head.appendChild(themeMeta);

const store = new Map();
const document = {
    documentElement: docEl,
    head, body,
    readyState: 'complete',
    activeElement: null,
    getElementById: id => registry.get(id) || null,
    createElement: tag => new El(tag),
    querySelector: sel => {
        if (sel.includes('theme-color')) return themeMeta;
        if (sel === 'main') return main;
        if (sel.startsWith('#')) return registry.get(sel.slice(1)) || null;
        return body.querySelector(sel) || main.querySelector(sel);
    },
    querySelectorAll: sel => {
        if (sel === '.accordion-item') return container.querySelectorAll('.accordion-item');
        if (sel === '.accordion-header') return container.querySelectorAll('.accordion-header');
        if (sel === '#mainNav a' || sel === '.reveal') return [];
        return body.querySelectorAll(sel);
    },
    addEventListener: () => {},
    removeEventListener: () => {}
};
docEl.style = {};

/* اسکرول ساختگی */
const winListeners = {};
const window = {
    location: { pathname: '/externship.html', hash: '#cardiology', search: '', href: 'http://x/externship.html#cardiology' },
    matchMedia: () => ({ matches: false, addEventListener: () => {}, addListener: () => {} }),
    addEventListener: (t, fn) => { (winListeners[t] = winListeners[t] || []).push(fn); },
    removeEventListener: () => {},
    scrollTo: () => {},
    requestAnimationFrame: fn => fn(0),
    getComputedStyle: () => ({
        getPropertyValue: p => (p === '--theme-color'
            ? (docEl.getAttribute('data-theme') === 'light' ? '#F1F7F9' : '#07161B')
            : '')
    }),
    history: { replaceState: () => {} },
    fetch: null
};

/* fetch ساختگی برای ایندکس جستجو */
let fetchCalls = 0;
const fakeFetch = (url, opts) => {
    fetchCalls++;
    if (String(url).indexOf('search-index.json') !== -1) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve(searchIndex) });
    }
    return Promise.resolve({ ok: false, json: () => Promise.resolve(null) });
};

const sandbox = {
    window, document, console,
    localStorage: {
        getItem: k => (store.has(k) ? store.get(k) : null),
        setItem: (k, v) => store.set(k, v)
    },
    getComputedStyle: window.getComputedStyle,
    fetch: fakeFetch,
    setTimeout, clearTimeout, Promise, Math, Date, JSON, String, Number, Array, Object, RegExp, Error
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);

const code = fs.readFileSync(ROOT + 'js/main.js', 'utf8');
vm.runInContext(code, sandbox, { filename: 'main.js' });

/* ---------- آزمون‌ها ---------- */
const checks = [];
const check = (name, cond) => checks.push({ name, ok: !!cond });

/* ۱) آکاردئون */
const target = registry.get('cardiology');
check('آکاردئون از هش باز شد', target && target.classList.contains('active'));
check('aria-expanded=true شد', target.querySelector('.accordion-header').getAttribute('aria-expanded') === 'true');
registry.get('urology').querySelector('.accordion-header').dispatch('click');
check('آیتم جدید باز شد', registry.get('urology').classList.contains('active'));
check('آیتم قبلی بسته شد', !target.classList.contains('active'));
check('aria قبلی false شد', target.querySelector('.accordion-header').getAttribute('aria-expanded') === 'false');

/* ۲) تم */
check('رنگ نوار مرورگر در تم تیره', themeMeta.getAttribute('content') === '#07161B');
themeBtn.dispatch('click');
check('تم به روشن تغییر کرد', docEl.getAttribute('data-theme') === 'light');
check('رنگ نوار مرورگر روشن شد', themeMeta.getAttribute('content') === '#F1F7F9');
check('تم در حافظه ذخیره شد', store.get('charcot-theme') === 'light');
themeBtn.dispatch('click');
check('بازگشت به تم تیره', docEl.getAttribute('data-theme') === 'dark' && themeMeta.getAttribute('content') === '#07161B');
check('API توست ساخته شد', typeof sandbox.window.showToast === 'function');

/* ۳) ابزار اسکرول */
const progress = body.querySelectorAll('.scroll-progress')[0];
const topBtn = body.querySelectorAll('.back-to-top')[0];
check('نوار پیشرفت ساخته شد', !!progress);
check('دکمهٔ بازگشت به بالا ساخته شد', !!topBtn);
docEl.scrollHeight = 4000;
docEl.clientHeight = 1000;
docEl.scrollTop = 1500;
(winListeners.scroll || []).forEach(fn => fn());
check('نوار پیشرفت به‌روز شد', progress && progress.style.width === '50%');
check('دکمهٔ بازگشت به بالا نمایش داده شد', topBtn && topBtn.classList.contains('show'));

/* ۴) فهرست چسبان */
const toc = main.querySelector('.toc-nav');
check('فهرست بخش‌ها ساخته شد', !!toc);
const tocLinks = toc ? toc.querySelectorAll('a') : [];
check('فهرست به تعداد آکاردئون‌ها لینک دارد', tocLinks.length === accordionCount);
check('لینک فهرست به لنگر درست اشاره می‌کند',
    tocLinks.length > 0 && tocLinks[0].getAttribute('href') === '#' + registry.get('internal-medicine').id);
check('چیدمان دوستونه فعال شد', main.querySelector('.page-layout.has-toc') !== null);
if (toc) {
    const third = tocLinks[3];
    const thirdId = third.getAttribute('href').slice(1);
    // اطمینان از اینکه رویداد به والد حباب می‌کند (مثل مرورگر واقعی)
    let bubbled = 0;
    toc.addEventListener('click', () => { bubbled++; });
    third.dispatch('click', { target: third });
    check('رویداد کلیک به فهرست حباب کرد', bubbled === 1);
    check('کلیک روی فهرست آکاردئون را باز کرد', registry.get(thirdId).classList.contains('active'));
}

/* ۵) جستجوی متن کامل */
searchBtn.dispatch('click');
const sInput = registry.get('searchInput') || body.querySelector('#searchInput');
const sResults = registry.get('searchResults') || body.querySelector('#searchResults');
check('پنجرهٔ جستجو ساخته شد', !!sInput && !!sResults);

if (sInput && sResults) {
    sInput.value = 'کورس';
    sInput.dispatch('input');
    const firstHtml = sResults.innerHTML;
    check('جستجوی عنوان نتیجه داد', firstHtml.indexOf('search-result') !== -1);

    sInput.value = 'متاستاز';
    sInput.dispatch('input');
    check('درخواست ایندکس متن ارسال شد', fetchCalls > 0);
}

/* نتیجه‌ها */
const failed = checks.filter(c => !c.ok);
checks.forEach(c => console.log((c.ok ? 'PASS  ' : 'FAIL  ') + c.name));
console.log('\nآکاردئون‌های تست‌شده: ' + accordionCount + ' | لینک فهرست: ' + tocLinks.length + ' | fetch: ' + fetchCalls);
console.log(failed.length ? 'FAILED: ' + failed.length : 'ALL RUNTIME CHECKS PASSED ✅');
process.exit(failed.length ? 1 : 0);
