"""
Stage 5 Models - AI Schedule Output

This module defines Pydantic models for the AI-generated schedule output.
The AI solver takes Stage 4 scheduling input and produces a minimal schedule
that assigns each required session to a day, time slot, and room.
"""

from datetime import datetime
from typing import List
from pydantic import BaseModel, Field, field_validator


class ScheduleMetadata(BaseModel):
    """Metadata for the AI-generated schedule."""

    generated_at: datetime = Field(alias="generatedAt")
    generator: str
    version: str
    total_sessions: int = Field(alias="totalSessions")
    description: str


class ScheduledSession(BaseModel):
    """A single scheduled session in the AI-generated timetable."""

    assignment_id: str = Field(alias="assignmentId")
    session_number: int = Field(alias="sessionNumber")
    day: str
    slot_id: str = Field(alias="slotId")
    room_id: str = Field(alias="roomId")

    @field_validator('day')
    @classmethod
    def validate_day(cls, v):
        valid_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        if v not in valid_days:
            raise ValueError(f'Day must be one of {valid_days}')
        return v

    @field_validator('slot_id')
    @classmethod
    def validate_slot_id(cls, v):
        """Validate slot ID format (single: S1, double: S1+S2)."""
        if not v:
            raise ValueError('Slot ID cannot be empty')

        # Check for valid single slot format (S followed by number)
        if '+' not in v:
            if not (v.startswith('S') and v[1:].isdigit()):
                raise ValueError('Single slot ID must be in format S<number>')
        else:
            # Check for valid double slot format (S1+S2)
            parts = v.split('+')
            if len(parts) != 2:
                raise ValueError('Double slot ID must be in format S<number>+S<number>')

            for part in parts:
                if not (part.startswith('S') and part[1:].isdigit()):
                    raise ValueError('Each slot in double slot ID must be in format S<number>')

        return v


class AISchedule(BaseModel):
    """Root model for AI-generated schedule output."""

    metadata: ScheduleMetadata
    schedule: List[ScheduledSession]

    @field_validator('schedule')
    @classmethod
    def validate_schedule(cls, v):
        if not v:
            raise ValueError('Schedule must contain at least one session')
        return v