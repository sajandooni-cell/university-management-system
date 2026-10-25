"""ورود و خروج مدیر"""
from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..models import Admin
from ..utils import login_required

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_id"):
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session.clear()
            session["admin_id"] = admin.id
            session["admin_username"] = admin.username
            flash(f"خوش آمدید، {admin.username} عزیز! ورود با موفقیت انجام شد.", "success")
            return redirect(url_for("dashboard.index"))
        flash("نام کاربری یا رمز عبور اشتباه است.", "danger")

    return render_template("login.html")


@bp.route("/logout", methods=["POST"])
@login_required
def logout():
    session.clear()
    flash("از سامانه خارج شدید.", "success")
    return redirect(url_for("auth.login"))
