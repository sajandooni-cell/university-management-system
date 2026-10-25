"""ثبت و مدیریت نمرات"""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import or_

from ..forms import semester_choices, validate_grade
from ..models import Course, Grade, Student, db
from ..utils import csv_response, login_required

bp = Blueprint("grades", __name__)


@bp.route("/grades")
@login_required
def list_grades():
    q = request.args.get("q", "").strip()
    student_id = request.args.get("student_id", "", type=str).strip()
    page = max(request.args.get("page", 1, type=int) or 1, 1)
    per_page = 10

    query = Grade.query.join(Student).join(Course)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Student.first_name.ilike(like),
                Student.last_name.ilike(like),
                Student.student_number.ilike(like),
                Course.title.ilike(like),
                Course.course_code.ilike(like),
            )
        )
    if student_id.isdigit():
        query = query.filter(Grade.student_id == int(student_id))

    pagination = query.order_by(Grade.created_at.desc(), Grade.id.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    students = Student.query.order_by(Student.student_number).all()
    return render_template(
        "grades/list.html",
        pagination=pagination,
        q=q,
        student_id=student_id,
        students=students,
    )


@bp.route("/grades/export")
@login_required
def export_grades():
    grades = Grade.query.join(Student).join(Course).order_by(Grade.id).all()
    rows = [
        [
            g.student.student_number,
            g.student.full_name,
            g.course.course_code,
            g.course.title,
            g.course.credits,
            g.score,
            g.semester or "",
        ]
        for g in grades
    ]
    headers = ["شماره دانشجویی", "نام و نام خانوادگی", "کد درس", "عنوان درس", "واحد", "نمره", "نیمسال"]
    return csv_response(rows, headers, filename="grades.csv")


@bp.route("/grades/add", methods=["GET", "POST"])
@login_required
def add_grade():
    if request.method == "POST":
        errors, data = validate_grade(request.form)
        if not errors:
            exists = Grade.query.filter_by(
                student_id=data["student_id"], course_id=data["course_id"]
            ).first()
            if exists:
                errors["course_id"] = "برای این دانشجو در این درس قبلاً نمره ثبت شده است."
        if not errors:
            grade = Grade(
                student_id=data["student_id"],
                course_id=data["course_id"],
                score=data["score"],
                semester=data["semester"],
            )
            db.session.add(grade)
            db.session.commit()
            flash("نمره با موفقیت ثبت شد.", "success")
            return redirect(url_for("grades.list_grades"))
        flash("ثبت نمره انجام نشد؛ خطاهای فرم را برطرف کنید.", "danger")

    students = Student.query.order_by(Student.student_number).all()
    courses = Course.query.order_by(Course.course_code).all()
    return render_template(
        "grades/form.html",
        form=request.form if request.method == "POST" else None,
        errors=errors if request.method == "POST" else {},
        item=None,
        students=students,
        courses=courses,
        semesters=semester_choices(),
    )


@bp.route("/grades/<int:gid>/edit", methods=["GET", "POST"])
@login_required
def edit_grade(gid: int):
    grade = Grade.query.get_or_404(gid)

    if request.method == "POST":
        errors, data = validate_grade(request.form)
        if not errors:
            exists = Grade.query.filter(
                Grade.student_id == data["student_id"],
                Grade.course_id == data["course_id"],
                Grade.id != gid,
            ).first()
            if exists:
                errors["course_id"] = "برای این دانشجو در این درس قبلاً نمره ثبت شده است."
        if not errors:
            grade.student_id = data["student_id"]
            grade.course_id = data["course_id"]
            grade.score = data["score"]
            grade.semester = data["semester"]
            db.session.commit()
            flash("نمره با موفقیت به‌روزرسانی شد.", "success")
            return redirect(url_for("grades.list_grades"))
        flash("به‌روزرسانی انجام نشد؛ خطاهای فرم را برطرف کنید.", "danger")
        return render_template(
            "grades/form.html",
            form=request.form,
            errors=errors,
            item=grade,
            students=Student.query.order_by(Student.student_number).all(),
            courses=Course.query.order_by(Course.course_code).all(),
            semesters=semester_choices(),
        )

    return render_template(
        "grades/form.html",
        form=None,
        errors={},
        item=grade,
        students=Student.query.order_by(Student.student_number).all(),
        courses=Course.query.order_by(Course.course_code).all(),
        semesters=semester_choices(),
    )


@bp.route("/grades/<int:gid>/delete", methods=["POST"])
@login_required
def delete_grade(gid: int):
    grade = Grade.query.get_or_404(gid)
    db.session.delete(grade)
    db.session.commit()
    flash("نمره با موفقیت حذف شد.", "success")
    return redirect(url_for("grades.list_grades"))
