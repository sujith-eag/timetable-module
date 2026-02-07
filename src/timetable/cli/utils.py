"""
CLI Utility Functions.

Shared utilities for CLI commands including output formatting,
progress bars, and export functions.
"""

from __future__ import annotations

import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.table import Table
from rich.tree import Tree

# Initialize Rich console for formatted output
console = Console()
error_console = Console(stderr=True)


def get_data_dir(data_dir: Optional[str] = None) -> Path:
    """
    Get the data directory from argument, environment variable, or settings.

    Priority order:
    1. Explicit --data-dir argument
    2. TIMETABLE_DATA_DIR environment variable
    3. Settings default data_dir
    4. Current working directory (fallback)

    Args:
        data_dir: Explicit data directory path

    Returns:
        Path to data directory

    Raises:
        click.ClickException: If no data directory specified or found
    """
    if data_dir:
        path = Path(data_dir).resolve()
    else:
        env_dir = os.environ.get("TIMETABLE_DATA_DIR")
        if env_dir:
            path = Path(env_dir)
        else:
            # Fall back to settings default
            from timetable.config.settings import get_settings
            settings = get_settings()
            path = settings.data_dir

    if not path.exists():
        raise click.ClickException(
            f"Data directory not found: {path}\n"
            "Specify with --data-dir or set TIMETABLE_DATA_DIR environment variable."
        )

    return path


def print_success(message: str) -> None:
    """Print a success message in green."""
    console.print(f"[green]✓[/green] {message}")


def print_error(message: str) -> None:
    """Print an error message in red."""
    error_console.print(f"[red]✗ Error:[/red] {message}")


def print_warning(message: str) -> None:
    """Print a warning message in yellow."""
    console.print(f"[yellow]⚠[/yellow] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[blue]ℹ[/blue] {message}")


def create_progress() -> Progress:
    """Create a Rich progress bar with custom styling."""
    return Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=40),
        TaskProgressColumn(),
        TextColumn("[dim]{task.fields[status]}"),
        console=console,
        transient=False,
    )


def export_to_csv(data: list[dict], filepath: Path) -> None:
    """Export a list of dictionaries to CSV file."""
    if not data:
        raise ValueError("No data to export")
    
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Flatten nested dicts for CSV
    def flatten_dict(d: dict, parent_key: str = "", sep: str = "_") -> dict:
        items: list[tuple[str, Any]] = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key, sep).items())
            elif isinstance(v, list):
                items.append((new_key, "; ".join(str(x) for x in v)))
            else:
                items.append((new_key, v))
        return dict(items)
    
    flat_data = [flatten_dict(row) for row in data]
    
    # Get all keys
    all_keys = set()
    for row in flat_data:
        all_keys.update(row.keys())
    fieldnames = sorted(all_keys)
    
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(flat_data)


def export_to_json(data: Any, filepath: Path, indent: int = 2) -> None:
    """Export data to JSON file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, default=str)


def export_to_markdown(data: list[dict], filepath: Path, title: str = "Export") -> None:
    """Export data to Markdown table."""
    if not data:
        raise ValueError("No data to export")
    
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    # Get headers from first row
    headers = list(data[0].keys())
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        
        # Header row
        f.write("| " + " | ".join(headers) + " |\n")
        f.write("| " + " | ".join(["---"] * len(headers)) + " |\n")
        
        # Data rows
        for row in data:
            values = []
            for h in headers:
                v = row.get(h, "")
                if isinstance(v, list):
                    v = ", ".join(str(x) for x in v)
                values.append(str(v))
            f.write("| " + " | ".join(values) + " |\n")


def print_header(title: str, subtitle: str = "") -> None:
    """Print a styled header panel."""
    if subtitle:
        content = f"[bold white]{title}[/bold white]\n[dim]{subtitle}[/dim]"
    else:
        content = f"[bold white]{title}[/bold white]"
    console.print(Panel(content, border_style="blue", padding=(0, 2)))


def print_summary_tree(title: str, items: dict[str, Any]) -> None:
    """Print a tree view of summary items."""
    tree = Tree(f"[bold]{title}[/bold]")
    for key, value in items.items():
        if isinstance(value, dict):
            branch = tree.add(f"[cyan]{key}[/cyan]")
            for k, v in value.items():
                branch.add(f"{k}: [green]{v}[/green]")
        else:
            tree.add(f"{key}: [green]{value}[/green]")
    console.print(tree)


def handle_error(e: Exception) -> None:
    """Handle an exception by printing error and exiting."""
    print_error(str(e))
    sys.exit(1)
