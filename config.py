"""پیکربندی برنامه - Config module"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = (BASE_DIR / "university.db").as_posix()

# اگر DATABASE_URL محیطی معتبر باشد استفاده می‌شود، در غیر این صورت SQLite محلی
_ENV_DATABASE = os.environ.get("DATABASE_URL", "")
_ENV_DATABASE_OK = _ENV_DATABASE.startswith(
    ("sqlite", "postgresql", "postgres", "mysql", "mariadb")
)


class Config:
    """پیکربندی پیش‌فرض"""
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-me-in-production")
    if _ENV_DATABASE_OK:
        SQLALCHEMY_DATABASE_URI = _ENV_DATABASE
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # محافظت CSRF فعال باشد
    ENABLE_CSRF = True
    # در اولین اجرا، در صورت خالی بودن پایگاه داده، داده نمونه ایجاد شود
    AUTO_SEED = True
    # تعداد ردیف در هر صفحه
    PER_PAGE = 10


class TestingConfig(Config):
    """پیکربندی مخصوص تست‌های خودکار"""
    TESTING = True
    ENABLE_CSRF = False
    AUTO_SEED = False
