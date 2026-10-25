"""تست‌های احراز هویت و امنیت"""
from university import create_app
from config import Config


class CsrfTestConfig(Config):
    TESTING = True
    AUTO_SEED = False
    ENABLE_CSRF = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


def test_login_page_loads(client):
    resp = client.get("/login")
    assert resp.status_code == 200
    assert "ورود" in resp.get_data(as_text=True)


def test_login_wrong_password(client):
    resp = client.post(
        "/login",
        data={"username": "admin", "password": "wrong"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    assert "اشتباه" in resp.get_data(as_text=True)


def test_login_success_redirects_to_dashboard(client):
    resp = client.post("/login", data={"username": "admin", "password": "admin123"})
    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/")


def test_dashboard_requires_login(client):
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 302
    assert "/login" in resp.headers["Location"]


def test_students_page_requires_login(client):
    resp = client.get("/students", follow_redirects=False)
    assert resp.status_code == 302


def test_logout(client, logged_in):
    resp = logged_in.post("/logout", follow_redirects=True)
    assert resp.status_code == 200
    # پس از خروج، داشبورد نباید مستقیم در دسترس باشد
    resp = logged_in.get("/", follow_redirects=False)
    assert resp.status_code == 302


def test_password_is_hashed(app):
    from university.models import Admin, db

    with app.app_context():
        admin = Admin.query.filter_by(username="admin").first()
        assert admin.password_hash != "admin123"
        assert admin.password_hash.startswith(("pbkdf2:", "scrypt:"))
        assert admin.check_password("admin123")
        assert not admin.check_password("admin124")


def _csrf_app(tmp_path, name):
    from university.models import Admin, db

    CsrfTestConfig.SQLALCHEMY_DATABASE_URI = f"sqlite:///{(tmp_path / name).as_posix()}"
    app = create_app(CsrfTestConfig)
    with app.app_context():
        admin = Admin(username="admin")
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
    return app


def test_csrf_blocks_post_without_token(tmp_path):
    app = _csrf_app(tmp_path, "csrf.db")
    client = app.test_client()
    resp = client.post("/login", data={"username": "admin", "password": "admin123"})
    assert resp.status_code == 400
    assert "CSRF" in resp.get_data(as_text=True)


def test_csrf_accepts_valid_token(tmp_path):
    app = _csrf_app(tmp_path, "csrf2.db")
    client = app.test_client()
    with client.session_transaction() as session:
        session["_csrf_token"] = "valid-token-123"
    resp = client.post(
        "/login",
        data={"username": "admin", "password": "admin123", "csrf_token": "valid-token-123"},
    )
    # توکن معتبر است؛ اگر رمز درست باشد به داشبورد ریدایرکت می‌شود
    assert resp.status_code == 302


def test_csrf_rejects_wrong_token(tmp_path):
    app = _csrf_app(tmp_path, "csrf3.db")
    client = app.test_client()
    with client.session_transaction() as session:
        session["_csrf_token"] = "valid-token-123"
    resp = client.post(
        "/login",
        data={"username": "admin", "password": "admin123", "csrf_token": "WRONG"},
    )
    assert resp.status_code == 400
