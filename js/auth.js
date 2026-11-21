/* ============================================================
   شارکوت | Charcot — احراز هویت (Supabase)
   ------------------------------------------------------------
   این فایل جای اسکریپت درون‌خطی صفحهٔ اصلی را گرفته است و
   این کارها را انجام می‌دهد:
     ۱) بارگذاری کتابخانهٔ supabase-js با چند مسیر جایگزین
        (اول نسخهٔ خودمیزبان، بعد CDN ها) و پیام خطای روشن
        در صورت شکست — قبلاً اگر CDN لود نمی‌شد، کل فرم‌ها
        بی‌صدا از کار می‌افتادند.
     ۲) ورود، ثبت‌نام، فراموشی رمز و «تعیین رمز عبور جدید»
        (جریان بازیابی قبلاً نیمه‌کاره بود: لینک ایمیل می‌آمد
        ولی هیچ فرمی برای گذاشتن رمز تازه وجود نداشت).
     ۳) ساخت/بازیابی رکورد پروفایل در جدول public.users؛
        اگر «تأیید ایمیل» روشن باشد و هنگام ثبت‌نام هنوز
        نشستی وجود نداشته باشد، سیاست RLS اجازهٔ درج نمی‌دهد؛
        در آن حالت درج به اولین ورود موفق موکول می‌شود.
     ۴) همگام‌سازی رابط کاربری با onAuthStateChange (ورود/خروج
        در تب دیگر هم بلافاصله دیده می‌شود).
   ============================================================ */
(function () {
    'use strict';

    /* ---------- پیکربندی ---------- */
    // کلید anon عمداً عمومی است؛ محافظت واقعی با RLS در supabase/schema.sql انجام می‌شود.
    var SUPABASE_URL = 'https://jpodptieqiqlcohauyjs.supabase.co';
    var SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impwb2RwdGllcWlxbGNvaGF1eWpzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTAzMzExMDQsImV4cCI6MjEwNTkwNzEwNH0.9sfzf1OIYiBQGd5NDjVVIGZ3tSGG4dwc5IqQpRfoBo0';

    // ۱) js/vendor/supabase.js (اگر خودت فایل را آنجا گذاشته باشی)
    // ۲) jsdelivr  ۳) unpkg  ۴) مسیر پیش‌فرض jsdelivr
    var LIB_SOURCES = [
        'js/vendor/supabase.js',
        'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.js',
        'https://unpkg.com/@supabase/supabase-js@2/dist/umd/supabase.js',
        'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2'
    ];

    var client = null;
    var profileChecked = false;
    var recoveryMode = looksLikeRecovery();

    var PANELS = {
        login: 'loginForm',
        register: 'registerForm',
        forgot: 'forgotPasswordForm',
        reset: 'resetPasswordForm',
        profile: 'userProfile'
    };

    /* ---------- ابزارها ---------- */
    function $(id) { return document.getElementById(id); }

    function val(id) {
        var el = $(id);
        return el ? el.value.trim() : '';
    }

    function toast(message, type) {
        if (typeof window.showToast === 'function') window.showToast(message, type || 'info');
    }

    function setText(id, text) {
        var el = $(id);
        if (el) el.textContent = text;
    }

    function setBusy(btn, busy, label) {
        if (!btn) return;
        if (busy) {
            if (!btn.dataset.label) btn.dataset.label = btn.textContent;
            btn.textContent = label || 'لطفاً صبر کنید...';
            btn.disabled = true;
            btn.setAttribute('aria-busy', 'true');
        } else {
            btn.textContent = btn.dataset.label || btn.textContent;
            btn.disabled = false;
            btn.removeAttribute('aria-busy');
        }
    }

    function showNotice(message, kind) {
        var box = $('authNotice');
        if (!box) {
            toast(message, kind === 'error' ? 'error' : 'info');
            return;
        }
        box.textContent = message;
        box.className = 'auth-notice ' + (kind || 'info');
        box.setAttribute('role', kind === 'error' ? 'alert' : 'status');
    }

    /* ---------- نمایش پنل‌ها ---------- */
    function showPanel(name) {
        Object.keys(PANELS).forEach(function (key) {
            var el = $(PANELS[key]);
            if (el) el.classList.toggle('hidden', key !== name);
        });

        var tabs = $('authTabs');
        var showTabs = name === 'login' || name === 'register';
        if (tabs) tabs.classList.toggle('hidden', !showTabs);

        var tabLogin = $('tabLogin');
        var tabRegister = $('tabRegister');
        if (tabLogin && tabRegister) {
            tabLogin.classList.toggle('active', name === 'login');
            tabRegister.classList.toggle('active', name === 'register');
            tabLogin.setAttribute('aria-selected', String(name === 'login'));
            tabRegister.setAttribute('aria-selected', String(name === 'register'));
        }
    }

    function switchTab(type) {
        showPanel(type === 'register' ? 'register' : 'login');
    }

    /* ---------- بارگذاری کتابخانه ---------- */
    function loadScript(src) {
        return new Promise(function (resolve, reject) {
            var s = document.createElement('script');
            s.src = src;
            s.async = false;
            s.onload = function () { resolve(src); };
            s.onerror = function () { s.remove(); reject(new Error('failed: ' + src)); };
            document.head.appendChild(s);
        });
    }

    async function loadLibrary() {
        if (window.supabase && window.supabase.createClient) return;
        for (var i = 0; i < LIB_SOURCES.length; i++) {
            try {
                await loadScript(LIB_SOURCES[i]);
            } catch (e) {
                continue; // مسیر بعدی
            }
            if (window.supabase && window.supabase.createClient) return;
        }
        throw new Error('supabase-js از هیچ مسیری بارگذاری نشد');
    }

    /* ---------- تشخیص لینک بازیابی رمز ---------- */
    function looksLikeRecovery() {
        var s = window.location.hash + window.location.search;
        return /(^|[#&?])type=recovery/.test(s) || /[#&?]code=/.test(s);
    }

    function clearRecoveryHash() {
        if (window.history && window.history.replaceState) {
            window.history.replaceState(null, '', window.location.pathname + window.location.search);
        }
        recoveryMode = false;
    }

    /* ---------- پروفایل کاربر ---------- */
    // اگر رکورد پروفایل ساخته نشده باشد (مثلاً چون هنگام ثبت‌نام «تأیید ایمیل»
    // روشن بوده و نشستی وجود نداشته)، اینجا در اولین ورود ساخته می‌شود.
    async function ensureProfile(user) {
        if (!client || !user) return false;
        var meta = user.user_metadata || {};
        try {
            var found = await client.from('users').select('id').eq('id', user.id).maybeSingle();
            if (found.error) throw found.error;
            if (found.data) return true;

            var inserted = await client.from('users').insert([{
                id: user.id,
                email: user.email,
                fullname: meta.fullname || null,
                username: meta.username || null,
                phone: meta.phone || null,
                university: meta.university || null
            }]);

            if (inserted.error) {
                if (inserted.error.code === '23505') {
                    toast('نام کاربری یا شمارهٔ تلفن وارد‌شده قبلاً ثبت شده است.', 'error');
                } else {
                    console.error('[charcot] خطا در ذخیرهٔ پروفایل:', inserted.error);
                    toast('ذخیرهٔ پروفایل کامل نشد؛ از پشتیبانی پیگیری کن.', 'error');
                }
                return false;
            }
            return true;
        } catch (err) {
            console.error('[charcot] خطا در بررسی پروفایل:', err);
            return false;
        }
    }

    /* ---------- نشست و رابط کاربری ---------- */
    async function checkSession() {
        if (!client) return;
        var res = await client.auth.getSession();
        var session = res && res.data ? res.data.session : null;

        if (session && session.user) {
            var user = session.user;
            var meta = user.user_metadata || {};
            setText('welcomeName', meta.fullname || user.email || 'کاربر گرامی');

            var details = 'ایمیل: ' + (user.email || '—');
            if (meta.username) details += ' • نام کاربری: ' + meta.username;
            if (meta.university) details += ' • دانشگاه: ' + meta.university;
            setText('welcomeDetails', details);

            showPanel('profile');

            if (!profileChecked && !recoveryMode) {
                profileChecked = true;
                ensureProfile(user);
            }
        } else {
            showPanel(recoveryMode ? 'reset' : 'login');
        }
    }

    /* ---------- اعتبارسنجی ---------- */
    var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    var USERNAME_RE = /^[A-Za-z0-9._-]{3,30}$/;
    var PHONE_RE = /^09\d{9}$/;

    function validateEmail(email) {
        if (!email) { toast('لطفاً ایمیل را وارد کنید.', 'error'); return false; }
        if (!EMAIL_RE.test(email)) { toast('فرمت ایمیل معتبر نیست.', 'error'); return false; }
        return true;
    }

    /* ---------- خطاهای Supabase ---------- */
    function reportAuthError(error, fallback) {
        var msg = (error && error.message) ? error.message : '';
        var low = msg.toLowerCase();

        if (low.indexOf('already registered') !== -1 || low.indexOf('already been registered') !== -1) {
            toast('قبلاً با این ایمیل ثبت‌نام کرده‌ای! از فرم ورود استفاده کن.', 'error');
            showPanel('login');
        } else if (error && error.status === 429) {
            toast('تلاش‌های زیادی انجام شده؛ چند دقیقه بعد دوباره امتحان کن.', 'error');
        } else if (low.indexOf('password') !== -1) {
            toast('رمز عبور پذیرفته نشد: ' + msg, 'error');
        } else if (low.indexOf('email') !== -1 || low.indexOf('invalid') !== -1) {
            toast('ایمیل معتبر نیست: ' + msg, 'error');
        } else {
            toast((fallback || 'خطایی رخ داد') + (msg ? ': ' + msg : ''), 'error');
        }
    }

    /* ---------- فرم‌ها ---------- */
    async function onRegister(e) {
        e.preventDefault();
        if (!client) return;

        var btn = $('regBtn');
        var form = e.currentTarget;
        var fullname = val('fullname');
        var username = val('username');
        var email = val('regEmail');
        var phone = val('phone');
        var university = val('university');
        var password = $('regPassword') ? $('regPassword').value : '';
        var confirm = $('regConfirmPassword') ? $('regConfirmPassword').value : '';

        if (!fullname) { toast('نام و نام خانوادگی را وارد کن.', 'error'); return; }
        if (!USERNAME_RE.test(username)) {
            toast('نام کاربری باید ۳ تا ۳۰ کاراکتر و فقط شامل حروف لاتین، رقم، نقطه، خط تیره یا زیرخط باشد.', 'error');
            return;
        }
        if (!validateEmail(email)) return;
        if (!PHONE_RE.test(phone)) {
            toast('شمارهٔ موبایل باید ۱۱ رقم و با 09 شروع شود (مثال: 09123456789).', 'error');
            return;
        }
        if (password.length < 6) { toast('رمز عبور باید حداقل ۶ کاراکتر باشد.', 'error'); return; }
        if (password !== confirm) { toast('رمز عبور و تکرار آن یکسان نیستند.', 'error'); return; }

        setBusy(btn, true, 'در حال ثبت‌نام...');
        try {
            var res = await client.auth.signUp({
                email: email,
                password: password,
                options: {
                    data: {
                        fullname: fullname,
                        username: username,
                        phone: phone,
                        university: university
                    }
                }
            });

            if (res.error) { reportAuthError(res.error, 'خطا در ثبت‌نام'); return; }

            var user = res.data ? res.data.user : null;
            // Supabase برای ایمیل تکراری کاربر جعلی با identities خالی برمی‌گرداند
            if (user && user.identities && user.identities.length === 0) {
                toast('قبلاً با این ایمیل ثبت‌نام کرده‌ای! وارد حساب خود شو.', 'error');
                showPanel('login');
                return;
            }

            if (res.data && res.data.session) {
                // «تأیید ایمیل» خاموش است: همین حالا نشست داریم و می‌توانیم پروفایل را بسازیم.
                var ok = await ensureProfile(user);
                if (ok) {
                    toast('ثبت‌نام شما با موفقیت انجام شد!', 'success');
                    if (form && form.reset) form.reset();
                    await checkSession();
                }
            } else {
                // «تأیید ایمیل» روشن است: درج پروفایل الان با RLS رد می‌شود؛
                // به اولین ورود موفق موکول می‌شود (ensureProfile در checkSession).
                toast('ثبت‌نام انجام شد. برای فعال‌سازی، لینک تأییدی که به ایمیلت فرستادیم را باز کن.', 'success');
                if (form && form.reset) form.reset();
                showPanel('login');
            }
        } catch (err) {
            console.error('[charcot] خطای ثبت‌نام:', err);
            toast('خطایی رخ داد، لطفاً دوباره تلاش کن.', 'error');
        } finally {
            setBusy(btn, false);
        }
    }

    async function onLogin(e) {
        e.preventDefault();
        if (!client) return;

        var btn = $('loginBtn');
        var email = val('loginEmail');
        var password = $('loginPassword') ? $('loginPassword').value : '';
        if (!validateEmail(email)) return;
        if (!password) { toast('رمز عبور را وارد کن.', 'error'); return; }

        setBusy(btn, true, 'در حال ورود...');
        try {
            var res = await client.auth.signInWithPassword({ email: email, password: password });
            if (res.error) {
                var low = (res.error.message || '').toLowerCase();
                if (low.indexOf('email not confirmed') !== -1) {
                    toast('ایمیلت هنوز تأیید نشده است؛ لینک تأیید را از ایمیلت باز کن.', 'error');
                } else {
                    toast('ایمیل یا رمز عبور نادرست است.', 'error');
                }
                return;
            }
            toast('ورود با موفقیت انجام شد!', 'success');
            profileChecked = false;
            await checkSession();
        } catch (err) {
            console.error('[charcot] خطای ورود:', err);
            toast('خطایی رخ داد، لطفاً دوباره تلاش کن.', 'error');
        } finally {
            setBusy(btn, false);
        }
    }

    async function onForgot(e) {
        e.preventDefault();
        if (!client) return;

        var btn = $('forgotBtn');
        var form = e.currentTarget;
        var email = val('forgotEmail');
        if (!validateEmail(email)) return;

        setBusy(btn, true, 'در حال ارسال...');
        try {
            var res = await client.auth.resetPasswordForEmail(email, {
                redirectTo: window.location.origin + window.location.pathname
            });
            if (res.error) { toast('خطا در ارسال ایمیل بازیابی: ' + res.error.message, 'error'); return; }
            toast('لینک بازیابی رمز عبور به ایمیل شما ارسال شد.', 'success');
            if (form && form.reset) form.reset();
            showPanel('login');
        } catch (err) {
            console.error('[charcot] خطای بازیابی رمز:', err);
            toast('خطایی رخ داد، لطفاً دوباره تلاش کن.', 'error');
        } finally {
            setBusy(btn, false);
        }
    }

    async function onResetPassword(e) {
        e.preventDefault();
        if (!client) return;

        var btn = $('resetBtn');
        var p1 = $('newPassword') ? $('newPassword').value : '';
        var p2 = $('newPassword2') ? $('newPassword2').value : '';

        if (p1.length < 6) { toast('رمز عبور جدید باید حداقل ۶ کاراکتر باشد.', 'error'); return; }
        if (p1 !== p2) { toast('رمز عبور و تکرار آن یکسان نیستند.', 'error'); return; }

        setBusy(btn, true, 'در حال ذخیره...');
        try {
            var res = await client.auth.updateUser({ password: p1 });
            if (res.error) {
                var low = (res.error.message || '').toLowerCase();
                if (low.indexOf('session') !== -1 || low.indexOf('jwt') !== -1) {
                    toast('لینک بازیابی منقضی شده است؛ دوباره درخواست بده.', 'error');
                    clearRecoveryHash();
                    showPanel('forgot');
                } else {
                    toast('خطا در تغییر رمز عبور: ' + res.error.message, 'error');
                }
                return;
            }
            toast('رمز عبور جدید ذخیره شد.', 'success');
            clearRecoveryHash();
            profileChecked = false;
            await checkSession();
        } catch (err) {
            console.error('[charcot] خطای تعیین رمز جدید:', err);
            toast('خطایی رخ داد، لطفاً دوباره تلاش کن.', 'error');
        } finally {
            setBusy(btn, false);
        }
    }

    async function onLogout() {
        if (!client) return;
        await client.auth.signOut();
        toast('شما از حساب کاربری خارج شدید.', 'info');
        profileChecked = false;
        await checkSession();
    }

    /* ---------- اتصال رویدادها ---------- */
    function bindUI() {
        var on = function (id, event, handler) {
            var el = $(id);
            if (el) el.addEventListener(event, handler);
        };

        on('tabLogin', 'click', function () { switchTab('login'); });
        on('tabRegister', 'click', function () { switchTab('register'); });
        on('forgotLink', 'click', function (e) { e.preventDefault(); showPanel('forgot'); });
        on('backToLoginLink', 'click', function (e) { e.preventDefault(); showPanel('login'); });
        on('backToLoginLink2', 'click', function (e) { e.preventDefault(); clearRecoveryHash(); showPanel('login'); });
        on('logoutBtn', 'click', onLogout);

        on('loginForm', 'submit', onLogin);
        on('registerForm', 'submit', onRegister);
        on('forgotPasswordForm', 'submit', onForgot);
        on('resetPasswordForm', 'submit', onResetPassword);
    }

    function disableForms(reason) {
        ['loginForm', 'registerForm', 'forgotPasswordForm', 'resetPasswordForm'].forEach(function (id) {
            var form = $(id);
            if (!form) return;
            form.querySelectorAll('input, button').forEach(function (el) { el.disabled = true; });
        });
        showNotice(reason, 'error');
    }

    /* ---------- راه‌اندازی ---------- */
    async function init() {
        bindUI();

        try {
            await loadLibrary();
        } catch (err) {
            console.error('[charcot]', err);
            disableForms('ارتباط با سرویس ورود برقرار نشد. اتصال اینترنت یا فیلترشکن را بررسی کن و صفحه را دوباره باز کن. بقیهٔ سایت بدون مشکل کار می‌کند.');
            return;
        }

        try {
            client = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
        } catch (err) {
            console.error('[charcot] خطا در ساخت کلاینت:', err);
            disableForms('راه‌اندازی سرویس ورود با خطا مواجه شد؛ لطفاً بعداً تلاش کن.');
            return;
        }

        // در دسترس بودن کلاینت برای اسکریپت‌های دیگر (مثلاً پنل مدیریت آینده)
        window.charcotAuth = { client: client };

        client.auth.onAuthStateChange(function (event, session) {
            if (event === 'PASSWORD_RECOVERY') {
                recoveryMode = true;
                showPanel('reset');
                return;
            }
            // طبق هشدار Supabase، داخل این callback نباید مستقیم await کرد.
            setTimeout(function () {
                if (event === 'SIGNED_IN') profileChecked = false;
                if (event === 'SIGNED_OUT') profileChecked = false;
                checkSession();
            }, 0);
        });

        if (recoveryMode) showPanel('reset');
        await checkSession();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
