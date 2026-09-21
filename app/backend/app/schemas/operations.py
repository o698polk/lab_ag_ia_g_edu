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


class CourseOut(BaseModel):
    id: int
    subject_id: int
    term_id: int
    parallel_code: str
    capacity: int
    status: str

    model_config = {"from_attributes": True}


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

    model_config = {"from_attributes": True}


class EnrollmentCreate(BaseModel):
    student_id: int
    course_id: int
    term_id: int


class EnrollmentOut(BaseModel):
    id: int
    student_id: int
    course_id: int
    term_id: int
    status: str
    enrolled_at: Optional[datetime] = None

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
