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
        "logs",
        "schemas"
    ],
}


@click.command()
@click.option(
    "-d", "--data-dir",
    type=click.Path(exists=False),
    help="Path to the data directory to initialize.",
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

    Creates the data directory structure and copies template Stage 1 files.
    This sets up a new timetable project ready for customization.

    \b
    Examples:
        timetable init                           # Initialize in default location
        timetable init --data-dir ./my-project   # Initialize in specific directory
        timetable init --force                   # Overwrite existing files
    """
    verbose = ctx.obj.get("verbose", False)

    try:
        # Determine data directory
        if data_dir:
            data_path = Path(data_dir)
        else:
            settings = get_settings()
            data_path = settings.data_dir

        print_header(f"Initializing Timetable Project")
        print_info(f"Data directory: {data_path}")

        # Create directory structure
        _create_directory_structure(data_path, verbose)

        # Copy template files
        _copy_template_files(data_path, force, verbose)

        # Create .env file if it doesn't exist
        _create_env_file(data_path, verbose)

        print_success("✅ Timetable project initialized successfully!")
        print_info(f"Next steps:")
        print_info(f"  1. Edit the Stage 1 files in {data_path}/stage_1/")
        print_info(f"  2. Run: timetable validate --stage 1")
        print_info(f"  3. Run: timetable build all")

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
    # Get the project root (where stage_1 directory exists)
    import timetable
    package_dir = Path(timetable.__file__).parent.parent.parent
    
    source_stage_1 = package_dir / "stage_1"
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