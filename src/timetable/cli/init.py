"""
Init command for timetable CLI.

Initializes a new timetable project with template files.
"""

import shutil
from pathlib import Path
from typing import Optional

import click

from timetable.config.settings import get_settings
from .utils import (
    print_success,
    print_error,
    print_info,
    print_header,
)


# Configuration for project initialization
INIT_CONFIG = {
    "directories": [
        "stage_1",
        "stage_2",
        "stage_3", 
        "stage_4",
        "stage_5",
        "stage_6",
        "logs"
    ],
    # Required Stage 1 template files for Sem 1&3 or Sem 2&4
    "required_files": [
        "config.json",
        "facultyBasic.json",
        "studentGroups.json",
        "roomPreferences.json",
    ],
    "sem13_files": [
        "subjects1CoreBasic.json",
        "subjects1Diff.json",
        "subjects3CoreBasic.json",
        "subjects3Diff.json",
        "elective3Differentiation.json",
        "faculty3Basic.json",
        "student3Groups.json",
        "room3Preferences.json",
    ],
    "sem24_files": [
        "subjects2CoreBasic.json",
        "subjects2ElectBasic.json",
        "subjects2Diff.json",
        "elective2Differentiation.json",
        "subjects4CoreBasic.json",
        "subjects4ElectBasic.json",
        "subjects4Diff.json",
    ],
}


def _check_python_environment(verbose: bool) -> None:
    """
    Check the Python environment and warn if using potentially wrong venv.
    
    This helps catch the common issue where multiple venvs exist and the
    wrong one is being used, resulting in missing template files.
    
    When working with editable installs (-e), checks for outdated package
    installations that may be missing recent functionality.
    """
    import sys
    import timetable
    from pathlib import Path
    
    venv_path = Path(sys.prefix)
    package_location = Path(timetable.__file__).parent
    
    # Check if we're in a virtual environment
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    if not in_venv:
        print_info("⚠️ Warning: Not running in a virtual environment")
        print_info("   Some features may not work correctly")
        return
    
    # Detect if using outdated package from different venv
    # The main issue to detect: package comes from obsidian-vaults old venv
    if "obsidian-vaults" in str(package_location):
        print_info("⚠️ Warning: Using outdated timetable package")
        print_info(f"   Location: {package_location}")
        print_info("   This venv has an old version without recent features.")
        print_info("   → Solution: pip install -e .")
        return
    
    # Show environment info in verbose mode if environment is correct
    if verbose:
        print_info(f"✓ Python environment: {venv_path}")
        print_info(f"✓ Package location: {package_location.parent}")


@click.command()

@click.option(
    "-d", "--data-dir",
    type=click.Path(exists=False),
    help="Path to the timetable project directory.",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing files.",
)
@click.pass_context
def init(ctx: click.Context, data_dir: Optional[str], force: bool) -> None:
    """
    Initialize a new timetable project.

    Creates the project directory and sets up the stage structure with template files.
    The project will have its own configuration and data isolation.

    \b
    Examples:
        timetable init --data-dir ~/projects/my_university_2026
        timetable init -d ./my_timetable_project --force
    """
    verbose = ctx.obj.get("verbose", False)

    try:
        # Check Python environment early
        _check_python_environment(verbose)
        
        # Determine project directory
        if data_dir:
            data_path = Path(data_dir)
        else:
            raise click.ClickException("Must specify --data-dir for the project directory.")

        data_path.mkdir(parents=True, exist_ok=True)

        print_header(f"Initializing Timetable Project")
        print_info(f"Project directory: {data_path}")

        # Create directory structure
        _create_directory_structure(data_path, verbose)

        # Copy template files
        _copy_template_files(data_path, force, verbose)

        # Create .env file if it doesn't exist
        _create_env_file(data_path, verbose)

        print_success("✅ Timetable project initialized successfully!")
        print_info(f"Next steps:")
        print_info(f"  1. Edit the Stage 1 files in {data_path}/stage_1/")
        print_info(f"  2. Run: cd {data_path}")
        print_info(f"  3. Run: timetable validate config")
        print_info(f"  4. Run: timetable build all")

    except Exception as e:
        print_error(f"Failed to initialize project: {e}")
        raise click.ClickException(f"Initialization failed: {e}")


def _create_directory_structure(data_path: Path, verbose: bool) -> None:
    """Create the required directory structure."""
    for dirname in INIT_CONFIG["directories"]:
        directory = data_path / dirname
        directory.mkdir(parents=True, exist_ok=True)
        if verbose:
            print_info(f"Created directory: {directory}")


def _copy_template_files(data_path: Path, force: bool, verbose: bool) -> None:
    """Copy template files from package data."""
    # Try to get templates from package data first
    templates_copied = _copy_package_templates(data_path, force, verbose)
    
    if not templates_copied:
        # Fallback to copying from project directory (development mode)
        _copy_project_templates(data_path, force, verbose)
    
    # Validate that all required files were copied
    _validate_template_files(data_path)


def _copy_package_templates(data_path: Path, force: bool, verbose: bool) -> bool:
    """Copy templates from installed package data."""
    try:
        import importlib.resources as resources
        
        # Try to access package data
        with resources.files("timetable").joinpath("templates") as templates_dir:
            if templates_dir.exists():
                return _copy_from_directory(templates_dir, data_path / "stage_1", force, verbose)
    except (ImportError, AttributeError, FileNotFoundError):
        pass
    
    return False


def _copy_project_templates(data_path: Path, force: bool, verbose: bool) -> None:
    """Copy templates from project directory (development fallback)."""
    # Get the package directory where templates are located
    import timetable
    package_dir = Path(timetable.__file__).parent
    
    source_stage_1 = package_dir / "stages" / "stage_1"
    if source_stage_1.exists():
        _copy_from_directory(source_stage_1, data_path / "stage_1", force, verbose)


def _copy_from_directory(source_dir: Path, dest_dir: Path, force: bool, verbose: bool) -> bool:
    """Copy files from source directory to destination."""
    if not source_dir.exists():
        return False
    
    copied = False
    for item in source_dir.iterdir():
        if item.is_file() and item.suffix == ".json":
            dest_file = dest_dir / item.name
            if dest_file.exists() and not force:
                if verbose:
                    print_info(f"Skipping existing file: {dest_file.name}")
                continue
            
            shutil.copy2(item, dest_file)
            copied = True
            if verbose:
                print_info(f"Copied template: {item.name}")
    
    return copied


def _validate_template_files(data_path: Path) -> None:
    """
    Validate that all required template files were copied.
    
    Args:
        data_path: Path to the project data directory
    """
    stage1_dir = data_path / "stage_1"
    
    # Check required files
    missing_files = []
    for filename in INIT_CONFIG["required_files"]:
        if not (stage1_dir / filename).exists():
            missing_files.append(filename)
    
    if missing_files:
        print_error(f"⚠️ Missing required files: {', '.join(missing_files)}")
        raise click.ClickException(
            f"Template files are incomplete. Missing: {', '.join(missing_files)}\n"
            f"Make sure you copied template files to {stage1_dir}/"
        )
    
    # Check what semester templates are available
    has_sem13 = all((stage1_dir / f).exists() for f in INIT_CONFIG["sem13_files"])
    has_sem24 = all((stage1_dir / f).exists() for f in INIT_CONFIG["sem24_files"])
    
    # Report what's available
    print_info("✅ Template Files Status:")
    
    if has_sem13:
        print_info("  ✓ Semester 1 & 3 files complete")
    else:
        missing_sem13 = [f for f in INIT_CONFIG["sem13_files"] if not (stage1_dir / f).exists()]
        print_info(f"  ✗ Semester 1 & 3 files incomplete (missing: {', '.join(missing_sem13[:2])}...)")
    
    if has_sem24:
        print_info("  ✓ Semester 2 & 4 files complete")
    else:
        missing_sem24 = [f for f in INIT_CONFIG["sem24_files"] if not (stage1_dir / f).exists()]
        print_info(f"  ✗ Semester 2 & 4 files incomplete (missing: {', '.join(missing_sem24[:2])}...)")
    
    # Count total files
    json_files = list(stage1_dir.glob("*.json"))
    print_info(f"  Total Stage 1 files: {len(json_files)}")
    
    if not has_sem13 and not has_sem24:
        print_error("⚠️ Warning: No complete semester sets found!")
        print_info("You can still proceed, but some functionality may be limited.")


def _copy_scripts(project_root: Path, data_path: Path, force: bool, verbose: bool) -> None:
    """Copy build scripts for each stage."""
    for stage_num in INIT_CONFIG["scripts_stages"]:
        source_scripts = project_root / f"stage_{stage_num}" / "scripts"
        dest_scripts = data_path / f"stage_{stage_num}" / "scripts"
        
        if source_scripts.exists():
            if dest_scripts.exists() and not force:
                if verbose:
                    print_info(f"Skipping existing scripts for stage {stage_num}")
                continue
            
def _create_env_file(data_path: Path, verbose: bool) -> None:
    """Create a .env file with basic configuration."""
    env_file = data_path / ".env"

    if env_file.exists():
        if verbose:
            print_info("Skipping existing .env file")
        return

    env_content = f"""# Timetable Project Configuration
# Generated by 'timetable init'

# Data directory (automatically set)
TIMETABLE_DATA_DIR={data_path}

# Logging
TIMETABLE_LOG_LEVEL=INFO

# Behavior
TIMETABLE_STRICT_MODE=false
TIMETABLE_VERBOSE=false
"""

    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(env_content)

    if verbose:
        print_info("Created .env file")