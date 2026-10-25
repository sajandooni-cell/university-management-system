"""پیکربندی مشترک تست‌ها"""
import pytest

from config import Config
from university import create_app
from university.models import db, Admin


class TestConfig(Config):
    TESTING = True
    ENABLE_CSRF = False
    AUTO_SEED = False
    SECRET_KEY = "test-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


@pytest.fixture()
def app(tmp_path):
    """ساخت اپ تست با پایگاه داده مجزا"""
    TestConfig.SQLALCHEMY_DATABASE_URI = f"sqlite:///{(tmp_path / 'test.db').as_posix()}"
    application = create_app(TestConfig)
    with application.app_context():
        db.create_all()
        admin = Admin(username="admin")
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
    yield application
    with application.app_context():
        db.session.remove()
        db.engine.dispose()


@pytest.fixture(autouse=True)
def _reset_login_throttle():
    """ایزوله‌سازی شمارنده محافظت brute-force بین تست‌ها"""
    from university.routes import auth as auth_routes

    auth_routes._FAILED_LOGINS.clear()
    auth_routes._LOCKED_UNTIL.clear()
    yield
    auth_routes._FAILED_LOGINS.clear()
    auth_routes._LOCKED_UNTIL.clear()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def logged_in(client):
    client.post("/login", data={"username": "admin", "password": "admin123"})
    return client


SAMPLE_STUDENT = {
    "student_number": "40112233",
    "first_name": "علی",
    "last_name": "رضایی",
    "national_id": "1234567890",
    "phone": "09123456789",
    "email": "ali@uni.ir",
    "major": "مهندسی کامپیوتر",
    "entry_year": "1402",
    "status": "active",
}
