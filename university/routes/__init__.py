"""ثبت همه Blueprintها"""
from flask import Flask


def register_blueprints(app: Flask) -> None:
    from . import auth, dashboard, students, teachers, courses, grades

    for blueprint in (auth.bp, dashboard.bp, students.bp, teachers.bp, courses.bp, grades.bp):
        app.register_blueprint(blueprint)
