"""تست‌های امنیتی نسخه ۱٫۱٫۰: هدرهای امنیتی، قفل ورود، تغییر رمز، صفحات خطا، سلامت"""
import time

from university.routes import auth as auth_routes


# ------------------------------------------------------- هدرهای امنیتی

def test_security_headers_on_login(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "DENY"
    assert resp.headers.get("Referrer-Policy") == "no-referrer"
    csp = resp.headers.get("Content-Security-Policy", "")
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert "form-action 'self'" in csp


def test_security_headers_on_static(client):
    resp = client.get("/static/css/style.css")
    assert resp.status_code == 200
    assert resp.headers.get("X-Frame-Options") == "DENY"


def test_session_cookie_is_httponly_and_samesite(client):
    resp = client.post("/login", data={"username": "admin", "password": "admin123"})
    set_cookie = resp.headers.get("Set-Cookie", "")
    assert "HttpOnly" in set_cookie
    assert "SameSite=Lax" in set_cookie


# ------------------------------------------------------- سلامت سامانه

def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"
    assert data["version"] == "1.1.0"


# ------------------------------------------------------- صفحات خطا

def test_404_custom_page(logged_in):
    resp = logged_in.get("/this-page-does-not-exist")
    assert resp.status_code == 404
    html = resp.get_data(as_text=True)
    assert "۴۰۴" in html
    assert "پیدا نشد" in html


def test_500_custom_page(client, app):
    def boom():
        from flask import abort
        abort(500)

    app.add_url_rule("/boom", "boom", boom)
    resp = client.get("/boom")
    assert resp.status_code == 500
    html = resp.get_data(as_text=True)
    assert "۵۰۰" in html


def test_400_custom_page_for_csrf(tmp_path):
    """با فعال بودن CSRF، ارسال فرم بدون توکن باید صفحه خطای ۴۰۰ فارسی برگرداند"""
    from config import Config
    from university import create_app
    from university.models import Admin, db

    class CsrfConfig(Config):
        TESTING = True
        AUTO_SEED = False
        ENABLE_CSRF = True
        SECRET_KEY = "csrf-test"
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{(tmp_path / 'c400.db').as_posix()}"

    app = create_app(CsrfConfig)
    with app.app_context():
        admin = Admin(username="admin")
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()

    client = app.test_client()
    resp = client.post("/login", data={"username": "admin", "password": "admin123"})
    assert resp.status_code == 400
    html = resp.get_data(as_text=True)
    assert "۴۰۰" in html
    assert "CSRF" in html


# ------------------------------------------------------- قفل ورود (brute-force)

def _wrong_login(client):
    return client.post("/login", data={"username": "admin", "password": "wrong-password"})


def test_failed_attempts_shown_in_message(client):
    resp = _wrong_login(client)
    assert resp.status_code == 200
    assert "تلاش ناموفق" in resp.get_data(as_text=True)


def test_login_lockout_after_max_attempts(client):
    for _ in range(5):
        _wrong_login(client)
    # حتی با رمز عبور درست هم ورود باید قفل باشد
    resp = client.post("/login", data={"username": "admin", "password": "admin123"})
    assert resp.status_code == 429
    assert "غیرفعال" in resp.get_data(as_text=True)


def test_login_lockout_expires(client):
    for _ in range(5):
        _wrong_login(client)
    assert client.post("/login", data={"username": "admin", "password": "admin123"}).status_code == 429
    # شبیه‌سازی گذشت زمان قفل
    for ip in list(auth_routes._LOCKED_UNTIL):
        auth_routes._LOCKED_UNTIL[ip] = time.time() - 1
    resp = client.post("/login", data={"username": "admin", "password": "admin123"})
    assert resp.status_code == 302


def test_failed_counter_cleared_after_success(client):
    _wrong_login(client)
    _wrong_login(client)
    resp = client.post("/login", data={"username": "admin", "password": "admin123"})
    assert resp.status_code == 302
    assert auth_routes._FAILED_LOGINS.get("127.0.0.1") is None
    assert auth_routes._LOCKED_UNTIL.get("127.0.0.1") is None


def test_lockout_counts_per_ip(client):
    _wrong_login(client)
    assert "203.0.113.9" not in auth_routes._FAILED_LOGINS
    assert "127.0.0.1" in auth_routes._FAILED_LOGINS


# ------------------------------------------------------- تغییر رمز عبور

def test_change_password_page_get(logged_in):
    resp = logged_in.get("/change-password")
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert "تغییر رمز عبور" in html
    assert "current_password" in html


def test_change_password_requires_login(client):
    resp = client.get("/change-password", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_change_password_wrong_current(logged_in):
    resp = logged_in.post(
        "/change-password",
        data={
            "current_password": "WRONG-PASS",
            "new_password": "NewPass1234",
            "confirm_password": "NewPass1234",
        },
        follow_redirects=True,
    )
    assert "اشتباه است" in resp.get_data(as_text=True)


def test_change_password_too_short(logged_in):
    resp = logged_in.post(
        "/change-password",
        data={
            "current_password": "admin123",
            "new_password": "short",
            "confirm_password": "short",
        },
        follow_redirects=True,
    )
    assert "حداقل ۸" in resp.get_data(as_text=True)


def test_change_password_mismatch(logged_in):
    resp = logged_in.post(
        "/change-password",
        data={
            "current_password": "admin123",
            "new_password": "NewPass1234",
            "confirm_password": "Other9999",
        },
        follow_redirects=True,
    )
    assert "یکسان نیست" in resp.get_data(as_text=True)


def test_change_password_same_as_old(logged_in):
    resp = logged_in.post(
        "/change-password",
        data={
            "current_password": "admin123",
            "new_password": "admin123",
            "confirm_password": "admin123",
        },
        follow_redirects=True,
    )
    assert "یکسان باشد" in resp.get_data(as_text=True)


def test_change_password_success_and_relogin(client, logged_in):
    resp = logged_in.post(
        "/change-password",
        data={
            "current_password": "admin123",
            "new_password": "NewSecure123",
            "confirm_password": "NewSecure123",
        },
        follow_redirects=True,
    )
    assert "موفقیت تغییر کرد" in resp.get_data(as_text=True)

    # خروج و سپس تلاش ورود با رمز قدیمی (باید رد شود)
    logged_in.post("/logout")
    old = client.post(
        "/login", data={"username": "admin", "password": "admin123"}, follow_redirects=True
    )
    assert "اشتباه است" in old.get_data(as_text=True)

    # ورود با رمز جدید (باید موفق باشد)
    new = client.post("/login", data={"username": "admin", "password": "NewSecure123"})
    assert new.status_code == 302
