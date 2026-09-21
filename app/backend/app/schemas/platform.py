# Ref: BL-O5-* | Skill: K-013/K-023 | Fase: F6
"""Schemas for dashboard, reports, notifications, user history."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DashboardOut(BaseModel):
    role_view: str
    indicators: Dict[str, Any]


class ReportGenerateIn(BaseModel):
    report_type: str = Field(
        description="students|teachers|enrollments|attendance|grades|averages|failure|kardex|teacher_load|term_academic|career"
    )
    format: str = Field(default="JSON", description="HTML|CSV|JSON")
    parameters: Optional[Dict[str, Any]] = None


class ReportGenerateOut(BaseModel):
    log_id: int
    report_type: str
    format: str
    result_status: str
    row_count: int
    content: str


class ReportLogOut(BaseModel):
    id: int
    user_id: int
    report_type: str
    format: str
    result_status: str
    row_count: int
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationCreate(BaseModel):
    user_id: int
    type: str = Field(description="INFO|WARNING|SUCCESS|ALERT|SECURITY|ACADEMIC")
    title: str
    body: Optional[str] = None


class NotificationOut(BaseModel):
    id: int
    user_id: int
    type: str
    title: str
    body: Optional[str] = None
    read_flag: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserHistoryOut(BaseModel):
    id: int
    user_id: int
    action: str
    module: str
    summary: str
    metadata_json: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReportCatalogOut(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
