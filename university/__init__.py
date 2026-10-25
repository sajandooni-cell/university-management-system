"""پکیج اصلی برنامه - Application factory"""
import logging

from flask import Flask, render_template

from config import Config
from .models import db, Admin, Student, Teacher, Course, Grade
from .utils import register_template_extensions, csrf_protect
from .seed_data import seed_sample_data

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("university")


def security_headers(response):
    """افزودن هدرهای امنیتی استاندارد به همه پاسخ‌ها"""
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'",
    )
    return response


def register_error_pages(app: Flask) -> None:
    """صفحات خطای سفارشی فارسی"""

    @app.errorhandler(400)
    def bad_request(error):
        return render_template("errors/400.html", description=error.description), 400

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template("errors/500.html"), 500


def create_app(config_class: type = Config) -> Flask:
    """ساخت و پیکربندی برنامه Flask"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # پایگاه داده
    db.init_app(app)

    # مسیرها (Blueprints)
    from .routes import register_blueprints
    register_blueprints(app)

    # فیلترها و متغیرهای قالب
    register_template_extensions(app)

    # محافظت CSRF برای همه درخواست‌های POST
    app.before_request(csrf_protect)

    # هدرهای امنیتی برای همه پاسخ‌ها
    app.after_request(security_headers)

    # صفحات خطای سفارشی
    register_error_pages(app)

    @app.route("/health")
    def health():
        """نقطه بررسی سلامت سامانه برای مانیتورینگ"""
        return {"status": "ok", "version": app.config["APP_VERSION"]}

    with app.app_context():
        db.create_all()
        if not app.config.get("TESTING"):
            _ensure_admin(app)
            if app.config.get("AUTO_SEED"):
                _seed_if_empty(app)

    return app


def _ensure_admin(app: Flask) -> None:
    """در صورت نبود هیچ مدیری، حساب پیش‌فرض ساخته می‌شود."""
    if Admin.query.count() == 0:
        admin = Admin(username="admin")
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        logger.warning(
            "حساب مدیر پیش‌فرض ساخته شد -> نام کاربری: admin | رمز عبور: admin123 "
            "(بلافاصله پس از ورود، رمز عبور را تغییر دهید)"
        )


def _seed_if_empty(app: Flask) -> None:
    """اگر پایگاه داده کاملاً خالی باشد، داده نمونه ایجاد می‌کند."""
    empty = (
        Student.query.count() == 0
        and Teacher.query.count() == 0
        and Course.query.count() == 0
        and Grade.query.count() == 0
    )
    if empty:
        seed_sample_data(students_count=20)
        logger.info("داده نمونه اولیه ایجاد شد (۲۰ دانشجو، ۶ استاد، ۱۰ درس، نمرات نمونه)")
