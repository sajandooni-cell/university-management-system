"""داشبورد آماری"""
from flask import Blueprint, render_template

from ..models import Course, Grade, Student, Teacher
from ..utils import login_required

bp = Blueprint("dashboard", __name__)


@bp.route("/")
@login_required
def index():
    students = Student.query.all()
    gpas = [(s, s.gpa) for s in students]
    valid_gpas = [g for _, g in gpas if g is not None]
    avg_gpa = round(sum(valid_gpas) / len(valid_gpas), 2) if valid_gpas else None

    recent_grades = (
        Grade.query.order_by(Grade.created_at.desc(), Grade.id.desc())
        .limit(6)
        .all()
    )

    top_students = sorted(
        ((s, g) for s, g in gpas if g is not None),
        key=lambda pair: pair[1],
        reverse=True,
    )[:5]

    stats = {
        "students": Student.query.count(),
        "teachers": Teacher.query.count(),
        "courses": Course.query.count(),
        "grades": Grade.query.count(),
        "avg_gpa": avg_gpa,
    }

    return render_template(
        "dashboard.html",
        stats=stats,
        recent_grades=recent_grades,
        top_students=top_students,
    )
