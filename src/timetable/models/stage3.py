"""
Pydantic models for Stage 3 data.

Stage 3 contains the final scheduling-ready data:
- teachingAssignments_sem[1|3].json: Individual teaching assignments with constraints
- studentGroupOverlapConstraints.json: Student group overlap rules
- statistics.json: Summary statistics for validation

These are the primary inputs for the scheduling algorithm.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ==================== Teaching Assignment Models ====================


class AssignmentConstraints(BaseModel):
    """Constraints for a teaching assignment."""

    model_config = ConfigDict(extra="forbid")

    student_group_conflicts: list[str] = Field(
        default_factory=list, alias="studentGroupConflicts"
    )
    faculty_conflicts: list[str] = Field(
        default_factory=list, alias="facultyConflicts"
    )
    fixed_day: Optional[str] = Field(None, alias="fixedDay")
    fixed_slot: Optional[str] = Field(None, alias="fixedSlot")
    must_be_in_room: Optional[str] = Field(None, alias="mustBeInRoom")


class TeachingAssignment(BaseModel):
    """A single teaching assignment (one faculty, one component, one section)."""

    model_config = ConfigDict(extra="forbid")

    assignment_id: str = Field(..., alias="assignmentId", min_length=1)
    subject_code: str = Field(..., alias="subjectCode", min_length=1)
    short_code: str = Field(..., alias="shortCode", min_length=1)
    subject_title: str = Field(..., alias="subjectTitle", min_length=1)
    component_id: str = Field(..., alias="componentId", min_length=1)
    component_type: Literal["theory", "tutorial", "practical"] = Field(
        ..., alias="componentType"
    )
    semester: int = Field(..., ge=1, le=8)
    faculty_id: str = Field(..., alias="facultyId", min_length=1)
    faculty_name: str = Field(..., alias="facultyName", min_length=1)
    student_group_ids: list[str] = Field(..., alias="studentGroupIds")
    sections: list[str] = Field(...)
    session_duration: int = Field(..., alias="sessionDuration", ge=1)
    sessions_per_week: int = Field(..., alias="sessionsPerWeek", ge=0)
    requires_room_type: Literal["lecture", "lab"] = Field(..., alias="requiresRoomType")
    preferred_rooms: list[str] = Field(default_factory=list, alias="preferredRooms")
    requires_contiguous: bool = Field(..., alias="requiresContiguous")
    block_size_slots: int = Field(..., alias="blockSizeSlots", ge=1)
    priority: Literal["high", "medium", "low"] = Field(...)
    is_elective: bool = Field(..., alias="isElective")
    is_diff_subject: bool = Field(..., alias="isDiffSubject")
    constraints: AssignmentConstraints = Field(...)

    @property
    def weekly_hours(self) -> float:
        """Calculate total weekly hours for this assignment."""
        return (self.session_duration * self.sessions_per_week) / 60.0

    @property
    def is_lab_session(self) -> bool:
        """Check if this is a lab session (practical or tutorial in lab)."""
        return self.requires_room_type == "lab"


class AssignmentStatistics(BaseModel):
    """Statistics about a set of teaching assignments."""

    model_config = ConfigDict(extra="forbid")

    total_assignments: int = Field(..., alias="totalAssignments", ge=0)
    by_type: dict[str, int] = Field(..., alias="byType")
    by_component_type: dict[str, int] = Field(..., alias="byComponentType")
    by_priority: dict[str, int] = Field(..., alias="byPriority")
    total_sessions: int = Field(..., alias="totalSessions", ge=0)
    total_weekly_hours: float = Field(..., alias="totalWeeklyHours", ge=0)
    faculty_assignments: dict[str, int] = Field(..., alias="facultyAssignments")
    room_requirements: dict[str, int] = Field(..., alias="roomRequirements")
    with_fixed_timing: int = Field(..., alias="withFixedTiming", ge=0)
    with_pre_allocated_rooms: int = Field(..., alias="withPreAllocatedRooms", ge=0)
    with_room_preferences: int = Field(..., alias="withRoomPreferences", ge=0)


class AssignmentMetadata(BaseModel):
    """Metadata about a teaching assignments file."""

    model_config = ConfigDict(extra="forbid")

    semester: int = Field(..., ge=1, le=8)
    generated_at: datetime = Field(..., alias="generatedAt")
    total_assignments: int = Field(..., alias="totalAssignments", ge=0)
    generator: str = Field(...)


class TeachingAssignmentsFile(BaseModel):
    """Wrapper for teachingAssignments_sem[N].json files."""

    model_config = ConfigDict(extra="forbid")

    metadata: AssignmentMetadata
    assignments: list[TeachingAssignment]
    statistics: AssignmentStatistics

    def get_assignment(self, assignment_id: str) -> Optional[TeachingAssignment]:
        """Get an assignment by ID."""
        for assign in self.assignments:
            if assign.assignment_id == assignment_id:
                return assign
        return None

    def get_assignments_for_faculty(self, faculty_id: str) -> list[TeachingAssignment]:
        """Get all assignments for a specific faculty."""
        return [a for a in self.assignments if a.faculty_id == faculty_id]

    def get_assignments_for_subject(
        self, subject_code: str
    ) -> list[TeachingAssignment]:
        """Get all assignments for a specific subject."""
        return [a for a in self.assignments if a.subject_code == subject_code]

    def get_assignments_for_group(
        self, student_group_id: str
    ) -> list[TeachingAssignment]:
        """Get all assignments for a student group."""
        return [
            a for a in self.assignments 
            if student_group_id in a.student_group_ids
        ]

    def get_theory_assignments(self) -> list[TeachingAssignment]:
        """Get all theory assignments."""
        return [a for a in self.assignments if a.component_type == "theory"]

    def get_lab_assignments(self) -> list[TeachingAssignment]:
        """Get all lab/practical assignments."""
        return [a for a in self.assignments if a.requires_room_type == "lab"]


# ==================== Student Group Overlap Constraints ====================


class StudentGroupOverlapConstraints(BaseModel):
    """Constraints defining which student groups cannot be scheduled together."""

    model_config = ConfigDict(extra="forbid")

    cannot_overlap_with: dict[str, list[str]] = Field(
        ..., alias="cannotOverlapWith",
        description="Groups that cannot have sessions at the same time"
    )
    can_run_parallel_with: dict[str, list[str]] = Field(
        ..., alias="canRunParallelWith",
        description="Groups that can have sessions at the same time"
    )

    def get_conflicts_for_group(self, group_id: str) -> list[str]:
        """Get all groups that conflict with the given group."""
        return self.cannot_overlap_with.get(group_id, [])

    def get_parallel_groups(self, group_id: str) -> list[str]:
        """Get all groups that can run in parallel with the given group."""
        return self.can_run_parallel_with.get(group_id, [])

    def can_schedule_together(self, group1: str, group2: str) -> bool:
        """Check if two groups can be scheduled at the same time."""
        conflicts1 = self.cannot_overlap_with.get(group1, [])
        conflicts2 = self.cannot_overlap_with.get(group2, [])
        return group2 not in conflicts1 and group1 not in conflicts2


# ==================== Statistics Models ====================


class ComponentStats(BaseModel):
    """Statistics for assignments by component type."""

    model_config = ConfigDict(extra="forbid")

    count: int = Field(..., ge=0)
    sessions: int = Field(..., ge=0)
    hours: float = Field(..., ge=0)


class TypeStats(BaseModel):
    """Statistics for assignments by type."""

    model_config = ConfigDict(extra="forbid")

    count: int = Field(..., ge=0)
    sessions: int = Field(..., ge=0)
    hours: Optional[float] = None


class PriorityStats(BaseModel):
    """Statistics for assignments by priority."""

    model_config = ConfigDict(extra="forbid")

    count: int = Field(..., ge=0)
    sessions: int = Field(..., ge=0)


class RoomTypeStats(BaseModel):
    """Statistics for assignments by room type."""

    model_config = ConfigDict(extra="forbid")

    count: int = Field(..., ge=0)
    sessions: int = Field(..., ge=0)


class FacultyDistributionEntry(BaseModel):
    """Faculty workload distribution entry."""

    model_config = ConfigDict(extra="forbid")

    faculty_name: str = Field(..., alias="facultyName")
    assignments: int = Field(..., ge=0)
    sessions: int = Field(..., ge=0)
    hours: float = Field(..., ge=0)
    subjects: list[str] = Field(default_factory=list)
    subject_count: int = Field(..., alias="subjectCount", ge=0)
    components: dict[str, int] = Field(default_factory=dict)


class SubjectCoverageEntry(BaseModel):
    """Subject coverage entry in statistics."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(...)
    faculty: list[str] = Field(default_factory=list)
    faculty_count: int = Field(..., alias="facultyCount", ge=0)
    components: list[str] = Field(default_factory=list)
    component_count: int = Field(..., alias="componentCount", ge=0)
    total_sessions: int = Field(..., alias="totalSessions", ge=0)
    sections: list[str] = Field(default_factory=list)


class StudentGroupStatsEntry(BaseModel):
    """Student group statistics entry."""

    model_config = ConfigDict(extra="forbid")

    assignments: int = Field(..., ge=0)
    sessions: int = Field(..., ge=0)
    hours: float = Field(..., ge=0)
    subjects: list[str] = Field(default_factory=list)
    subject_count: int = Field(..., alias="subjectCount", ge=0)


class ConstraintStats(BaseModel):
    """Statistics about constraints in assignments."""

    model_config = ConfigDict(extra="forbid")

    with_student_conflicts: int = Field(..., alias="withStudentConflicts", ge=0)
    with_faculty_conflicts: int = Field(..., alias="withFacultyConflicts", ge=0)
    with_fixed_timing: int = Field(..., alias="withFixedTiming", ge=0)
    with_room_allocation: int = Field(..., alias="withRoomAllocation", ge=0)
    with_room_preferences: int = Field(..., alias="withRoomPreferences", ge=0)
    with_contiguous_requirement: int = Field(..., alias="withContiguousRequirement", ge=0)


class RoomRequirementStats(BaseModel):
    """Statistics about room requirements."""

    model_config = ConfigDict(extra="forbid")

    unique_rooms_needed: int = Field(..., alias="uniqueRoomsNeeded", ge=0)
    pre_allocated_rooms: list[str] = Field(..., alias="preAllocatedRooms")
    preferred_rooms_list: list[str] = Field(..., alias="preferredRoomsList")


class SemesterStats(BaseModel):
    """Statistics for a single semester."""

    model_config = ConfigDict(extra="forbid")

    semester: int = Field(..., ge=1, le=8)
    total_assignments: int = Field(..., alias="totalAssignments", ge=0)
    total_sessions: int = Field(..., alias="totalSessions", ge=0)
    total_hours: float = Field(..., alias="totalHours", ge=0)
    by_type: dict[str, TypeStats] = Field(..., alias="byType")
    by_component: dict[str, ComponentStats] = Field(..., alias="byComponent")
    by_priority: dict[str, PriorityStats] = Field(..., alias="byPriority")
    by_room_type: dict[str, RoomTypeStats] = Field(..., alias="byRoomType")
    faculty_distribution: dict[str, FacultyDistributionEntry] = Field(
        ..., alias="facultyDistribution"
    )
    subject_coverage: dict[str, SubjectCoverageEntry] = Field(
        ..., alias="subjectCoverage"
    )
    student_groups: dict[str, StudentGroupStatsEntry] = Field(
        ..., alias="studentGroups"
    )
    constraints: ConstraintStats = Field(...)
    conflict_patterns: dict[str, int] = Field(..., alias="conflictPatterns")
    room_requirements: RoomRequirementStats = Field(..., alias="roomRequirements")


class FacultyWorkloadEntry(BaseModel):
    """Faculty workload entry for combined statistics."""

    model_config = ConfigDict(extra="forbid")

    faculty_name: str = Field(..., alias="facultyName")
    sem1: dict[str, Any] = Field(...)
    sem3: dict[str, Any] = Field(...)
    total: dict[str, Any] = Field(...)


class ResourceAnalysis(BaseModel):
    """Combined resource analysis."""

    model_config = ConfigDict(extra="forbid")

    lecture_room_sessions: int = Field(..., alias="lectureRoomSessions", ge=0)
    lab_sessions: int = Field(..., alias="labSessions", ge=0)
    theory_sessions: int = Field(..., alias="theorySessions", ge=0)
    practical_sessions: int = Field(..., alias="practicalSessions", ge=0)
    tutorial_sessions: int = Field(..., alias="tutorialSessions", ge=0)


class CombinedStats(BaseModel):
    """Combined statistics across all semesters."""

    model_config = ConfigDict(extra="forbid")

    total_assignments: int = Field(..., alias="totalAssignments", ge=0)
    total_sessions: int = Field(..., alias="totalSessions", ge=0)
    total_hours: float = Field(..., alias="totalHours", ge=0)
    faculty_workload: dict[str, FacultyWorkloadEntry] = Field(..., alias="facultyWorkload")
    resource_analysis: ResourceAnalysis = Field(..., alias="resourceAnalysis")


class StatisticsMetadata(BaseModel):
    """Metadata for statistics file."""

    model_config = ConfigDict(extra="forbid")

    generated_at: datetime = Field(..., alias="generatedAt")
    generator: str = Field(...)
    version: str = Field(...)


class StatisticsFile(BaseModel):
    """Wrapper for statistics.json file."""

    model_config = ConfigDict(extra="forbid")

    metadata: StatisticsMetadata
    semester1: Optional[SemesterStats] = None
    semester2: Optional[SemesterStats] = None
    semester3: Optional[SemesterStats] = None
    semester4: Optional[SemesterStats] = None
    combined: CombinedStats

    def get_semester_stats(self, semester: int) -> Optional[SemesterStats]:
        """Dynamically get statistics for any semester.
        
        Args:
            semester: Semester number (1, 2, 3, or 4)
            
        Returns:
            SemesterStats for the semester, or None if not available
        """
        stats_map = {
            1: self.semester1,
            2: self.semester2,
            3: self.semester3,
            4: self.semester4,
        }
        return stats_map.get(semester)
