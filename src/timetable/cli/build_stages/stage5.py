"""
Stage 5 build functionality.
"""

from pathlib import Path
from typing import List, Tuple, Optional

from timetable.core.loader import DataLoader
from timetable.core.exceptions import TimetableError
from . import run_script, get_scripts_dir


def build_stage5(data_path: Path, validate: bool = False, verbose: bool = False) -> List[Tuple[str, bool, str]]:
    """
    Build Stage 5 data from Stage 4 inputs.

    Generates:
    - ai_solved_schedule.json (AI-optimized conflict-free schedule)
    - scheduleTemplate.json (Phase 1 template format)

    The AI scheduler runs first to generate an optimized schedule,
    then the template generator creates the Phase 1 format from Stage 4 data.

    Args:
        data_path: Path to the data directory
        validate: Whether to run validation after building
        verbose: Whether to show detailed output

    Returns:
        List of (description, success, output) tuples
    """
    scripts_dir = get_scripts_dir(5)

    if not scripts_dir.exists():
        return [("Stage 5 scripts", False, f"Scripts directory not found: {scripts_dir}")]

    results = []

    # Check prerequisites
    loader = DataLoader(data_path)
    try:
        scheduling_input = loader.load_scheduling_input()
        results.append(("Prerequisites check", True, f"Stage 4 data found: {len(scheduling_input.assignments)} assignments"))
    except TimetableError as e:
        results.append(("Prerequisites check", False, f"Stage 4 data not found or invalid: {e}"))
        return results

    build_scripts = [
        ("generate_schedule_template.py", "Generating schedule template (Phase 1 format)"),
        ("schedule.py", "AI-optimized schedule generation"),
    ]

    if validate:
        build_scripts.append(("validate_stage5.py", "Validating Stage 5 data"))

    # Run build scripts
    for script_name, description in build_scripts:
        script_path = scripts_dir / script_name

        if not script_path.exists():
            results.append((description, False, f"Script not found: {script_path}"))
            continue

        success, output = run_script(script_path, data_path, description)
        results.append((description, success, output))

    return results