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

    def __init__(self, timetable_path: Path, data_dir: Path = None):
        """
        Initializes the generator.
        
        Args:
            timetable_path: Path to the enriched timetable JSON file.
            data_dir: Base data directory for outputs.
        """
        print("📂 Loading timetable...")
        self.timetable_data = self._load_json(timetable_path)
        self.data_dir = data_dir or timetable_path.parent.parent

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

        self.unscheduled_assignments = self.timetable_data.get('unscheduledAssignments', [])
        self.slots_info = self._get_slots_info()
        self.days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        print(f"   ✓ Loaded {len(self.sessions)} scheduled sessions.")
        if self.unscheduled_assignments:
            print(f"   ✓ Loaded {len(self.unscheduled_assignments)} unscheduled assignments.")

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
            
            output_dir = self.data_dir / "stage_6" / "views"
            output_dir.mkdir(exist_ok=True, parents=True)
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
            
            # Format room: use "NA" for NOT_APPLICABLE
            room_display = "NA" if session['roomId'] == "NOT_APPLICABLE" else f"Room: {session['roomId']}"
            
            entry = (
                f"**{session['subjectTitle']}**" if session.get('subjectTitle') and session['subjectTitle'] != session.get('shortCode') 
                else f"**{session['shortCode']}**"
            )
            # Add faculty/instructors with consolidated supporting staff (compact format)
            primary_faculty = session['facultyId']
            supporting_list = [staff['id'] for staff in session.get('supportingStaff', [])]
            
            if supporting_list:
                faculty_str = f"{primary_faculty}, Support: {', '.join(supporting_list)}"
            else:
                faculty_str = primary_faculty
            
            entry += f" ({session['componentType']})<br>{faculty_str}<br>{room_display}"
            
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
                for slot_id in self.slots_info.keys():
                    # Collect ALL entries: single-slot AND double-slot start (both can coexist!)
                    entries = []
                    
                    # 1. Check for single-slot match
                    single_key = f"{day}-{slot_id}"
                    if single_key in section_schedules[section_code]:
                        entries.extend(section_schedules[section_code][single_key])
                    
                    # 2. Check if this is the START of a double-slot (combine, don't skip)
                    for double_slot in ['S1+S2', 'S3+S4', 'S5+S6', 'S6+S7']:
                        if slot_id == double_slot.split('+')[0]:  # This slot starts the double
                            double_key = f"{day}-{double_slot}"
                            if double_key in section_schedules[section_code]:
                                entries.extend(section_schedules[section_code][double_key])
                    
                    # 3. If no entries yet, check if this is the CONTINUATION of a double-slot
                    if not entries:
                        for double_slot in ['S1+S2', 'S3+S4', 'S5+S6', 'S6+S7']:
                            if slot_id == double_slot.split('+')[1]:  # This slot continues a double
                                double_key = f"{day}-{double_slot}"
                                if double_key in section_schedules[section_code]:
                                    prev_entries = section_schedules[section_code][double_key]
                                    cont_markers = [f"*({e.split('**')[1]} cont.)*" for e in prev_entries]
                                    entries = cont_markers
                                    break
                    
                    # 4. Add to row
                    if entries:
                        row.append("<hr>".join(entries))
                    else:
                        row.append("")
                
                report_parts.append("| " + " | ".join(row) + " |")
            report_parts.append("\n---\n")  # Separator between sections
        
        # Add unscheduled assignments summary for this semester
        unscheduled_sem = [a for a in self.unscheduled_assignments if a['semester'] == semester]
        if unscheduled_sem:
            report_parts.append(f"\n## ❌ Unscheduled Assignments - Semester {semester}\n")
            report_parts.append("| Subject | Type | Faculty | Component | Groups | Sessions |\n")
            report_parts.append("|:--- |:--- |:--- |:--- |:--- |:--- |\n")
            for a in sorted(unscheduled_sem, key=lambda x: (x['facultyId'], x['subjectCode'])):
                report_parts.append(
                    f"| {a['subjectCode']} | {a.get('assignmentType', 'N/A')} | {a['facultyName']} ({a['facultyId']}) | "
                    f"{a['componentType']} | {', '.join(a['studentGroupIds'])} | "
                    f"{a['sessionsPerWeek']}/week |\n"
                )
            report_parts.append("")

        return "\n".join(report_parts)

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Generate student schedule views from an enriched timetable.")
    parser.add_argument("--data-dir", required=True, help="Data directory path")
    args = parser.parse_args()

    # Automatically find the enriched timetable
    timetable_file = Path(args.data_dir) / "stage_6" / "timetable_enriched.json"

    try:
        generator = StudentViewGenerator(timetable_file, Path(args.data_dir))
        generator.generate_reports()
            
        print(f"\n✅ Student schedule reports successfully generated in the `stage_6/views/` directory.")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
