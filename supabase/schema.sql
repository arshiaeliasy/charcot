-- ============================================================
-- شارکوت | Charcot — اسکیمای دیتابیس Supabase
-- اجرا: داشبورد Supabase → SQL Editor → New query → Paste → Run
-- ============================================================

-- ۱) جدول پروفایل کاربران ------------------------------------
--    با جدول auth.users (که خود Supabase می‌سازد) لینک است.
create table if not exists public.users (
    id          uuid primary key references auth.users (id) on delete cascade,
    email       text,
    fullname    text,
    username    text unique not null,          -- نام کاربری یکتا (خطای 23505)
    phone       text unique,                   -- شماره موبایل یکتا
    university  text,
    created_at  timestamptz not null default now(),
    updated_at  timestamptz not null default now()
);

-- ۲) فعال‌سازی Row Level Security -----------------------------
--    بدون RLS، ایمن‌سازی دسترسی‌ها ممکن نیست.
alter table public.users enable row level security;

-- ۳) سیاست‌های دسترسی ----------------------------------------
--    هر کاربر فقط به رکورد خودش دسترسی دارد.
drop policy if exists "users_insert_own" on public.users;
create policy "users_insert_own"
    on public.users for insert
    with check (auth.uid() = id);

drop policy if exists "users_select_own" on public.users;
create policy "users_select_own"
    on public.users for select
    using (auth.uid() = id);

drop policy if exists "users_update_own" on public.users;
create policy "users_update_own"
    on public.users for update
    using (auth.uid() = id)
    with check (auth.uid() = id);

-- ۴) به‌روزرسانی خودکار updated_at ---------------------------
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists users_set_updated_at on public.users;
create trigger users_set_updated_at
    before update on public.users
    for each row
    execute function public.set_updated_at();

-- ۵) بررسی نهایی ---------------------------------------------
--    پس از Run، از منوی Table Editor باید جدول users را ببینی
--    با ستون‌ها: id, email, fullname, username, phone, university,
--               created_at, updated_at
select column_name, data_type, is_nullable
from information_schema.columns
where table_schema = 'public' and table_name = 'users'
order by ordinal_position;
