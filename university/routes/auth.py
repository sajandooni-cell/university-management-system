"""ورود، خروج، محافظت brute-force و تغییر رمز عبور مدیر"""
import time

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from ..models import Admin, db
from ..utils import login_required

bp = Blueprint("auth", __name__)

# شمارش تلاش‌های ناموفق ورود برای هر IP (محافظت در برابر حمله brute-force)
# ساختار: {ip: (تعداد تلاش, زمان اولین تلاش)}
_FAILED_LOGINS: dict = {}
# ساختار: {ip: زمان پایان قفل}
_LOCKED_UNTIL: dict = {}


def _client_ip() -> str:
    """استخراج IP واقعی کاربر (با پشتیبانی از پروکسی معکوس)"""
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _seconds_locked(ip: str) -> int:
    """تعداد ثانیه باقی‌مانده قفل ورود؛ در صورت اتمام قفل، شمارنده‌ها پاک می‌شوند."""
    until = _LOCKED_UNTIL.get(ip)
    if until is None:
        return 0
    remaining = int(until - time.time())
    if remaining <= 0:
        _LOCKED_UNTIL.pop(ip, None)
        _FAILED_LOGINS.pop(ip, None)
        return 0
    return remaining


def _record_failed_login(ip: str) -> int:
    """ثبت تلاش ناموفق؛ خروجی: تعداد تلاش‌های ناموفق در پنجره زمانی فعلی"""
    now = time.time()
    window = current_app.config["LOGIN_LOCKOUT_SECONDS"]
    count, first_ts = _FAILED_LOGINS.get(ip, (0, now))
    if now - first_ts > window:
        count, first_ts = 0, now
    count += 1
    _FAILED_LOGINS[ip] = (count, first_ts)
    if count >= current_app.config["LOGIN_MAX_ATTEMPTS"]:
        _LOCKED_UNTIL[ip] = now + window
        current_app.logger.warning(
            "IP %s locked for %s seconds after %d failed login attempts",
            ip,
            window,
            count,
        )
    return count


def _clear_failed_logins(ip: str) -> None:
    """پاک‌سازی شمارنده‌ها پس از ورود موفق"""
    _FAILED_LOGINS.pop(ip, None)
    _LOCKED_UNTIL.pop(ip, None)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_id"):
        return redirect(url_for("dashboard.index"))

    ip = _client_ip()

    if request.method == "POST":
        locked_for = _seconds_locked(ip)
        if locked_for:
            flash(
                f"به دلیل تلاش‌های ناموفق مکرر، ورود برای {locked_for} ثانیه غیرفعال است. "
                "لطفاً کمی بعد دوباره تلاش کنید.",
                "danger",
            )
            return render_template("login.html"), 429

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            _clear_failed_logins(ip)
            session.clear()
            session["admin_id"] = admin.id
            session["admin_username"] = admin.username
            session.permanent = True
            flash(f"خوش آمدید، {admin.username} عزیز! ورود با موفقیت انجام شد.", "success")
            return redirect(url_for("dashboard.index"))

        current_app.logger.warning(
            "Failed login attempt for username=%r from IP %s", username, ip
        )
        attempts = _record_failed_login(ip)
        max_attempts = current_app.config["LOGIN_MAX_ATTEMPTS"]
        remaining = max_attempts - attempts
        if remaining > 0:
            flash(
                f"نام کاربری یا رمز عبور اشتباه است. ({attempts} تلاش ناموفق — "
                f"پس از {max_attempts} تلاش، ورود موقتاً غیرفعال می‌شود.)",
                "danger",
            )
        else:
            flash(
                f"به دلیل {max_attempts} تلاش ناموفق، ورود برای "
                f"{current_app.config['LOGIN_LOCKOUT_SECONDS']} ثانیه غیرفعال شد.",
                "danger",
            )

    return render_template("login.html")


@bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    """تغییر رمز عبور مدیر وارد‌شده به سامانه"""
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        admin = db.session.get(Admin, session.get("admin_id"))

        if admin is None or not admin.check_password(current_password):
            flash("رمز عبور فعلی اشتباه است.", "danger")
        elif len(new_password) < 8:
            flash("رمز عبور جدید باید حداقل ۸ کاراکتر باشد.", "danger")
        elif new_password != confirm_password:
            flash("تکرار رمز عبور جدید با رمز عبور جدید یکسان نیست.", "danger")
        elif admin.check_password(new_password):
            flash("رمز عبور جدید نباید با رمز عبور فعلی یکسان باشد.", "danger")
        else:
            admin.set_password(new_password)
            db.session.commit()
            current_app.logger.info("Password changed for admin %s", admin.username)
            flash("رمز عبور شما با موفقیت تغییر کرد.", "success")
            return redirect(url_for("auth.change_password"))

    return render_template("change_password.html")


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("از سامانه خارج شدید.", "success")
    return redirect(url_for("auth.login"))
