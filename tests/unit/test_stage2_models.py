"""
Tests for Stage 2 Pydantic models.

Tests cover:
- SubjectFull and SubjectComponent models
- FacultyFull with assignments and workload stats
- File wrapper models (SubjectsFullFile, FacultyFullFile)
- Validation and computed properties
"""

import pytest
from pydantic import ValidationError

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


# ==================== SubjectComponent Tests ====================


class TestSubjectComponent:
    """Tests for SubjectComponent model."""

    def test_valid_theory_component(self):
        """Test valid theory component."""
        comp = SubjectComponent(
            componentId="CS101_TH",
            componentType="theory",
            credits=3,
            sessionDuration=55,
            sessionsPerWeek=3,
            totalWeeklyMinutes=165,
            mustBeInRoomType="lecture",
            blockSizeSlots=1,
            mustBeContiguous=False,
        )
        assert comp.component_id == "CS101_TH"
        assert comp.component_type == "theory"
        assert comp.credits == 3
        assert comp.session_duration == 55
        assert comp.sessions_per_week == 3
        assert comp.must_be_in_room_type == "lecture"
        assert not comp.must_be_contiguous

    def test_valid_practical_component(self):
        """Test valid practical component."""
        comp = SubjectComponent(
            componentId="CS101_PR",
            componentType="practical",
            credits=1,
            sessionDuration=110,
            sessionsPerWeek=1,
            totalWeeklyMinutes=110,
            mustBeInRoomType="lab",
            blockSizeSlots=2,
            mustBeContiguous=True,
        )
        assert comp.component_id == "CS101_PR"
        assert comp.component_type == "practical"
        assert comp.must_be_in_room_type == "lab"
        assert comp.block_size_slots == 2
        assert comp.must_be_contiguous

    def test_valid_tutorial_component(self):
        """Test valid tutorial component."""
        comp = SubjectComponent(
            componentId="CS101_TU",
            componentType="tutorial",
            credits=1,
            sessionDuration=110,
            sessionsPerWeek=1,
            totalWeeklyMinutes=110,
            mustBeInRoomType="lab",
            blockSizeSlots=2,
            mustBeContiguous=True,
        )
        assert comp.component_type == "tutorial"

    def test_invalid_component_type(self):
        """Test invalid component type is rejected."""
        with pytest.raises(ValidationError):
            SubjectComponent(
                componentId="CS101_XX",
                componentType="invalid",  # Invalid type
                credits=1,
                sessionDuration=55,
                sessionsPerWeek=1,
                totalWeeklyMinutes=55,
                mustBeInRoomType="lecture",
                blockSizeSlots=1,
                mustBeContiguous=False,
            )

    def test_invalid_room_type(self):
        """Test invalid room type is rejected."""
        with pytest.raises(ValidationError):
            SubjectComponent(
                componentId="CS101_TH",
                componentType="theory",
                credits=3,
                sessionDuration=55,
                sessionsPerWeek=3,
                totalWeeklyMinutes=165,
                mustBeInRoomType="seminar",  # Invalid
                blockSizeSlots=1,
                mustBeContiguous=False,
            )


# ==================== SubjectFull Tests ====================


class TestSubjectFull:
    """Tests for SubjectFull model."""

    @pytest.fixture
    def sample_components(self):
        """Create sample components for testing."""
        return [
            SubjectComponent(
                componentId="25MCA11_TH",
                componentType="theory",
                credits=3,
                sessionDuration=55,
                sessionsPerWeek=3,
                totalWeeklyMinutes=165,
                mustBeInRoomType="lecture",
                blockSizeSlots=1,
                mustBeContiguous=False,
            ),
            SubjectComponent(
                componentId="25MCA11_PR",
                componentType="practical",
                credits=1,
                sessionDuration=110,
                sessionsPerWeek=1,
                totalWeeklyMinutes=110,
                mustBeInRoomType="lab",
                blockSizeSlots=2,
                mustBeContiguous=True,
            ),
        ]

    def test_valid_core_subject(self, sample_components):
        """Test valid core subject."""
        subject = SubjectFull(
            subjectCode="25MCA11",
            shortCode="PwP",
            title="Programming with Python",
            creditPattern=[3, 0, 1],
            totalCredits=4,
            department="MCA",
            semester=1,
            isElective=False,
            type="core",
            components=sample_components,
        )
        assert subject.subject_code == "25MCA11"
        assert subject.short_code == "PwP"
        assert subject.total_credits == 4
        assert not subject.is_elective
        assert subject.type == "core"
        assert len(subject.components) == 2

    def test_valid_elective_subject(self, sample_components):
        """Test valid elective subject."""
        subject = SubjectFull(
            subjectCode="24MCAAD1",
            shortCode="AIOT",
            title="Artificial Intelligence of Things",
            creditPattern=[0, 1, 2],
            totalCredits=3,
            department="MCA",
            semester=3,
            isElective=True,
            type="elective",
            components=sample_components,
        )
        assert subject.is_elective
        assert subject.type == "elective"

    def test_diff_subject_with_fixed_timing(self):
        """Test diff subject with fixed timing."""
        subject = SubjectFull(
            subjectCode="24MCAP1",
            shortCode="Project",
            title="Project - Phase 1",
            creditPattern=[0, 0, 6],
            totalCredits=6,
            department="MCA",
            semester=3,
            isElective=False,
            type="diff",
            priority="high",
            assignedTo="all_faculty",
            sections=["A", "B"],
            fixedTiming=FixedTiming(
                day="Tue",
                slots=["S6", "S7"],
                duration=110,
            ),
            components=[],
        )
        assert subject.type == "diff"
        assert subject.priority == "high"
        assert subject.fixed_timing is not None
        assert subject.fixed_timing.day == "Tue"
        assert subject.fixed_timing.slots == ["S6", "S7"]

    def test_credit_properties(self, sample_components):
        """Test credit property accessors."""
        subject = SubjectFull(
            subjectCode="25MCA11",
            shortCode="PwP",
            title="Programming with Python",
            creditPattern=[3, 0, 1],
            totalCredits=4,
            department="MCA",
            semester=1,
            isElective=False,
            type="core",
            components=sample_components,
        )
        assert subject.theory_credits == 3
        assert subject.tutorial_credits == 0
        assert subject.practical_credits == 1

    def test_get_component(self, sample_components):
        """Test get_component method."""
        subject = SubjectFull(
            subjectCode="25MCA11",
            shortCode="PwP",
            title="Programming with Python",
            creditPattern=[3, 0, 1],
            totalCredits=4,
            department="MCA",
            semester=1,
            isElective=False,
            type="core",
            components=sample_components,
        )
        comp = subject.get_component("25MCA11_TH")
        assert comp is not None
        assert comp.component_type == "theory"

        missing = subject.get_component("MISSING")
        assert missing is None

    def test_get_components_by_type(self, sample_components):
        """Test get_components_by_type method."""
        subject = SubjectFull(
            subjectCode="25MCA11",
            shortCode="PwP",
            title="Programming with Python",
            creditPattern=[3, 0, 1],
            totalCredits=4,
            department="MCA",
            semester=1,
            isElective=False,
            type="core",
            components=sample_components,
        )
        theory = subject.get_components_by_type("theory")
        assert len(theory) == 1
        assert theory[0].component_id == "25MCA11_TH"

        practical = subject.get_components_by_type("practical")
        assert len(practical) == 1

    def test_invalid_credit_pattern_length(self):
        """Test invalid credit pattern length is rejected."""
        with pytest.raises(ValidationError):
            SubjectFull(
                subjectCode="CS101",
                shortCode="CS",
                title="Computer Science",
                creditPattern=[3, 1],  # Only 2 values
                totalCredits=4,
                department="CS",
                semester=1,
                isElective=False,
                type="core",
                components=[],
            )


# ==================== SubjectsFullFile Tests ====================


class TestSubjectsFullFile:
    """Tests for SubjectsFullFile model."""

    @pytest.fixture
    def sample_subjects(self):
        """Create sample subjects for testing."""
        return [
            SubjectFull(
                subjectCode="25MCA11",
                shortCode="PwP",
                title="Programming with Python",
                creditPattern=[3, 0, 1],
                totalCredits=4,
                department="MCA",
                semester=1,
                isElective=False,
                type="core",
                components=[],
            ),
            SubjectFull(
                subjectCode="24MCAAD1",
                shortCode="AIOT",
                title="AI of Things",
                creditPattern=[0, 1, 2],
                totalCredits=3,
                department="MCA",
                semester=3,
                isElective=True,
                type="elective",
                components=[],
            ),
        ]

    def test_get_subject(self, sample_subjects):
        """Test get_subject method."""
        file = SubjectsFullFile(subjects=sample_subjects)
        
        subj = file.get_subject("25MCA11")
        assert subj is not None
        assert subj.title == "Programming with Python"

        missing = file.get_subject("MISSING")
        assert missing is None

    def test_get_subjects_by_semester(self, sample_subjects):
        """Test get_subjects_by_semester method."""
        file = SubjectsFullFile(subjects=sample_subjects)
        
        sem1 = file.get_subjects_by_semester(1)
        assert len(sem1) == 1
        assert sem1[0].subject_code == "25MCA11"

        sem3 = file.get_subjects_by_semester(3)
        assert len(sem3) == 1
        assert sem3[0].is_elective

    def test_get_elective_subjects(self, sample_subjects):
        """Test get_elective_subjects method."""
        file = SubjectsFullFile(subjects=sample_subjects)
        electives = file.get_elective_subjects()
        assert len(electives) == 1
        assert electives[0].subject_code == "24MCAAD1"

    def test_get_core_subjects(self, sample_subjects):
        """Test get_core_subjects method."""
        file = SubjectsFullFile(subjects=sample_subjects)
        core = file.get_core_subjects()
        assert len(core) == 1
        assert core[0].subject_code == "25MCA11"


# ==================== FacultyFull Tests ====================


class TestFacultyFull:
    """Tests for FacultyFull model."""

    @pytest.fixture
    def sample_faculty(self):
        """Create sample faculty for testing."""
        return FacultyFull(
            facultyId="MM",
            name="Dr M. Manjunath",
            designation="Associate Professor",
            department="MCA",
            primaryAssignments=[
                PrimaryAssignment(
                    subjectCode="24MCAAD1",
                    semester=3,
                    sections=["A", "B"],
                    studentGroupIds=["ELEC_AD_A1", "ELEC_AD_B1"],
                    componentIds=["24MCAAD1_TU", "24MCAAD1_PR"],
                    componentTypes=["tutorial", "practical"],
                    role="primary",
                    weeklyHoursPerSection=6,
                    totalWeeklyHours=12,
                    sessionsPerWeekPerSection=3,
                    totalSessionsPerWeek=6,
                ),
                PrimaryAssignment(
                    subjectCode="25MCA15",
                    semester=1,
                    sections=["B"],
                    studentGroupIds=["MCA_SEM1_B"],
                    componentIds=["25MCA15_TH"],
                    componentTypes=["theory"],
                    role="primary",
                    weeklyHoursPerSection=3,
                    totalWeeklyHours=3,
                    sessionsPerWeekPerSection=3,
                    totalSessionsPerWeek=3,
                ),
            ],
            supportingAssignments=[
                SupportingAssignment(
                    subjectCode="25MCA17",
                    semester=1,
                    sections=["A"],
                    studentGroupIds=["MCA_SEM1_A"],
                    componentIds=["25MCA17_TU", "25MCA17_PR"],
                    componentTypes=["tutorial", "practical"],
                    role="supporting",
                    weeklyHoursPerSection=6,
                    totalWeeklyHours=6,
                    sessionsPerWeekPerSection=3,
                    totalSessionsPerWeek=3,
                ),
            ],
            workloadStats=WorkloadStats(
                theoryHours=3,
                tutorialHours=4,
                practicalHours=10,
                totalSessions=10,
                totalWeeklyHours=17,
            ),
        )

    def test_valid_faculty(self, sample_faculty):
        """Test valid faculty creation."""
        assert sample_faculty.faculty_id == "MM"
        assert sample_faculty.name == "Dr M. Manjunath"
        assert sample_faculty.designation == "Associate Professor"
        assert len(sample_faculty.primary_assignments) == 2
        assert len(sample_faculty.supporting_assignments) == 1

    def test_workload_stats(self, sample_faculty):
        """Test workload stats."""
        stats = sample_faculty.workload_stats
        assert stats.theory_hours == 3
        assert stats.tutorial_hours == 4
        assert stats.practical_hours == 10
        assert stats.total_weekly_hours == 17

    def test_get_primary_assignment(self, sample_faculty):
        """Test get_primary_assignment method."""
        assign = sample_faculty.get_primary_assignment("24MCAAD1")
        assert assign is not None
        assert assign.semester == 3
        assert "tutorial" in assign.component_types

        missing = sample_faculty.get_primary_assignment("MISSING")
        assert missing is None

    def test_get_assignments_for_semester(self, sample_faculty):
        """Test get_assignments_for_semester method."""
        sem1 = sample_faculty.get_assignments_for_semester(1)
        assert len(sem1) == 1
        assert sem1[0].subject_code == "25MCA15"

        sem3 = sample_faculty.get_assignments_for_semester(3)
        assert len(sem3) == 1
        assert sem3[0].subject_code == "24MCAAD1"

    def test_total_subjects(self, sample_faculty):
        """Test total_subjects property."""
        # 2 primary + 1 supporting = 3 unique subjects
        assert sample_faculty.total_subjects == 3

    def test_is_supporting_only(self, sample_faculty):
        """Test is_supporting_only property."""
        assert not sample_faculty.is_supporting_only

        # Create faculty with only supporting assignments
        supporting_only = FacultyFull(
            facultyId="XX",
            name="Test Faculty",
            designation="Assistant Professor",
            department="CS",
            primaryAssignments=[],
            supportingAssignments=[
                SupportingAssignment(
                    subjectCode="CS101",
                    semester=1,
                    sections=["A", "B"],
                    studentGroupIds=["CS_SEM1_A", "CS_SEM1_B"],
                    componentIds=["CS101_TU", "CS101_PR"],
                    componentTypes=["tutorial", "practical"],
                    role="supporting",
                    weeklyHoursPerSection=6,
                    totalWeeklyHours=12,
                    sessionsPerWeekPerSection=3,
                    totalSessionsPerWeek=6,
                ),
            ],
            workloadStats=WorkloadStats(
                theoryHours=0,
                tutorialHours=0,
                practicalHours=0,
                totalSessions=0,
                totalWeeklyHours=0,
            ),
        )
        assert supporting_only.is_supporting_only


# ==================== FacultyFullFile Tests ====================


class TestFacultyFullFile:
    """Tests for FacultyFullFile model."""

    @pytest.fixture
    def sample_faculty_list(self):
        """Create sample faculty list for testing."""
        return [
            FacultyFull(
                facultyId="MM",
                name="Dr M. Manjunath",
                designation="Associate Professor",
                department="MCA",
                primaryAssignments=[
                    PrimaryAssignment(
                        subjectCode="25MCA15",
                        semester=1,
                        sections=["B"],
                        studentGroupIds=["MCA_SEM1_B"],
                        componentIds=["25MCA15_TH"],
                        componentTypes=["theory"],
                        role="primary",
                        weeklyHoursPerSection=3,
                        totalWeeklyHours=3,
                        sessionsPerWeekPerSection=3,
                        totalSessionsPerWeek=3,
                    ),
                ],
                supportingAssignments=[],
                workloadStats=WorkloadStats(
                    theoryHours=3,
                    tutorialHours=0,
                    practicalHours=0,
                    totalSessions=3,
                    totalWeeklyHours=3,
                ),
            ),
            FacultyFull(
                facultyId="SM",
                name="Ms Swathi M",
                designation="Assistant Professor",
                department="MCA",
                primaryAssignments=[
                    PrimaryAssignment(
                        subjectCode="25MCA15",
                        semester=1,
                        sections=["A"],
                        studentGroupIds=["MCA_SEM1_A"],
                        componentIds=["25MCA15_TH"],
                        componentTypes=["theory"],
                        role="primary",
                        weeklyHoursPerSection=3,
                        totalWeeklyHours=3,
                        sessionsPerWeekPerSection=3,
                        totalSessionsPerWeek=3,
                    ),
                ],
                supportingAssignments=[],
                workloadStats=WorkloadStats(
                    theoryHours=3,
                    tutorialHours=0,
                    practicalHours=0,
                    totalSessions=3,
                    totalWeeklyHours=3,
                ),
            ),
        ]

    def test_get_faculty(self, sample_faculty_list):
        """Test get_faculty method."""
        file = FacultyFullFile(faculty=sample_faculty_list)
        
        fac = file.get_faculty("MM")
        assert fac is not None
        assert fac.name == "Dr M. Manjunath"

        missing = file.get_faculty("MISSING")
        assert missing is None

    def test_get_faculty_by_subject(self, sample_faculty_list):
        """Test get_faculty_by_subject method."""
        file = FacultyFullFile(faculty=sample_faculty_list)
        faculty = file.get_faculty_by_subject("25MCA15")
        assert len(faculty) == 2
        
        faculty_ids = {f.faculty_id for f in faculty}
        assert faculty_ids == {"MM", "SM"}

    def test_get_faculty_by_department(self, sample_faculty_list):
        """Test get_faculty_by_department method."""
        file = FacultyFullFile(faculty=sample_faculty_list)
        faculty = file.get_faculty_by_department("MCA")
        assert len(faculty) == 2


# ==================== FixedTiming Tests ====================


class TestFixedTiming:
    """Tests for FixedTiming model."""

    def test_valid_fixed_timing(self):
        """Test valid fixed timing creation."""
        timing = FixedTiming(
            day="Tue",
            slots=["S6", "S7"],
            duration=110,
        )
        assert timing.day == "Tue"
        assert timing.slots == ["S6", "S7"]
        assert timing.duration == 110

    def test_fixed_timing_without_duration(self):
        """Test fixed timing without duration (optional)."""
        timing = FixedTiming(
            day="Fri",
            slots=["S7"],
        )
        assert timing.day == "Fri"
        assert timing.slots == ["S7"]
        assert timing.duration is None
