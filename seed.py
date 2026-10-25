"""اسکریپت ایجاد داده نمونه - اجرا: python seed.py"""
from university import create_app
from university.models import db, Admin, Student, Teacher, Course, Grade
from university.seed_data import seed_sample_data


def main() -> None:
    app = create_app()
    with app.app_context():
        if Student.query.count() == 0:
            print("در حال ایجاد داده نمونه...")
            result = seed_sample_data(students_count=20)
            print(
                f"ایجاد شد: {result['students']} دانشجو، {result['teachers']} استاد، "
                f"{result['courses']} درس، {result['grades']} نمره"
            )
        else:
            print("داده نمونه از قبل موجود است؛ چیزی اضافه نشد.")

        print("-" * 40)
        print(f"دانشجویان: {Student.query.count()}")
        print(f"اساتید: {Teacher.query.count()}")
        print(f"دروس: {Course.query.count()}")
        print(f"نمرات: {Grade.query.count()}")
        print(f"مدیران: {Admin.query.count()}")
        print("-" * 40)
        print("ورود به سامانه -> نام کاربری: admin | رمز عبور: admin123")


if __name__ == "__main__":
    main()
