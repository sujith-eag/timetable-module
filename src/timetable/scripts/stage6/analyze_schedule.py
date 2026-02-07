#!/usr/bin/env python3
"""
Stage 6: Schedule Analysis and Conflict Report Generator

This script performs a comprehensive analysis of a generated timetable to identify
conflicts, constraint violations, and potential quality issues.

It checks for:
- Hard Conflicts: Faculty, Room, and Student Group double-booking.
- Constraint Violations: Room capacity issues.
- Soft Conflicts (Workload): Faculty consecutive session limits.

The script generates a detailed Markdown report of its findings.
"""

import json
import sys
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime

class ScheduleAnalyzer:
    """Analyzes an enriched timetable for conflicts and quality issues."""

    def __init__(self, timetable_path: Path):
        """
        Initializes the analyzer by loading all necessary data files.
        
        Args:
            timetable_path: Path to the enriched timetable JSON file to be analyzed.
        """
        self.timetable_path = timetable_path
        self.base_dir = timetable_path.parent.parent
        
        self.timetable_data = self._load_json(self.timetable_path)
        self.scheduling_input = self._load_json(self.base_dir / "stage_4/schedulingInput.json")
        self.overlap_constraints = self._load_json(self.base_dir / "stage_3/studentGroupOverlapConstraints.json")

        # Intelligently find the session list
        session_keys = ['timetable_A', 'timetable', 'sessions']
        self.sessions = []
        for key in session_keys:
            if key in self.timetable_data:
                self.sessions = self.timetable_data[key]
                print(f"   ✓ Found session data under key: '{key}'")
                break
        
        if not self.sessions:
            print(f"❌ FATAL: Could not find session data under any of the expected keys: {session_keys} in {self.timetable_path.name}")
            sys.exit(1)

        # For efficient lookups
        self.rooms_map = {room['roomId']: room for room in self.scheduling_input['rooms']}
        self.student_groups_map = {group['studentGroupId']: group for group in self.scheduling_input['studentGroups']}
        
        # Add elective groups to the map as well
        for group in self.scheduling_input.get('electiveStudentGroups', []):
            self.student_groups_map[group['studentGroupId']] = group

    def _load_json(self, path: Path) -> dict:
        """Loads a JSON file and returns its content."""
        print(f"📂 Loading {path.name}...")
        if not path.exists():
            print(f"❌ FATAL: File not found at {path}")
            sys.exit(1)
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def analyze(self) -> str:
        """
        Runs all analysis checks and returns a formatted Markdown report.
        """
        print("⚙️ Starting schedule analysis...")
        
        # A grid to store session info for easy conflict detection
        faculty_grid = defaultdict(list)
        room_grid = defaultdict(list)
        student_group_grid = defaultdict(list)

        for session in self.sessions:
            day, slot = session.get('day'), session.get('slotId')
            if not day or not slot:
                continue
            
            time_key = f"{day}-{slot}"
            
            # Populate grids
            faculty_grid[f"{session['facultyId']}-{time_key}"].append(session['sessionId'])
            room_grid[f"{session['roomId']}-{time_key}"].append(session['sessionId'])
            for group in session['studentGroupIds']:
                student_group_grid[f"{group}-{time_key}"].append(session['sessionId'])

        report_parts = [f"# Schedule Analysis Report for `{self.timetable_path.name}`"]
        report_parts.append(f"> Generated on: {datetime.now().isoformat()}")
        
        # --- Run Analyses ---
        print("Checking for hard conflicts...")
        faculty_conflicts = self._analyze_faculty_conflicts(faculty_grid)
        room_conflicts = self._analyze_room_conflicts(room_grid)
        student_conflicts = self._analyze_student_group_conflicts()
        
        print("Checking for constraint violations...")
        capacity_violations = self._analyze_room_capacity()

        print("Checking for workload issues...")
        workload_violations = self._analyze_faculty_workload()

        # --- Build Report ---
        hard_conflicts_found = faculty_conflicts or room_conflicts or student_conflicts or capacity_violations
        
        report_parts.append("\n## 📋 Summary")
        if not hard_conflicts_found:
            report_parts.append("✅ **No hard conflicts found.** The schedule appears to be valid.")
        else:
            report_parts.append("❌ **Hard conflicts detected!** The schedule is invalid and requires correction.")
        
        report_parts.append(self._format_report_section("Faculty Conflicts", faculty_conflicts))
        report_parts.append(self._format_report_section("Room Conflicts", room_conflicts))
        report_parts.append(self._format_report_section("Student Group Conflicts", student_conflicts))
        report_parts.append(self._format_report_section("Room Capacity Violations", capacity_violations))
        report_parts.append(self._format_report_section("Faculty Workload Issues", workload_violations))

        print("✅ Analysis complete.")
        return "\n".join(report_parts)

    def _format_report_section(self, title: str, issues: list) -> str:
        """Formats a list of issues into a Markdown section."""
        if not issues:
            return f"\n### {title}\n\n- None found."
        
        section = [f"\n### {title} ({len(issues)} found)"]
        for issue in issues:
            section.append(f"- {issue}")
        return "\n".join(section)

    def _analyze_faculty_conflicts(self, faculty_grid: dict) -> list:
        """Finds faculty members scheduled for multiple sessions at the same time."""
        conflicts = []
        for key, sessions in faculty_grid.items():
            if len(sessions) > 1:
                fac_id, time_key = key.split('-', 1)
                conflicts.append(f"**Faculty Conflict:** `{fac_id}` is double-booked at `{time_key}` in sessions: `{', '.join(sessions)}`.")
        return conflicts

    def _analyze_room_conflicts(self, room_grid: dict) -> list:
        """Finds rooms booked for multiple sessions at the same time."""
        conflicts = []
        for key, sessions in room_grid.items():
            if len(sessions) > 1:
                room_id, time_key = key.split('-', 1)
                conflicts.append(f"**Room Conflict:** `{room_id}` is double-booked at `{time_key}` for sessions: `{', '.join(sessions)}`.")
        return conflicts

    def _analyze_student_group_conflicts(self) -> list:
        """Finds conflicting student groups scheduled at the same time."""
        conflicts = []
        overlap_map = self.overlap_constraints['cannotOverlapWith']
        
        # Create a grid of groups per timeslot
        grid = defaultdict(set)
        for session in self.sessions:
            day, slot = session.get('day'), session.get('slotId')
            if not day or not slot:
                continue
            time_key = f"{day}-{slot}"
            grid[time_key].update(session['studentGroupIds'])

        for time_key, groups_in_slot in grid.items():
            if len(groups_in_slot) > 1:
                group_list = list(groups_in_slot)
                for i, g1 in enumerate(group_list):
                    for g2 in group_list[i+1:]:
                        if g2 in overlap_map.get(g1, []):
                            conflicts.append(f"**Student Group Conflict:** Groups `{g1}` and `{g2}` have an overlap at `{time_key}`.")
        return sorted(list(set(conflicts)))

    def _analyze_room_capacity(self) -> list:
        """Finds sessions where student count exceeds room capacity."""
        violations = []
        for session in self.sessions:
            room_id = session.get('roomId')
            if not room_id or room_id not in self.rooms_map:
                continue

            room_capacity = self.rooms_map[room_id]['capacity']
            
            total_students = 0
            for group_id in session['studentGroupIds']:
                if group_id in self.student_groups_map:
                    total_students += self.student_groups_map[group_id].get('studentCount', 0)
            
            if total_students > room_capacity:
                violations.append(f"**Room Capacity Violation:** Session `{session['sessionId']}` has `{total_students}` students in room `{room_id}` which only has capacity for `{room_capacity}`.")
        return violations

    def _analyze_faculty_workload(self) -> list:
        """Analyzes faculty workload for soft constraint violations like too many consecutive hours."""
        issues = []
        max_consecutive = self.scheduling_input['configuration']['resourceConstraints']['maxConsecutiveSlotsPerFaculty']
        
        faculty_schedules = defaultdict(list)
        for session in self.sessions:
            day, slot = session.get('day'), session.get('slotId')
            if not day or not slot:
                continue
            
            # Get numerical value of slot for sorting
            slot_num = int(slot.replace('S', '').split('+')[0])
            faculty_schedules[session['facultyId']].append((day, slot_num))

        for fac_id, schedule in faculty_schedules.items():
            # Sort by day, then slot
            schedule.sort()
            
            consecutive_count = 1
            for i in range(1, len(schedule)):
                prev_day, prev_slot = schedule[i-1]
                curr_day, curr_slot = schedule[i]
                
                if prev_day == curr_day and curr_slot == prev_slot + 1:
                    consecutive_count += 1
                else:
                    consecutive_count = 1 # Reset
                
                if consecutive_count > max_consecutive:
                    issues.append(f"**Faculty Workload:** `{fac_id}` has more than {max_consecutive} consecutive sessions on `{curr_day}`.")
                    break # Only report once per faculty per day
        return sorted(list(set(issues)))



def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Analyze a timetable for conflicts and generate a report.")
    parser.add_argument(
        "timetable_file",
        type=Path,
        help="Path to the enriched timetable JSON file (e.g., ../timetable_enriched.json)"
    )
    args = parser.parse_args()

    try:
        analyzer = ScheduleAnalyzer(args.timetable_file)
        report_content = analyzer.analyze()
        
        output_path = Path(__file__).parent.parent / "reports" / "schedule_analysis_report.md"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
            
        print(f"\n✅ Report successfully generated at: {output_path}")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
