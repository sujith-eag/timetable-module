"""
Stage 3 build functionality.
"""

from pathlib import Path
from typing import List, Tuple, Optional

from timetable.core.loader import DataLoader
from timetable.core.exceptions import TimetableError
from timetable.core.semester_detector import detect_active_semesters
from . import run_script, get_scripts_dir


def _detect_semesters(data_path: Path) -> List[int]:
    """
    Detect which semesters are present in the project.
    
    Uses studentGroups.json analysis to determine active semesters.
    Falls back to checking Stage 2 faculty data if detection fails.
    Semesters are built in pairs: 1&3 or 2&4.
    
    Args:
        data_path: Path to the data directory
        
    Returns:
        List of semester numbers present (e.g., [1, 3] or [2, 4])
    """
    try:
        # Primary method: detect from studentGroups.json
        loader = DataLoader(data_path)
        if loader.has_semester_detection():
            return list(loader.get_active_semesters())
        
        # Fallback: check faculty assignments in Stage 2
        faculty = loader.load_faculty_full()
        semesters_present = []
        
        for faculty_member in faculty:
            for assignment in faculty_member.get("primaryAssignments", []):
                sem = assignment.get("semester")
                if sem and sem not in semesters_present:
                    semesters_present.append(sem)
        
        if semesters_present:
            return sorted(semesters_present)
        
    except Exception:
        pass
    
    # If all detection fails, default to Sem 1&3 (legacy behavior)
    return [1, 3]


def build_stage3(data_path: Path, validate: bool = True, reports: bool = True, verbose: bool = False) -> List[Tuple[str, bool, str]]:
    """
    Build Stage 3 data from Stage 2 inputs.

    Generates:
    - teachingAssignments_sem1/2/3/4.json (as applicable)
    - studentGroupOverlapConstraints.json
    - statistics.json
    - reports/ (markdown reports)

    Handles both semester pairs: 1&3 or 2&4

    Args:
        data_path: Path to the data directory
        validate: Whether to run validation after building
        reports: Whether to generate reports
        verbose: Whether to show detailed output

    Returns:
        List of (description, success, output) tuples
    """
    scripts_dir = get_scripts_dir(3)

    if not scripts_dir.exists():
        return [("Stage 3 scripts", False, f"Scripts directory not found: {scripts_dir}")]

    results = []

    # Initialize loader and logging
    loader = DataLoader(data_path)

    # Check prerequisites
    try:
        faculty = loader.load_faculty_full()
        subjects = loader.load_subjects_full()
        results.append(("Prerequisites check", True, f"Stage 2 data found: {len(subjects)} subjects, {len(faculty)} faculty"))
    except TimetableError as e:
        results.append(("Prerequisites check", False, f"Stage 2 data not found or invalid: {e}"))
        return results

    # Detect which semesters to build
    semesters_to_build = _detect_semesters(data_path)
    results.append((
        "Semester Detection",
        True,
        f"Will build assignments for Semester(s): {', '.join(map(str, semesters_to_build))}"
    ))
    
    # Build scripts based on detected semesters
    build_scripts = [
        ("generate_overlap_matrix.py", "Generating overlap constraints"),
    ]
    
    # Add semester-specific assignment builders
    for sem in semesters_to_build:
        script_name = f"build_assignments_sem{sem}.py"
        description = f"Building Semester {sem} assignments"
        build_scripts.append((script_name, description))
    
    if validate:
        build_scripts.append(("validate_stage3.py", "Validating assignments"))

    build_scripts.append(("generate_statistics.py", "Generating statistics"))

    if reports:
        build_scripts.append(("generate_reports.py", "Generating reports"))

    for script_name, description in build_scripts:
        script_path = scripts_dir / script_name

        if not script_path.exists():
            results.append((description, False, f"Script not found: {script_path}"))
            continue

        success, output = run_script(script_path, data_path, description)
        results.append((description, success, output))

    return results


def get_stage3_scripts() -> List[str]:
    """Return list of scripts for Stage 3."""
    return [
        "generate_overlap_matrix.py",
        "build_assignments_sem3.py",
        "build_assignments_sem1.py",
        "validate_stage3.py",
        "generate_statistics.py",
        "generate_reports.py",
    ]