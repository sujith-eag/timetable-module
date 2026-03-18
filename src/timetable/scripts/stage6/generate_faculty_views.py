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
        """Creates a sorted map of INDIVIDUAL time slots.
        
        Extracts individual slots from both single slots (S1, S2) and 
        double-slot combinations (S1+S2 -> S1, S2; S3+S4 -> S3, S4).
        Returns complete header with all individual slots in time order.
        """
        slots = defaultdict(dict)
        for session in self.sessions:
            slot_id = session['slotId']
            
            if '+' in slot_id:
                # For double-slot entries like S1+S2, extract both slots
                parts = slot_id.split('+')
                for part in parts:
                    if part not in slots:  # Not yet recorded
                        slots[part]['start'] = session['startTime']
                        slots[part]['end'] = session['endTime']
            else:
                # Single slot - use as is
                slots[slot_id]['start'] = session['startTime']
                slots[slot_id]['end'] = session['endTime']
        
        # Sort slots by start time, then by slot ID
        sorted_slots = sorted(slots.items(), key=lambda item: (item[1]['start'], item[0]))
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
            
            # Format room: use "NA" for NOT_APPLICABLE
            room_display = "NA" if session['roomId'] == "NOT_APPLICABLE" else f"Room: {session['roomId']}"
            
            entry = (
                (f"**{session['subjectTitle']}**" if session.get('subjectTitle') and session['subjectTitle'] != session.get('shortCode') 
                 else f"**{session['shortCode']}**") +
                f" ({session['componentType']})<br>"
                f"{', '.join(session['studentGroupIds'])}<br>"
                f"{room_display}"
            )
            faculty_schedules[fac_id][f"{day}-{slot}"].append(entry)

            # Supporting staff
            for staff in session.get('supportingStaff', []):
                staff_id = staff['id']
                staff_name = staff['name']
                if staff_id not in all_faculty:
                    all_faculty[staff_id] = staff_name
                
                support_entry = (
                    (f"*(Support)*<br>**{session['subjectTitle']}**" if session.get('subjectTitle') and session['subjectTitle'] != session.get('shortCode')
                     else f"*(Support)*<br>**{session['shortCode']}**") +
                    f" ({session['componentType']})<br>"
                    f"{', '.join(session['studentGroupIds'])}<br>"
                    f"{room_display}"
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
                for slot_id in self.slots_info.keys():
                    # Collect ALL entries: single-slot AND double-slot start (both can coexist!)
                    entries = []
                    
                    # 1. Check for single-slot match
                    single_key = f"{day}-{slot_id}"
                    if single_key in faculty_schedules[fac_id]:
                        entries.extend(faculty_schedules[fac_id][single_key])
                    
                    # 2. Check if this is the START of a double-slot (combine, don't skip)
                    for double_slot in ['S1+S2', 'S3+S4', 'S5+S6', 'S6+S7']:
                        if slot_id == double_slot.split('+')[0]:  # This slot starts the double
                            double_key = f"{day}-{double_slot}"
                            if double_key in faculty_schedules[fac_id]:
                                entries.extend(faculty_schedules[fac_id][double_key])
                    
                    # 3. If no entries yet, check if this is the CONTINUATION of a double-slot
                    if not entries:
                        for double_slot in ['S1+S2', 'S3+S4', 'S5+S6', 'S6+S7']:
                            if slot_id == double_slot.split('+')[1]:  # This slot continues a double
                                double_key = f"{day}-{double_slot}"
                                if double_key in faculty_schedules[fac_id]:
                                    prev_entries = faculty_schedules[fac_id][double_key]
                                    cont_markers = [f"*({e.split('**')[1]} cont.)*" for e in prev_entries]
                                    entries = cont_markers
                                    break
                    
                    # 4. Add to row
                    if entries:
                        row.append("<hr>".join(entries))
                    else:
                        row.append("")
                
                report_parts.append("| " + " | ".join(row) + " |")
            report_parts.append("\n---\n")

        return "\n".join(report_parts)

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Generate faculty schedule views from an enriched timetable.")
    parser.add_argument("--data-dir", required=True, help="Data directory path")
    args = parser.parse_args()

    # Automatically find the enriched timetable
    timetable_file = Path(args.data_dir) / "stage_6" / "timetable_enriched.json"

    try:
        generator = FacultyViewGenerator(timetable_file)
        report_content = generator.generate_report()
        
        output_dir = Path(args.data_dir) / "stage_6" / "views"
        output_dir.mkdir(exist_ok=True, parents=True)
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
