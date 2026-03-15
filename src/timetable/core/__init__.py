"""
Core functionality for the timetable system.

This module contains shared utilities, exceptions, and base classes.
"""

from timetable.core.exceptions import (
    ConfigurationError,
    DataLoadError,
    SchedulingError,
    StageError,
    TimetableError,
    ValidationError,
)
from timetable.core.loader import (
    DataLoader,
    load_and_validate,
    load_config,
    load_faculty,
    load_json,
    load_room_preferences,
    load_student_groups,
    load_subjects,
    validate_model,
)
from timetable.core.logging import get_logger, setup_logging
from timetable.core.semester_detector import (
    detect_active_semesters,
    describe_active_semesters,
    get_elective_differentiation_files,
    get_subject_files_for_semesters,
    is_semester_active,
)

__all__ = [
    # Exceptions
    "TimetableError",
    "ValidationError",
    "DataLoadError",
    "ConfigurationError",
    "StageError",
    "SchedulingError",
    # Logging
    "get_logger",
    "setup_logging",
    # Loader
    "DataLoader",
    "load_json",
    "load_and_validate",
    "validate_model",
    "load_config",
    "load_faculty",
    "load_subjects",
    "load_student_groups",
    "load_room_preferences",
    # Semester Detection
    "detect_active_semesters",
    "is_semester_active",
    "get_subject_files_for_semesters",
    "get_elective_differentiation_files",
    "describe_active_semesters",
]
