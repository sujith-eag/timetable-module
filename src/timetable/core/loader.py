"""
Data loading utilities for the timetable system.

This module provides functions to load and validate JSON data files
from each stage of the pipeline. All loaded data is validated against
Pydantic models to ensure type safety and data integrity.

Usage:
    from timetable.core.loader import DataLoader

    # Create loader with data directory
    loader = DataLoader("/path/to/data")

    # Load Stage 1 data
    config = loader.load_config()
    faculty = loader.load_faculty()
    subjects = loader.load_subjects(semester=1)
    groups = loader.load_student_groups()

    # Load Stage 2 data
    faculty_full = loader.load_faculty_full()
    subjects_full = loader.load_subjects_full()

    # Load Stage 3 data
    assignments = loader.load_teaching_assignments(semester=1)
    overlaps = loader.load_overlap_constraints()
    statistics = loader.load_statistics()

    # Or use convenience functions
    from timetable.core.loader import load_json, load_config
    data = load_json("path/to/file.json")
    config = load_config("stage_1/config.json")
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional, TypeVar, Union

from pydantic import BaseModel, ValidationError as PydanticValidationError

from timetable.core.exceptions import DataLoadError, ValidationError
from timetable.core.logging import get_logger
from timetable.models.stage1 import (
    Config,
    ConfigFile,
    Faculty,
    FacultyFile,
    RoomPreference,
    RoomPreferenceFile,
    StudentGroupFile,
    Subject,
    SubjectFile,
)
from timetable.models.stage2 import (
    FacultyFull,
    FacultyFullFile,
    SubjectFull,
    SubjectsFullFile,
)
from timetable.models.stage3 import (
    StatisticsFile,
    StudentGroupOverlapConstraints,
    TeachingAssignmentsFile,
)
from timetable.models.stage4 import SchedulingInput
from timetable.models.stage5 import AISchedule
from timetable.models.stage6 import (
    EnrichedTimetable,
)

logger = get_logger(__name__)

# Type variable for generic model loading
T = TypeVar("T", bound=BaseModel)


def load_json(filepath: Union[str, Path]) -> dict[str, Any]:
    """
    Load a JSON file and return its contents as a dictionary.

    Args:
        filepath: Path to the JSON file

    Returns:
        Dictionary containing the parsed JSON data

    Raises:
        DataLoadError: If file cannot be read or parsed

    Example:
        >>> data = load_json("stage_1/config.json")
        >>> print(data["config"]["dayStart"])
    """
    filepath = Path(filepath)
    logger.debug(f"Loading JSON file: {filepath}")

    if not filepath.exists():
        raise DataLoadError(
            f"File not found: {filepath}",
            filepath=filepath,
            details={"error_type": "file_not_found"},
        )

    if not filepath.is_file():
        raise DataLoadError(
            f"Path is not a file: {filepath}",
            filepath=filepath,
            details={"error_type": "not_a_file"},
        )

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.debug(f"Successfully loaded: {filepath}")
        return data
    except json.JSONDecodeError as e:
        raise DataLoadError(
            f"Invalid JSON syntax at line {e.lineno}, column {e.colno}: {e.msg}",
            filepath=filepath,
            details={
                "error_type": "json_parse_error",
                "line": e.lineno,
                "column": e.colno,
            },
        ) from e
    except PermissionError as e:
        raise DataLoadError(
            f"Permission denied reading file: {filepath}",
            filepath=filepath,
            details={"error_type": "permission_denied"},
        ) from e
    except OSError as e:
        raise DataLoadError(
            f"Error reading file: {e}",
            filepath=filepath,
            details={"error_type": "io_error"},
        ) from e


def validate_model(
    data: dict[str, Any],
    model_class: type[T],
    filepath: Optional[Union[str, Path]] = None,
) -> T:
    """
    Validate data against a Pydantic model.

    Args:
        data: Dictionary data to validate
        model_class: Pydantic model class to validate against
        filepath: Optional filepath for error messages

    Returns:
        Validated model instance

    Raises:
        ValidationError: If data doesn't match the model schema

    Example:
        >>> data = {"subjectCode": "CS101", ...}
        >>> subject = validate_model(data, Subject)
    """
    try:
        return model_class.model_validate(data)
    except PydanticValidationError as e:
        # Format error messages nicely
        errors = []
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            msg = error["msg"]
            errors.append(f"  - {field}: {msg}")

        error_msg = f"Validation failed with {len(e.errors())} error(s):\n" + "\n".join(
            errors
        )

        raise ValidationError(
            error_msg,
            field=None,
            details={
                "model": model_class.__name__,
                "filepath": str(filepath) if filepath else None,
                "errors": e.errors(),
            },
        ) from e


def load_and_validate(
    filepath: Union[str, Path],
    model_class: type[T],
) -> T:
    """
    Load a JSON file and validate it against a Pydantic model.

    Args:
        filepath: Path to the JSON file
        model_class: Pydantic model class to validate against

    Returns:
        Validated model instance

    Raises:
        DataLoadError: If file cannot be read
        ValidationError: If data doesn't match the model

    Example:
        >>> config_file = load_and_validate("config.json", ConfigFile)
        >>> config = config_file.config
    """
    data = load_json(filepath)
    return validate_model(data, model_class, filepath)


class DataLoader:
    """
    Data loader for timetable data files.

    This class provides methods to load all data files from the stage
    directories with automatic validation.

    Attributes:
        data_dir: Root directory containing stage directories
        strict: If True, raise errors on warnings

    Example:
        >>> loader = DataLoader("/path/to/data")
        >>> config = loader.load_config()
        >>> subjects = loader.load_subjects(semester=1)
    """

    def __init__(
        self,
        data_dir: Union[str, Path],
        strict: bool = False,
    ) -> None:
        """
        Initialize the data loader.

        Args:
            data_dir: Root directory containing stage_1, stage_2, etc.
            strict: If True, treat warnings as errors
        """
        self.data_dir = Path(data_dir)
        self.strict = strict
        self._cache: dict[str, Any] = {}

        if not self.data_dir.exists():
            raise DataLoadError(
                f"Data directory not found: {self.data_dir}",
                filepath=self.data_dir,
            )

    def stage_dir(self, stage: int) -> Path:
        """Get the directory path for a specific stage."""
        return self.data_dir / f"stage_{stage}"

    def _load_cached(
        self,
        cache_key: str,
        loader_func: callable,
    ) -> Any:
        """Load with caching support."""
        if cache_key not in self._cache:
            self._cache[cache_key] = loader_func()
        return self._cache[cache_key]

    def clear_cache(self) -> None:
        """Clear all cached data."""
        self._cache.clear()
        logger.debug("Cache cleared")

    # ==================== Stage 1 Loaders ====================

    def load_config(self) -> Config:
        """
        Load the configuration from stage_1/config.json.

        Returns:
            Validated Config object

        Raises:
            DataLoadError: If file cannot be read
            ValidationError: If data is invalid
        """
        return self._load_cached("config", lambda: self._load_config_impl())

    def _load_config_impl(self) -> Config:
        """Implementation of config loading."""
        filepath = self.stage_dir(1) / "config.json"
        config_file = load_and_validate(filepath, ConfigFile)
        logger.info(f"Loaded config with {len(config_file.config.time_slots)} time slots")
        return config_file.config

    def load_faculty(self) -> list[Faculty]:
        """
        Load faculty data from stage_1/facultyBasic.json.

        Returns:
            List of validated Faculty objects

        Raises:
            DataLoadError: If file cannot be read
            ValidationError: If data is invalid
        """
        return self._load_cached("faculty", lambda: self._load_faculty_impl())

    def _load_faculty_impl(self) -> list[Faculty]:
        """Implementation of faculty loading."""
        filepath = self.stage_dir(1) / "facultyBasic.json"
        faculty_file = load_and_validate(filepath, FacultyFile)
        logger.info(f"Loaded {len(faculty_file.faculty)} faculty members")
        return faculty_file.faculty

    def load_subjects(
        self,
        semester: Optional[int] = None,
        include_electives: bool = True,
    ) -> list[Subject]:
        """
        Load subjects from stage_1 subject files.

        Args:
            semester: If provided, only load subjects for this semester
            include_electives: Whether to include elective subjects

        Returns:
            List of validated Subject objects

        Raises:
            DataLoadError: If file cannot be read
            ValidationError: If data is invalid
        """
        cache_key = f"subjects_{semester}_{include_electives}"
        return self._load_cached(cache_key, lambda: self._load_subjects_impl(semester, include_electives))

    def _load_subjects_impl(
        self,
        semester: Optional[int],
        include_electives: bool,
    ) -> list[Subject]:
        """Implementation of subjects loading."""
        subjects: list[Subject] = []
        stage1_dir = self.stage_dir(1)

        # Determine which files to load
        files_to_load = []
        if semester is None or semester == 1:
            files_to_load.append(("subjects1CoreBasic.json", False))
        if semester is None or semester == 3:
            files_to_load.append(("subjects3CoreBasic.json", False))
            if include_electives:
                files_to_load.append(("subjects3ElectBasic.json", True))

        for filename, is_elective in files_to_load:
            filepath = stage1_dir / filename
            if filepath.exists():
                subject_file = load_and_validate(filepath, SubjectFile)
                # Filter electives if not requested
                if is_elective and not include_electives:
                    continue
                subjects.extend(subject_file.subjects)
                logger.debug(
                    f"Loaded {len(subject_file.subjects)} subjects from {filename}"
                )

        # Filter by semester if specified
        if semester is not None:
            subjects = [s for s in subjects if s.semester == semester]

        logger.info(f"Loaded {len(subjects)} subjects total")
        return subjects

    def load_student_groups(self) -> StudentGroupFile:
        """
        Load student groups from stage_1/studentGroups.json.

        Returns:
            Validated StudentGroupFile object containing all group data

        Raises:
            DataLoadError: If file cannot be read
            ValidationError: If data is invalid
        """
        return self._load_cached("student_groups", lambda: self._load_student_groups_impl())

    def _load_student_groups_impl(self) -> StudentGroupFile:
        """Implementation of student groups loading."""
        filepath = self.stage_dir(1) / "studentGroups.json"
        groups_file = load_and_validate(filepath, StudentGroupFile)
        logger.info(
            f"Loaded {len(groups_file.student_groups)} student groups, "
            f"{len(groups_file.elective_student_groups)} elective groups"
        )
        return groups_file

    def load_room_preferences(self) -> list[RoomPreference]:
        """
        Load room preferences from stage_1/roomPreferences.json.

        Returns:
            List of validated RoomPreference objects

        Raises:
            DataLoadError: If file cannot be read
            ValidationError: If data is invalid
        """
        filepath = self.stage_dir(1) / "roomPreferences.json"
        prefs_file = load_and_validate(filepath, RoomPreferenceFile)
        logger.info(f"Loaded {len(prefs_file.room_preferences)} room preferences")
        return prefs_file.room_preferences

    # ==================== Stage 2 Loaders ====================

    def load_faculty_full(self) -> list[FacultyFull]:
        """
        Load full faculty data from stage_2/faculty2Full.json.

        Returns:
            List of validated FacultyFull objects with assignments

        Raises:
            DataLoadError: If file cannot be read
            ValidationError: If data is invalid
        """
        filepath = self.stage_dir(2) / "faculty2Full.json"
        faculty_file = load_and_validate(filepath, FacultyFullFile)
        logger.info(f"Loaded {len(faculty_file.faculty)} faculty with full assignments")
        return faculty_file.faculty

    def load_subjects_full(self) -> list[SubjectFull]:
        """
        Load full subject data from stage_2/subjects2Full.json.

        Returns:
            List of validated SubjectFull objects with components

        Raises:
            DataLoadError: If file cannot be read
            ValidationError: If data is invalid
        """
        filepath = self.stage_dir(2) / "subjects2Full.json"
        subjects_file = load_and_validate(filepath, SubjectsFullFile)
        logger.info(f"Loaded {len(subjects_file.subjects)} subjects with components")
        return subjects_file.subjects

    def load_all_stage2(self) -> dict[str, Any]:
        """
        Load all Stage 2 data at once.

        Returns:
            Dictionary with all Stage 2 data:
            - faculty_full: List of FacultyFull
            - subjects_full: List of SubjectFull

        Raises:
            DataLoadError: If any file cannot be read
            ValidationError: If any data is invalid
        """
        return {
            "faculty_full": self.load_faculty_full(),
            "subjects_full": self.load_subjects_full(),
        }

    # ==================== Stage 3 Loaders ====================

    def load_teaching_assignments(
        self, semester: int
    ) -> TeachingAssignmentsFile:
        """
        Load teaching assignments for a specific semester.

        Args:
            semester: Semester number (1 or 3)

        Returns:
            TeachingAssignmentsFile with all assignments and statistics

        Raises:
            DataLoadError: If file cannot be read
            ValidationError: If data is invalid
        """
        filepath = self.stage_dir(3) / f"teachingAssignments_sem{semester}.json"
        assignments_file = load_and_validate(filepath, TeachingAssignmentsFile)
        logger.info(
            f"Loaded {len(assignments_file.assignments)} assignments for semester {semester}"
        )
        return assignments_file

    def load_all_teaching_assignments(
        self, semesters: Optional[list[int]] = None
    ) -> dict[int, TeachingAssignmentsFile]:
        """
        Load teaching assignments for multiple semesters.

        Args:
            semesters: List of semester numbers to load (default: [1, 3])

        Returns:
            Dictionary mapping semester to TeachingAssignmentsFile

        Raises:
            DataLoadError: If any file cannot be read
            ValidationError: If any data is invalid
        """
        if semesters is None:
            semesters = [1, 3]

        result = {}
        for sem in semesters:
            filepath = self.stage_dir(3) / f"teachingAssignments_sem{sem}.json"
            if filepath.exists():
                result[sem] = self.load_teaching_assignments(sem)
            else:
                logger.warning(f"Assignments file not found for semester {sem}")
        return result

    def load_overlap_constraints(self) -> StudentGroupOverlapConstraints:
        """
        Load student group overlap constraints from stage_3.

        Returns:
            StudentGroupOverlapConstraints defining scheduling conflicts

        Raises:
            DataLoadError: If file cannot be read
            ValidationError: If data is invalid
        """
        filepath = self.stage_dir(3) / "studentGroupOverlapConstraints.json"
        constraints = load_and_validate(filepath, StudentGroupOverlapConstraints)
        logger.info(
            f"Loaded overlap constraints for {len(constraints.cannot_overlap_with)} groups"
        )
        return constraints

    def load_statistics(self) -> StatisticsFile:
        """
        Load statistics from stage_3/statistics.json.

        Returns:
            StatisticsFile with all semester and combined statistics

        Raises:
            DataLoadError: If file cannot be read
            ValidationError: If data is invalid
        """
        filepath = self.stage_dir(3) / "statistics.json"
        stats = load_and_validate(filepath, StatisticsFile)
        logger.info(
            f"Loaded statistics: {stats.combined.total_assignments} total assignments"
        )
        return stats

    def load_all_stage3(self) -> dict[str, Any]:
        """
        Load all Stage 3 data at once.

        Returns:
            Dictionary with all Stage 3 data:
            - assignments: Dict mapping semester to TeachingAssignmentsFile
            - overlap_constraints: StudentGroupOverlapConstraints
            - statistics: StatisticsFile

        Raises:
            DataLoadError: If any file cannot be read
            ValidationError: If any data is invalid
        """
        return {
            "assignments": self.load_all_teaching_assignments(),
            "overlap_constraints": self.load_overlap_constraints(),
            "statistics": self.load_statistics(),
        }

    def load_scheduling_input(self) -> SchedulingInput:
        """
        Load Stage 4 scheduling input data.

        Returns:
            SchedulingInput: Validated scheduling input data

        Raises:
            DataLoadError: If file cannot be read
            ValidationError: If data is invalid
        """
        return self._load_cached("scheduling_input", lambda: self._load_scheduling_input_impl())

    def _load_scheduling_input_impl(self) -> SchedulingInput:
        """Implementation of scheduling input loading."""
        filepath = self.stage_dir(4) / "schedulingInput.json"
        scheduling_input = load_and_validate(filepath, SchedulingInput)
        logger.info(
            f"Loaded scheduling input: {scheduling_input.metadata.total_assignments} assignments, "
            f"{len(scheduling_input.student_groups)} student groups, "
            f"{scheduling_input.metadata.total_rooms} rooms"
        )
        return scheduling_input

    def load_ai_schedule(self) -> AISchedule:
        """
        Load Stage 5 AI-generated schedule data.

        Returns:
            AISchedule: Validated AI-generated schedule data

        Raises:
            DataLoadError: If file cannot be read
            ValidationError: If data is invalid
        """
        filepath = self.stage_dir(5) / "ai_solved_schedule.json"
        ai_schedule = load_and_validate(filepath, AISchedule)
        logger.info(
            f"Loaded AI schedule: {ai_schedule.metadata.total_sessions} sessions scheduled"
        )
        return ai_schedule

    def load_enriched_timetable(self) -> EnrichedTimetable:
        """
        Load Stage 6 enriched timetable data.

        Returns:
            EnrichedTimetable: Validated enriched timetable data

        Raises:
            DataLoadError: If file cannot be read
            ValidationError: If data is invalid
        """
        filepath = self.stage_dir(6) / "timetable_enriched.json"
        enriched_timetable = load_and_validate(filepath, EnrichedTimetable)
        logger.info(
            f"Loaded enriched timetable: {enriched_timetable.metadata.total_sessions} sessions, "
            f"generated by {enriched_timetable.metadata.generator}"
        )
        return enriched_timetable

    # ==================== Convenience Methods ====================

    def load_all_stage1(self) -> dict[str, Any]:
        """
        Load all Stage 1 data at once.

        Returns:
            Dictionary with all Stage 1 data:
            - config: Config object
            - faculty: List of Faculty
            - subjects: List of Subject
            - student_groups: StudentGroupFile
            - room_preferences: List of RoomPreference

        Raises:
            DataLoadError: If any file cannot be read
            ValidationError: If any data is invalid
        """
        return {
            "config": self.load_config(),
            "faculty": self.load_faculty(),
            "subjects": self.load_subjects(),
            "student_groups": self.load_student_groups(),
            "room_preferences": self.load_room_preferences(),
        }

    def validate_stage1(self) -> list[str]:
        """
        Validate all Stage 1 data and return any warnings.

        Returns:
            List of warning messages (empty if all valid)

        Raises:
            DataLoadError: If any file cannot be read
            ValidationError: If any data is invalid (in strict mode)
        """
        warnings: list[str] = []

        # Load all data (validates on load)
        data = self.load_all_stage1()

        # Cross-validate references
        subject_codes = {s.subject_code for s in data["subjects"]}
        faculty_subjects = set()
        for f in data["faculty"]:
            faculty_subjects.update(f.get_all_subject_codes())

        # Check for unassigned subjects
        unassigned = subject_codes - faculty_subjects
        if unassigned:
            msg = f"Subjects not assigned to any faculty: {unassigned}"
            warnings.append(msg)
            logger.warning(msg)

        # Check for invalid subject references in faculty
        invalid_refs = faculty_subjects - subject_codes
        if invalid_refs:
            msg = f"Faculty references unknown subjects: {invalid_refs}"
            warnings.append(msg)
            logger.warning(msg)

        return warnings


# ==================== Module-level convenience functions ====================


def load_config(filepath: Union[str, Path]) -> Config:
    """Load and validate a config.json file."""
    return load_and_validate(filepath, ConfigFile).config


def load_faculty(filepath: Union[str, Path]) -> list[Faculty]:
    """Load and validate a facultyBasic.json file."""
    return load_and_validate(filepath, FacultyFile).faculty


def load_subjects(filepath: Union[str, Path]) -> list[Subject]:
    """Load and validate a subjects JSON file."""
    return load_and_validate(filepath, SubjectFile).subjects


def load_student_groups(filepath: Union[str, Path]) -> StudentGroupFile:
    """Load and validate a studentGroups.json file."""
    return load_and_validate(filepath, StudentGroupFile)


def load_room_preferences(filepath: Union[str, Path]) -> list[RoomPreference]:
    """Load and validate a roomPreferences.json file."""
    return load_and_validate(filepath, RoomPreferenceFile).room_preferences


# Stage 2 convenience functions


def load_faculty_full(filepath: Union[str, Path]) -> list[FacultyFull]:
    """Load and validate a faculty2Full.json file."""
    return load_and_validate(filepath, FacultyFullFile).faculty


def load_subjects_full(filepath: Union[str, Path]) -> list[SubjectFull]:
    """Load and validate a subjects2Full.json file."""
    return load_and_validate(filepath, SubjectsFullFile).subjects


# Stage 3 convenience functions


def load_teaching_assignments(filepath: Union[str, Path]) -> TeachingAssignmentsFile:
    """Load and validate a teachingAssignments JSON file."""
    return load_and_validate(filepath, TeachingAssignmentsFile)


def load_overlap_constraints(filepath: Union[str, Path]) -> StudentGroupOverlapConstraints:
    """Load and validate a studentGroupOverlapConstraints.json file."""
    return load_and_validate(filepath, StudentGroupOverlapConstraints)


def load_statistics(filepath: Union[str, Path]) -> StatisticsFile:
    """Load and validate a statistics.json file."""
    return load_and_validate(filepath, StatisticsFile)


def load_scheduling_input(filepath: Union[str, Path]) -> SchedulingInput:
    """Load and validate a schedulingInput.json file."""
    return load_and_validate(filepath, SchedulingInput)


def load_ai_schedule(filepath: Union[str, Path]) -> AISchedule:
    """Load and validate an ai_solved_schedule.json file."""
    return load_and_validate(filepath, AISchedule)


# Stage 6 convenience functions

def load_enriched_timetable(filepath: Union[str, Path]) -> EnrichedTimetable:
    """Load and validate a timetable_enriched.json file."""
    return load_and_validate(filepath, EnrichedTimetable)

