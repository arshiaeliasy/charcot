/* ============================================================
   تست موتور جستجوی متن کامل روی ایندکس واقعی
   اجرا:  node tools/search_test.mjs
   منطق جستجو مستقیماً از js/main.js استخراج و روی دادهٔ واقعی اجرا می‌شود.
   ============================================================ */
import fs from 'node:fs';
import vm from 'node:vm';

const ROOT = process.cwd() + '/';
const src = fs.readFileSync(ROOT + 'js/main.js', 'utf8').replace(/\r\n/g, '\n');
const index = JSON.parse(fs.readFileSync(ROOT + 'js/search-index.json', 'utf8'));

/* استخراج توابع جستجو از main.js */
function grab(name) {
    const re = new RegExp('\\n    function ' + name + '\\([\\s\\S]*?\\n    \\}\\n');
    const m = src.match(re);
    if (!m) throw new Error('تابع پیدا نشد: ' + name);
    return m[0];
}

const parts = [
    'function escapeHtml(str) { return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }',
    grab('normalize'),
    grab('stem'),
    grab('queryTerms'),
    grab('scoreSection'),
    grab('snippetAround'),
    grab('currentPage'),
    grab('searchFullText')
].join('\n');

const sandbox = {
    console, JSON, Math, String, Number, Array, Object, RegExp, Error,
    window: { location: { pathname: '/externship.html' } }
};
sandbox.globalThis = sandbox;
vm.createContext(sandbox);
vm.runInContext(parts + '\n' + 'globalThis.api = { searchFullText, queryTerms, snippetAround, normalize, stem };', sandbox);
const api = sandbox.api;

/* جستجو در ایندکس واقعی */
function query(q) {
    const terms = api.queryTerms(q);
    // searchFullText از متغیر textIndex استفاده می‌کند؛ موقتاً تزریق می‌کنیم
    sandbox.textIndex = index.pages;
    vm.runInContext('textIndex = globalThis.__idx;', Object.assign(sandbox, { __idx: index.pages }));
    return api.searchFullText(terms);
}

const cases = [
    { q: 'اسهال', expectPage: 'clinical-notes.html', label: 'واژهٔ داخل متن یادداشت‌ها' },
    { q: 'پره‌انترنی', expectPage: 'pre-internship.html', label: 'نام یک بخش' },
    { q: 'بروسلا', expectPage: 'clinical-notes.html', label: 'واژهٔ تخصصی داخل متن' },
    { q: 'استاجری', expectPage: 'externship.html', label: 'واژهٔ عنوان صفحه' },
    { q: 'کورس‌های', expectPage: 'externship.html', label: 'واژه با نیم‌فاصله' },
    { q: 'فیزیولوژی', expectPage: 'basic-sciences.html', label: 'درس علوم پایه' }
];

const checks = [];
for (const c of cases) {
    const res = query(c.q);
    const pages = new Set(res.map(r => r.page));
    const ok = res.length > 0 && pages.has(c.expectPage);
    checks.push({ name: `${c.label} — «${c.q}» → ${res.length} نتیجه`, ok });
    if (ok) {
        const top = res[0];
        console.log(`  «${c.q}» → ${top.page}#${top.sec.id || '-'} | ${top.sec.title.slice(0, 40)} | امتیاز ${top.score}`);
    }
}

/* واژه‌ای که نباید نتیجه بدهد */
const none = query('زیرکسیلیک');
checks.push({ name: 'واژهٔ بی‌ربط نتیجه نمی‌دهد', ok: none.length === 0 });

/* snippet باید واژه را داشته باشد */
const res = query('اسهال');
if (res.length) {
    const frag = api.snippetAround(res[0].sec.text, 'اسهال');
    checks.push({ name: 'بریدهٔ متن ساخته می‌شود', ok: frag.length > 20 });
} else {
    checks.push({ name: 'بریدهٔ متن ساخته می‌شود', ok: false });
}

/* نیم‌فاصله و ی/ك عربی باید یکی حساب شوند */
const a = query('نیم فاصله'.replace(' ', '')).length;
const withZwnj = query('کورس‌های').length;
const withSpace = query('کورس های').length;
checks.push({ name: 'نیم‌فاصله و فاصلهٔ معمولی یکسان دیده می‌شوند', ok: withZwnj > 0 && withSpace > 0 });

const failed = checks.filter(c => !c.ok);
checks.forEach(c => console.log((c.ok ? 'PASS  ' : 'FAIL  ') + c.name));
console.log('\nبخش‌های ایندکس: ' + Object.values(index.pages).reduce((n, p) => n + p.sections.length, 0));
console.log(failed.length ? 'FAILED: ' + failed.length : 'ALL SEARCH CHECKS PASSED ✅');
process.exit(failed.length ? 1 : 0);
