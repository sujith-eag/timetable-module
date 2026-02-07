"""
Build command group for timetable CLI.

Builds stage data files by running the stage build scripts.
"""

import sys
import subprocess
from pathlib import Path
from typing import Optional

import click
from rich.panel import Panel
from rich.table import Table

from timetable.core.loader import DataLoader
from timetable.core.exceptions import TimetableError
from .utils import (
    console,
    get_data_dir,
    print_success,
    print_error,
    print_warning,
    print_info,
    print_header,
    create_progress,
)


@click.group()
@click.pass_context
def build(ctx: click.Context) -> None:
    """
    Build timetable data stages.

    Runs the build scripts to generate derived data files.

    \b
    Examples:
        timetable build stage2 --data-dir ./data
        timetable build stage3 --data-dir ./data
        timetable build all --data-dir ./data
    """
    pass


def _run_build_script(script_path: Path, cwd: Path, data_path: Path, description: str, *extra_args: str) -> tuple[bool, str]:
    """Run a build script and return success status and output."""
    try:
        cmd = [sys.executable, str(script_path), "--data-dir", str(data_path)]
        cmd.extend(extra_args)
        
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        output = result.stdout
        if result.stderr:
            output += "\n" + result.stderr
        
        return result.returncode == 0, output
        
    except subprocess.TimeoutExpired:
        return False, f"Timeout: {description} took longer than 120 seconds"
    except Exception as e:
        return False, f"Error: {str(e)}"


@build.command(name="stage2")
@click.option(
    "-d", "--data-dir",
    type=click.Path(exists=False),
    help="Path to the data directory.",
)
@click.option(
    "--validate/--no-validate",
    default=True,
    help="Run validation after building.",
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="Show detailed output.",
)
@click.pass_context
def build_stage2(
    ctx: click.Context,
    data_dir: Optional[str],
    validate: bool,
    verbose: bool,
) -> None:
    """
    Build Stage 2 data from Stage 1 inputs.

    Generates:
    - subjects2Full.json (subjects with expanded components)
    - faculty2Full.json (faculty with workload calculations)

    \b
    Prerequisites:
    - Stage 1 data must be complete and valid
    """
    try:
        data_path = get_data_dir(data_dir)
        # Scripts are now in the package, not in the data directory
        import timetable
        scripts_dir = Path(timetable.__file__).parent / "scripts" / "stage2"
        
        if not scripts_dir.exists():
            raise click.ClickException(f"Stage 2 scripts directory not found: {scripts_dir}")
        
        print_header("Stage 2 Build", f"Data directory: {data_path}")
        console.print()
        
        # Check prerequisites
        print_info("Checking prerequisites...")
        loader = DataLoader(data_path)
        try:
            subjects = loader.load_subjects()
            faculty = loader.load_faculty()
            print_success(f"Stage 1 data found: {len(subjects)} subjects, {len(faculty)} faculty")
        except TimetableError as e:
            print_error(f"Stage 1 data not found or invalid: {e}")
            sys.exit(1)
        
        console.print()
        
        build_scripts = [
            ("build_subjects_full.py", "Building subjects with components"),
            ("build_faculty_full.py", "Building faculty with workload"),
        ]
        
        if validate:
            build_scripts.append(("validate_stage2.py", "Validating Stage 2 data"))
        
        results = []
        
        with create_progress() as progress:
            task = progress.add_task(
                "Building Stage 2...",
                total=len(build_scripts),
                status="Starting"
            )
            
            for script_name, description in build_scripts:
                progress.update(task, status=description)
                script_path = scripts_dir / script_name
                
                if not script_path.exists():
                    results.append((description, False, f"Script not found: {script_path}"))
                    progress.update(task, advance=1)
                    continue
                
                success, output = _run_build_script(script_path, scripts_dir, data_path, description)
                results.append((description, success, output))
                
                if verbose and output:
                    console.print(f"\n[dim]{output}[/dim]")
                
                progress.update(task, advance=1)
            
            progress.update(task, status="Complete")
        
        console.print()
        
        # Show results
        all_success = True
        for description, success, output in results:
            if success:
                print_success(description)
            else:
                print_error(description)
                if not verbose:
                    # Show error output even if not verbose
                    for line in output.split('\n')[-5:]:
                        if line.strip():
                            console.print(f"    [dim]{line}[/dim]")
                all_success = False
        
        console.print()
        
        if all_success:
            # Show generated files
            stage2_dir = data_path / "stage_2"
            files = ["subjects2Full.json", "faculty2Full.json"]
            
            console.print(Panel.fit(
                "[bold green]✓ Stage 2 build complete![/bold green]",
                border_style="green"
            ))
            
            console.print("\n[bold]Generated files:[/bold]")
            for filename in files:
                filepath = stage2_dir / filename
                if filepath.exists():
                    size = filepath.stat().st_size
                    console.print(f"  • {filename} ({size:,} bytes)")
        else:
            print_error("Stage 2 build failed. Check errors above.")
            sys.exit(1)
        
    except TimetableError as e:
        print_error(str(e))
        sys.exit(1)


@build.command(name="stage3")
@click.option(
    "-d", "--data-dir",
    type=click.Path(exists=False),
    help="Path to the data directory.",
)
@click.option(
    "--validate/--no-validate",
    default=True,
    help="Run validation after building.",
)
@click.option(
    "--reports/--no-reports",
    default=True,
    help="Generate reports after building.",
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="Show detailed output.",
)
@click.pass_context
def build_stage3(
    ctx: click.Context,
    data_dir: Optional[str],
    validate: bool,
    reports: bool,
    verbose: bool,
) -> None:
    """
    Build Stage 3 data from Stage 2 inputs.

    Generates:
    - teachingAssignments_sem1.json
    - teachingAssignments_sem3.json
    - studentGroupOverlapConstraints.json
    - statistics.json
    - reports/ (markdown reports)

    \b
    Prerequisites:
    - Stage 2 data must be complete and valid
    """
    try:
        data_path = get_data_dir(data_dir)
        # Scripts are now in the package, not in the data directory
        import timetable
        scripts_dir = Path(timetable.__file__).parent / "scripts" / "stage3"
        
        if not scripts_dir.exists():
            raise click.ClickException(f"Stage 3 scripts directory not found: {scripts_dir}")
        
        print_header("Stage 3 Build", f"Data directory: {data_path}")
        console.print()
        
        # Check prerequisites
        print_info("Checking prerequisites...")
        loader = DataLoader(data_path)
        try:
            faculty = loader.load_faculty_full()
            subjects = loader.load_subjects_full()
            print_success(f"Stage 2 data found: {len(subjects)} subjects, {len(faculty)} faculty")
        except TimetableError as e:
            print_error(f"Stage 2 data not found or invalid: {e}")
            print_info("Run 'timetable build stage2' first")
            sys.exit(1)
        
        console.print()
        
        build_scripts = [
            ("generate_overlap_matrix.py", "Generating overlap constraints"),
            ("build_assignments_sem3.py", "Building Semester 3 assignments"),
            ("build_assignments_sem1.py", "Building Semester 1 assignments"),
        ]
        
        if validate:
            build_scripts.append(("validate_stage3.py", "Validating assignments"))
        
        build_scripts.append(("generate_statistics.py", "Generating statistics"))
        
        if reports:
            build_scripts.append(("generate_reports.py", "Generating reports"))
        
        results = []
        
        with create_progress() as progress:
            task = progress.add_task(
                "Building Stage 3...",
                total=len(build_scripts),
                status="Starting"
            )
            
            for script_name, description in build_scripts:
                progress.update(task, status=description)
                script_path = scripts_dir / script_name
                
                if not script_path.exists():
                    results.append((description, False, f"Script not found: {script_path}"))
                    progress.update(task, advance=1)
                    continue
                
                success, output = _run_build_script(script_path, scripts_dir, data_path, description)
                results.append((description, success, output))
                
                if verbose and output:
                    console.print(f"\n[dim]{output}[/dim]")
                
                progress.update(task, advance=1)
            
            progress.update(task, status="Complete")
        
        console.print()
        
        # Show results
        all_success = True
        for description, success, output in results:
            if success:
                print_success(description)
            else:
                print_error(description)
                if not verbose:
                    for line in output.split('\n')[-5:]:
                        if line.strip():
                            console.print(f"    [dim]{line}[/dim]")
                all_success = False
        
        console.print()
        
        if all_success:
            stage3_dir = data_path / "stage_3"
            
            console.print(Panel.fit(
                "[bold green]✓ Stage 3 build complete![/bold green]",
                border_style="green"
            ))
            
            console.print("\n[bold]Generated files:[/bold]")
            files = [
                "teachingAssignments_sem1.json",
                "teachingAssignments_sem3.json",
                "studentGroupOverlapConstraints.json",
                "statistics.json",
            ]
            for filename in files:
                filepath = stage3_dir / filename
                if filepath.exists():
                    size = filepath.stat().st_size
                    console.print(f"  • {filename} ({size:,} bytes)")
            
            if reports and (stage3_dir / "reports").exists():
                console.print("\n[bold]Reports:[/bold]")
                for report in sorted((stage3_dir / "reports").glob("*.md")):
                    console.print(f"  • reports/{report.name}")
        else:
            print_error("Stage 3 build failed. Check errors above.")
            sys.exit(1)
        
    except TimetableError as e:
        print_error(str(e))
        sys.exit(1)


@build.command(name="stage4")
@click.option(
    "-d", "--data-dir",
    type=click.Path(exists=False),
    help="Path to the data directory.",
)
@click.option(
    "--validate/--no-validate",
    default=True,
    help="Run validation after building.",
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="Show detailed output.",
)
@click.pass_context
def build_stage4(
    ctx: click.Context,
    data_dir: Optional[str],
    validate: bool,
    verbose: bool,
) -> None:
    """
    Build Stage 4 data from Stage 3 inputs.

    Generates:
    - schedulingInput.json (complete input for AI solver)

    \b
    Prerequisites:
    - Stage 3 data must be complete and valid
    """
    try:
        data_path = get_data_dir(data_dir)
        # Scripts are now in the package, not in the data directory
        import timetable
        scripts_dir = Path(timetable.__file__).parent / "scripts" / "stage4"
        
        if not scripts_dir.exists():
            raise click.ClickException(f"Stage 4 scripts directory not found: {scripts_dir}")
        
        print_header("Stage 4 Build", f"Data directory: {data_path}")
        console.print()

        # Check prerequisites
        print_info("Checking prerequisites...")
        loader = DataLoader(data_path)
        try:
            assignments1 = loader.load_teaching_assignments(semester=1)
            assignments3 = loader.load_teaching_assignments(semester=3)
            overlap = loader.load_overlap_constraints()
            print_success(f"Stage 3 data found: {len(assignments1.assignments)} sem1, {len(assignments3.assignments)} sem3 assignments")
        except TimetableError as e:
            print_error(f"Stage 3 data not found or invalid: {e}")
            print_info("Run 'timetable build stage3' first")
            sys.exit(1)

        console.print()

        build_scripts = [
            ("build_scheduling_input.py", "Building scheduling input for AI solver"),
        ]

        if validate:
            build_scripts.append(("validate_stage4.py", "Validating Stage 4 data"))

        results = []

        with create_progress() as progress:
            task = progress.add_task(
                "Building Stage 4...",
                total=len(build_scripts),
                status="Starting"
            )

            for script_name, description in build_scripts:
                progress.update(task, status=description)
                script_path = scripts_dir / script_name

                if not script_path.exists():
                    results.append((description, False, f"Script not found: {script_path}"))
                    progress.update(task, advance=1)
                    continue

                success, output = _run_build_script(script_path, scripts_dir, data_path, description)
                results.append((description, success, output))
                
                if verbose and output:
                    console.print(f"\n[dim]{output}[/dim]")
                
                progress.update(task, advance=1)
            
            progress.update(task, status="Complete")
        
        console.print()
        
        # Show results
        all_success = True
        for description, success, output in results:
            if success:
                print_success(description)
            else:
                print_error(description)
                if not verbose:
                    # Show error output even if not verbose
                    for line in output.split('\n')[-5:]:
                        if line.strip():
                            console.print(f"    [dim]{line}[/dim]")
                all_success = False
        
        console.print()

        if all_success:
            # Show generated files
            stage4_dir = data_path / "stage_4"
            files = ["schedulingInput.json"]

            console.print(Panel.fit(
                "[bold green]✓ Stage 4 build complete![/bold green]",
                border_style="green"
            ))

            console.print("\n[bold]Generated files:[/bold]")
            for filename in files:
                filepath = stage4_dir / filename
                if filepath.exists():
                    size = filepath.stat().st_size
                    console.print(f"  • {filename} ({size:,} bytes)")
        else:
            print_error("Stage 4 build failed. Check errors above.")
            sys.exit(1)

    except TimetableError as e:
        print_error(str(e))
        sys.exit(1)


@build.command(name="stage5")
@click.option(
    "-d", "--data-dir",
    type=click.Path(exists=False),
    help="Path to the data directory.",
)
@click.option(
    "--validate/--no-validate",
    default=True,
    help="Run validation after building.",
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="Show detailed output.",
)
@click.pass_context
def build_stage5(
    ctx: click.Context,
    data_dir: Optional[str],
    validate: bool,
    verbose: bool,
) -> None:
    """
    Build Stage 5 data from Stage 4 inputs.

    Generates:
    - ai_solved_schedule.json (AI-generated schedule template)

    \b
    Prerequisites:
    - Stage 4 data must be complete and valid
    """
    try:
        data_path = get_data_dir(data_dir)
        # Scripts are now in the package, not in the data directory
        import timetable
        scripts_dir = Path(timetable.__file__).parent / "scripts" / "stage5"
        
        if not scripts_dir.exists():
            raise click.ClickException(f"Stage 5 scripts directory not found: {scripts_dir}")
        
        print_header("Stage 5 Build", f"Data directory: {data_path}")
        console.print()

        # Check prerequisites
        print_info("Checking prerequisites...")
        loader = DataLoader(data_path)
        try:
            scheduling_input = loader.load_scheduling_input()
            print_success(f"Stage 4 data found: {len(scheduling_input.assignments)} assignments")
        except TimetableError as e:
            print_error(f"Stage 4 data not found or invalid: {e}")
            print_info("Run 'timetable build stage4' first")
            sys.exit(1)

        console.print()

        build_scripts = [
            ("generate_schedule_template.py", "Generating AI schedule template"),
        ]

        if validate:
            build_scripts.append(("validate_stage5.py", "Validating Stage 5 data"))

        results = []

        with create_progress() as progress:
            task = progress.add_task(
                "Building Stage 5...",
                total=len(build_scripts),
                status="Starting"
            )

            for script_name, description in build_scripts:
                progress.update(task, status=description)
                script_path = scripts_dir / script_name

                if not script_path.exists():
                    results.append((description, False, f"Script not found: {script_path}"))
                    progress.update(task, advance=1)
                    continue

                success, output = _run_build_script(script_path, scripts_dir, data_path, description)
                results.append((description, success, output))
                
                if verbose and output:
                    console.print(f"\n[dim]{output}[/dim]")
                
                progress.update(task, advance=1)
            
            progress.update(task, status="Complete")
        
        console.print()
        
        # Show results
        all_success = True
        for description, success, output in results:
            if success:
                print_success(description)
            else:
                print_error(description)
                if not verbose:
                    # Show error output even if not verbose
                    for line in output.split('\n')[-5:]:
                        if line.strip():
                            console.print(f"    [dim]{line}[/dim]")
                all_success = False

        console.print()

        if all_success:
            # Show generated files
            stage5_dir = data_path / "stage_5"
            files = ["ai_solved_schedule.json"]

            console.print(Panel.fit(
                "[bold green]✓ Stage 5 build complete![/bold green]",
                border_style="green"
            ))

            console.print("\n[bold]Generated files:[/bold]")
            for filename in files:
                filepath = stage5_dir / filename
                if filepath.exists():
                    size = filepath.stat().st_size
                    console.print(f"  • {filename} ({size:,} bytes)")
        else:
            print_error("Stage 5 build failed. Check errors above.")
            sys.exit(1)

    except TimetableError as e:
        print_error(str(e))
        sys.exit(1)


@build.command(name="stage6")
@click.option(
    "-d", "--data-dir",
    type=click.Path(exists=False),
    help="Path to the data directory.",
)
@click.option(
    "--validate/--no-validate",
    default=True,
    help="Run validation after building.",
)
@click.option(
    "--views/--no-views",
    default=True,
    help="Generate faculty and student views.",
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="Show detailed output.",
)
@click.pass_context
def build_stage6(
    ctx: click.Context,
    data_dir: Optional[str],
    validate: bool,
    views: bool,
    verbose: bool,
) -> None:
    """
    Build Stage 6 data from Stage 5 inputs.

    Generates:
    - timetable_enriched.json (complete enriched timetable)
    - views/ (faculty and student views)
    - reports/ (analysis reports)

    \b
    Prerequisites:
    - Stage 5 data must be complete and valid
    """
    try:
        data_path = get_data_dir(data_dir)
        # Scripts are now in the package, not in the data directory
        import timetable
        scripts_dir = Path(timetable.__file__).parent / "scripts" / "stage6"
        
        if not scripts_dir.exists():
            raise click.ClickException(f"Stage 6 scripts directory not found: {scripts_dir}")

        print_header("Stage 6 Build", f"Data directory: {data_path}")
        console.print()

        # Check prerequisites
        print_info("Checking prerequisites...")
        loader = DataLoader(data_path)
        try:
            ai_schedule = loader.load_ai_schedule()
            print_success(f"Stage 5 data found: {len(ai_schedule.schedule)} scheduled sessions")
        except TimetableError as e:
            print_error(f"Stage 5 data not found or invalid: {e}")
            print_info("Run 'timetable build stage5' first")
            sys.exit(1)

        console.print()

        build_scripts = [
            ("enrich_schedule.py", "Enriching schedule with full details"),
            ("analyze_schedule.py", "Analyzing schedule quality"),
        ]

        if validate:
            build_scripts.append(("validate_assignments.py", "Validating enriched assignments"))

        if views:
            build_scripts.extend([
                ("generate_faculty_views.py", "Generating faculty views"),
                ("generate_student_views.py", "Generating student views"),
            ])

        results = []

        with create_progress() as progress:
            task = progress.add_task(
                "Building Stage 6...",
                total=len(build_scripts),
                status="Starting"
            )

            for script_name, description in build_scripts:
                progress.update(task, status=description)
                script_path = scripts_dir / script_name

                if not script_path.exists():
                    results.append((description, False, f"Script not found: {script_path}"))
                    progress.update(task, advance=1)
                    continue

                # Special handling for enrich_schedule.py which needs schedule file argument
                if script_name == "enrich_schedule.py":
                    success, output = _run_build_script(script_path, scripts_dir, data_path, description, "ai_solved_schedule.json")
                else:
                    success, output = _run_build_script(script_path, scripts_dir, data_path, description)
                
                results.append((description, success, output))
                
                if verbose and output:
                    console.print(f"\n[dim]{output}[/dim]")
                
                progress.update(task, advance=1)
            
            progress.update(task, status="Complete")
        
        console.print()
        
        # Show results
        all_success = True
        for description, success, output in results:
            if success:
                print_success(description)
            else:
                print_error(description)
                if not verbose:
                    # Show error output even if not verbose
                    for line in output.split('\n')[-5:]:
                        if line.strip():
                            console.print(f"    [dim]{line}[/dim]")
                all_success = False

        console.print()

        if all_success:
            # Show generated files
            stage6_dir = data_path / "stage_6"
            files = ["timetable_enriched.json"]

            console.print(Panel.fit(
                "[bold green]✓ Stage 6 build complete![/bold green]",
                border_style="green"
            ))

            console.print("\n[bold]Generated files:[/bold]")
            for filename in files:
                filepath = stage6_dir / filename
                if filepath.exists():
                    size = filepath.stat().st_size
                    console.print(f"  • {filename} ({size:,} bytes)")

            if views and (stage6_dir / "views").exists():
                console.print("\n[bold]Views:[/bold]")
                for view in sorted((stage6_dir / "views").glob("*.md")):
                    console.print(f"  • views/{view.name}")

            if (stage6_dir / "reports").exists():
                console.print("\n[bold]Reports:[/bold]")
                for report in sorted((stage6_dir / "reports").glob("*.md")):
                    console.print(f"  • reports/{report.name}")
        else:
            print_error("Stage 6 build failed. Check errors above.")
            sys.exit(1)

    except TimetableError as e:
        print_error(str(e))
        sys.exit(1)


@build.command(name="all")
@click.option(
    "-d", "--data-dir",
    type=click.Path(exists=False),
    help="Path to the data directory.",
)
@click.option(
    "--validate/--no-validate",
    default=True,
    help="Run validation after each stage.",
)
@click.option(
    "-v", "--verbose",
    is_flag=True,
    help="Show detailed output.",
)
@click.pass_context
def build_all(
    ctx: click.Context,
    data_dir: Optional[str],
    validate: bool,
    verbose: bool,
) -> None:
    """
    Build all stages (2, 3, 4, 5 and 6) in sequence.

    Runs the complete build pipeline:
    1. Validates Stage 1 data
    2. Builds Stage 2 (subjects, faculty)
    3. Builds Stage 3 (assignments, constraints, statistics)
    4. Builds Stage 4 (scheduling input for AI)
    5. Builds Stage 5 (AI schedule template)
    6. Builds Stage 6 (enriched timetable with views)

    \b
    Prerequisites:
    - Stage 1 data must be complete and valid
    """
    try:
        data_path = get_data_dir(data_dir)
        
        print_header("Full Pipeline Build", f"Data directory: {data_path}")
        console.print()
        
        # Validate Stage 1
        print_info("Checking Stage 1 prerequisites...")
        loader = DataLoader(data_path)
        try:
            config = loader.load_config()
            subjects = loader.load_subjects()
            faculty = loader.load_faculty()
            groups = loader.load_student_groups()
            
            print_success(f"Config: {len(config.time_slots)} slots, {len(config.resources.rooms)} rooms")
            print_success(f"Subjects: {len(subjects)}")
            print_success(f"Faculty: {len(faculty)}")
            print_success(f"Student Groups: {len(groups.student_groups)}")
        except TimetableError as e:
            print_error(f"Stage 1 data error: {e}")
            sys.exit(1)
        
        console.print()
        
        # Build Stage 2
        console.print("[bold cyan]═══ Building Stage 2 ═══[/bold cyan]")
        ctx.invoke(build_stage2, data_dir=data_dir, validate=validate, verbose=verbose)
        
        console.print()
        
        # Build Stage 3
        console.print("[bold cyan]═══ Building Stage 3 ═══[/bold cyan]")
        ctx.invoke(build_stage3, data_dir=data_dir, validate=validate, reports=True, verbose=verbose)
        
        console.print()
        
        # Build Stage 4
        console.print("[bold cyan]═══ Building Stage 4 ═══[/bold cyan]")
        ctx.invoke(build_stage4, data_dir=data_dir, validate=validate, verbose=verbose)
        
        console.print()
        
        # Build Stage 5
        console.print("[bold cyan]═══ Building Stage 5 ═══[/bold cyan]")
        ctx.invoke(build_stage5, data_dir=data_dir, validate=validate, verbose=verbose)
        
        console.print()
        
        # Build Stage 6
        console.print("[bold cyan]═══ Building Stage 6 ═══[/bold cyan]")
        ctx.invoke(build_stage6, data_dir=data_dir, validate=validate, views=True, verbose=verbose)
        
        console.print()
        console.print(Panel.fit(
            "[bold green]✓ Full pipeline build complete![/bold green]\n\n"
            "All stages built successfully.\n"
            "Run 'timetable status' to see a summary.",
            border_style="green"
        ))
        
    except TimetableError as e:
        print_error(str(e))
        sys.exit(1)
    except SystemExit:
        # Re-raise SystemExit from sub-commands
        raise


@build.command(name="check")
@click.option(
    "-d", "--data-dir",
    type=click.Path(exists=False),
    help="Path to the data directory.",
)
@click.pass_context
def build_check(ctx: click.Context, data_dir: Optional[str]) -> None:
    """
    Check what stages are ready to build.

    Shows the current state of each stage and what's needed.
    """
    try:
        data_path = get_data_dir(data_dir)
        loader = DataLoader(data_path)
        
        print_header("Build Readiness Check", f"Data directory: {data_path}")
        console.print()
        
        table = Table(title="Stage Status", show_header=True)
        table.add_column("Stage", style="cyan")
        table.add_column("Status", style="white")
        table.add_column("Details", style="dim")
        
        # Stage 1 check
        try:
            config = loader.load_config()
            subjects = loader.load_subjects()
            faculty = loader.load_faculty()
            groups = loader.load_student_groups()
            
            table.add_row(
                "Stage 1 (Input)",
                "[green]✓ Ready[/green]",
                f"{len(subjects)} subjects, {len(faculty)} faculty"
            )
            stage1_ready = True
        except TimetableError as e:
            table.add_row(
                "Stage 1 (Input)",
                "[red]✗ Missing[/red]",
                str(e)[:50]
            )
            stage1_ready = False
        
        # Stage 2 check
        try:
            faculty = loader.load_faculty_full()
            subjects = loader.load_subjects_full()
            
            table.add_row(
                "Stage 2 (Enriched)",
                "[green]✓ Built[/green]",
                f"{len(subjects)} subjects with components"
            )
            stage2_ready = True
        except TimetableError:
            if stage1_ready:
                table.add_row(
                    "Stage 2 (Enriched)",
                    "[yellow]○ Not built[/yellow]",
                    "Run: timetable build stage2"
                )
            else:
                table.add_row(
                    "Stage 2 (Enriched)",
                    "[red]✗ Blocked[/red]",
                    "Stage 1 required first"
                )
            stage2_ready = False
        
        # Stage 3 check
        try:
            assignments = loader.load_all_teaching_assignments()
            stats = loader.load_statistics()
            
            total = sum(len(a.assignments) for a in assignments.values())
            table.add_row(
                "Stage 3 (Assignments)",
                "[green]✓ Built[/green]",
                f"{total} assignments"
            )
            stage3_ready = True
        except TimetableError:
            if stage2_ready:
                table.add_row(
                    "Stage 3 (Assignments)",
                    "[yellow]○ Not built[/yellow]",
                    "Run: timetable build stage3"
                )
            else:
                table.add_row(
                    "Stage 3 (Assignments)",
                    "[red]✗ Blocked[/red]",
                    "Stage 2 required first"
                )
            stage3_ready = False
        
        # Stage 4 check
        try:
            scheduling_input = loader.load_scheduling_input()
            
            table.add_row(
                "Stage 4 (AI Input)",
                "[green]✓ Built[/green]",
                f"{len(scheduling_input.assignments)} assignments for AI"
            )
            stage4_ready = True
        except TimetableError:
            if stage3_ready:
                table.add_row(
                    "Stage 4 (AI Input)",
                    "[yellow]○ Not built[/yellow]",
                    "Run: timetable build stage4"
                )
            else:
                table.add_row(
                    "Stage 4 (AI Input)",
                    "[red]✗ Blocked[/red]",
                    "Stage 3 required first"
                )
            stage4_ready = False
        
        # Stage 5 check
        try:
            ai_schedule = loader.load_ai_schedule()
            
            table.add_row(
                "Stage 5 (AI Output)",
                "[green]✓ Built[/green]",
                f"{len(ai_schedule.schedule)} scheduled sessions"
            )
            stage5_ready = True
        except TimetableError:
            if stage4_ready:
                table.add_row(
                    "Stage 5 (AI Output)",
                    "[yellow]○ Not built[/yellow]",
                    "Run: timetable build stage5"
                )
            else:
                table.add_row(
                    "Stage 5 (AI Output)",
                    "[red]✗ Blocked[/red]",
                    "Stage 4 required first"
                )
            stage5_ready = False
        
        # Stage 6 check
        try:
            enriched_timetable = loader.load_enriched_timetable()
            
            table.add_row(
                "Stage 6 (Enriched)",
                "[green]✓ Built[/green]",
                f"{enriched_timetable.metadata.total_sessions} sessions"
            )
        except TimetableError:
            if stage5_ready:
                table.add_row(
                    "Stage 6 (Enriched)",
                    "[yellow]○ Not built[/yellow]",
                    "Run: timetable build stage6"
                )
            else:
                table.add_row(
                    "Stage 6 (Enriched)",
                    "[red]✗ Blocked[/red]",
                    "Stage 5 required first"
                )
        
        console.print(table)
        
        console.print("\n[bold]Commands:[/bold]")
        console.print("  timetable build stage2   - Build Stage 2 from Stage 1")
        console.print("  timetable build stage3   - Build Stage 3 from Stage 2")
        console.print("  timetable build stage4   - Build Stage 4 from Stage 3")
        console.print("  timetable build stage5   - Build Stage 5 from Stage 4")
        console.print("  timetable build stage6   - Build Stage 6 from Stage 5")
        console.print("  timetable build all      - Build all stages")
        
    except TimetableError as e:
        print_error(str(e))
        sys.exit(1)
