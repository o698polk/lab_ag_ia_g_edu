from datetime import datetime

from app.extensions import db


class Career(db.Model):
    __tablename__ = "careers"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    duration_semesters = db.Column(db.Integer, default=8)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    students = db.relationship("Student", back_populates="career")
    subjects = db.relationship("Subject", back_populates="career")
    curriculum_items = db.relationship("Curriculum", back_populates="career")

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "duration_semesters": self.duration_semesters,
            "is_active": self.is_active,
        }


class Subject(db.Model):
    __tablename__ = "subjects"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    credits = db.Column(db.Integer, default=3)
    career_id = db.Column(db.Integer, db.ForeignKey("careers.id"), nullable=True)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    career = db.relationship("Career", back_populates="subjects")
    courses = db.relationship("Course", back_populates="subject")

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "credits": self.credits,
            "career_id": self.career_id,
            "career_name": self.career.name if self.career else None,
            "description": self.description,
            "is_active": self.is_active,
        }


class Curriculum(db.Model):
    __tablename__ = "curriculum"

    id = db.Column(db.Integer, primary_key=True)
    career_id = db.Column(db.Integer, db.ForeignKey("careers.id"), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    level = db.Column(db.Integer, nullable=False)
    prerequisite_subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    career = db.relationship("Career", back_populates="curriculum_items")
    subject = db.relationship("Subject", foreign_keys=[subject_id])
    prerequisite = db.relationship("Subject", foreign_keys=[prerequisite_subject_id])

    __table_args__ = (db.UniqueConstraint("career_id", "subject_id", name="uq_career_subject"),)

    def to_dict(self):
        return {
            "id": self.id,
            "career_id": self.career_id,
            "subject_id": self.subject_id,
            "subject_name": self.subject.name if self.subject else None,
            "level": self.level,
            "prerequisite_subject_id": self.prerequisite_subject_id,
        }


class Term(db.Model):
    __tablename__ = "terms"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    grades_closed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    courses = db.relationship("Course", back_populates="term")

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "is_active": self.is_active,
            "grades_closed": self.grades_closed,
        }


class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey("subjects.id"), nullable=False)
    term_id = db.Column(db.Integer, db.ForeignKey("terms.id"), nullable=False)
    career_id = db.Column(db.Integer, db.ForeignKey("careers.id"), nullable=True)
    parallel = db.Column(db.String(10), default="A")
    capacity = db.Column(db.Integer, default=40)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    subject = db.relationship("Subject", back_populates="courses")
    term = db.relationship("Term", back_populates="courses")
    career = db.relationship("Career")
    assignments = db.relationship("Assignment", back_populates="course")
    enrollments = db.relationship("Enrollment", back_populates="course")
    schedules = db.relationship("Schedule", back_populates="course")
    grades = db.relationship("Grade", back_populates="course")
    attendance_records = db.relationship("Attendance", back_populates="course")

    def to_dict(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "subject_id": self.subject_id,
            "subject_name": self.subject.name if self.subject else None,
            "term_id": self.term_id,
            "term_name": self.term.name if self.term else None,
            "career_id": self.career_id,
            "parallel": self.parallel,
            "capacity": self.capacity,
            "is_active": self.is_active,
        }


class Assignment(db.Model):
    __tablename__ = "assignments"

    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teachers.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    teacher = db.relationship("Teacher", back_populates="assignments")
    course = db.relationship("Course", back_populates="assignments")

    __table_args__ = (db.UniqueConstraint("teacher_id", "course_id", name="uq_teacher_course"),)

    def to_dict(self):
        return {
            "id": self.id,
            "teacher_id": self.teacher_id,
            "teacher_name": self.teacher.user.full_name if self.teacher and self.teacher.user else None,
            "course_id": self.course_id,
            "course_name": self.course.name if self.course else None,
        }


class Enrollment(db.Model):
    __tablename__ = "enrollments"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    status = db.Column(db.String(20), default="activa")  # activa, retirada, congelada
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student", back_populates="enrollments")
    course = db.relationship("Course", back_populates="enrollments")

    __table_args__ = (db.UniqueConstraint("student_id", "course_id", name="uq_student_course"),)

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student_name": self.student.user.full_name if self.student and self.student.user else None,
            "course_id": self.course_id,
            "course_name": self.course.name if self.course else None,
            "term_id": self.course.term_id if self.course else None,
            "career_id": self.course.career_id if self.course else None,
            "status": self.status,
            "enrolled_at": self.enrolled_at.isoformat() if self.enrolled_at else None,
        }


class Schedule(db.Model):
    __tablename__ = "schedules"

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Lunes ... 6=Domingo
    start_time = db.Column(db.String(5), nullable=False)  # HH:MM
    end_time = db.Column(db.String(5), nullable=False)
    classroom = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    course = db.relationship("Course", back_populates="schedules")

    def to_dict(self):
        days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        course = self.course
        return {
            "id": self.id,
            "course_id": self.course_id,
            "course_name": course.name if course else None,
            "course_code": course.code if course else None,
            "subject_name": course.subject.name if course and course.subject else None,
            "term_id": course.term_id if course else None,
            "term_name": course.term.name if course and course.term else None,
            "parallel": course.parallel if course else None,
            "day_of_week": self.day_of_week,
            "day_name": days[self.day_of_week] if 0 <= self.day_of_week <= 6 else None,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "classroom": self.classroom,
        }


class Grade(db.Model):
    __tablename__ = "grades"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    partial1 = db.Column(db.Float, nullable=True)
    partial2 = db.Column(db.Float, nullable=True)
    supplementary = db.Column(db.Float, nullable=True)
    final_grade = db.Column(db.Float, nullable=True)
    status = db.Column(db.String(20), default="en_curso")  # en_curso, aprobado, reprobado
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student")
    course = db.relationship("Course", back_populates="grades")

    __table_args__ = (db.UniqueConstraint("student_id", "course_id", name="uq_grade_student_course"),)

    def compute(self):
        if self.partial1 is not None and self.partial2 is not None:
            avg = (self.partial1 + self.partial2) / 2.0
            if avg < 7.0 and self.supplementary is not None:
                self.final_grade = self.supplementary
            else:
                self.final_grade = avg
            if self.final_grade is not None:
                self.status = "aprobado" if self.final_grade >= 7.0 else "reprobado"
        return self

    @property
    def average(self):
        if self.partial1 is not None and self.partial2 is not None:
            return round((self.partial1 + self.partial2) / 2.0, 2)
        return None

    @property
    def needs_supplementary(self):
        avg = self.average
        return avg is not None and avg < 7.0

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student_name": self.student.user.full_name if self.student and self.student.user else None,
            "course_id": self.course_id,
            "course_name": self.course.name if self.course else None,
            "term_id": self.course.term_id if self.course else None,
            "term_name": self.course.term.name if self.course and self.course.term else None,
            "career_id": self.course.career_id if self.course else None,
            "partial1": self.partial1,
            "partial2": self.partial2,
            "supplementary": self.supplementary,
            "average": self.average,
            "needs_supplementary": self.needs_supplementary,
            "final_grade": self.final_grade,
            "status": self.status,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("students.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    session_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # presente, ausente, tardanza, justificada
    notes = db.Column(db.String(255))
    recorded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship("Student")
    course = db.relationship("Course", back_populates="attendance_records")

    __table_args__ = (
        db.UniqueConstraint("student_id", "course_id", "session_date", name="uq_attendance_session"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "student_name": self.student.user.full_name if self.student and self.student.user else None,
            "course_id": self.course_id,
            "course_name": self.course.name if self.course else None,
            "term_id": self.course.term_id if self.course else None,
            "career_id": self.course.career_id if self.course else None,
            "session_date": self.session_date.isoformat() if self.session_date else None,
            "status": self.status,
            "notes": self.notes,
        }
