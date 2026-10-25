"""اعتبارسنجی سمت سرور برای فرم‌ها"""
import re
from datetime import datetime

STATUS_VALUES = {"active", "graduated", "dismissed"}

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _clean(value) -> str:
    return (value or "").strip() if isinstance(value, str) else ""


def semester_choices() -> list[str]:
    years = (1402, 1403, 1404, 1405)
    return [f"{y}-{s}" for y in years for s in (1, 2)]


def validate_person(form, *, number_field: str) -> tuple[dict, dict]:
    """اعتبارسنجی مشترک دانشجو/استاد؛ خروجی: (خطاها، داده‌های تمیز)"""
    errors = {}
    data = {}

    number = _clean(form.get(number_field))
    if not number:
        errors[number_field] = "این فیلد الزامی است."
    elif not number.isdigit() or not (3 <= len(number) <= 12):
        errors[number_field] = "شماره باید فقط شامل رقم و بین ۳ تا ۱۲ رقم باشد."
    data[number_field] = number

    data["first_name"] = _clean(form.get("first_name"))
    if len(data["first_name"]) < 2:
        errors["first_name"] = "نام باید حداقل ۲ حرف باشد."

    data["last_name"] = _clean(form.get("last_name"))
    if len(data["last_name"]) < 2:
        errors["last_name"] = "نام خانوادگی باید حداقل ۲ حرف باشد."

    data["phone"] = _clean(form.get("phone"))
    if data["phone"] and not re.fullmatch(r"0\d{9,10}", data["phone"]):
        errors["phone"] = "شماره موبایل باید با ۰ شروع شود و ۱۰ یا ۱۱ رقم باشد."

    data["email"] = _clean(form.get("email"))
    if data["email"] and not EMAIL_RE.fullmatch(data["email"]):
        errors["email"] = "قالب ایمیل معتبر نیست."

    return errors, data


def validate_student(form) -> tuple[dict, dict]:
    """اعتبارسنجی فرم دانشجو"""
    errors, data = validate_person(form, number_field="student_number")

    national_id = _clean(form.get("national_id"))
    if national_id and not re.fullmatch(r"\d{10}", national_id):
        errors["national_id"] = "کد ملی باید دقیقاً ۱۰ رقم باشد."
    data["national_id"] = national_id or None

    data["major"] = _clean(form.get("major"))

    entry_year = _clean(form.get("entry_year"))
    if entry_year:
        try:
            value = int(entry_year)
            if not (1350 <= value <= 1410):
                raise ValueError
            data["entry_year"] = value
        except ValueError:
            errors["entry_year"] = "سال ورود باید عددی بین ۱۳۵۰ تا ۱۴۱۰ باشد."
    else:
        data["entry_year"] = None

    data["status"] = _clean(form.get("status")) or "active"
    if data["status"] not in STATUS_VALUES:
        errors["status"] = "وضعیت انتخاب‌شده معتبر نیست."

    return errors, data


def validate_teacher(form) -> tuple[dict, dict]:
    """اعتبارسنجی فرم استاد"""
    errors, data = validate_person(form, number_field="teacher_number")
    data["department"] = _clean(form.get("department"))
    return errors, data


def validate_course(form) -> tuple[dict, dict]:
    """اعتبارسنجی فرم درس"""
    errors = {}
    data = {}

    code = _clean(form.get("course_code"))
    if not code:
        errors["course_code"] = "کد درس الزامی است."
    elif not re.fullmatch(r"[A-Za-z0-9\-]{2,20}", code):
        errors["course_code"] = "کد درس باید ۲ تا ۲۰ کاراکتر لاتین/عدد باشد."
    data["course_code"] = code

    data["title"] = _clean(form.get("title"))
    if len(data["title"]) < 3:
        errors["title"] = "عنوان درس باید حداقل ۳ حرف باشد."

    credits = _clean(form.get("credits"))
    try:
        value = int(credits)
        if not (1 <= value <= 6):
            raise ValueError
        data["credits"] = value
    except (TypeError, ValueError):
        errors["credits"] = "تعداد واحد باید عددی بین ۱ تا ۶ باشد."
        data["credits"] = credits

    teacher_id = _clean(form.get("teacher_id"))
    data["teacher_id"] = int(teacher_id) if teacher_id.isdigit() else None

    data["semester"] = _clean(form.get("semester")) or None

    return errors, data


def validate_grade(form) -> tuple[dict, dict]:
    """اعتبارسنجی فرم نمره"""
    errors = {}
    data = {}

    for field in ("student_id", "course_id"):
        value = _clean(form.get(field))
        if not value.isdigit():
            errors[field] = "انتخاب این فیلد الزامی است."
        else:
            data[field] = int(value)

    raw_score = _clean(form.get("score")).replace(",", ".").replace("٫", ".")
    try:
        score = round(float(raw_score), 2)
        if not (0 <= score <= 20):
            raise ValueError
        data["score"] = score
    except (TypeError, ValueError):
        errors["score"] = "نمره باید عددی بین ۰ تا ۲۰ باشد."
        data["score"] = raw_score

    data["semester"] = _clean(form.get("semester")) or None
    if data["semester"] and data["semester"] not in semester_choices():
        errors["semester"] = "نیمسال انتخاب‌شده معتبر نیست."

    return errors, data
