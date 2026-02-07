#!/usr/bin/env python3
"""
Stage 6: Faculty Schedule View Generator

This script generates a human-readable weekly schedule for each faculty member
from an enriched timetable JSON file. It includes both primary teaching
assignments and sessions where the faculty member is listed as supporting staff.
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import sys

class FacultyViewGenerator:
    """Generates Markdown schedules for each faculty member."""

    def __init__(self, timetable_path: Path):
        """
        Initializes the generator.
        
        Args:
            timetable_path: Path to the enriched timetable JSON file.
        """
        print("📂 Loading timetable...")
        self.timetable_data = self._load_json(timetable_path)
        self.sessions = self.timetable_data.get('timetable_A', []) or self.timetable_data.get('timetable', [])
        if not self.sessions:
            print(f"❌ FATAL: Could not find session data under 'timetable_A' or 'timetable' key in {timetable_path.name}")
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


    def generate_report(self) -> str:
        """
        Generates the full Markdown report for all faculty members.
        """
        print("⚙️ Processing schedules for all faculty...")
        faculty_schedules = defaultdict(lambda: defaultdict(list))
        all_faculty = {}

        for session in self.sessions:
            day, slot = session.get('day'), session.get('slotId')
            if not day or not slot:
                continue

            # Primary faculty
            fac_id = session['facultyId']
            fac_name = session['facultyName']
            if fac_id not in all_faculty:
                all_faculty[fac_id] = fac_name
            
            entry = (
                f"**{session['shortCode']}** ({session['componentType']})<br>"
                f"{', '.join(session['studentGroupIds'])}<br>"
                f"Room: {session['roomId']}"
            )
            faculty_schedules[fac_id][f"{day}-{slot}"].append(entry)

            # Supporting staff
            for staff in session.get('supportingStaff', []):
                staff_id = staff['id']
                staff_name = staff['name']
                if staff_id not in all_faculty:
                    all_faculty[staff_id] = staff_name
                
                support_entry = (
                    f"*(Support)*<br>"
                    f"**{session['shortCode']}** ({session['componentType']})<br>"
                    f"{', '.join(session['studentGroupIds'])}<br>"
                    f"Room: {session['roomId']}"
                )
                faculty_schedules[staff_id][f"{day}-{slot}"].append(support_entry)
        
        print(f"   ✓ Processed data for {len(all_faculty)} faculty members.")
        
        # Build Markdown report
        report_parts = ["# Faculty Weekly Schedules"]
        report_parts.append(f"> Generated on: {datetime.now().isoformat()}\n")

        for fac_id, fac_name in sorted(all_faculty.items()):
            report_parts.append(f"## Timetable for: {fac_name} ({fac_id})\n")
            
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
                    starting_entries.extend(faculty_schedules[fac_id].get(single_key, []))

                    # 2. Check for double-slot sessions starting here
                    for d_slot in ['S1+S2', 'S3+S4', 'S5+S6', 'S6+S7']:
                        if slot_id == d_slot.split('+')[0]:
                            double_key = f"{day}-{d_slot}"
                            starting_entries.extend(faculty_schedules[fac_id].get(double_key, []))
                    
                    final_entry = ""
                    if starting_entries:
                        final_entry = "<hr>".join(starting_entries)
                    else:
                        # 3. Only if nothing starts here, check for continuation
                        for d_slot in ['S1+S2', 'S3+S4', 'S5+S6', 'S6+S7']:
                            if slot_id == d_slot.split('+')[1]: # This is the second half
                                prev_slot_key = f"{day}-{d_slot}"
                                prev_entries = faculty_schedules[fac_id].get(prev_slot_key)
                                if prev_entries:
                                    # A faculty can't be in two places, so there's only one entry
                                    short_code = prev_entries[0].split('**')[1]
                                    final_entry = f"*({short_code} cont.)*"
                                    break
                    
                    row.append(final_entry)
                report_parts.append("| " + " | ".join(row) + " |")
            report_parts.append("\n---\n")

        return "\n".join(report_parts)

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Generate faculty schedule views from an enriched timetable.")
    parser.add_argument(
        "timetable_file",
        type=Path,
        help="Path to the enriched timetable JSON file (e.g., ../timetable_enriched.json)"
    )
    args = parser.parse_args()

    try:
        generator = FacultyViewGenerator(args.timetable_file)
        report_content = generator.generate_report()
        
        output_dir = Path(__file__).parent.parent / "views"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "faculty_schedules.md"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
            
        print(f"\n✅ Faculty schedules report successfully generated at: {output_path}")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
