"""
Pydantic models for Stage 2 data.

Stage 2 contains the processed/enriched data:
- faculty2Full.json: Faculty with full assignment details and workload stats
- subjects2Full.json: Subjects with expanded component details

These are built from Stage 1 data and contain calculated fields.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ==================== Subject Component Models ====================


class SubjectComponent(BaseModel):
    """A single component of a subject (theory, tutorial, or practical)."""

    model_config = ConfigDict(extra="allow")

    component_id: str = Field(..., alias="componentId", min_length=1)
    component_type: Literal["theory", "tutorial", "practical"] = Field(
        ..., alias="componentType"
    )
    credits: int = Field(..., ge=0)
    session_duration: int = Field(
        ..., alias="sessionDuration", ge=1, description="Duration in minutes"
    )
    sessions_per_week: int = Field(..., alias="sessionsPerWeek", ge=0)
    total_weekly_minutes: int = Field(..., alias="totalWeeklyMinutes", ge=0)
    must_be_in_room_type: Literal["lecture", "lab"] = Field(..., alias="mustBeInRoomType")
    block_size_slots: int = Field(..., alias="blockSizeSlots", ge=1)
    must_be_contiguous: bool = Field(..., alias="mustBeContiguous")


class FixedTiming(BaseModel):
    """Fixed timing for a subject (pre-scheduled)."""

    model_config = ConfigDict(extra="allow")

    day: str = Field(..., description="Day of the week (Mon, Tue, etc.)")
    slots: list[str] = Field(..., description="Slot IDs for the session")
    duration: Optional[int] = Field(None, description="Duration in minutes")


class SubjectFull(BaseModel):
    """A subject with fully expanded components (Stage 2 output)."""

    model_config = ConfigDict(extra="forbid")

    subject_code: str = Field(..., alias="subjectCode", min_length=1)
    short_code: Optional[str] = Field(None, alias="shortCode")
    title: str = Field(..., min_length=1)
    credit_pattern: list[int] = Field(..., alias="creditPattern")
    total_credits: int = Field(..., alias="totalCredits", ge=0)
    department: str = Field(...)
    semester: int = Field(..., ge=1, le=8)
    is_elective: bool = Field(default=False, alias="isElective")
    type: Literal["core", "elective", "diff"] = Field(...)
    components: list[SubjectComponent] = Field(default_factory=list)
    
    # Optional fields for special subjects
    priority: Optional[Literal["high", "medium", "low", "external"]] = None
    assigned_to: Optional[str] = Field(None, alias="assignedTo")
    sections: Optional[list[str]] = None
    fixed_timing: Optional[FixedTiming] = Field(None, alias="fixedTiming")
    not_in_main_timetable: Optional[bool] = Field(None, alias="notInMainTimetable")
    student_count: Optional[int] = Field(None, alias="studentCount")
    flexible: Optional[bool] = None

    @field_validator("credit_pattern")
    @classmethod
    def validate_credit_pattern(cls, v: list[int]) -> list[int]:
        """Validate credit pattern has exactly 3 non-negative integers."""
        if len(v) != 3:
            raise ValueError("Credit pattern must have exactly 3 values [theory, tutorial, practical]")
        for credit in v:
            if credit < 0:
                raise ValueError("Credits cannot be negative")
        return v

    @property
    def theory_credits(self) -> int:
        """Get theory credits."""
        return self.credit_pattern[0]

    @property
    def tutorial_credits(self) -> int:
        """Get tutorial credits."""
        return self.credit_pattern[1]

    @property
    def practical_credits(self) -> int:
        """Get practical credits."""
        return self.credit_pattern[2]

    def get_component(self, component_id: str) -> Optional[SubjectComponent]:
        """Get a component by ID."""
        for comp in self.components:
            if comp.component_id == component_id:
                return comp
        return None

    def get_components_by_type(
        self, component_type: str
    ) -> list[SubjectComponent]:
        """Get all components of a specific type."""
        return [c for c in self.components if c.component_type == component_type]


class SubjectsFullFile(BaseModel):
    """Wrapper for subjects2Full.json file."""

    model_config = ConfigDict(extra="allow")

    subjects: list[SubjectFull]

    def get_subject(self, subject_code: str) -> Optional[SubjectFull]:
        """Get a subject by code."""
        for subj in self.subjects:
            if subj.subject_code == subject_code:
                return subj
        return None

    def get_subjects_by_semester(self, semester: int) -> list[SubjectFull]:
        """Get all subjects for a specific semester."""
        return [s for s in self.subjects if s.semester == semester]

    def get_elective_subjects(self) -> list[SubjectFull]:
        """Get all elective subjects."""
        return [s for s in self.subjects if s.is_elective]

    def get_core_subjects(self) -> list[SubjectFull]:
        """Get all core subjects."""
        return [s for s in self.subjects if not s.is_elective and s.type == "core"]


# ==================== Faculty Assignment Models ====================


class PrimaryAssignment(BaseModel):
    """A primary teaching assignment for a faculty member."""

    model_config = ConfigDict(extra="forbid")

    subject_code: str = Field(..., alias="subjectCode", min_length=1)
    semester: int = Field(..., ge=1, le=8)
    sections: list[str] = Field(default_factory=list)
    student_group_ids: list[str] = Field(..., alias="studentGroupIds")
    component_ids: list[str] = Field(..., alias="componentIds")
    component_types: list[Literal["theory", "tutorial", "practical"]] = Field(
        ..., alias="componentTypes"
    )
    role: Literal["primary"] = Field(...)
    weekly_hours_per_section: int = Field(..., alias="weeklyHoursPerSection", ge=0)
    total_weekly_hours: int = Field(..., alias="totalWeeklyHours", ge=0)
    sessions_per_week_per_section: int = Field(
        ..., alias="sessionsPerWeekPerSection", ge=0
    )
    total_sessions_per_week: int = Field(..., alias="totalSessionsPerWeek", ge=0)


class SupportingAssignment(BaseModel):
    """A supporting assignment (backup/helper) for a faculty member.
    
    Can be assigned section-wise or to all sections. Structure mirrors PrimaryAssignment
    to support detailed scheduling information.
    """

    model_config = ConfigDict(extra="forbid")

    subject_code: str = Field(..., alias="subjectCode", min_length=1)
    semester: int = Field(..., ge=1, le=8)
    sections: list[str] = Field(default_factory=list)
    student_group_ids: list[str] = Field(..., alias="studentGroupIds")
    component_ids: list[str] = Field(..., alias="componentIds")
    component_types: list[Literal["theory", "tutorial", "practical"]] = Field(
        ..., alias="componentTypes"
    )
    role: Literal["supporting"] = Field(...)
    weekly_hours_per_section: int = Field(..., alias="weeklyHoursPerSection", ge=0)
    total_weekly_hours: int = Field(..., alias="totalWeeklyHours", ge=0)
    sessions_per_week_per_section: int = Field(
        ..., alias="sessionsPerWeekPerSection", ge=0
    )
    total_sessions_per_week: int = Field(..., alias="totalSessionsPerWeek", ge=0)


class WorkloadStats(BaseModel):
    """Workload statistics for a faculty member."""

    model_config = ConfigDict(extra="forbid")

    theory_hours: int = Field(..., alias="theoryHours", ge=0)
    tutorial_hours: int = Field(..., alias="tutorialHours", ge=0)
    practical_hours: int = Field(..., alias="practicalHours", ge=0)
    total_sessions: int = Field(..., alias="totalSessions", ge=0)
    total_weekly_hours: int = Field(..., alias="totalWeeklyHours", ge=0)


class FacultyFull(BaseModel):
    """A faculty member with full assignment details (Stage 2 output)."""

    model_config = ConfigDict(extra="forbid")

    faculty_id: str = Field(..., alias="facultyId", min_length=1)
    name: str = Field(..., min_length=1)
    designation: str = Field(...)
    department: str = Field(...)
    primary_assignments: list[PrimaryAssignment] = Field(
        default_factory=list, alias="primaryAssignments"
    )
    supporting_assignments: list[SupportingAssignment] = Field(
        default_factory=list, alias="supportingAssignments"
    )
    workload_stats: WorkloadStats = Field(..., alias="workloadStats")

    def get_primary_assignment(
        self, subject_code: str
    ) -> Optional[PrimaryAssignment]:
        """Get primary assignment for a specific subject."""
        for assign in self.primary_assignments:
            if assign.subject_code == subject_code:
                return assign
        return None

    def get_assignments_for_semester(
        self, semester: int
    ) -> list[PrimaryAssignment]:
        """Get all primary assignments for a semester."""
        return [a for a in self.primary_assignments if a.semester == semester]

    @property
    def total_subjects(self) -> int:
        """Get total number of subjects (primary + supporting)."""
        primary_codes = {a.subject_code for a in self.primary_assignments}
        supporting_codes = {a.subject_code for a in self.supporting_assignments}
        return len(primary_codes | supporting_codes)

    @property
    def is_supporting_only(self) -> bool:
        """Check if faculty only has supporting assignments."""
        return len(self.primary_assignments) == 0


class FacultyFullFile(BaseModel):
    """Wrapper for faculty2Full.json file."""

    model_config = ConfigDict(extra="forbid")

    faculty: list[FacultyFull]

    def get_faculty(self, faculty_id: str) -> Optional[FacultyFull]:
        """Get a faculty member by ID."""
        for fac in self.faculty:
            if fac.faculty_id == faculty_id:
                return fac
        return None

    def get_faculty_by_subject(self, subject_code: str) -> list[FacultyFull]:
        """Get all faculty teaching a specific subject."""
        result = []
        for fac in self.faculty:
            for assign in fac.primary_assignments:
                if assign.subject_code == subject_code:
                    result.append(fac)
                    break
        return result

    def get_faculty_by_department(self, department: str) -> list[FacultyFull]:
        """Get all faculty in a department."""
        return [f for f in self.faculty if f.department == department]
