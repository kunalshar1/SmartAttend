
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from functools import wraps

from extensions import db
from models.student import Student
from models.course import Course
from models.enrollment import Enrollment
from models.attendance import Attendance

student_bp = Blueprint("student", __name__, url_prefix="/admin/students")


def admin_required(function):
    @wraps(function)
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.role != "admin":
            return "Access Denied", 403
        return function(*args, **kwargs)
    return wrapper


@student_bp.route("/")
@admin_required
def student_list():
    students = Student.query.all()
    return render_template("students.html", students=students)


@student_bp.route("/add", methods=["GET", "POST"])
@admin_required
def add_student():

    courses = Course.query.order_by(Course.course_name).all()

    if request.method == "POST":
        student = Student(
            name=request.form.get("name", "").strip(),
            roll_number=request.form.get("roll_number", "").strip(),
            email=request.form.get("email", "").strip().lower(),
            course=request.form.get("course", "").strip(),
            semester=request.form.get("semester", "").strip()
        )

        db.session.add(student)

        try:
            db.session.commit()
            flash("Student added successfully!", "success")
            return redirect(url_for("student.student_list"))

        except IntegrityError:
            db.session.rollback()
            flash("Roll number or email already exists!", "error")

    return render_template("add_student.html", courses=courses)


@student_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_student(id):

    student = db.session.get(Student, id)

    if not student:
        flash("Student not found!", "error")
        return redirect(url_for("student.student_list"))

    courses = Course.query.order_by(Course.course_name).all()

    if request.method == "POST":
        student.name = request.form.get("name", "").strip()
        student.roll_number = request.form.get("roll_number", "").strip()
        student.email = request.form.get("email", "").strip().lower()
        student.course = request.form.get("course", "").strip()
        student.semester = request.form.get("semester", "").strip()

        try:
            db.session.commit()
            flash("Student updated successfully!", "success")
            return redirect(url_for("student.student_list"))

        except IntegrityError:
            db.session.rollback()
            flash("Roll number or email already exists!", "error")

    return render_template(
        "edit_student.html",
        student=student,
        courses=courses
    )


@student_bp.route("/delete/<int:id>", methods=["POST"])
@admin_required
def delete_student(id):

    student = db.session.get(Student, id)

    if not student:
        flash("Student not found!", "error")
        return redirect(url_for("student.student_list"))

    try:
        # Delete attendance records first
        Attendance.query.filter_by(
            student_id=student.id
        ).delete(synchronize_session=False)

        # Delete enrollment records
        Enrollment.query.filter_by(
            student_id=student.id
        ).delete(synchronize_session=False)

        # Delete student
        db.session.delete(student)

        db.session.commit()

        flash("Student and related records deleted successfully!", "success")

    except Exception:
        db.session.rollback()
        flash("Unable to delete student. Please try again.", "error")

    return redirect(url_for("student.student_list"))
