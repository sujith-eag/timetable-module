"""
Stage 6: Enriched Timetable Models

This module defines Pydantic models for the final enriched timetable output,
including detailed session information, analysis reports, and human-readable views.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator


class EnrichedSessionMetadata(BaseModel):
    """Metadata for the enriched timetable."""
    generated_at: datetime = Field(..., alias="generatedAt")
    generator: str
    version: str
    source_file: str = Field(..., alias="sourceFile")
    total_sessions: int = Field(..., alias="totalSessions")
    description: str
    last_updated: Optional[datetime] = Field(None, alias="lastUpdated")
    updated_by: Optional[str] = Field(None, alias="updatedBy")


class SupportingStaff(BaseModel):
    """Information about supporting staff for a session."""
    id: str
    name: str


class EnrichedSession(BaseModel):
    """A fully enriched session with all detailed information."""
    session_id: str = Field(..., alias="sessionId")
    day: str
    slot_id: str = Field(..., alias="slotId")
    start_time: str = Field(..., alias="startTime")
    end_time: str = Field(..., alias="endTime")
    room_id: str = Field(..., alias="roomId")
    subject_code: str = Field(..., alias="subjectCode")
    subject_title: str = Field(..., alias="subjectTitle")
    component_type: str = Field(..., alias="componentType")  # theory, practical, tutorial
    faculty_id: str = Field(..., alias="facultyId")
    faculty_name: str = Field(..., alias="facultyName")
    student_group_ids: List[str] = Field(..., alias="studentGroupIds")
    semester: int
    sections: List[str]
    supporting_staff: List[SupportingStaff] = Field(..., alias="supportingStaff")
    short_code: str = Field(..., alias="shortCode")

    @field_validator('day')
    @classmethod
    def validate_day(cls, v):
        valid_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        if v not in valid_days:
            raise ValueError(f'Day must be one of {valid_days}, got {v}')
        return v

    @field_validator('component_type')
    @classmethod
    def validate_component_type(cls, v):
        valid_types = ['theory', 'practical', 'tutorial']
        if v not in valid_types:
            raise ValueError(f'Component type must be one of {valid_types}, got {v}')
        return v

    @field_validator('slot_id')
    @classmethod
    def validate_slot_id(cls, v):
        # Allow single slots (S1-S7) and double slots (S1+S2, S3+S4, etc.)
        import re
        if not re.match(r'^S\d+(?:\+S\d+)?$', v):
            raise ValueError(f'Slot ID must be in format S<num> or S<num>+S<num>, got {v}')
        return v


class EnrichedTimetable(BaseModel):
    """The complete enriched timetable with metadata and sessions."""
    metadata: EnrichedSessionMetadata
    timetable_a: List[EnrichedSession] = Field(..., alias="timetable_A")

    @field_validator('timetable_a')
    @classmethod
    def validate_session_count(cls, v):
        if len(v) == 0:
            raise ValueError('Timetable must contain at least one session')
        return v