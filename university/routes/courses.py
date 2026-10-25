"""مدیریت دروس"""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from ..forms import semester_choices, validate_course
from ..models import Course, Teacher, db
from ..utils import login_required

bp = Blueprint("courses", __name__)


@bp.route("/courses")
@login_required
def list_courses():
    q = request.args.get("q", "").strip()
    page = max(request.args.get("page", 1, type=int) or 1, 1)
    per_page = 10

    query = Course.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            Course.title.ilike(like)
            | Course.course_code.ilike(like)
            | Course.semester.ilike(like)
        )
    pagination = query.order_by(Course.course_code.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return render_template("courses/list.html", pagination=pagination, q=q)


@bp.route("/courses/add", methods=["GET", "POST"])
@login_required
def add_course():
    if request.method == "POST":
        errors, data = validate_course(request.form)
        if not errors and Course.query.filter_by(course_code=data["course_code"]).first():
            errors["course_code"] = "این کد درس قبلاً ثبت شده است."
        if not errors:
            course = Course(**data)
            db.session.add(course)
            db.session.commit()
            flash(f"درس «{course.title}» با موفقیت ثبت شد.", "success")
            return redirect(url_for("courses.list_courses"))
        flash("ذخیره انجام نشد؛ خطاهای فرم را برطرف کنید.", "danger")
        return render_template(
            "courses/form.html",
            form=request.form,
            errors=errors,
            item=None,
            teachers=Teacher.query.order_by(Teacher.last_name).all(),
            semesters=semester_choices(),
        )

    return render_template(
        "courses/form.html",
        form=None,
        errors={},
        item=None,
        teachers=Teacher.query.order_by(Teacher.last_name).all(),
        semesters=semester_choices(),
    )


@bp.route("/courses/<int:cid>/edit", methods=["GET", "POST"])
@login_required
def edit_course(cid: int):
    course = Course.query.get_or_404(cid)

    if request.method == "POST":
        errors, data = validate_course(request.form)
        if not errors:
            dup = Course.query.filter(
                Course.course_code == data["course_code"], Course.id != cid
            ).first()
            if dup:
                errors["course_code"] = "این کد درس برای درس دیگری ثبت شده است."
        if not errors:
            for key, value in data.items():
                setattr(course, key, value)
            db.session.commit()
            flash(f"اطلاعات درس «{course.title}» با موفقیت به‌روزرسانی شد.", "success")
            return redirect(url_for("courses.list_courses"))
        flash("به‌روزرسانی انجام نشد؛ خطاهای فرم را برطرف کنید.", "danger")
        return render_template(
            "courses/form.html",
            form=request.form,
            errors=errors,
            item=course,
            teachers=Teacher.query.order_by(Teacher.last_name).all(),
            semesters=semester_choices(),
        )

    return render_template(
        "courses/form.html",
        form=None,
        errors={},
        item=course,
        teachers=Teacher.query.order_by(Teacher.last_name).all(),
        semesters=semester_choices(),
    )


@bp.route("/courses/<int:cid>/delete", methods=["POST"])
@login_required
def delete_course(cid: int):
    course = Course.query.get_or_404(cid)
    title = course.title
    db.session.delete(course)
    db.session.commit()
    flash(f"درس «{title}» و نمرات مرتبط با آن حذف شد.", "success")
    return redirect(url_for("courses.list_courses"))
