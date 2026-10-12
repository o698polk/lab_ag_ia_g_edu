from datetime import datetime

from app.extensions import db


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    student_code = db.Column(db.String(50), unique=True, nullable=False)
    document_id = db.Column(db.String(50))
    phone = db.Column(db.String(30))
    address = db.Column(db.String(255))
    birth_date = db.Column(db.Date, nullable=True)
    career_id = db.Column(db.Integer, db.ForeignKey("careers.id"), nullable=True)
    guardian_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    guardian_name = db.Column(db.String(150))
    guardian_phone = db.Column(db.String(30))
    status = db.Column(db.String(30), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", foreign_keys=[user_id], back_populates="student")
    guardian = db.relationship("User", foreign_keys=[guardian_user_id])
    career = db.relationship("Career", back_populates="students")
    enrollments = db.relationship("Enrollment", back_populates="student")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "student_code": self.student_code,
            "document_id": self.document_id,
            "phone": self.phone,
            "address": self.address,
            "birth_date": self.birth_date.isoformat() if self.birth_date else None,
            "career_id": self.career_id,
            "career_name": self.career.name if self.career else None,
            "guardian_user_id": self.guardian_user_id,
            "guardian_name": self.guardian_name,
            "guardian_phone": self.guardian_phone,
            "status": self.status,
            "full_name": self.user.full_name if self.user else None,
            "first_name": self.user.first_name if self.user else None,
            "last_name": self.user.last_name if self.user else None,
            "email": self.user.email if self.user else None,
        }


class Teacher(db.Model):
    __tablename__ = "teachers"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    teacher_code = db.Column(db.String(50), unique=True, nullable=False)
    document_id = db.Column(db.String(50))
    phone = db.Column(db.String(30))
    specialty = db.Column(db.String(150))
    title = db.Column(db.String(150))
    status = db.Column(db.String(30), default="active")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", foreign_keys=[user_id], back_populates="teacher")
    assignments = db.relationship("Assignment", back_populates="teacher")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "teacher_code": self.teacher_code,
            "document_id": self.document_id,
            "phone": self.phone,
            "specialty": self.specialty,
            "title": self.title,
            "status": self.status,
            "full_name": self.user.full_name if self.user else None,
            "first_name": self.user.first_name if self.user else None,
            "last_name": self.user.last_name if self.user else None,
            "email": self.user.email if self.user else None,
        }
