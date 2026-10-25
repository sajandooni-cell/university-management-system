"""تست‌های ثبت نمره، محاسبه معدل وزنی و کارنامه"""
from university.models import Course, Grade, Student, db


def _make_student(app, number="55555", name="علی", family="رضایی") -> int:
    with app.app_context():
        student = Student(student_number=number, first_name=name, last_name=family, status="active")
        db.session.add(student)
        db.session.commit()
        return student.id


def _make_course(app, code="C101", title="درس آزمایشی", credits=3) -> int:
    with app.app_context():
        course = Course(course_code=code, title=title, credits=credits)
        db.session.add(course)
        db.session.commit()
        return course.id


def test_gpa_weighted_calculation(app):
    """معدل وزنی: (18×3 + 12×2) ÷ 5 = 15.6"""
    with app.app_context():
        student = Student(student_number="60001", first_name="زهرا", last_name="کریمی", status="active")
        c1 = Course(course_code="C1", title="درس سه‌واحدی", credits=3)
        c2 = Course(course_code="C2", title="درس دو‌واحدی", credits=2)
        db.session.add_all([student, c1, c2])
        db.session.commit()
        sid, c1id, c2id = student.id, c1.id, c2.id

        db.session.add_all([
            Grade(student_id=sid, course_id=c1id, score=18, semester="1404-1"),
            Grade(student_id=sid, course_id=c2id, score=12, semester="1404-1"),
        ])
        db.session.commit()
        assert student.gpa == 15.6


def test_gpa_no_grades_returns_none(app):
    with app.app_context():
        student = Student(student_number="60002", first_name="بدون", last_name="نمره", status="active")
        db.session.add(student)
        db.session.commit()
        assert student.gpa is None


def test_gpa_updates_after_score_edit(logged_in, app):
    sid = _make_student(app)
    cid = _make_course(app, "ED1", "درس ویرایش", credits=2)
    logged_in.post(
        "/grades/add",
        data={"student_id": str(sid), "course_id": str(cid), "score": "10", "semester": "1404-1"},
        follow_redirects=True,
    )
    with app.app_context():
        grade = Grade.query.one()
        gid = grade.id
        student = Student.query.get(sid)
        assert student.gpa == 10.0

    logged_in.post(
        f"/grades/{gid}/edit",
        data={"student_id": str(sid), "course_id": str(cid), "score": "20", "semester": "1404-1"},
        follow_redirects=True,
    )
    with app.app_context():
        assert Student.query.get(sid).gpa == 20.0


def test_add_grade_success(logged_in, app):
    sid = _make_student(app)
    cid = _make_course(app)
    resp = logged_in.post(
        "/grades/add",
        data={"student_id": str(sid), "course_id": str(cid), "score": "17.5", "semester": "1404-1"},
        follow_redirects=True,
    )
    assert resp.status_code == 200
    with app.app_context():
        assert Grade.query.count() == 1
        assert Grade.query.one().score == 17.5


def test_add_grade_invalid_score_rejected(logged_in, app):
    sid = _make_student(app)
    cid = _make_course(app)
    resp = logged_in.post(
        "/grades/add",
        data={"student_id": str(sid), "course_id": str(cid), "score": "25", "semester": "1404-1"},
    )
    assert "۰ تا ۲۰" in resp.get_data(as_text=True)


def test_add_grade_duplicate_rejected(logged_in, app):
    sid = _make_student(app)
    cid = _make_course(app)
    payload = {"student_id": str(sid), "course_id": str(cid), "score": "15", "semester": "1404-1"}
    logged_in.post("/grades/add", data=payload, follow_redirects=True)
    resp = logged_in.post("/grades/add", data=payload)
    assert "قبلاً نمره ثبت شده" in resp.get_data(as_text=True)


def test_delete_grade(logged_in, app):
    sid = _make_student(app)
    cid = _make_course(app)
    logged_in.post(
        "/grades/add",
        data={"student_id": str(sid), "course_id": str(cid), "score": "15", "semester": "1404-1"},
    )
    with app.app_context():
        gid = Grade.query.one().id
    resp = logged_in.post(f"/grades/{gid}/delete", follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert Grade.query.count() == 0


def test_transcript_page_shows_gpa(logged_in, app):
    sid = _make_student(app, "80001", "مریم", "نوری")
    c1 = _make_course(app, "T1", "ریاضی", credits=3)
    c2 = _make_course(app, "T2", "فیزیک", credits=2)
    logged_in.post(
        "/grades/add",
        data={"student_id": str(sid), "course_id": str(c1), "score": "18", "semester": "1404-1"},
    )
    logged_in.post(
        "/grades/add",
        data={"student_id": str(sid), "course_id": str(c2), "score": "12", "semester": "1404-1"},
    )
    resp = logged_in.get(f"/students/{sid}/transcript")
    body = resp.get_data(as_text=True)
    assert resp.status_code == 200
    assert "کارنامه" in body
    assert "معدل وزنی" in body
    assert "۱۵٫۶" in body  # (18×3 + 12×2) ÷ 5 = 15.6


def test_transcript_404_for_missing_student(logged_in):
    resp = logged_in.get("/students/99999/transcript")
    assert resp.status_code == 404


def test_grades_export_csv(logged_in, app):
    sid = _make_student(app, "90001", "امیر", "صادقی")
    cid = _make_course(app, "EX1", "درس خروجی", credits=3)
    logged_in.post(
        "/grades/add",
        data={"student_id": str(sid), "course_id": str(cid), "score": "14", "semester": "1404-1"},
    )
    resp = logged_in.get("/grades/export")
    assert resp.status_code == 200
    body = resp.get_data().decode("utf-8-sig")
    assert "امیر صادقی" in body
    assert "درس خروجی" in body
