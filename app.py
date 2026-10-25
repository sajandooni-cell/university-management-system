"""نقطه ورود برنامه - سامانه مدیریت دانشگاهی"""
from university import create_app

app = create_app()

if __name__ == "__main__":
    print("=" * 60)
    print("  سامانه مدیریت دانشگاهی")
    print("  آدرس: http://127.0.0.1:5000")
    print("  نام کاربری پیش‌فرض: admin  |  رمز عبور: admin123")
    print("=" * 60)
    app.run(debug=True, host="127.0.0.1", port=5000)
