"""
Status Command - Show system status and data availability.
"""

from __future__ import annotations

import sys
from typing import Optional

import click
from rich.table import Table

from timetable.core.exceptions import TimetableError
from timetable.core.loader import DataLoader

from .utils import (
    console,
    get_data_dir,
    print_error,
    print_header,
)


@click.command()
@click.option(
    "-d", "--data-dir",
    type=click.Path(exists=False),
    help="Path to the data directory.",
)
@click.pass_context
def status(ctx: click.Context, data_dir: Optional[str]) -> None:
    """
    Show system status and data availability.

    Displays an overview of all stages and their data status.

    \b
    Examples:
        timetable status
        timetable status --data-dir ./data
    """
    try:
        data_path = get_data_dir(data_dir)
        loader = DataLoader(data_path)

        print_header("Timetable System Status", f"Data directory: {data_path}")
        console.print()

        # Create status table
        table = Table(title="Stage Status Overview", show_header=True)
        table.add_column("Stage", style="cyan", width=10)
        table.add_column("Description", style="white", width=30)
        table.add_column("Status", style="bold", width=12)
        table.add_column("Files/Records", style="green", width=20)

        stages_info = [
            (1, "Configuration Input", [
                ("config.json", lambda: loader.load_config()),
                ("facultyBasic.json", lambda: loader.load_faculty()),
                ("subjects*.json", lambda: loader.load_subjects()),
                ("studentGroups.json", lambda: loader.load_student_groups()),
            ]),
            (2, "Built Data", [
                ("faculty2Full.json", lambda: loader.load_faculty_full()),
                ("subjects2Full.json", lambda: loader.load_subjects_full()),
            ]),
            (3, "Teaching Assignments", [
                ("assignments_sem1", lambda: loader.load_teaching_assignments(semester=1)),
                ("assignments_sem3", lambda: loader.load_teaching_assignments(semester=3)),
                ("statistics.json", lambda: loader.load_statistics()),
            ]),
            (4, "Scheduling Input", [
                ("schedulingInput.json", lambda: loader.load_scheduling_input()),
            ]),
            (5, "AI Schedule Output", [
                ("ai_solved_schedule.json", lambda: loader.load_ai_schedule()),
            ]),
            (6, "Enriched Output", [
                ("timetable_enriched.json", lambda: loader.load_enriched_timetable()),
            ]),
        ]

        for stage_num, description, file_checks in stages_info:
            status_text = "[green]✓ Ready[/green]"
            file_info = []
            
            for file_desc, load_fn in file_checks:
                try:
                    data = load_fn()
                    if hasattr(data, '__len__') and not isinstance(data, str) and not hasattr(data, 'model_fields'):
                        if hasattr(data, 'assignments'):
                            count = len(data.assignments)
                        elif hasattr(data, 'student_groups'):
                            count = len(data.student_groups)
                        else:
                            count = len(data)
                        file_info.append(f"{file_desc}: {count}")
                    elif hasattr(data, 'assignments'):  # Pydantic models with assignments
                        count = len(data.assignments)
                        file_info.append(f"{file_desc}: {count}")
                    else:
                        file_info.append(f"{file_desc}: ✓")
                except Exception:
                    status_text = "[yellow]⚠ Partial[/yellow]"
                    file_info.append(f"{file_desc}: [red]✗[/red]")
            
            if "[red]" in status_text or all("[red]" in f for f in file_info):
                status_text = "[red]✗ Missing[/red]"
            
            table.add_row(
                f"Stage {stage_num}",
                description,
                status_text,
                "\n".join(file_info[:3]) + ("..." if len(file_info) > 3 else "")
            )

        console.print(table)
        console.print()

        # Additional info
        console.print("[bold]Quick Commands:[/bold]")
        console.print("  • [cyan]timetable validate --all[/cyan] - Validate all data")
        console.print("  • [cyan]timetable info all[/cyan] - Show detailed summaries")
        console.print("  • [cyan]timetable export all[/cyan] - Export all data")

    except TimetableError as e:
        print_error(str(e))
        sys.exit(1)
