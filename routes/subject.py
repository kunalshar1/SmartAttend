
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from sqlalchemy.exc import IntegrityError

from extensions import db
from models.subject import Subject
from models.user import User
from models.course import Course

subject_bp = Blueprint(
    "subject",
    __name__,
    url_prefix="/admin/subjects"
)


def admin_required(function):
    @wraps(function)
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.role != "admin":
            return "Access Denied", 403
        return function(*args, **kwargs)
    return wrapper


# View all subjects
@subject_bp.route("/")
@admin_required
def subject_list():
    subjects = Subject.query.all()
    return render_template(
        "subjects.html",
        subjects=subjects
    )


# Add subject
@subject_bp.route("/add", methods=["GET", "POST"])
@admin_required
def add_subject():

    teachers = User.query.filter_by(role="teacher").all()
    courses = Course.query.order_by(Course.course_name).all()

    if request.method == "POST":
        teacher_id = request.form.get("teacher_id")

        subject = Subject(
            subject_name=request.form.get("subject_name", "").strip(),
            subject_code=request.form.get("subject_code", "").strip().upper(),
            course=request.form.get("course", "").strip(),
            semester=request.form.get("semester", "").strip(),
            teacher_id=int(teacher_id) if teacher_id else None
        )

        if not subject.subject_name or not subject.subject_code:
            flash("Subject name and code are required!", "error")
            return render_template(
                "add_subject.html",
                teachers=teachers,
                courses=courses
            )

        if subject.teacher_id and not User.query.filter_by(
            id=subject.teacher_id, role="teacher"
        ).first():
            flash("Invalid teacher selected!", "error")
            return render_template(
                "add_subject.html",
                teachers=teachers,
                courses=courses
            )

        db.session.add(subject)

        try:
            db.session.commit()
            flash("Subject added successfully!", "success")
            return redirect(url_for("subject.subject_list"))

        except IntegrityError:
            db.session.rollback()
            flash("Subject code already exists!", "error")

    return render_template(
        "add_subject.html",
        teachers=teachers,
        courses=courses
    )


# Edit subject
@subject_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_subject(id):

    subject = db.session.get(Subject, id)

    if not subject:
        flash("Subject not found!", "error")
        return redirect(url_for("subject.subject_list"))

    teachers = User.query.filter_by(role="teacher").all()
    courses = Course.query.order_by(Course.course_name).all()

    if request.method == "POST":
        subject.subject_name = request.form.get("subject_name", "").strip()
        subject.subject_code = request.form.get("subject_code", "").strip().upper()
        subject.course = request.form.get("course", "").strip()
        subject.semester = request.form.get("semester", "").strip()

        teacher_id = request.form.get("teacher_id")
        subject.teacher_id = int(teacher_id) if teacher_id else None

        if not subject.subject_name or not subject.subject_code:
            flash("Subject name and code are required!", "error")
            return render_template(
                "edit_subject.html",
                subject=subject,
                teachers=teachers,
                courses=courses
            )

        if subject.teacher_id and not User.query.filter_by(
            id=subject.teacher_id, role="teacher"
        ).first():
            flash("Invalid teacher selected!", "error")
            return render_template(
                "edit_subject.html",
                subject=subject,
                teachers=teachers,
                courses=courses
            )

        try:
            db.session.commit()
            flash("Subject updated successfully!", "success")
            return redirect(url_for("subject.subject_list"))

        except IntegrityError:
            db.session.rollback()
            flash("Subject code already exists!", "error")

    return render_template(
        "edit_subject.html",
        subject=subject,
        teachers=teachers,
        courses=courses
    )


# Delete subject
@subject_bp.route("/delete/<int:id>", methods=["POST"])
@admin_required
def delete_subject(id):
    subject = db.session.get(Subject, id)

    if subject:
        db.session.delete(subject)
        db.session.commit()
        flash("Subject deleted successfully!", "success")

    return redirect(url_for("subject.subject_list"))
