"""تست‌های مدیریت اساتید و دروس"""
SAMPLE_TEACHER = {
    "teacher_number": "1001",
    "first_name": "محمود",
    "last_name": "فرهادی",
    "department": "مهندسی کامپیوتر",
    "phone": "09121112233",
    "email": "farhadi@uni.ir",
}

SAMPLE_COURSE = {
    "course_code": "CS101",
    "title": "برنامه‌نویسی پیشرفته",
    "credits": "3",
    "teacher_id": "",
    "semester": "1404-1",
}


def test_add_teacher_success(logged_in):
    resp = logged_in.post("/teachers/add", data=SAMPLE_TEACHER, follow_redirects=True)
    assert resp.status_code == 200
    assert "محمود" in resp.get_data(as_text=True)


def test_add_teacher_duplicate_rejected(logged_in):
    logged_in.post("/teachers/add", data=SAMPLE_TEACHER)
    duplicate = dict(SAMPLE_TEACHER, email="other@uni.ir")
    resp = logged_in.post("/teachers/add", data=duplicate)
    assert "قبلاً ثبت شده" in resp.get_data(as_text=True)


def test_edit_teacher(logged_in, app):
    logged_in.post("/teachers/add", data=SAMPLE_TEACHER)
    with app.app_context():
        from university.models import Teacher

        tid = Teacher.query.filter_by(teacher_number="1001").first().id
    resp = logged_in.post(
        f"/teachers/{tid}/edit",
        data=dict(SAMPLE_TEACHER, department="هوش مصنوعی"),
        follow_redirects=True,
    )
    assert "هوش مصنوعی" in resp.get_data(as_text=True)


def test_delete_teacher_sets_courses_teacher_null(logged_in, app):
    with app.app_context():
        from university.models import Course, Teacher, db

        teacher = Teacher(teacher_number="2002", first_name="لیلا", last_name="ستوده")
        db.session.add(teacher)
        db.session.commit()
        course = Course(course_code="CS999", title="درس آزمایشی", credits=2, teacher_id=teacher.id)
        db.session.add(course)
        db.session.commit()
        tid = teacher.id
        cid = course.id

    resp = logged_in.post(f"/teachers/{tid}/delete", follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        course = Course.query.get(cid)
        assert course is not None
        assert course.teacher_id is None


def test_add_course_success(logged_in):
    resp = logged_in.post("/courses/add", data=SAMPLE_COURSE, follow_redirects=True)
    assert resp.status_code == 200
    assert "برنامه‌نویسی پیشرفته" in resp.get_data(as_text=True)


def test_add_course_duplicate_code_rejected(logged_in):
    logged_in.post("/courses/add", data=SAMPLE_COURSE)
    duplicate = dict(SAMPLE_COURSE, title="درس تکراری")
    resp = logged_in.post("/courses/add", data=duplicate)
    assert "قبلاً ثبت شده" in resp.get_data(as_text=True)


def test_add_course_invalid_credits_rejected(logged_in):
    bad = dict(SAMPLE_COURSE, credits="9")
    resp = logged_in.post("/courses/add", data=bad)
    assert "۱ تا ۶" in resp.get_data(as_text=True)


def test_edit_course(logged_in, app):
    logged_in.post("/courses/add", data=SAMPLE_COURSE)
    with app.app_context():
        from university.models import Course

        cid = Course.query.filter_by(course_code="CS101").first().id
    resp = logged_in.post(
        f"/courses/{cid}/edit",
        data=dict(SAMPLE_COURSE, title="برنامه‌نویسی پیشرفته (پایتون)"),
        follow_redirects=True,
    )
    assert "پایتون" in resp.get_data(as_text=True)


def test_delete_course_cascades_grades(logged_in, app):
    with app.app_context():
        from university.models import Course, Grade, Student, db

        student = Student(student_number="77777", first_name="تست", last_name="کاسکید", status="active")
        db.session.add(student)
        db.session.commit()
        course = Course(course_code="DEL1", title="درس حذف‌شدنی", credits=3)
        db.session.add(course)
        db.session.commit()
        grade = Grade(student_id=student.id, course_id=course.id, score=15, semester="1404-1")
        db.session.add(grade)
        db.session.commit()
        cid = course.id

    resp = logged_in.post(f"/courses/{cid}/delete", follow_redirects=True)
    assert resp.status_code == 200
    with app.app_context():
        assert Course.query.get(cid) is None
        assert Grade.query.count() == 0


def test_course_search(logged_in):
    logged_in.post("/courses/add", data=SAMPLE_COURSE, follow_redirects=True)
    other = dict(SAMPLE_COURSE, course_code="MA101", title="ریاضی عمومی")
    logged_in.post("/courses/add", data=other, follow_redirects=True)

    resp = logged_in.get("/courses", query_string={"q": "ریاضی"})
    body = resp.get_data(as_text=True)
    assert "ریاضی" in body
    assert "برنامه‌نویسی پیشرفته" not in body
