"""مدل‌های پایگاه داده - SQLAlchemy models"""
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()

STATUS_ACTIVE = "active"
STATUS_GRADUATED = "graduated"
STATUS_DISMISSED = "dismissed"


class Admin(db.Model):
    """حساب مدیر سامانه"""
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    def __repr__(self) -> str:
        return f"<Admin {self.username}>"


class Student(db.Model):
    """دانشجو"""
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    national_id = db.Column(db.String(20), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    major = db.Column(db.String(100), nullable=True)
    entry_year = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), default=STATUS_ACTIVE, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    grades = db.relationship(
        "Grade", backref="student", cascade="all, delete-orphan", lazy=True
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    @property
    def gpa(self):
        """معدل وزنی = مجموع(نمره × واحد) ÷ مجموع واحدها"""
        rows = [(g.score, g.course.credits) for g in self.grades if g.score is not None]
        if not rows:
            return None
        total_points = sum(score * credits for score, credits in rows)
        total_credits = sum(credits for _, credits in rows)
        if total_credits == 0:
            return None
        return round(total_points / total_credits, 2)

    def __repr__(self) -> str:
        return f"<Student {self.student_number} {self.full_name}>"


class Teacher(db.Model):
    """استاد"""
    __tablename__ = "teachers"

    id = db.Column(db.Integer, primary_key=True)
    teacher_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    department = db.Column(db.String(100), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    courses = db.relationship("Course", backref="teacher", lazy=True)

    @property
    def full_name(self) -> str:
        return f"دکتر {self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<Teacher {self.teacher_number} {self.full_name}>"


class Course(db.Model):
    """درس"""
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    course_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    credits = db.Column(db.Integer, nullable=False, default=2)
    teacher_id = db.Column(
        db.Integer, db.ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True
    )
    semester = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    grades = db.relationship(
        "Grade", backref="course", cascade="all, delete-orphan", lazy=True
    )

    def __repr__(self) -> str:
        return f"<Course {self.course_code} {self.title}>"


class Grade(db.Model):
    """نمره دانشجو در یک درس"""
    __tablename__ = "grades"
    __table_args__ = (
        db.UniqueConstraint("student_id", "course_id", name="uq_grade_student_course"),
    )

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(
        db.Integer, db.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_id = db.Column(
        db.Integer, db.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    score = db.Column(db.Float, nullable=False)
    semester = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def __repr__(self) -> str:
        return f"<Grade student={self.student_id} course={self.course_id} score={self.score}>"
