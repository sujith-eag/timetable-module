#!/usr/bin/env python3
"""
Stage 6: Enrich Schedule to Full Timetable Format
Takes minimal Stage 5 schedule and enriches it with all details.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class ScheduleEnricher:
    def __init__(self):
        self.stage4_dir = Path(__file__).parent.parent.parent / "stage_4"
        self.stage5_dir = Path(__file__).parent.parent.parent / "stage_5"
        self.stage6_dir = Path(__file__).parent.parent.parent / "stage_6"
        self.stage6_dir.mkdir(exist_ok=True)
        
        self.scheduling_input = None
        self.assignments_map = {}
        self.time_slots_map = {}
        self.slot_combinations_map = {}
        
    def load_data(self):
        """Load Stage 4 scheduling input"""
        print("📂 Loading scheduling input...")
        
        input_file = self.stage4_dir / "schedulingInput.json"
        with open(input_file, 'r') as f:
            self.scheduling_input = json.load(f)
        
        # Build lookup maps
        for assignment in self.scheduling_input['assignments']:
            self.assignments_map[assignment['assignmentId']] = assignment
        
        for slot in self.scheduling_input['timeSlots']:
            key = f"{slot['day']}_{slot['slotId']}"
            self.time_slots_map[key] = slot
        
        # Build slot combinations map
        for combo in self.scheduling_input['slotCombinations']:
            if combo['type'] == 'single':
                slot_id = combo['slots'][0]
                self.slot_combinations_map[slot_id] = combo
            else:
                slot_id = "+".join(combo['slots'])
                self.slot_combinations_map[slot_id] = combo
        
        print(f"   ✓ Loaded {len(self.assignments_map)} assignments")
        print(f"   ✓ Built lookup maps")
        print()
    
    def load_schedule(self, schedule_file: Path) -> List[Dict]:
        """Load Stage 5 schedule"""
        print(f"📂 Loading schedule from {schedule_file.name}...")
        
        with open(schedule_file, 'r') as f:
            data = json.load(f)
        
        schedule = data.get('schedule', data)  # Handle both formats
        
        print(f"   ✓ Loaded {len(schedule)} sessions")
        print()
        
        return schedule
    
    def get_time_info(self, day: str, slot_id: str) -> Dict:
        """Get time information for a day/slot combination"""
        # Handle both single and double slots
        if '+' in slot_id:
            # Double slot like "S1+S2"
            slots = slot_id.split('+')
            first_slot_key = f"{day}_{slots[0]}"
            last_slot_key = f"{day}_{slots[1]}"
            
            if first_slot_key in self.time_slots_map and last_slot_key in self.time_slots_map:
                first = self.time_slots_map[first_slot_key]
                last = self.time_slots_map[last_slot_key]
                
                return {
                    "startTime": first['start'],
                    "endTime": last['end']
                }
        else:
            # Single slot
            key = f"{day}_{slot_id}"
            if key in self.time_slots_map:
                slot = self.time_slots_map[key]
                return {
                    "startTime": slot['start'],
                    "endTime": slot['end']
                }
        
        return {"startTime": None, "endTime": None}
    
    def enrich_session(self, session: Dict, session_counter: int) -> Dict:
        """Enrich a single session with full details"""
        assignment_id = session['assignmentId']
        assignment = self.assignments_map.get(assignment_id)
        
        if not assignment:
            print(f"   ⚠️  Warning: Assignment {assignment_id} not found in scheduling input")
            return None
        
        day = session.get('day')
        slot_id = session.get('slotId')
        room_id = session.get('roomId')
        
        # Get time information
        time_info = self.get_time_info(day, slot_id) if day and slot_id else {"startTime": None, "endTime": None}
        
        # Build enriched session
        enriched = {
            "sessionId": f"S_{session_counter:03d}",
            "day": day,
            "slotId": slot_id,
            "startTime": time_info['startTime'],
            "endTime": time_info['endTime'],
            "roomId": room_id,
            "subjectCode": assignment['subjectCode'],
            "shortCode": assignment.get('shortCode', assignment['subjectCode']),
            "subjectTitle": assignment['subjectTitle'],
            "componentType": assignment['componentType'],
            "facultyId": assignment['facultyId'],
            "facultyName": assignment['facultyName'],
            "studentGroupIds": assignment['studentGroupIds'],
            "semester": assignment['semester'],
            "sections": assignment['sections'],
            "supportingStaff": []
        }
        
        return enriched
    
    def enrich_schedule(self, schedule: List[Dict]) -> List[Dict]:
        """Enrich entire schedule"""
        print("✨ Enriching schedule...")
        print()
        
        enriched_schedule = []
        session_counter = 1
        
        skipped = 0
        enriched = 0
        
        for session in schedule:
            # Skip sessions with no day/slot (not yet scheduled)
            if not session.get('day') or not session.get('slotId'):
                skipped += 1
                continue
            
            enriched_session = self.enrich_session(session, session_counter)
            
            if enriched_session:
                enriched_schedule.append(enriched_session)
                session_counter += 1
                enriched += 1
        
        print(f"   ✓ Enriched {enriched} sessions")
        if skipped > 0:
            print(f"   ⚠️  Skipped {skipped} unscheduled sessions (no day/slot)")
        print()
        
        return enriched_schedule
    
    def save_enriched(self, enriched_schedule: List[Dict], original_file: str):
        """Save enriched timetable"""
        output = {
            "metadata": {
                "generatedAt": datetime.now().isoformat(),
                "generator": "enrich_schedule.py",
                "version": "1.0",
                "sourceFile": original_file,
                "totalSessions": len(enriched_schedule),
                "description": "Enriched timetable with full session details"
            },
            "timetable": enriched_schedule
        }
        
        output_file = self.stage6_dir / "timetable_enriched.json"
        
        print("💾 Saving enriched timetable...")
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        file_size = output_file.stat().st_size
        print(f"   ✓ Saved to: {output_file}")
        print(f"   ✓ File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        print()
        
        return output_file
    
    def generate_statistics(self, enriched_schedule: List[Dict]):
        """Generate statistics about enriched timetable"""
        print("=" * 70)
        print("ENRICHED TIMETABLE STATISTICS")
        print("=" * 70)
        print()
        
        total = len(enriched_schedule)
        
        # By day
        by_day = {}
        for session in enriched_schedule:
            day = session['day']
            by_day[day] = by_day.get(day, 0) + 1
        
        print("📅 Sessions by Day:")
        for day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']:
            count = by_day.get(day, 0)
            if count > 0:
                print(f"   • {day}: {count} sessions")
        print()
        
        # By component type
        by_component = {}
        for session in enriched_schedule:
            comp = session['componentType']
            by_component[comp] = by_component.get(comp, 0) + 1
        
        print("📝 Sessions by Component Type:")
        for comp, count in sorted(by_component.items()):
            print(f"   • {comp.capitalize()}: {count} sessions")
        print()
        
        # By semester
        by_semester = {}
        for session in enriched_schedule:
            sem = session['semester']
            by_semester[sem] = by_semester.get(sem, 0) + 1
        
        print("🎓 Sessions by Semester:")
        for sem, count in sorted(by_semester.items()):
            print(f"   • Semester {sem}: {count} sessions")
        print()
        
        # By room type
        by_room_type = {}
        for session in enriched_schedule:
            room_id = session.get('roomId')
            if room_id:
                if room_id.startswith('LAB'):
                    room_type = 'Lab'
                else:
                    room_type = 'Lecture'
                by_room_type[room_type] = by_room_type.get(room_type, 0) + 1
        
        print("🏢 Sessions by Room Type:")
        for room_type, count in sorted(by_room_type.items()):
            print(f"   • {room_type}: {count} sessions")
        print()
        
        # Unique subjects
        unique_subjects = set(s['subjectCode'] for s in enriched_schedule)
        print(f"📚 Unique Subjects: {len(unique_subjects)}")
        print()
        
        # Unique faculty
        unique_faculty = set(s['facultyId'] for s in enriched_schedule)
        print(f"👥 Faculty Teaching: {len(unique_faculty)}")
        print()
    
    def validate_schedule(self, enriched_schedule: List[Dict]):
        """Basic validation of enriched schedule"""
        print("🔍 Validating schedule...")
        print()
        
        issues = []
        
        # Check for conflicts
        faculty_slots = {}
        room_slots = {}
        student_group_slots = {}
        
        for session in enriched_schedule:
            day = session['day']
            slot = session['slotId']
            faculty = session['facultyId']
            room = session.get('roomId')
            student_groups = session['studentGroupIds']
            
            time_key = f"{day}_{slot}"
            
            # Faculty conflicts
            if faculty:
                if faculty not in faculty_slots:
                    faculty_slots[faculty] = {}
                if time_key in faculty_slots[faculty]:
                    issues.append(f"Faculty conflict: {faculty} at {day} {slot}")
                    issues.append(f"  Sessions: {faculty_slots[faculty][time_key]} and {session['sessionId']}")
                else:
                    faculty_slots[faculty][time_key] = session['sessionId']
            
            # Room conflicts
            if room:
                if room not in room_slots:
                    room_slots[room] = {}
                if time_key in room_slots[room]:
                    issues.append(f"Room conflict: {room} at {day} {slot}")
                    issues.append(f"  Sessions: {room_slots[room][time_key]} and {session['sessionId']}")
                else:
                    room_slots[room][time_key] = session['sessionId']
            
            # Student group conflicts
            for sg in student_groups:
                if sg not in student_group_slots:
                    student_group_slots[sg] = {}
                if time_key in student_group_slots[sg]:
                    # This might be OK if groups can overlap - just note it
                    pass
                else:
                    student_group_slots[sg][time_key] = session['sessionId']
        
        if issues:
            print(f"   ⚠️  Found {len(issues)} potential issues:")
            for issue in issues[:10]:  # Show first 10
                print(f"      {issue}")
            if len(issues) > 10:
                print(f"      ... and {len(issues) - 10} more")
        else:
            print("   ✅ No obvious conflicts detected")
        
        print()


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 enrich_schedule.py <schedule_file>")
        print()
        print("Examples:")
        print("  python3 enrich_schedule.py ../stage_5/scheduleTemplate.json")
        print("  python3 enrich_schedule.py ../stage_5/scheduleExample.json")
        print("  python3 enrich_schedule.py my_schedule.json")
        return 1
    
    schedule_file = Path(sys.argv[1])
    
    if not schedule_file.exists():
        print(f"❌ Error: File not found: {schedule_file}")
        return 1
    
    try:
        enricher = ScheduleEnricher()
        
        print("=" * 70)
        print("STAGE 6: ENRICH SCHEDULE TO FULL TIMETABLE")
        print("=" * 70)
        print()
        
        # Load data
        enricher.load_data()
        schedule = enricher.load_schedule(schedule_file)
        
        # Enrich
        enriched = enricher.enrich_schedule(schedule)
        
        if not enriched:
            print("❌ No sessions were enriched!")
            print("   Make sure your schedule has day and slotId filled in.")
            return 1
        
        # Save
        output_file = enricher.save_enriched(enriched, schedule_file.name)
        
        # Statistics
        enricher.generate_statistics(enriched)
        
        # Validation
        enricher.validate_schedule(enriched)
        
        print("=" * 70)
        print("✅ ENRICHMENT COMPLETE")
        print("=" * 70)
        print()
        
        print(f"📄 Enriched timetable saved to:")
        print(f"   {output_file}")
        print()
        
        print("📊 Summary:")
        print(f"   • Total sessions: {len(enriched)}")
        print(f"   • Format: Full timetable with all details")
        print()
        
        print("Next Steps:")
        print("   • Review timetable_enriched.json")
        print("   • Check for conflicts in validation output")
        print("   • Generate grids and reports")
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
