"""
Pydantic models for Stage 1 data.

Stage 1 contains the raw input data:
- config.json: Time slots, rooms, constraints
- facultyBasic.json: Faculty information
- subjects[1|3]CoreBasic.json: Subject definitions
- subjects3ElectBasic.json: Elective subjects
- studentGroups.json: Student groups and elective mappings
- roomPreferences.json: Room preferences per subject/component

All models use strict validation and provide helpful error messages.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ==================== Config Models ====================


class TimeSlot(BaseModel):
    """A single time slot in the schedule."""

    model_config = ConfigDict(extra="forbid")

    slot_id: str = Field(..., alias="slotId", description="Unique slot identifier (S1-S7)")
    start: str = Field(..., description="Start time (HH:MM format)")
    end: str = Field(..., description="End time (HH:MM format)")
    length_minutes: int = Field(
        ..., alias="lengthMinutes", ge=1, description="Duration in minutes"
    )

    @field_validator("start", "end")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        """Validate time is in HH:MM format."""
        parts = v.split(":")
        if len(parts) != 2:
            raise ValueError(f"Time must be in HH:MM format, got: {v}")
        try:
            hour, minute = int(parts[0]), int(parts[1])
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError(f"Invalid time values: {v}")
        except ValueError as e:
            raise ValueError(f"Invalid time format: {v}") from e
        return v


class BreakWindow(BaseModel):
    """A break period in the schedule."""

    model_config = ConfigDict(extra="forbid")

    start: str = Field(..., description="Break start time")
    end: str = Field(..., description="Break end time")
    type: Literal["short", "lunch"] = Field(..., description="Break type")


class DaySlotPattern(BaseModel):
    """Slot pattern for each day of the week."""

    model_config = ConfigDict(extra="forbid")

    mon: list[str] = Field(default_factory=list, alias="Mon")
    tue: list[str] = Field(default_factory=list, alias="Tue")
    wed: list[str] = Field(default_factory=list, alias="Wed")
    thu: list[str] = Field(default_factory=list, alias="Thu")
    fri: list[str] = Field(default_factory=list, alias="Fri")
    sat: list[str] = Field(default_factory=list, alias="Sat")

    def get_slots_for_day(self, day: str) -> list[str]:
        """Get slot IDs for a specific day."""
        day_map = {
            "Mon": self.mon,
            "Tue": self.tue,
            "Wed": self.wed,
            "Thu": self.thu,
            "Fri": self.fri,
            "Sat": self.sat,
        }
        return day_map.get(day, [])


class CreditToHours(BaseModel):
    """Mapping of credit types to hours."""

    model_config = ConfigDict(extra="forbid")

    theory: int = Field(..., ge=0, description="Hours per theory credit")
    tutorial: int = Field(..., ge=0, description="Hours per tutorial credit")
    practical: int = Field(..., ge=0, description="Hours per practical credit")


class ValidSlotCombinations(BaseModel):
    """Valid slot combinations for different session types."""

    model_config = ConfigDict(extra="forbid")

    single: list[str] = Field(default_factory=list, description="Single slot options")
    double: list[str] = Field(default_factory=list, description="Double slot combinations")
    saturday: list[str] = Field(default_factory=list, description="Saturday slot options")
    note: Optional[str] = Field(None, description="Additional notes")


class SessionType(BaseModel):
    """Configuration for a session type."""

    model_config = ConfigDict(extra="forbid")

    duration: int = Field(..., ge=1, description="Duration in minutes")
    requires_contiguous: bool = Field(
        ..., alias="requiresContiguous", description="Whether slots must be contiguous"
    )


class SessionTypes(BaseModel):
    """All session type configurations."""

    model_config = ConfigDict(extra="forbid")

    theory: SessionType
    tutorial: SessionType
    practical: SessionType


class ResourceConstraints(BaseModel):
    """Resource scheduling constraints."""

    model_config = ConfigDict(extra="forbid")

    max_consecutive_slots_per_faculty: int = Field(
        ..., alias="maxConsecutiveSlotsPerFaculty", ge=1
    )
    max_daily_slots_per_student_group: int = Field(
        ..., alias="maxDailySlotsPerStudentGroup", ge=1
    )
    min_gap_between_same_faculty: int = Field(
        ..., alias="minGapBetweenSameFaculty", ge=0
    )


class Room(BaseModel):
    """A room resource."""

    model_config = ConfigDict(extra="forbid")

    room_id: str = Field(..., alias="roomId", description="Unique room identifier")
    type: Literal["lecture", "lab"] = Field(..., description="Room type")
    capacity: int = Field(..., ge=1, description="Room capacity")


class Resources(BaseModel):
    """Available resources (rooms)."""

    model_config = ConfigDict(extra="forbid")

    rooms: list[Room] = Field(default_factory=list)

    def get_room(self, room_id: str) -> Optional[Room]:
        """Get a room by ID."""
        for room in self.rooms:
            if room.room_id == room_id:
                return room
        return None

    def get_rooms_by_type(self, room_type: str) -> list[Room]:
        """Get all rooms of a specific type."""
        return [r for r in self.rooms if r.type == room_type]


class Config(BaseModel):
    """Main configuration containing all scheduling parameters."""

    model_config = ConfigDict(extra="forbid")

    day_start: str = Field(..., alias="dayStart")
    day_end: str = Field(..., alias="dayEnd")
    weekdays: list[str] = Field(...)
    day_slot_pattern: DaySlotPattern = Field(..., alias="daySlotPattern")
    break_windows: list[BreakWindow] = Field(..., alias="breakWindows")
    time_slots: list[TimeSlot] = Field(..., alias="timeSlots")
    theory_session_minutes: int = Field(..., alias="theorySessionMinutes")
    lab_tutorial_session_minutes: int = Field(..., alias="labTutorialSessionMinutes")
    credit_to_hours: CreditToHours = Field(..., alias="creditToHours")
    credit_pattern: Optional[dict[str, str]] = Field(None, alias="creditPattern")
    valid_slot_combinations: ValidSlotCombinations = Field(
        ..., alias="validSlotCombinations"
    )
    session_types: SessionTypes = Field(..., alias="sessionTypes")
    resource_constraints: ResourceConstraints = Field(..., alias="resourceConstraints")
    resources: Resources = Field(...)

    def get_slot(self, slot_id: str) -> Optional[TimeSlot]:
        """Get a time slot by ID."""
        for slot in self.time_slots:
            if slot.slot_id == slot_id:
                return slot
        return None


class ConfigFile(BaseModel):
    """Wrapper for config.json file."""

    model_config = ConfigDict(extra="forbid")

    config: Config


# ==================== Faculty Models ====================


# Faculty assignment can be either a string (subject code) or a dict mapping to sections
AssignedSubject = Union[str, dict[str, list[str]]]


class Faculty(BaseModel):
    """A faculty member."""

    model_config = ConfigDict(extra="forbid")

    faculty_id: str = Field(..., alias="facultyId", min_length=1)
    name: str = Field(..., min_length=1)
    designation: str = Field(...)
    assigned_subjects: list[AssignedSubject] = Field(
        default_factory=list, alias="assignedSubjects"
    )
    supporting_subjects: list[str] = Field(
        default_factory=list, alias="supportingSubjects"
    )

    def get_all_subject_codes(self) -> set[str]:
        """Get all subject codes (assigned + supporting)."""
        codes = set(self.supporting_subjects)
        for subj in self.assigned_subjects:
            if isinstance(subj, str):
                codes.add(subj)
            elif isinstance(subj, dict):
                codes.update(subj.keys())
        return codes


class FacultyFile(BaseModel):
    """Wrapper for facultyBasic.json file."""

    model_config = ConfigDict(extra="forbid")

    faculty: list[Faculty]


# ==================== Subject Models ====================


class Subject(BaseModel):
    """A subject/course."""

    model_config = ConfigDict(extra="allow")

    subject_code: str = Field(..., alias="subjectCode", min_length=1)
    short_code: str = Field(..., alias="shortCode", min_length=1)
    title: str = Field(..., min_length=1)
    credit_pattern: Annotated[list[int], Field(min_length=3, max_length=3)] = Field(
        ..., alias="creditPattern"
    )
    total_credits: int = Field(..., alias="totalCredits", ge=0)
    department: str = Field(...)
    semester: int = Field(..., ge=1, le=8)
    is_elective: bool = Field(..., alias="isElective")
    type: Literal["core", "elective", "diff"] = Field(...)

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

    @model_validator(mode="after")
    def validate_total_credits(self) -> "Subject":
        """Validate total credits matches sum of credit pattern."""
        expected = sum(self.credit_pattern)
        if self.total_credits != expected:
            raise ValueError(
                f"Total credits ({self.total_credits}) doesn't match "
                f"sum of credit pattern ({expected})"
            )
        return self

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

    @property
    def has_theory(self) -> bool:
        """Check if subject has theory component."""
        return self.theory_credits > 0

    @property
    def has_tutorial(self) -> bool:
        """Check if subject has tutorial component."""
        return self.tutorial_credits > 0

    @property
    def has_practical(self) -> bool:
        """Check if subject has practical component."""
        return self.practical_credits > 0


class SubjectFile(BaseModel):
    """Wrapper for subjects JSON files."""

    model_config = ConfigDict(extra="forbid")

    subjects: list[Subject]


# ==================== Student Group Models ====================


class StudentGroup(BaseModel):
    """A student group (section)."""

    model_config = ConfigDict(extra="forbid")

    semester: int = Field(..., ge=1, le=8)
    section: str = Field(..., min_length=1)
    student_count: int = Field(..., alias="studentCount", ge=0)
    student_group_id: str = Field(..., alias="studentGroupId", min_length=1)
    compulsory_subjects: list[str] = Field(
        default_factory=list, alias="compulsorySubjects"
    )


class ElectiveSubjectGroup(BaseModel):
    """A group of elective subjects that can run in parallel."""

    model_config = ConfigDict(extra="forbid")

    group_id: str = Field(..., alias="groupId")
    group_name: str = Field(..., alias="groupName")
    description: Optional[str] = None
    subject_codes: list[str] = Field(..., alias="subjectCodes")


class ElectiveStudentGroup(BaseModel):
    """A student sub-group for electives."""

    model_config = ConfigDict(extra="forbid")

    student_group_id: str = Field(..., alias="studentGroupId")
    parent_group_id: str = Field(..., alias="parentGroupId")
    student_count: int = Field(..., alias="studentCount", ge=0)
    sections: list[str] = Field(...)
    description: Optional[str] = None
    source_sections: list[str] = Field(..., alias="sourceSections")


class GroupHierarchyEntry(BaseModel):
    """Entry in the group hierarchy."""

    model_config = ConfigDict(extra="ignore")  # Allow extra fields

    children: list[str] = Field(default_factory=list)
    parent: Optional[str] = None
    parents: Optional[list[str]] = None
    description: Optional[str] = None


class StudentGroupFile(BaseModel):
    """Wrapper for studentGroups.json file."""

    model_config = ConfigDict(extra="forbid")

    student_groups: list[StudentGroup] = Field(..., alias="studentGroups")
    elective_subject_groups: list[ElectiveSubjectGroup] = Field(
        default_factory=list, alias="electiveSubjectGroups"
    )
    elective_student_groups: list[ElectiveStudentGroup] = Field(
        default_factory=list, alias="electiveStudentGroups"
    )
    group_hierarchy: dict[str, GroupHierarchyEntry] = Field(
        default_factory=dict, alias="groupHierarchy"
    )

    def get_group(self, group_id: str) -> Optional[StudentGroup]:
        """Get a student group by ID."""
        for group in self.student_groups:
            if group.student_group_id == group_id:
                return group
        return None

    def get_elective_group(self, group_id: str) -> Optional[ElectiveStudentGroup]:
        """Get an elective student group by ID."""
        for group in self.elective_student_groups:
            if group.student_group_id == group_id:
                return group
        return None


# ==================== Room Preference Models ====================


class RoomPreference(BaseModel):
    """Room preference for a subject component."""

    model_config = ConfigDict(extra="forbid")

    subject_code: str = Field(..., alias="subjectCode")
    component_type: Literal["theory", "tutorial", "practical"] = Field(
        ..., alias="componentType"
    )
    semester: int = Field(..., ge=1, le=8)
    student_group_id: str = Field(..., alias="studentGroupId")
    preferred_rooms: list[str] = Field(..., alias="preferredRooms")
    room_allocations: Optional[dict[str, str]] = Field(
        None, alias="roomAllocations"
    )


class RoomPreferenceFile(BaseModel):
    """Wrapper for roomPreferences.json file."""

    model_config = ConfigDict(extra="forbid")

    room_preferences: list[RoomPreference] = Field(..., alias="roomPreferences")

    def get_preferences_for_subject(
        self, subject_code: str, component_type: Optional[str] = None
    ) -> list[RoomPreference]:
        """Get all preferences for a subject, optionally filtered by component."""
        prefs = [p for p in self.room_preferences if p.subject_code == subject_code]
        if component_type:
            prefs = [p for p in prefs if p.component_type == component_type]
        return prefs
