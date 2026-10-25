"""مدیریت دانشجویان: لیست، جستجو، صف‌بندی، افزودن، ویرایش، حذف، خروجی CSV، کارنامه"""
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from sqlalchemy import or_

from ..forms import validate_student
from ..models import db, Student
from ..utils import STATUS_LABELS, csv_response, login_required

bp = Blueprint("students", __name__)


def _filtered_query(q: str, status: str):
    query = Student.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Student.first_name.ilike(like),
                Student.last_name.ilike(like),
                Student.student_number.ilike(like),
                Student.national_id.ilike(like),
                Student.major.ilike(like),
            )
        )
    if status:
        query = query.filter(Student.status == status)
    return query.order_by(Student.student_number.asc())


@bp.route("/students")
@login_required
def list_students():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    page = max(request.args.get("page", 1, type=int) or 1, 1)
    per_page = current_app.config.get("PER_PAGE", 10)

    pagination = _filtered_query(q, status).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return render_template(
        "students/list.html",
        pagination=pagination,
        q=q,
        status=status,
        status_labels=STATUS_LABELS,
    )


@bp.route("/students/export")
@login_required
def export_students():
    q = request.args.get("q", "").strip()
    status = request.args.get("status", "").strip()
    students = _filtered_query(q, status).all()

    rows = [
        [
            s.student_number,
            s.first_name,
            s.last_name,
            s.national_id or "",
            s.phone or "",
            s.email or "",
            s.major or "",
            s.entry_year or "",
            STATUS_LABELS.get(s.status, s.status),
            s.gpa if s.gpa is not None else "",
        ]
        for s in students
    ]
    headers = [
        "شماره دانشجویی", "نام", "نام خانوادگی", "کد ملی", "موبایل",
        "ایمیل", "رشته تحصیلی", "سال ورود", "وضعیت", "معدل",
    ]
    return csv_response(rows, headers, filename="students.csv")


@bp.route("/students/add", methods=["GET", "POST"])
@login_required
def add_student():
    if request.method == "POST":
        errors, data = validate_student(request.form)
        if not errors:
            if Student.query.filter_by(student_number=data["student_number"]).first():
                errors["student_number"] = "این شماره دانشجویی قبلاً ثبت شده است."
            elif data["national_id"] and Student.query.filter_by(national_id=data["national_id"]).first():
                errors["national_id"] = "این کد ملی قبلاً ثبت شده است."
        if not errors:
            student = Student(**data)
            db.session.add(student)
            db.session.commit()
            flash(f"دانشجوی «{student.full_name}» با موفقیت ثبت شد.", "success")
            return redirect(url_for("students.list_students"))
        flash("ذخیره انجام نشد؛ خطاهای فرم را برطرف کنید.", "danger")
        return render_template("students/form.html", form=request.form, errors=errors, item=None)

    return render_template("students/form.html", form=None, errors={}, item=None)


@bp.route("/students/<int:sid>/edit", methods=["GET", "POST"])
@login_required
def edit_student(sid: int):
    student = Student.query.get_or_404(sid)

    if request.method == "POST":
        errors, data = validate_student(request.form)
        if not errors:
            dup_number = Student.query.filter(
                Student.student_number == data["student_number"], Student.id != sid
            ).first()
            dup_national = None
            if data["national_id"]:
                dup_national = Student.query.filter(
                    Student.national_id == data["national_id"], Student.id != sid
                ).first()
            if dup_number:
                errors["student_number"] = "این شماره دانشجویی برای دانشجوی دیگری ثبت شده است."
            elif dup_national:
                errors["national_id"] = "این کد ملی برای دانشجوی دیگری ثبت شده است."
        if not errors:
            for key, value in data.items():
                setattr(student, key, value)
            db.session.commit()
            flash(f"اطلاعات «{student.full_name}» با موفقیت به‌روزرسانی شد.", "success")
            return redirect(url_for("students.list_students"))
        flash("به‌روزرسانی انجام نشد؛ خطاهای فرم را برطرف کنید.", "danger")
        return render_template("students/form.html", form=request.form, errors=errors, item=student)

    return render_template("students/form.html", form=None, errors={}, item=student)


@bp.route("/students/<int:sid>/delete", methods=["POST"])
@login_required
def delete_student(sid: int):
    student = Student.query.get_or_404(sid)
    name = student.full_name
    db.session.delete(student)
    db.session.commit()
    flash(f"دانشجوی «{name}» و تمام نمرات او حذف شد.", "success")
    return redirect(url_for("students.list_students"))


@bp.route("/students/<int:sid>/transcript")
@login_required
def transcript(sid: int):
    student = Student.query.get_or_404(sid)
    grades = sorted(
        student.grades,
        key=lambda g: (g.semester or "", g.course.title),
    )
    total_credits = sum(g.course.credits for g in grades)
    passed = [g for g in grades if g.score >= 10]
    return render_template(
        "students/transcript.html",
        student=student,
        grades=grades,
        total_credits=total_credits,
        passed_count=len(passed),
    )
