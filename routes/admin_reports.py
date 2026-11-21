
from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from functools import wraps
from datetime import datetime, timedelta

from models.subject import Subject
from models.student import Student
from models.course import Course
from models.enrollment import Enrollment
from models.attendance import Attendance, AttendanceSession
from models.user import User


admin_reports_bp = Blueprint(
    "admin_reports",
    __name__,
    url_prefix="/admin/reports"
)


def admin_required(function):
    @wraps(function)
    @login_required
    def wrapper(*args, **kwargs):
        if current_user.role != "admin":
            return "Access Denied", 403
        return function(*args, **kwargs)
    return wrapper


@admin_reports_bp.route("/attendance")
@admin_required
def attendance_report():

    subject_id = request.args.get("subject_id", type=int)
    teacher_id = request.args.get("teacher_id", type=int)
    course = request.args.get("course", "").strip()
    semester = request.args.get("semester", "").strip()
    date_filter = request.args.get("date", "").strip()

    subjects = Subject.query.order_by(Subject.subject_name).all()
    teachers = User.query.filter_by(role="teacher").order_by(User.name).all()
    courses = Course.query.order_by(Course.course_name).all()

    semesters = [
        "1st", "2nd", "3rd", "4th",
        "5th", "6th", "7th", "8th"
    ]

    query = AttendanceSession.query

    if subject_id:
        query = query.filter(
            AttendanceSession.subject_id == subject_id
        )

    if teacher_id:
        query = query.filter(
            AttendanceSession.teacher_id == teacher_id
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

        session_present = sum(
            1 for student in students
            if student.id in present_ids
        )

        reports.append({
            "session": session,
            "subject": session.subject,
            "teacher": session.teacher,
            "students": student_rows,
            "total_students": len(students),
            "present": session_present,
            "absent": len(students) - session_present
        })

    total_students = total_present + total_absent

    percentage = (
        round((total_present / total_students) * 100, 2)
        if total_students > 0 else 0
    )

    return render_template(
        "admin_attendance_report.html",
        subjects=subjects,
        teachers=teachers,
        courses=courses,
        semesters=semesters,
        reports=reports,
        total_present=total_present,
        total_absent=total_absent,
        total_students=total_students,
        percentage=percentage,
        selected_subject=subject_id,
        selected_teacher=teacher_id,
        selected_course=course,
        selected_semester=semester,
        selected_date=date_filter
    )
