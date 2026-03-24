"""
Pytest configuration and shared fixtures for the timetable test suite.

This module provides:
- Common fixtures for all tests
- Sample data fixtures based on actual stage data
- Temporary directory fixtures
- Configuration fixtures
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generator

import pytest

if TYPE_CHECKING:
    from timetable.config.settings import Settings


# ==================== Path Fixtures ====================


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def stage1_fixtures_dir(fixtures_dir: Path) -> Path:
    """Return the path to stage1 fixtures."""
    return fixtures_dir / "stage1"


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_data_dir(temp_dir: Path) -> Path:
    """Create a temporary data directory structure matching stages."""
    for stage in ["stage_1", "stage_2", "stage_3", "stage_4", "stage_5", "stage_6"]:
        (temp_dir / stage).mkdir()
        (temp_dir / stage / "scripts").mkdir()
    return temp_dir


# ==================== Sample Data Fixtures ====================


@pytest.fixture
def sample_config() -> dict[str, Any]:
    """Sample configuration matching stage_1/config.json structure."""
    return {
        "config": {
            "dayStart": "09:00",
            "dayEnd": "16:30",
            "weekdays": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"],
            "daySlotPattern": {
                "Mon": ["S1", "S2", "S3", "S4", "S5", "S6", "S7"],
                "Tue": ["S1", "S2", "S3", "S4", "S5", "S6", "S7"],
                "Wed": ["S1", "S2", "S3", "S4", "S5", "S6", "S7"],
                "Thu": ["S1", "S2", "S3", "S4", "S5", "S6", "S7"],
                "Fri": ["S1", "S2", "S3", "S4", "S5", "S6", "S7"],
                "Sat": ["S1", "S2", "S3", "S4"],
            },
            "breakWindows": [
                {"start": "10:50", "end": "11:05", "type": "short"},
                {"start": "12:55", "end": "13:45", "type": "lunch"},
            ],
            "timeSlots": [
                {"slotId": "S1", "start": "09:00", "end": "09:55", "lengthMinutes": 55},
                {"slotId": "S2", "start": "09:55", "end": "10:50", "lengthMinutes": 55},
                {"slotId": "S3", "start": "11:05", "end": "12:00", "lengthMinutes": 55},
                {"slotId": "S4", "start": "12:00", "end": "12:55", "lengthMinutes": 55},
                {"slotId": "S5", "start": "13:45", "end": "14:40", "lengthMinutes": 55},
                {"slotId": "S6", "start": "14:40", "end": "15:35", "lengthMinutes": 55},
                {"slotId": "S7", "start": "15:35", "end": "16:30", "lengthMinutes": 55},
            ],
            "theorySessionMinutes": 55,
            "labTutorialSessionMinutes": 110,
            "creditToHours": {"theory": 1, "tutorial": 2, "practical": 2},
            "validSlotCombinations": {
                "single": ["S1", "S2", "S3", "S4", "S5", "S6", "S7"],
                "double": ["S1+S2", "S3+S4", "S5+S6", "S6+S7"],
                "saturday": ["S1+S2", "S3+S4"],
            },
            "sessionTypes": {
                "theory": {"duration": 55, "requiresContiguous": False},
                "tutorial": {"duration": 110, "requiresContiguous": True},
                "practical": {"duration": 110, "requiresContiguous": True},
            },
            "resourceConstraints": {
                "maxConsecutiveSlotsPerFaculty": 5,
                "maxDailySlotsPerStudentGroup": 7,
                "minGapBetweenSameFaculty": 0,
            },
            "resources": {
                "rooms": [
                    {"roomId": "AB-402", "type": "lecture", "capacity": 60},
                    {"roomId": "AB-411", "type": "lecture", "capacity": 60},
                    {"roomId": "AB-412", "type": "lecture", "capacity": 60},
                    {"roomId": "LAB-1", "type": "lab", "capacity": 60},
                    {"roomId": "LAB-2", "type": "lab", "capacity": 60},
                ],
            },
        }
    }


@pytest.fixture
def sample_faculty() -> dict[str, Any]:
    """Sample faculty data matching actual schema."""
    return {
        "facultyBasic": [
            {
                "facultyId": "FAC001",
                "name": "Dr. John Smith",
                "designation": "Professor",
                "assignedSubjects": ["CS101"],
                "supportingSubjects": ["CS102"],
            },
            {
                "facultyId": "FAC002",
                "name": "Dr. Jane Doe",
                "designation": "Associate Professor",
                "assignedSubjects": [{"CS301": ["A", "B"]}],
                "supportingSubjects": [{"CS102": ["A"]}],
            },
        ]
    }


@pytest.fixture
def sample_subjects() -> dict[str, Any]:
    """Sample subjects data matching actual schema."""
    return {
        "subjects": [
            {
                "subjectCode": "CS101",
                "shortCode": "IP",
                "title": "Introduction to Programming",
                "creditPattern": [3, 0, 1],
                "totalCredits": 4,
                "department": "MCA",
                "semester": 1,
                "isElective": False,
                "type": "core",
            },
            {
                "subjectCode": "CS301",
                "shortCode": "DS",
                "title": "Data Structures",
                "creditPattern": [3, 1, 0],
                "totalCredits": 4,
                "department": "MCA",
                "semester": 3,
                "isElective": False,
                "type": "core",
            },
        ]
    }


@pytest.fixture
def sample_student_groups() -> dict[str, Any]:
    """Sample student groups data."""
    return {
        "studentGroups": [
            {
                "semester": 1,
                "section": "A",
                "studentCount": 45,
                "studentGroupId": "SEM1-A",
                "compulsorySubjects": ["CS101", "CS102"],
            },
            {
                "semester": 1,
                "section": "B",
                "studentCount": 42,
                "studentGroupId": "SEM1-B",
                "compulsorySubjects": ["CS101", "CS102"],
            },
            {
                "semester": 3,
                "section": "A",
                "studentCount": 48,
                "studentGroupId": "SEM3-A",
                "compulsorySubjects": ["CS301"],
            },
        ],
        "electiveSubjectGroups": [
            {
                "groupId": "ELEC_CAT_AD",
                "groupName": "Advanced Development",
                "description": "AD electives",
                "subjectCodes": ["AD1", "AD2"],
            }
        ],
        "electiveStudentGroups": [
            {
                "studentGroupId": "ELEC_AD_A1",
                "parentGroupId": "ELEC_CAT_AD",
                "studentCount": 30,
                "sections": ["A"],
                "description": "AD sub-group A",
                "sourceSections": ["SEM3-A"],
            }
        ],
        "groupHierarchy": {
            "SEM3-A": {
                "children": ["ELEC_AD_A1"],
                "description": "Section A parent",
            }
        },
    }


@pytest.fixture
def sample_teaching_assignment() -> dict[str, Any]:
    """Sample teaching assignment from stage 3."""
    return {
        "assignmentId": "ASSIGN-001",
        "subjectId": "CS101",
        "subjectName": "Introduction to Programming",
        "facultyId": "FAC001",
        "facultyName": "Dr. John Smith",
        "studentGroups": ["SEM1-A", "SEM1-B"],
        "sessionType": "theory",
        "sessionsPerWeek": 3,
        "roomPreference": {"type": "lecture", "preferredRooms": ["AB-402"]},
    }


@pytest.fixture
def sample_scheduling_input() -> dict[str, Any]:
    """Sample scheduling input from stage 4."""
    return {
        "metadata": {
            "generatedAt": "2024-01-15T10:00:00Z",
            "version": "4.0",
            "semester": "odd",
        },
        "timeSlots": [
            {"slotId": "S1", "start": "09:00", "end": "09:55"},
            {"slotId": "S2", "start": "09:55", "end": "10:50"},
        ],
        "rooms": [
            {"roomId": "AB-402", "type": "lecture", "capacity": 60},
        ],
        "sessions": [
            {
                "sessionId": "SES-001",
                "assignmentId": "ASSIGN-001",
                "sessionType": "theory",
                "duration": 1,
                "facultyId": "FAC001",
                "studentGroups": ["SEM1-A", "SEM1-B"],
            }
        ],
    }


# ==================== File Creation Fixtures ====================


@pytest.fixture
def config_file(temp_dir: Path, sample_config: dict[str, Any]) -> Path:
    """Create a temporary config.json file."""
    config_path = temp_dir / "config.json"
    config_path.write_text(json.dumps(sample_config, indent=2))
    return config_path


@pytest.fixture
def stage1_data_dir(
    temp_data_dir: Path,
    sample_config: dict[str, Any],
    sample_faculty: dict[str, Any],
    sample_subjects: dict[str, Any],
    sample_student_groups: dict[str, Any],
) -> Path:
    """Create a complete stage_1 directory with sample data."""
    stage1_dir = temp_data_dir / "stage_1"

    # Write all stage 1 files
    (stage1_dir / "config.json").write_text(json.dumps(sample_config, indent=2))
    (stage1_dir / "facultyBasic.json").write_text(
        json.dumps({"faculty": sample_faculty["facultyBasic"]}, indent=2)
    )
    (stage1_dir / "subjects1CoreBasic.json").write_text(
        json.dumps(sample_subjects, indent=2)
    )
    (stage1_dir / "studentGroups.json").write_text(
        json.dumps(sample_student_groups, indent=2)
    )

    return stage1_dir


# ==================== Settings Fixtures ====================


@pytest.fixture
def test_settings(temp_data_dir: Path) -> "Settings":
    """Create test settings with temporary directories."""
    # Defer import to avoid circular imports
    from timetable.config.settings import Settings

    return Settings(
        data_dir=temp_data_dir,
        log_level="DEBUG",
        log_file=None,  # Don't write to log file during tests
    )


@pytest.fixture
def env_settings(temp_data_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Set environment variables for settings tests."""
    monkeypatch.setenv("TIMETABLE_DATA_DIR", str(temp_data_dir))
    monkeypatch.setenv("TIMETABLE_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("TIMETABLE_STRICT_MODE", "true")


# ==================== Assertion Helpers ====================


def assert_json_valid(data: dict[str, Any]) -> None:
    """Assert that data can be serialized to valid JSON."""
    try:
        json.dumps(data)
    except (TypeError, ValueError) as e:
        pytest.fail(f"Data is not JSON serializable: {e}")


def assert_keys_present(data: dict[str, Any], required_keys: list[str]) -> None:
    """Assert that all required keys are present in a dictionary."""
    missing = [key for key in required_keys if key not in data]
    if missing:
        pytest.fail(f"Missing required keys: {missing}")


# Make assertion helpers available to all tests
@pytest.fixture
def json_assertions() -> type:
    """Provide assertion helper functions."""

    class Assertions:
        @staticmethod
        def json_valid(data: dict[str, Any]) -> None:
            assert_json_valid(data)

        @staticmethod
        def keys_present(data: dict[str, Any], required_keys: list[str]) -> None:
            assert_keys_present(data, required_keys)

    return Assertions
