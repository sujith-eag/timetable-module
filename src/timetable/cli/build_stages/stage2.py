"""
Stage 2 build functionality.
"""

from pathlib import Path
from typing import List, Tuple, Optional

from timetable.core.loader import DataLoader
from timetable.core.exceptions import TimetableError
from . import run_script, get_scripts_dir


def build_stage2(data_path: Path, validate: bool = True, verbose: bool = False) -> List[Tuple[str, bool, str]]:
    """
    Build Stage 2 data from Stage 1 inputs.

    Generates:
    - subjects2Full.json (subjects with expanded components)
    - faculty2Full.json (faculty with workload calculations)

    Args:
        data_path: Path to the data directory
        validate: Whether to run validation after building
        verbose: Whether to show detailed output

    Returns:
        List of (description, success, output) tuples
    """
    scripts_dir = get_scripts_dir(2)

    if not scripts_dir.exists():
        return [("Stage 2 scripts", False, f"Scripts directory not found: {scripts_dir}")]

    results = []

    # Initialize loader and detect active semesters
    loader = DataLoader(data_path)
    
    # Log detected semesters
    if loader.has_semester_detection():
        active_semesters = loader.get_active_semesters()
        results.append((
            "Semester Detection",
            True,
            f"Active semesters detected: {active_semesters}"
        ))
    else:
        results.append((
            "Semester Detection",
            False,
            "Could not detect active semesters from studentGroups.json. Will load all available data."
        ))

    # Check prerequisites
    try:
        subjects = loader.load_subjects()
        faculty = loader.load_faculty()
        results.append(("Prerequisites check", True, f"Stage 1 data found: {len(subjects)} subjects, {len(faculty)} faculty"))
    except TimetableError as e:
        results.append(("Prerequisites check", False, f"Stage 1 data not found or invalid: {e}"))
        return results

    build_scripts = [
        ("build_subjects_full.py", "Building subjects with components"),
        ("build_faculty_full.py", "Building faculty with workload"),
    ]

    if validate:
        build_scripts.append(("validate_stage2.py", "Validating Stage 2 data"))

    for script_name, description in build_scripts:
        script_path = scripts_dir / script_name

        if not script_path.exists():
            results.append((description, False, f"Script not found: {script_path}"))
            continue

        success, output = run_script(script_path, data_path, description)
        results.append((description, success, output))

    return results


def get_stage2_scripts() -> List[str]:
    """Return list of scripts for Stage 2."""
    return ["build_subjects_full.py", "build_faculty_full.py", "validate_stage2.py"]