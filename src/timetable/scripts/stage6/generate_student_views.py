#!/usr/bin/env python3
"""
Stage 6: Student Schedule View Generator

This script generates a human-readable weekly schedule for each student section
from an enriched timetable JSON file. It creates separate files for each semester.
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import sys

class StudentViewGenerator:
    """Generates Markdown schedules for each student section."""

    def __init__(self, timetable_path: Path):
        """
        Initializes the generator.
        
        Args:
            timetable_path: Path to the enriched timetable JSON file.
        """
        print("📂 Loading timetable...")
        self.timetable_data = self._load_json(timetable_path)

        # Intelligently find the session list
        session_keys = ['timetable_A', 'timetable', 'sessions']
        self.sessions = []
        for key in session_keys:
            if key in self.timetable_data:
                self.sessions = self.timetable_data[key]
                print(f"   ✓ Found session data under key: '{key}'")
                break
        
        if not self.sessions:
            print(f"❌ FATAL: Could not find session data under any of the expected keys: {session_keys} in {timetable_path.name}")
            sys.exit(1)

        self.slots_info = self._get_slots_info()
        self.days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        print(f"   ✓ Loaded {len(self.sessions)} scheduled sessions.")

    def _load_json(self, path: Path) -> dict:
        """Loads a JSON file."""
        if not path.exists():
            print(f"❌ FATAL: Timetable file not found at {path}")
            sys.exit(1)
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _get_slots_info(self) -> dict:
        """Creates a sorted map of time slots."""
        slots = defaultdict(dict)
        for session in self.sessions:
            slot_id = session['slotId']
            if '+' not in slot_id: # Only use single slots for rows
                 slots[slot_id]['start'] = session['startTime']
                 slots[slot_id]['end'] = session['endTime']
        
        # Sort slots by start time
        sorted_slots = sorted(slots.items(), key=lambda item: item[1]['start'])
        return dict(sorted_slots)

    def generate_reports(self):
        """
        Generates and saves Markdown reports for all relevant semesters.
        """
        print("⚙️ Processing schedules for all student groups...")
        
        # Segregate sessions by semester and get all unique sections
        sessions_by_sem = defaultdict(list)
        all_sections_by_sem = defaultdict(set)
        
        for session in self.sessions:
            semester = session['semester']
            sessions_by_sem[semester].append(session)
            for section in session.get('sections', []):
                all_sections_by_sem[semester].add(section)

        semesters_to_run = sorted(sessions_by_sem.keys())
        print(f"   ✓ Found data for semesters: {semesters_to_run}")

        for sem in semesters_to_run:
            sem_sections = sorted(list(all_sections_by_sem[sem]))
            report_content = self._generate_semester_report(sem, sem_sections, sessions_by_sem[sem])
            
            output_dir = Path(__file__).parent.parent / "views"
            output_dir.mkdir(exist_ok=True)
            output_path = output_dir / f"student_schedules_sem{sem}.md"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            print(f"   ✓ Semester {sem} report generated at: {output_path}")

    def _generate_semester_report(self, semester: int, sections: list, sessions: list) -> str:
        """Generates the full Markdown report for a single semester."""
        
        # Pre-process schedules for each section
        section_schedules = defaultdict(lambda: defaultdict(list))
        for session in sessions:
            day, slot = session.get('day'), session.get('slotId')
            if not day or not slot:
                continue
            
            entry = (
                f"**{session['shortCode']}** ({session['componentType']})<br>"
                f"{session['facultyId']}<br>"
                f"Room: {session['roomId']}"
            )
            
            for section_code in session.get('sections', []):
                if section_code in sections:
                    section_schedules[section_code][f"{day}-{slot}"].append(entry)

        # Build Markdown report
        report_parts = [f"# Student Weekly Schedules - Semester {semester}"]
        report_parts.append(f"> Generated on: {datetime.now().isoformat()}\n")

        for section_code in sections:
            report_parts.append(f"## Timetable for: Section {section_code}\n")
            
            # Header
            slot_headers = [f"{slot_id}<br>({times['start']}-{times['end']})" for slot_id, times in self.slots_info.items()]
            header = "| Day | " + " | ".join(slot_headers) + " |"
            separator = "|:--- | " + " | ".join([":---"] * len(self.slots_info)) + " |"
            report_parts.append(header)
            report_parts.append(separator)

            # Rows
            for day in self.days:
                row = [f"**{day}**"]
                for slot_id, times in self.slots_info.items():
                    # New, more robust logic
                    starting_entries = []
                    
                    # 1. Check for single-slot sessions starting here
                    single_key = f"{day}-{slot_id}"
                    starting_entries.extend(section_schedules[section_code].get(single_key, []))

                    # 2. Check for double-slot sessions starting here
                    for d_slot in ['S1+S2', 'S3+S4', 'S5+S6', 'S6+S7']:
                        if slot_id == d_slot.split('+')[0]:
                            double_key = f"{day}-{d_slot}"
                            starting_entries.extend(section_schedules[section_code].get(double_key, []))
                    
                    final_entry = ""
                    if starting_entries:
                        final_entry = "<hr>".join(starting_entries)
                    else:
                        # 3. Only if nothing starts here, check for continuation
                        for d_slot in ['S1+S2', 'S3+S4', 'S5+S6', 'S6+S7']:
                            if slot_id == d_slot.split('+')[1]: # This is the second half
                                prev_slot_key = f"{day}-{d_slot}"
                                prev_entries = section_schedules[section_code].get(prev_slot_key)
                                if prev_entries:
                                    cont_markers = [f"*({e.split('**')[1]} cont.)*" for e in prev_entries]
                                    final_entry = "<hr>".join(cont_markers)
                                    break
                    
                    row.append(final_entry)
                report_parts.append("| " + " | ".join(row) + " |")
            report_parts.append("\n---\n")

        return "\n".join(report_parts)

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Generate student schedule views from an enriched timetable.")
    parser.add_argument(
        "timetable_file",
        type=Path,
        help="Path to the enriched timetable JSON file (e.g., ../timetable_enriched.json)"
    )
    args = parser.parse_args()

    try:
        generator = StudentViewGenerator(args.timetable_file)
        generator.generate_reports()
            
        print(f"\n✅ Student schedule reports successfully generated in the `stage_6/views/` directory.")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
