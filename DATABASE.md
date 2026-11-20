# 🗄️ راهنمای دیتابیس (Supabase)

سایت شارکوت از **Supabase** برای ورود/ثبت‌نام و ذخیره پروفایل کاربران استفاده می‌کند.
این فایل مرحله‌به‌مرحله توضیح می‌دهد چطور دیتابیس را درست راه‌اندازی کنی.

> فایل SQL آماده: [`supabase/schema.sql`](supabase/schema.sql)

---

## قدم ۱ — ورود به داشبورد

1. به <https://supabase.com> برو و وارد حساب شو.
2. پروژهٔ `jpodptieqiqlcohauyjs` را باز کن (همان پروژه‌ای که در سایت تنظیم شده).

## قدم ۲ — ساخت جدول `users`

1. از منوی سمت راست روی **SQL Editor** بزن.
2. روی **New query** کلیک کن.
3. کل محتوای فایل `supabase/schema.sql` را کپی-پیست کن.
4. روی **Run** بزن (پایین-سمت راست) و پیام موفقیت را ببین.

اگر پیام `relation "public.users" already exists` دادی، یعنی جدول از قبل هست؛
فقط مطمئن شو ستون‌های `username` و `phone` یکتا (unique) هستند و RLS فعال است.

## قدم ۳ — بررسی RLS

1. از منوی **Authentication → Policies** (یا Table Editor → users → Policies) باید ۳ سیاست ببینی:
   - `users_insert_own` — کاربر فقط خودش را ثبت کند
   - `users_select_own` — کاربر فقط خودش را بخواند
   - `users_update_own` — کاربر فقط خودش را ویرایش کند
2. اگر نبود، دوباره `schema.sql` را Run کن.

## قدم ۴ — تنظیم ایمیل (اختیاری اما پیشنهادی)

1. **Authentication → Sign In / Providers → Email**
2. برای شروع کار، **Confirm email** را خاموش کن تا ثبت‌نام سریع‌تر تست شود.
   (بعداً هر وقت خواستی می‌توانی دوباره روشن کنی.)
3. **Authentication → URL Configuration**:
   - Site URL: آدرس اصلی سایت‌ات (مثلاً `https://arshiaeliasy.github.io/charcot/`)
   - Redirect URLs: همان آدرس را اضافه کن تا لینک بازیابی رمز عبور کار کند.

## قدم ۵ — تست ثبت‌نام

1. سایت را باز کن (`index.html`).
2. تب **ثبت‌نام جدید** را بزن و فرم را با ایمیل و رمز معتبر پر کن.
3. پیام «ثبت‌نام شما با موفقیت انجام شد!» باید بیاید.
4. به داشبورد برو: **Authentication → Users** → کاربر جدید را ببین.
   **Table Editor → users** → رکورد پروفایل (نام، ایمیل، موبایل، دانشگاه) را ببین.

## خطاهای رایج

| پیام خطا | علت | راه‌حل |
|---|---|---|
| `relation "public.users" does not exist` | جدول ساخته نشده | قدم ۲ را انجام بده |
| `new row violates row-level security` | RLS یا سیاست ناقص است | قدم ۳ — دوباره `schema.sql` را Run کن |
| `duplicate key value violates unique constraint` (23505) | نام کاربری یا موبایل تکراری | پیام داخل سایت همین را نشان می‌دهد؛ رفعش کن |
| ایمیل بازیابی نمی‌آید | Redirect URL تنظیم نشده | قدم ۴ — URL Configuration |

## نکته امنیتی

کلید `anon` که در `index.html` است عمومی است و اشتباه نیست؛
محافظت واقعی از طریق **RLS** انجام می‌شود (همان ۳ سیاست بالا).
هرگز کلید `service_role` را داخل کد سایت قرار نده.
