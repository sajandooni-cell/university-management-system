# راهنمای استقرار روی GitHub

این راهنما توضیح می‌دهد چطور این پروژه را روی GitHub منتشر و به‌روزرسانی کنید.

> ⚠️ **مهم:** هرگز توکن (Token) خود را داخل کد، فایل یا Commit قرار ندهید. توکن فقط در دستورهای موقت استفاده می‌شود.

---

## ۱) ساخت مخزن (Repository)

از رابط وب GitHub استفاده کنید:

1. وارد [github.com](https://github.com) شوید و روی **New repository** کلیک کنید.
2. نام مخزن: `university-management-system`
3. سطح دسترسی را انتخاب کنید (Public یا Private).
4. گزینه‌های «Add a README» و «.gitignore» را **خالی بگذارید** (فایل‌ها از قبل موجودند).
5. روی **Create repository** کلیک کنید.

یا با GitHub API:

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/user/repos \
  -d '{"name":"university-management-system","description":"University Management System with Flask (Persian RTL UI)","private":false}'
```

---

## ۲) انتشار اولیه کد

در ریشه پروژه (`university-management-system/`):

```bash
git init
git add .
git commit -m "Initial release: University Management System (Flask, Persian RTL)"
git branch -M main

# اتصال به مخزن — نام کاربری خودتان را جایگزین کنید
git remote add origin https://github.com/YOUR_USERNAME/university-management-system.git

# انتشار (رمز عبور/توکن را در پاسخ به سوال Git وارد کنید)
git push -u origin main
```

### انتشار با توکن Personal Access Token

اگر می‌خواهید با توکن push کنید، توکن را موقتاً در دستور push قرار دهید (این روش توکن را در تاریخچه `bash` باقی می‌گذارد، پس پس از کار، توکن را از GitHub باطل/Revoke کنید):

```bash
git push https://x-access-token:YOUR_GITHUB_TOKEN@github.com/YOUR_USERNAME/university-management-system.git main
```

روش امن‌تر — استفاده از Git Credential Manager که رمز را در حافظه امن نگه می‌دارد:

```bash
git config credential.helper manager     # ویندوز (از پیش نصب است)
git push -u origin main                  # یک بار توکن را در پنجره ورود GitHub وارد کنید
```

---

## ۳) به‌روزرسانی کد در آینده

بعد از هر تغییر:

```bash
git add .
git commit -m "توضیح کوتاه تغییرات"
git push origin main
```

---

## ۴) دریافت نسخه روی سیستم دیگر (Clone)

```bash
git clone https://github.com/YOUR_USERNAME/university-management-system.git
cd university-management-system

# ویندوز: روی run.bat دابل‌کلیک کنید
# لینوکس/مک:
pip install -r requirements.txt
python app.py
```

سپس مرورگر: `http://127.0.0.1:5000` — کاربر: `admin` / رمز: `admin123`

---

## ۵) اجرای خودکار تست‌ها با GitHub Actions

این پروژه شامل `.github/workflows/tests.yml` است؛ با هر push، تمام ۴۶ تست به‌صورت خودکار روی GitHub اجرا می‌شوند. نتیجه را در تب **Actions** مخزن ببینید.

---

## ۶) ساخت نسخه ZIP آماده انتشار

```bash
# بدون فایل‌های موقت و پایگاه داده (طبق .gitignore)
git archive --format=zip -o university-management-system.zip main
```

---

## ۷) نکات امنیتی مهم

| نکته | توضیح |
|------|-------|
| توکن را Commit نکنید | توکن فقط در دستورهای موقت استفاده شود |
| `.gitignore` را حذف نکنید | فایل‌های `*.db`، `.venv` و `__pycache__` نباید وارد مخزن شوند |
| رمز پیش‌فرض را عوض کنید | `admin123` فقط برای دموی اولیه است |
| SECRET_KEY | در استقرار واقعی از متغیر محیطی تنظیم کنید |
| توکن لو رفته | اگر توکنی عمومی شد، فوراً در GitHub → Settings → Developer settings آن را Revoke کنید |
