"""ابزارهای عمومی: CSRF، فیلترهای قالب، CSV، لاگین اجباری"""
import csv
import io
import secrets
from datetime import date, datetime
from functools import wraps

from flask import (
    Response,
    abort,
    current_app,
    flash,
    redirect,
    request,
    session,
    url_for,
)

from .jalali import gregorian_to_jalali, jalali_str

FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

STATUS_LABELS = {
    "active": "فعال",
    "graduated": "فارغ‌التحصیل",
    "dismissed": "منقطع",
}


def fa_number(value):
    """تبدیل ارقام لاتین به فارسی برای نمایش"""
    if value is None or value == "":
        return "—"
    text = str(value).translate(FA_DIGITS)
    return text.replace(".", "٫")


def status_fa(status: str) -> str:
    return STATUS_LABELS.get(status, status)


def grade_letter(score) -> str:
    """مقدار توصیفی نمره"""
    if score is None:
        return "—"
    if score >= 17:
        return "عالی"
    if score >= 14:
        return "خوب"
    if score >= 12:
        return "قابل قبول"
    if score >= 10:
        return "قبول"
    return "مردود"


def today_jalali() -> str:
    jy, jm, jd = gregorian_to_jalali(date.today().year, date.today().month, date.today().day)
    return fa_number(jalali_str(jy, jm, jd))


def jalali_date(dt):
    if not dt:
        return "—"
    jy, jm, jd = gregorian_to_jalali(dt.year, dt.month, dt.day)
    return fa_number(jalali_str(jy, jm, jd))


# ---------------------------------------------------------------- CSRF

def generate_csrf_token() -> str:
    """تولید/بازیابی توکن CSRF مبتنی بر نشست"""
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_hex(32)
    return session["_csrf_token"]


def csrf_protect():
    """بررسی توکن CSRF برای همه درخواست‌های POST"""
    if not current_app.config.get("ENABLE_CSRF", True):
        return None
    if request.method == "POST":
        sent = request.form.get("csrf_token", "")
        expected = session.get("_csrf_token", "")
        if not expected or not sent or sent != expected:
            abort(400, description="توکن CSRF نامعتبر یا منقضی شده است. صفحه را دوباره بارگذاری کنید.")


# ---------------------------------------------------------------- Auth

def login_required(view):
    """دکوراتور اجباری کردن ورود مدیر"""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_id"):
            flash("برای دسترسی به این صفحه ابتدا وارد شوید.", "warning")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------- CSV

def csv_response(rows, headers: list, filename: str = "export.csv") -> Response:
    """ساخت پاسخ CSV سازگار با اکسل فارسی (UTF-8 با BOM)"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    body = "\ufeff" + output.getvalue()
    return Response(
        body,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ---------------------------------------------------------------- Template

def register_template_extensions(app) -> None:
    app.jinja_env.filters["fa"] = fa_number
    app.jinja_env.filters["status_fa"] = status_fa
    app.jinja_env.filters["jalali"] = jalali_date
    app.jinja_env.filters["grade_letter"] = grade_letter
    app.jinja_env.globals["grade_letter"] = grade_letter
    app.jinja_env.globals["csrf_token"] = generate_csrf_token
    app.jinja_env.globals["today_jalali"] = today_jalali
    app.jinja_env.globals["status_labels"] = STATUS_LABELS
    app.jinja_env.globals["now_year"] = datetime.now().year
