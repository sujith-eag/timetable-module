"""
Stage 4 Models - Scheduling Input for AI Solver

This module defines Pydantic models for the scheduling input data structure
that serves as input to the AI timetable solver.
"""

from datetime import datetime
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field, field_validator


class SchedulingMetadata(BaseModel):
    """Metadata for the scheduling input."""

    generated_at: datetime = Field(alias="generatedAt")
    generator: str
    version: str
    total_assignments: int = Field(alias="totalAssignments")
    semester1_assignments: int = Field(alias="semester1Assignments")
    semester3_assignments: int = Field(alias="semester3Assignments")
    total_time_slots: int = Field(alias="totalTimeSlots")
    total_rooms: int = Field(alias="totalRooms")
    description: str


class SchedulingConfiguration(BaseModel):
    """Configuration settings for scheduling."""

    weekdays: List[str]
    day_start: str = Field(alias="dayStart")
    day_end: str = Field(alias="dayEnd")
    break_windows: List[Dict[str, str]] = Field(alias="breakWindows")
    session_types: Dict[str, Dict[str, Union[int, bool]]] = Field(alias="sessionTypes")
    resource_constraints: Dict[str, int] = Field(alias="resourceConstraints")


class TimeSlotInfo(BaseModel):
    """Information about a time slot."""

    slot_id: str = Field(alias="slotId")
    day: str
    start: str
    end: str
    duration_minutes: int = Field(alias="durationMinutes")

    @field_validator('day')
    @classmethod
    def validate_day(cls, v):
        valid_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        if v not in valid_days:
            raise ValueError(f'Day must be one of {valid_days}')
        return v


class SlotCombination(BaseModel):
    """A combination of time slots (single or double)."""

    slots: List[str]  # List of slot IDs
    type: str  # "single" or "double"
    duration_minutes: int = Field(alias="durationMinutes")

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        if v not in ['single', 'double']:
            raise ValueError('Type must be either "single" or "double"')
        return v


class StudentGroupInfo(BaseModel):
    """Information about a student group."""

    semester: int
    section: str
    student_count: int = Field(alias="studentCount")
    student_group_id: str = Field(alias="studentGroupId")
    compulsory_subjects: List[str] = Field(alias="compulsorySubjects")
    elective_subjects: Optional[List[str]] = Field(default=None, alias="electiveSubjects")


class RoomInfo(BaseModel):
    """Information about a room."""

    room_id: str = Field(alias="roomId")
    type: str  # "lecture", "lab", etc.
    capacity: int

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        valid_types = ['lecture', 'lab', 'tutorial', 'seminar']
        if v not in valid_types:
            raise ValueError(f'Room type must be one of {valid_types}')
        return v


class SchedulingConstraints(BaseModel):
    """Global scheduling constraints."""

    student_group_overlap: Dict[str, Dict[str, List[str]]] = Field(alias="studentGroupOverlap")
    faculty_list: List[str] = Field(alias="facultyList")
    student_group_list: List[str] = Field(alias="studentGroupList")
    hard_constraints: Dict[str, bool] = Field(alias="hardConstraints")
    soft_constraints: Dict[str, bool] = Field(alias="softConstraints")


class AssignmentConstraints(BaseModel):
    """Constraints specific to a teaching assignment."""

    student_group_conflicts: List[str] = Field(alias="studentGroupConflicts")
    faculty_conflicts: List[str] = Field(alias="facultyConflicts")
    fixed_day: Optional[str] = Field(alias="fixedDay")
    fixed_slot: Optional[str] = Field(alias="fixedSlot")
    must_be_in_room: Optional[str] = Field(alias="mustBeInRoom")


class SchedulingAssignment(BaseModel):
    """A teaching assignment to be scheduled."""

    assignment_id: str = Field(alias="assignmentId")
    subject_code: str = Field(alias="subjectCode")
    short_code: str = Field(alias="shortCode")
    subject_title: str = Field(alias="subjectTitle")
    component_type: str = Field(alias="componentType")
    semester: int
    faculty_id: str = Field(alias="facultyId")
    faculty_name: str = Field(alias="facultyName")
    student_group_ids: List[str] = Field(alias="studentGroupIds")
    sections: List[str]
    session_duration: int = Field(alias="sessionDuration")
    sessions_per_week: int = Field(alias="sessionsPerWeek")
    total_sessions_needed: int = Field(alias="totalSessionsNeeded")
    requires_room_type: str = Field(alias="requiresRoomType")
    preferred_rooms: List[str] = Field(alias="preferredRooms")
    requires_contiguous: bool = Field(alias="requiresContiguous")
    valid_slot_types: List[str] = Field(alias="validSlotTypes")
    priority: str
    is_elective: bool = Field(alias="isElective")
    constraints: AssignmentConstraints

    @field_validator('component_type')
    @classmethod
    def validate_component_type(cls, v):
        valid_types = ['theory', 'practical', 'tutorial']
        if v not in valid_types:
            raise ValueError(f'Component type must be one of {valid_types}')
        return v

    @field_validator('requires_room_type')
    @classmethod
    def validate_room_type(cls, v):
        valid_types = ['lecture', 'lab', 'tutorial', 'seminar']
        if v not in valid_types:
            raise ValueError(f'Required room type must be one of {valid_types}')
        return v

    @field_validator('valid_slot_types')
    @classmethod
    def validate_slot_types(cls, v):
        valid_types = ['single', 'double']
        for slot_type in v:
            if slot_type not in valid_types:
                raise ValueError(f'Valid slot types must be from {valid_types}')
        return v

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        valid_priorities = ['low', 'medium', 'high', 'critical']
        if v not in valid_priorities:
            raise ValueError(f'Priority must be one of {valid_priorities}')
        return v


class SchedulingInput(BaseModel):
    """Root model for scheduling input data."""

    metadata: SchedulingMetadata
    configuration: SchedulingConfiguration
    time_slots: List[TimeSlotInfo] = Field(alias="timeSlots")
    slot_combinations: List[SlotCombination] = Field(alias="slotCombinations")
    rooms: List[RoomInfo]
    student_groups: List[StudentGroupInfo] = Field(alias="studentGroups")
    constraints: SchedulingConstraints
    assignments: List[SchedulingAssignment]

    @field_validator('time_slots')
    @classmethod
    def validate_time_slots(cls, v):
        if not v:
            raise ValueError('At least one time slot is required')
        return v

    @field_validator('assignments')
    @classmethod
    def validate_assignments(cls, v):
        if not v:
            raise ValueError('At least one assignment is required')
        return v