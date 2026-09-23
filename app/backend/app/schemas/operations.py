# Ref: BL-O3-* | Skill: K-013/K-017 | Fase: F6
"""Schemas for academic operations."""

from datetime import datetime, time
from typing import Optional

from pydantic import BaseModel, Field


class CourseCreate(BaseModel):
    subject_id: int
    term_id: int
    parallel_code: str = "A"
    capacity: int = Field(default=40, ge=1)
    hours_theory: int = Field(default=0, ge=0)
    hours_practical: int = Field(default=0, ge=0)
    hours_autonomous: int = Field(default=0, ge=0)
    teacher_id: Optional[int] = None


class CourseUpdate(BaseModel):
    parallel_code: Optional[str] = None
    capacity: Optional[int] = Field(default=None, ge=1)
    hours_theory: Optional[int] = Field(default=None, ge=0)
    hours_practical: Optional[int] = Field(default=None, ge=0)
    hours_autonomous: Optional[int] = Field(default=None, ge=0)
    status: Optional[str] = None
    teacher_id: Optional[int] = None


class CourseOut(BaseModel):
    id: int
    subject_id: int
    term_id: int
    parallel_code: str
    capacity: int
    hours_theory: int = 0
    hours_practical: int = 0
    hours_autonomous: int = 0
    status: str
    teacher_id: Optional[int] = None
    hours_total: int = 0
    hours_attendable: int = 0
    course_name: str = ""
    subject_name: str = ""
    subject_code: str = ""
    term_name: str = ""
    term_code: str = ""
    teacher_name: str = ""

    model_config = {"from_attributes": True}


class CourseRosterStudent(BaseModel):
    student_id: int
    student_code: str
    name: str
    enrollment_id: int
    status: str


class AssignmentCreate(BaseModel):
    teacher_id: int
    course_id: int
    term_id: int


class AssignmentOut(BaseModel):
    id: int
    teacher_id: int
    course_id: int
    term_id: int
    status: str
    teacher_name: str = ""
    course_name: str = ""
    subject_name: str = ""
    term_name: str = ""

    model_config = {"from_attributes": True}


class EnrollmentCreate(BaseModel):
    student_id: int
    course_id: int
    term_id: int


class EnrollmentBulk(BaseModel):
    course_id: int
    term_id: int
    student_ids: list[int] = Field(default_factory=list)


class EnrollmentOut(BaseModel):
    id: int
    student_id: int
    course_id: int
    term_id: int
    status: str
    enrolled_at: Optional[datetime] = None
    student_name: str = ""
    course_name: str = ""
    subject_name: str = ""
    term_name: str = ""

    model_config = {"from_attributes": True}


class ClassroomCreate(BaseModel):
    code: str
    name: str
    capacity: int = 40


class ClassroomOut(BaseModel):
    id: int
    code: str
    name: str
    capacity: int

    model_config = {"from_attributes": True}


class ScheduleCreate(BaseModel):
    course_id: int
    teacher_id: int
    classroom_id: int
    term_id: int
    day_of_week: str
    start_time: time
    end_time: time


class ScheduleOut(BaseModel):
    id: int
    course_id: int
    teacher_id: int
    classroom_id: int
    term_id: int
    day_of_week: str
    start_time: time
    end_time: time

    model_config = {"from_attributes": True}


class AbacCheckOut(BaseModel):
    teaching_assignment_exists: bool
    teacher_id: int
    course_id: int
    term_id: int
