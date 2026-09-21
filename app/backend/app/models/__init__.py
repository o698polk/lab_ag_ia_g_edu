# Ref: BL-O1/O2/O3/O4/O5 | Skill: K-014 | Fase: F6
"""ORM models package."""

from app.models.iam import (
    Permission,
    RefreshToken,
    Role,
    RolePermission,
    SessionToken,
    User,
    UserRole,
)
from app.models.academic import (
    AcademicTerm,
    Career,
    Curriculum,
    CurriculumSubject,
    Student,
    Subject,
    SubjectPrerequisite,
    Teacher,
)
from app.models.operations import (
    Classroom,
    Course,
    Enrollment,
    Schedule,
    TeachingAssignment,
)
from app.models.evaluation import (
    AttendanceRecord,
    AttendanceSession,
    Evaluation,
    EvaluationType,
    Grade,
    KardexEntry,
)
from app.models.platform import (
    Notification,
    Report,
    ReportLog,
    UserHistoryEvent,
)

__all__ = [
    "User",
    "Role",
    "Permission",
    "UserRole",
    "RolePermission",
    "SessionToken",
    "RefreshToken",
    "Career",
    "Subject",
    "SubjectPrerequisite",
    "Curriculum",
    "CurriculumSubject",
    "AcademicTerm",
    "Student",
    "Teacher",
    "Course",
    "TeachingAssignment",
    "Enrollment",
    "Classroom",
    "Schedule",
    "AttendanceSession",
    "AttendanceRecord",
    "EvaluationType",
    "Evaluation",
    "Grade",
    "KardexEntry",
    "Report",
    "ReportLog",
    "Notification",
    "UserHistoryEvent",
]
