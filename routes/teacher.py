
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy.exc import IntegrityError
from functools import wraps

from extensions import db
from models.user import User
from models.subject import Subject
from models.enrollment import Enrollment
from models.student import Student
from models.course import Course
from models.attendance import Attendance, AttendanceSession
from datetime import datetime, timedelta


teacher_bp = Blueprint(
    "teacher",
    __name__,
    url_prefix="/admin/teachers"
)


def admin_required(function):
    @wraps(function)
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.role != "admin":
            return "Access Denied", 403
        return function(*args, **kwargs)
    return wrapper


# View all teachers
@teacher_bp.route("/")
@admin_required
def teacher_list():
    teachers = User.query.filter_by(role="teacher").all()
    return render_template("teachers.html", teachers=teachers)


# Add teacher
@teacher_bp.route("/add", methods=["GET", "POST"])
@admin_required
def add_teacher():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            flash("All fields are required!", "error")
            return render_template("add_teacher.html")

        teacher = User(
            name=name,
            email=email,
            role="teacher"
        )

        teacher.set_password(password)
        db.session.add(teacher)

        try:
            db.session.commit()
            flash("Teacher added successfully!", "success")
            return redirect(url_for("teacher.teacher_list"))

        except IntegrityError:
            db.session.rollback()
            flash("Email already registered!", "error")

    return render_template("add_teacher.html")


# Edit teacher
@teacher_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@admin_required
def edit_teacher(id):
    teacher = User.query.filter_by(
        id=id,
        role="teacher"
    ).first()

    if not teacher:
        flash("Teacher not found!", "error")
        return redirect(url_for("teacher.teacher_list"))

    if request.method == "POST":
        teacher.name = request.form.get("name", "").strip()
        teacher.email = request.form.get("email", "").strip().lower()

        if not teacher.name or not teacher.email:
            flash("Name and email are required!", "error")
            return render_template("edit_teacher.html", teacher=teacher)

        try:
            db.session.commit()
            flash("Teacher updated successfully!", "success")
            return redirect(url_for("teacher.teacher_list"))

        except IntegrityError:
            db.session.rollback()
            flash("Email already registered!", "error")

    return render_template("edit_teacher.html", teacher=teacher)


# Delete teacher
@teacher_bp.route("/delete/<int:id>", methods=["POST"])
@admin_required
def delete_teacher(id):
    teacher = User.query.filter_by(
        id=id,
        role="teacher"
    ).first()

    if teacher:
        db.session.delete(teacher)
        db.session.commit()
        flash("Teacher deleted successfully!", "success")

    return redirect(url_for("teacher.teacher_list"))


# Teacher - View My Assigned Subjects
@teacher_bp.route("/my-subjects")
@login_required
def my_subjects():
    if current_user.role != "teacher":
        return "Access Denied", 403

    subjects = Subject.query.filter_by(
        teacher_id=current_user.id
    ).all()

    return render_template(
        "my_subjects.html",
        subjects=subjects
    )


# Teacher - View Enrolled Students
@teacher_bp.route("/student-records")
@login_required
def student_records():

    if current_user.role != "teacher":
        return "Access Denied", 403

    enrollments = (
        Enrollment.query
        .join(Subject)
        .filter(Subject.teacher_id == current_user.id)
        .all()
    )

    course_groups = {}

    for enrollment in enrollments:
        student = enrollment.student

        course_name = student.course or "Other"
        semester_name = student.semester or "Not Specified"

        group_key = (course_name, semester_name)

        if group_key not in course_groups:
            course_groups[group_key] = []

        course_groups[group_key].append(enrollment)

    return render_template(
        "student_records.html",
        course_groups=course_groups
    )


# Teacher - Attendance Records and Reports
@teacher_bp.route("/attendance-records")
@login_required
def attendance_records():

    if current_user.role != "teacher":
        return "Access Denied", 403

    subject_id = request.args.get("subject_id", type=int)
    course = request.args.get("course", "").strip()
    semester = request.args.get("semester", "").strip()
    date_filter = request.args.get("date", "").strip()

    # Get only subjects assigned to this teacher
    subjects = Subject.query.filter_by(
        teacher_id=current_user.id
    ).all()

    # Get courses from Course Management
    courses = Course.query.order_by(
        Course.course_name
    ).all()

    # Semester options
    semesters = [
        "1st", "2nd", "3rd", "4th",
        "5th", "6th", "7th", "8th"
    ]

    # Get this teacher's attendance sessions
    query = AttendanceSession.query.filter_by(
        teacher_id=current_user.id
    )

    if subject_id:
        query = query.filter(
            AttendanceSession.subject_id == subject_id
        )

    if course:
        query = query.filter(
            AttendanceSession.course == course
        )

    if semester:
        query = query.filter(
            AttendanceSession.semester == semester
        )

    if date_filter:
        try:
            selected_date = datetime.strptime(
                date_filter, "%Y-%m-%d"
            )

            next_date = selected_date + timedelta(days=1)

            query = query.filter(
                AttendanceSession.created_at >= selected_date,
                AttendanceSession.created_at < next_date
            )

        except ValueError:
            date_filter = ""

    sessions = query.order_by(
        AttendanceSession.created_at.desc()
    ).all()

    reports = []

    total_present = 0
    total_absent = 0

    for session in sessions:

        # Find students enrolled in this subject,
        # course and semester
        students = (
            Student.query
            .join(Enrollment)
            .filter(
                Enrollment.subject_id == session.subject_id,
                Student.course == session.course,
                Student.semester == session.semester
            )
            .order_by(Student.roll_number)
            .all()
        )

        attendance_records = Attendance.query.filter_by(
            session_id=session.id
        ).all()

        present_ids = {
            record.student_id
            for record in attendance_records
            if record.status == "Present"
        }

        student_rows = []

        for student in students:

            is_present = student.id in present_ids

            student_rows.append({
                "student": student,
                "status": "Present" if is_present else "Absent"
            })

            if is_present:
                total_present += 1
            else:
                total_absent += 1

        reports.append({
            "session": session,
            "subject": session.subject,
            "students": student_rows,
            "total_students": len(students),
            "present": len(present_ids),
            "absent": len(students) - len(present_ids)
        })

    total = total_present + total_absent

    percentage = (
        round((total_present / total) * 100, 2)
        if total > 0 else 0
    )

    return render_template(
        "attendance_records.html",
        subjects=subjects,
        courses=courses,
        semesters=semesters,
        reports=reports,
        total_present=total_present,
        total_absent=total_absent,
        total_students=total,
        percentage=percentage,
        selected_subject=subject_id,
        selected_course=course,
        selected_semester=semester,
        selected_date=date_filter
    )
