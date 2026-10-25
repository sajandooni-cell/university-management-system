"""ایجاد داده نمونه برای نمایش و تست برنامه"""
import random

from .models import db, Student, Teacher, Course, Grade, STATUS_ACTIVE, STATUS_GRADUATED

FIRST_NAMES = [
    "علی", "سارا", "حسین", "فاطمه", "محمد", "زهرا", "رضا", "مریم", "امیر", "نگار",
    "پارسا", "الهام", "سینا", "نیلوفر", "بهنام", "شیرین", "آرش", "پریسا", "کیان", "ترمه",
    "مهدی", "سمانه", "بابک", "لیلا",
]
LAST_NAMES = [
    "رضایی", "محمدی", "احمدی", "حسینی", "کریمی", "موسوی", "جعفری", "نوری", "صادقی", "تهرانی",
    "کاظمی", "رحیمی", "مرادی", "شریفی", "قاسمی", "عباسی", "دهقانی", "اکبری", "زارع", "سلطانی",
    "بهرامی", "فتحی", "صالحی", "امیری",
]
MAJORS = [
    "مهندسی کامپیوتر", "مهندسی برق", "مهندسی مکانیک",
    "مدیریت", "حسابداری", "مهندسی معماری",
]

TEACHERS = [
    ("محمود", "فرهادی", "مهندسی کامپیوتر"),
    ("لیلا", "ستوده", "مهندسی کامپیوتر"),
    ("حسن", "مرتضوی", "مهندسی برق"),
    ("فرشته", "امینی", "ریاضی"),
    ("کاوه", "نیک‌پور", "مدیریت"),
    ("مریم", "خلج", "فیزیک"),
]

COURSES = [
    ("CS101", "برنامه‌نویسی پیشرفته", 3),
    ("CS201", "ساختمان داده", 3),
    ("CS202", "پایگاه داده", 3),
    ("MA101", "ریاضی عمومی ۱", 3),
    ("PH101", "فیزیک پایه", 3),
    ("CS305", "شبکه‌های کامپیوتری", 3),
    ("CS310", "هوش مصنوعی", 3),
    ("CS210", "سیستم عامل", 3),
    ("GE201", "اقتصاد مهندسی", 2),
    ("GE110", "زبان انگلیسی", 2),
]

SEMESTERS = ["1403-1", "1403-2", "1404-1", "1404-2"]


def seed_sample_data(students_count: int = 20) -> dict:
    """ایجاد داده نمونه؛ خروجی: تعداد رکوردهای ایجادشده"""
    rng = random.Random(42)

    teachers = []
    for i, (first, last, dept) in enumerate(TEACHERS, start=1):
        teacher = Teacher(
            teacher_number=f"1{i:03d}",
            first_name=first,
            last_name=last,
            department=dept,
            email=f"t{i}@uni.ir",
            phone=f"091210000{i:02d}",
        )
        teachers.append(teacher)
        db.session.add(teacher)

    courses = []
    for i, (code, title, credits) in enumerate(COURSES):
        course = Course(
            course_code=code,
            title=title,
            credits=credits,
            teacher=teachers[i % len(teachers)],
            semester=rng.choice(SEMESTERS),
        )
        courses.append(course)
        db.session.add(course)

    db.session.flush()

    used_national = set()
    students = []
    for i in range(students_count):
        first = FIRST_NAMES[i % len(FIRST_NAMES)]
        last = LAST_NAMES[(i * 5 + 2) % len(LAST_NAMES)]
        while True:
            national_id = str(rng.randint(1000000000, 1999999999))
            if national_id not in used_national:
                used_national.add(national_id)
                break
        status = STATUS_ACTIVE
        if i % 9 == 4:
            status = STATUS_GRADUATED
        student = Student(
            student_number=f"4011{i + 1:04d}",
            first_name=first,
            last_name=last,
            national_id=national_id,
            phone=f"0912{i + 1:07d}",
            email=f"student{i + 1}@uni.ir",
            major=MAJORS[i % len(MAJORS)],
            entry_year=rng.choice([1400, 1401, 1402, 1403, 1404]),
            status=status,
        )
        students.append(student)
        db.session.add(student)

    db.session.flush()

    grade_count = 0
    for student in students:
        picked = rng.sample(courses, k=rng.randint(4, min(6, len(courses))))
        for course in picked:
            score = round(rng.uniform(8.0, 20.0), 1)
            if rng.random() < 0.12:
                score = 20.0
            db.session.add(
                Grade(
                    student_id=student.id,
                    course_id=course.id,
                    score=score,
                    semester=rng.choice(SEMESTERS),
                )
            )
            grade_count += 1

    db.session.commit()
    return {
        "teachers": len(teachers),
        "courses": len(courses),
        "students": len(students),
        "grades": grade_count,
    }
