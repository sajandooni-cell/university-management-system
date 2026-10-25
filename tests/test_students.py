"""تست‌های مدیریت دانشجویان و خروجی CSV"""
from tests.conftest import SAMPLE_STUDENT


def test_add_student_success(logged_in):
    resp = logged_in.post("/students/add", data=SAMPLE_STUDENT, follow_redirects=True)
    assert resp.status_code == 200
    assert "علی رضایی" in resp.get_data(as_text=True)


def test_add_student_duplicate_number_rejected(logged_in):
    logged_in.post("/students/add", data=SAMPLE_STUDENT)
    duplicate = dict(SAMPLE_STUDENT, national_id="9999999999")
    resp = logged_in.post("/students/add", data=duplicate)
    assert "قبلاً ثبت شده" in resp.get_data(as_text=True)


def test_add_student_invalid_number_rejected(logged_in):
    bad = dict(SAMPLE_STUDENT, student_number="abc!")
    resp = logged_in.post("/students/add", data=bad)
    assert "فقط شامل رقم" in resp.get_data(as_text=True)


def test_add_student_invalid_national_id_rejected(logged_in):
    bad = dict(SAMPLE_STUDENT, national_id="12345")
    resp = logged_in.post("/students/add", data=bad)
    assert "کد ملی" in resp.get_data(as_text=True)


def test_edit_student(logged_in, app):
    logged_in.post("/students/add", data=SAMPLE_STUDENT)
    with app.app_context():
        from university.models import Student

        sid = Student.query.filter_by(student_number="40112233").first().id
    updated = dict(SAMPLE_STUDENT, first_name="علیرضا")
    resp = logged_in.post(f"/students/{sid}/edit", data=updated, follow_redirects=True)
    assert resp.status_code == 200
    assert "علیرضا" in resp.get_data(as_text=True)


def test_delete_student(logged_in, app):
    logged_in.post("/students/add", data=SAMPLE_STUDENT)
    with app.app_context():
        from university.models import Student

        sid = Student.query.filter_by(student_number="40112233").first().id
    resp = logged_in.post(f"/students/{sid}/delete", follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert Student.query.filter_by(student_number="40112233").count() == 0


def test_search_students(logged_in):
    logged_in.post("/students/add", data=SAMPLE_STUDENT, follow_redirects=True)
    other = dict(SAMPLE_STUDENT, student_number="40119999", first_name="سارا", last_name="محمدی", national_id="1098765432")
    logged_in.post("/students/add", data=other, follow_redirects=True)

    resp = logged_in.get("/students", query_string={"q": "سارا"})
    body = resp.get_data(as_text=True)
    assert "سارا" in body
    assert "40112233" not in body


def test_search_by_student_number(logged_in):
    logged_in.post("/students/add", data=SAMPLE_STUDENT)
    resp = logged_in.get("/students", query_string={"q": "40112233"})
    assert "علی" in resp.get_data(as_text=True)


def test_pagination_page_param(logged_in):
    resp = logged_in.get("/students", query_string={"page": 1})
    assert resp.status_code == 200
    resp = logged_in.get("/students", query_string={"page": 99})
    assert resp.status_code == 200


def test_export_csv_with_bom(logged_in):
    logged_in.post("/students/add", data=SAMPLE_STUDENT)
    resp = logged_in.get("/students/export")
    assert resp.status_code == 200
    assert resp.mimetype == "text/csv"
    raw = resp.get_data()
    assert raw.startswith(b"\xef\xbb\xbf")  # UTF-8 BOM برای اکسل
    body = raw.decode("utf-8-sig")
    assert "شماره دانشجویی" in body
    assert "علی" in body
    assert "40112233" in body
