
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps

from extensions import db
from models.student import Student
from models.subject import Subject
from models.enrollment import Enrollment

enrollment_bp = Blueprint(
    "enrollment",
    __name__,
    url_prefix="/admin/enrollments"
)


def admin_required(function):
    @wraps(function)
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.role != "admin":
            return "Access Denied", 403
        return function(*args, **kwargs)
    return wrapper


# View all enrollments
@enrollment_bp.route("/")
@admin_required
def enrollment_list():
    enrollments = Enrollment.query.all()

    return render_template(
        "enrollments.html",
        enrollments=enrollments
    )


# Add student enrollment
@enrollment_bp.route("/add", methods=["GET", "POST"])
@admin_required
def add_enrollment():

    students = Student.query.all()
    subjects = Subject.query.all()

    if request.method == "POST":

        student_id = request.form.get("student_id")
        subject_id = request.form.get("subject_id")

        if not student_id or not subject_id:
            flash("Please select both student and subject!", "error")

            return render_template(
                "add_enrollment.html",
                students=students,
                subjects=subjects
            )

        enrollment = Enrollment.query.filter_by(
            student_id=student_id,
            subject_id=subject_id
        ).first()

        if enrollment:
            flash("Student is already enrolled in this subject!", "error")

            return render_template(
                "add_enrollment.html",
                students=students,
                subjects=subjects
            )

        new_enrollment = Enrollment(
            student_id=int(student_id),
            subject_id=int(subject_id)
        )

        db.session.add(new_enrollment)
        db.session.commit()

        flash("Student enrolled successfully!", "success")

        return redirect(url_for("enrollment.enrollment_list"))

    return render_template(
        "add_enrollment.html",
        students=students,
        subjects=subjects
    )


# Delete enrollment
@enrollment_bp.route("/delete/<int:id>", methods=["POST"])
@admin_required
def delete_enrollment(id):

    enrollment = db.session.get(Enrollment, id)

    if enrollment:
        db.session.delete(enrollment)
        db.session.commit()

        flash("Enrollment deleted successfully!", "success")

    return redirect(url_for("enrollment.enrollment_list"))
