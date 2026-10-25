"""مدیریت اساتید"""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..forms import validate_teacher
from ..models import Course, Teacher, db
from ..utils import login_required

bp = Blueprint("teachers", __name__)


@bp.route("/teachers")
@login_required
def list_teachers():
    q = request.args.get("q", "").strip()
    page = max(request.args.get("page", 1, type=int) or 1, 1)
    per_page = 10

    query = Teacher.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            Teacher.first_name.ilike(like)
            | Teacher.last_name.ilike(like)
            | Teacher.teacher_number.ilike(like)
            | Teacher.department.ilike(like)
        )
    pagination = query.order_by(Teacher.teacher_number.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return render_template("teachers/list.html", pagination=pagination, q=q)


@bp.route("/teachers/add", methods=["GET", "POST"])
@login_required
def add_teacher():
    if request.method == "POST":
        errors, data = validate_teacher(request.form)
        if not errors and Teacher.query.filter_by(teacher_number=data["teacher_number"]).first():
            errors["teacher_number"] = "این شماره استادی قبلاً ثبت شده است."
        if not errors:
            teacher = Teacher(**data)
            db.session.add(teacher)
            db.session.commit()
            flash(f"استاد «{teacher.full_name}» با موفقیت ثبت شد.", "success")
            return redirect(url_for("teachers.list_teachers"))
        flash("ذخیره انجام نشد؛ خطاهای فرم را برطرف کنید.", "danger")
        return render_template("teachers/form.html", form=request.form, errors=errors, item=None)

    return render_template("teachers/form.html", form=None, errors={}, item=None)


@bp.route("/teachers/<int:tid>/edit", methods=["GET", "POST"])
@login_required
def edit_teacher(tid: int):
    teacher = Teacher.query.get_or_404(tid)

    if request.method == "POST":
        errors, data = validate_teacher(request.form)
        if not errors:
            dup = Teacher.query.filter(
                Teacher.teacher_number == data["teacher_number"], Teacher.id != tid
            ).first()
            if dup:
                errors["teacher_number"] = "این شماره استادی برای استاد دیگری ثبت شده است."
        if not errors:
            for key, value in data.items():
                setattr(teacher, key, value)
            db.session.commit()
            flash(f"اطلاعات «{teacher.full_name}» با موفقیت به‌روزرسانی شد.", "success")
            return redirect(url_for("teachers.list_teachers"))
        flash("به‌روزرسانی انجام نشد؛ خطاهای فرم را برطرف کنید.", "danger")
        return render_template("teachers/form.html", form=request.form, errors=errors, item=teacher)

    return render_template("teachers/form.html", form=None, errors={}, item=teacher)


@bp.route("/teachers/<int:tid>/delete", methods=["POST"])
@login_required
def delete_teacher(tid: int):
    teacher = Teacher.query.get_or_404(tid)
    name = teacher.full_name
    for course in teacher.courses:
        course.teacher_id = None
    db.session.delete(teacher)
    db.session.commit()
    flash(f"استاد «{name}» حذف شد؛ دروس او بدون استاد شدند.", "success")
    return redirect(url_for("teachers.list_teachers"))
