"""تست ابزارهای عمومی و مدل‌ها"""
from university.jalali import gregorian_to_jalali
from university.utils import fa_number, grade_letter, status_fa


def test_jalali_known_dates():
    assert gregorian_to_jalali(2024, 3, 20) == (1403, 1, 1)
    assert gregorian_to_jalali(2025, 3, 21) == (1404, 1, 1)
    assert gregorian_to_jalali(2026, 10, 26) == (1405, 8, 4)
    assert gregorian_to_jalali(2026, 3, 21) == (1405, 1, 1)


def test_fa_number():
    assert fa_number(1405) == "۱۴۰۵"
    assert fa_number(15.6) == "۱۵٫۶"
    assert fa_number(None) == "—"
    assert fa_number("") == "—"
    assert fa_number("40112233") == "۴۰۱۱۲۲۳۳"


def test_grade_letter():
    assert grade_letter(20) == "عالی"
    assert grade_letter(17) == "عالی"
    assert grade_letter(16.9) == "خوب"
    assert grade_letter(14) == "خوب"
    assert grade_letter(13) == "قابل قبول"
    assert grade_letter(10) == "قبول"
    assert grade_letter(9.9) == "مردود"
    assert grade_letter(0) == "مردود"
    assert grade_letter(None) == "—"


def test_status_fa():
    assert status_fa("active") == "فعال"
    assert status_fa("graduated") == "فارغ‌التحصیل"
    assert status_fa("dismissed") == "منقطع"
    assert status_fa("unknown") == "unknown"


def test_password_hashing_unique_salts():
    from university.models import Admin

    a1, a2 = Admin(username="u1"), Admin(username="u2")
    a1.set_password("same-password")
    a2.set_password("same-password")
    assert a1.password_hash != a2.password_hash
    assert a1.check_password("same-password")
    assert a2.check_password("same-password")


def test_student_full_name():
    from university.models import Student

    student = Student(student_number="1", first_name="علی", last_name="رضایی")
    assert student.full_name == "علی رضایی"
