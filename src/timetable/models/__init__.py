"""
Pydantic models for timetable data validation.

This module provides type-safe data models for all stages of the
timetable generation pipeline. Models are organized by stage:

- Stage 1: Raw input data (config, faculty, subjects, student groups)
- Stage 2: Enriched data (full faculty, full subjects with components)
- Stage 3: Teaching assignments and constraints
- Stage 4: Scheduling input for solver
- Stage 5: AI-generated schedule
- Stage 6: Enriched output with views

Usage:
    from timetable.models import Subject, Faculty, StudentGroup
    from timetable.models.stage1 import Config, TimeSlot, Room
    from timetable.models.stage2 import FacultyFull, SubjectFull
    from timetable.models.stage3 import TeachingAssignment

    # Validate data
    subject = Subject(subjectCode="CS101", title="Intro to CS", ...)
    
    # Load and validate from file
    from timetable.core.loader import load_subjects
    subjects = load_subjects("stage_1/subjects.json")
"""

from timetable.models.stage1 import (
    BreakWindow,
    Config,
    ConfigFile,
    CreditToHours,
    DaySlotPattern,
    ElectiveStudentGroup,
    ElectiveSubjectGroup,
    Faculty,
    FacultyFile,
    GroupHierarchyEntry,
    ResourceConstraints,
    Resources,
    Room,
    RoomPreference,
    RoomPreferenceFile,
    SessionType,
    SessionTypes,
    StudentGroup,
    StudentGroupFile,
    Subject,
    SubjectFile,
    TimeSlot,
    ValidSlotCombinations,
)

from timetable.models.stage2 import (
    FacultyFull,
    FacultyFullFile,
    FixedTiming,
    PrimaryAssignment,
    SubjectComponent,
    SubjectFull,
    SubjectsFullFile,
    SupportingAssignment,
    WorkloadStats,
)

from timetable.models.stage3 import (
    AssignmentConstraints,
    AssignmentMetadata,
    AssignmentStatistics,
    CombinedStats,
    ConstraintStats,
    FacultyDistributionEntry,
    FacultyWorkloadEntry,
    ResourceAnalysis,
    RoomRequirementStats,
    SemesterStats,
    StatisticsFile,
    StatisticsMetadata,
    StudentGroupOverlapConstraints,
    StudentGroupStatsEntry,
    SubjectCoverageEntry,
    TeachingAssignment,
    TeachingAssignmentsFile,
)

from timetable.models.stage4 import (
    AssignmentConstraints as Stage4AssignmentConstraints,
    RoomInfo,
    SchedulingAssignment,
    SchedulingConfiguration,
    SchedulingConstraints,
    SchedulingInput,
    SchedulingMetadata,
    SlotCombination,
    TimeSlotInfo,
)

from timetable.models.stage5 import (
    AISchedule,
    ScheduleMetadata,
    ScheduledSession,
)

from timetable.models.stage6 import (
    EnrichedSession,
    EnrichedSessionMetadata,
    EnrichedTimetable,
    SupportingStaff,
)

__all__ = [
    # Stage 1: Config models
    "Config",
    "ConfigFile",
    "TimeSlot",
    "BreakWindow",
    "DaySlotPattern",
    "CreditToHours",
    "ValidSlotCombinations",
    "SessionType",
    "SessionTypes",
    "ResourceConstraints",
    "Room",
    "Resources",
    # Stage 1: Entity models
    "Faculty",
    "FacultyFile",
    "Subject",
    "SubjectFile",
    "StudentGroup",
    "StudentGroupFile",
    "ElectiveStudentGroup",
    "ElectiveSubjectGroup",
    "GroupHierarchyEntry",
    "RoomPreference",
    "RoomPreferenceFile",
    # Stage 2: Full entity models
    "FacultyFull",
    "FacultyFullFile",
    "SubjectFull",
    "SubjectsFullFile",
    "SubjectComponent",
    "FixedTiming",
    "PrimaryAssignment",
    "SupportingAssignment",
    "WorkloadStats",
    # Stage 3: Teaching assignments
    "TeachingAssignment",
    "TeachingAssignmentsFile",
    "AssignmentConstraints",
    "AssignmentMetadata",
    "AssignmentStatistics",
    "StudentGroupOverlapConstraints",
    # Stage 3: Statistics
    "StatisticsFile",
    "StatisticsMetadata",
    "SemesterStats",
    "CombinedStats",
    "ConstraintStats",
    "FacultyDistributionEntry",
    "FacultyWorkloadEntry",
    "StudentGroupStatsEntry",
    "SubjectCoverageEntry",
    "RoomRequirementStats",
    "ResourceAnalysis",
    # Stage 4: Scheduling input
    "SchedulingInput",
    "SchedulingMetadata",
    "SchedulingConfiguration",
    "TimeSlotInfo",
    "SlotCombination",
    "RoomInfo",
    "SchedulingConstraints",
    "SchedulingAssignment",
    "Stage4AssignmentConstraints",
    # Stage 5: AI schedule output
    "AISchedule",
    "ScheduleMetadata",
    "ScheduledSession",
    # Stage 6: Enriched output
    "EnrichedTimetable",
    "EnrichedSessionMetadata",
    "EnrichedSession",
    "SupportingStaff",
]
