
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError

from extensions import db
from models.course import Course

course_bp = Blueprint(
    "course",
    __name__,
    url_prefix="/admin/courses"
)


@course_bp.route("/")
@login_required
def course_list():

    if current_user.role != "admin":
        return "Access Denied", 403

    courses = Course.query.order_by(Course.course_name).all()

    return render_template(
        "courses.html",
        courses=courses
    )


@course_bp.route("/add", methods=["GET", "POST"])
@login_required
def add_course():

    if current_user.role != "admin":
        return "Access Denied", 403

    if request.method == "POST":

        course_name = request.form.get(
            "course_name", ""
        ).strip()

        if not course_name:
            flash("Please enter a course name.", "error")
            return redirect(url_for("course.add_course"))

        course = Course(course_name=course_name)

        db.session.add(course)

        try:
            db.session.commit()
            flash("Course added successfully!", "success")
            return redirect(url_for("course.course_list"))

        except IntegrityError:
            db.session.rollback()
            flash("This course already exists.", "error")

    return render_template("add_course.html")


@course_bp.route("/delete/<int:id>", methods=["POST"])
@login_required
def delete_course(id):

    if current_user.role != "admin":
        return "Access Denied", 403

    course = db.session.get(Course, id)

    if course:
        db.session.delete(course)
        db.session.commit()
        flash("Course deleted successfully!", "success")

    return redirect(url_for("course.course_list"))

