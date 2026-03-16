#!/usr/bin/env python3
"""
Stage 4: Scheduling Input Viewer
Interactive viewer to explore the scheduling input data
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

class SchedulingInputViewer:
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # Auto-detect for development
            script_dir = Path(__file__).parent
            self.data_dir = script_dir.parent.parent
        else:
            self.data_dir = Path(data_dir)
        
        input_file = self.data_dir / "stage_4" / "schedulingInput.json"
        
        if not input_file.exists():
            raise FileNotFoundError(f"Scheduling input not found: {input_file}")
        
        with open(input_file, 'r') as f:
            self.data = json.load(f)
    
    def show_summary(self):
        """Show overall summary"""
        print("=" * 70)
        print("SCHEDULING INPUT SUMMARY")
        print("=" * 70)
        print()
        
        meta = self.data['metadata']
        active_semesters = meta.get('activeSemesters', [1, 3])
        
        print(f"📊 Total Assignments: {meta['totalAssignments']}")
        print(f"   Active Semesters: {active_semesters}")
        
        # Display assignment counts for active semesters dynamically
        for sem in active_semesters:
            sem_key = f'semester{sem}Assignments'
            sem_count = meta.get(sem_key)
            if sem_count is not None:
                print(f"   • Semester {sem}: {sem_count}")
        print()
        
        print(f"🕐 Time Slots: {meta['totalTimeSlots']}")
        print(f"🏢 Rooms: {meta['totalRooms']}")
        print(f"👥 Faculty: {len(self.data['constraints']['facultyList'])}")
        print(f"🎓 Student Groups: {len(self.data['constraints']['studentGroupList'])}")
        print()
    
    def list_assignments(self, filter_by: str = None):
        """List all assignments with optional filtering"""
        assignments = self.data['assignments']
        
        if filter_by:
            if filter_by.startswith('sem'):
                sem = int(filter_by.replace('sem', ''))
                assignments = [a for a in assignments if a['semester'] == sem]
            elif filter_by in ['theory', 'practical', 'tutorial']:
                assignments = [a for a in assignments if a['componentType'] == filter_by]
            elif filter_by in ['high', 'medium', 'low']:
                assignments = [a for a in assignments if a['priority'] == filter_by]
        
        print(f"\n📋 Assignments ({len(assignments)}):")
        print("-" * 70)
        
        for i, a in enumerate(assignments, 1):
            sessions_info = f"{a['sessionsPerWeek']}x{a['sessionDuration']}min"
            sections_info = ",".join(a['sections'])
            
            print(f"{i:2d}. {a['assignmentId']}")
            print(f"    {a['subjectTitle']} ({a['componentType'].upper()})")
            print(f"    Faculty: {a['facultyName']} | Sections: {sections_info}")
            print(f"    Sessions: {sessions_info} | Priority: {a['priority']}")
            print()
    
    def show_assignment_details(self, assignment_id: str):
        """Show detailed information about a specific assignment"""
        assignment = next((a for a in self.data['assignments'] if a['assignmentId'] == assignment_id), None)
        
        if not assignment:
            print(f"❌ Assignment {assignment_id} not found")
            return
        
        print("\n" + "=" * 70)
        print(f"ASSIGNMENT DETAILS: {assignment_id}")
        print("=" * 70)
        print()
        
        print(f"📚 Subject: {assignment['subjectTitle']} ({assignment['subjectCode']})")
        print(f"📝 Component: {assignment['componentType'].upper()}")
        print(f"📅 Semester: {assignment['semester']}")
        print(f"⭐ Priority: {assignment['priority']}")
        print(f"🎯 Elective: {'Yes' if assignment['isElective'] else 'No'}")
        print()
        
        print(f"👨‍🏫 Faculty: {assignment['facultyName']} ({assignment['facultyId']})")
        print(f"👥 Sections: {', '.join(assignment['sections'])}")
        print(f"🎓 Student Groups: {', '.join(assignment['studentGroupIds'])}")
        print()
        
        print(f"⏱️  Session Duration: {assignment['sessionDuration']} minutes")
        print(f"📆 Sessions Per Week: {assignment['sessionsPerWeek']}")
        print(f"🔗 Requires Contiguous: {'Yes' if assignment['requiresContiguous'] else 'No'}")
        print(f"✅ Valid Slot Types: {', '.join(assignment['validSlotTypes'])}")
        print()
        
        print(f"🏢 Room Type Required: {assignment['requiresRoomType']}")
        if assignment['preferredRooms']:
            print(f"   Preferred Rooms: {', '.join(assignment['preferredRooms'])}")
        if assignment['constraints']['mustBeInRoom']:
            print(f"   ⚠️  MUST use room: {assignment['constraints']['mustBeInRoom']}")
        print()
        
        print("🚫 Constraints:")
        print(f"   • Student Group Conflicts: {', '.join(assignment['constraints']['studentGroupConflicts'])}")
        print(f"   • Faculty Conflicts: {', '.join(assignment['constraints']['facultyConflicts'])}")
        if assignment['constraints']['fixedDay']:
            print(f"   • Fixed Day: {assignment['constraints']['fixedDay']}")
        if assignment['constraints']['fixedSlot']:
            print(f"   • Fixed Slot: {assignment['constraints']['fixedSlot']}")
        print()
    
    def show_time_slots(self):
        """Show all available time slots"""
        print("\n" + "=" * 70)
        print("TIME SLOTS")
        print("=" * 70)
        print()
        
        weekdays = self.data['configuration']['weekdays']
        
        for day in weekdays:
            day_slots = [ts for ts in self.data['timeSlots'] if ts['day'] == day]
            print(f"{day}:")
            for slot in day_slots:
                print(f"  {slot['slotId']}: {slot['start']}-{slot['end']} ({slot['durationMinutes']} min)")
            print()
    
    def show_slot_combinations(self):
        """Show valid slot combinations"""
        print("\n" + "=" * 70)
        print("VALID SLOT COMBINATIONS")
        print("=" * 70)
        print()
        
        singles = [c for c in self.data['slotCombinations'] if c['type'] == 'single']
        doubles = [c for c in self.data['slotCombinations'] if c['type'] == 'double']
        
        print(f"Single Slots ({len(singles)}) - For 55-minute sessions:")
        for combo in singles:
            print(f"  • {combo['slots'][0]} ({combo['durationMinutes']} min)")
        print()
        
        print(f"Double Slots ({len(doubles)}) - For 110-minute sessions:")
        for combo in doubles:
            slots_str = "+".join(combo['slots'])
            print(f"  • {slots_str} ({combo['durationMinutes']} min)")
        print()
    
    def show_rooms(self):
        """Show all available rooms"""
        print("\n" + "=" * 70)
        print("ROOMS")
        print("=" * 70)
        print()
        
        by_type = {}
        for room in self.data['rooms']:
            room_type = room['type']
            if room_type not in by_type:
                by_type[room_type] = []
            by_type[room_type].append(room)
        
        for room_type, rooms in sorted(by_type.items()):
            print(f"{room_type.upper()} Rooms ({len(rooms)}):")
            for room in rooms:
                print(f"  • {room['roomId']} (Capacity: {room['capacity']})")
            print()
    
    def show_faculty(self):
        """Show all faculty members"""
        print("\n" + "=" * 70)
        print("FACULTY MEMBERS")
        print("=" * 70)
        print()
        
        faculty_list = sorted(self.data['constraints']['facultyList'])
        
        for fac_id in faculty_list:
            assignments = [a for a in self.data['assignments'] if a['facultyId'] == fac_id]
            total_sessions = sum(a['sessionsPerWeek'] for a in assignments)
            
            if assignments:
                name = assignments[0]['facultyName']
                print(f"• {name} ({fac_id})")
                print(f"  Assignments: {len(assignments)} | Sessions/week: {total_sessions}")
        print()
    
    def show_student_groups(self):
        """Show all student groups"""
        print("\n" + "=" * 70)
        print("STUDENT GROUPS")
        print("=" * 70)
        print()
        
        for group in self.data['studentGroups']:
            print(f"• {group['groupId']}: {group['description']}")
            print(f"  Size: {group['size']} | Semester: {group['semester']}")
            if 'parentGroups' in group and group['parentGroups']:
                print(f"  Parent Groups: {', '.join(group['parentGroups'])}")
            print()
    
    def show_constraint_matrix(self):
        """Show student group overlap constraints"""
        print("\n" + "=" * 70)
        print("STUDENT GROUP OVERLAP CONSTRAINTS")
        print("=" * 70)
        print()
        
        overlap = self.data['constraints']['studentGroupOverlap']
        
        print("Cannot Overlap With (CONFLICTS):")
        print("-" * 70)
        for group_id, conflicts in sorted(overlap['cannotOverlapWith'].items()):
            print(f"  {group_id:15s} ⊗ {', '.join(conflicts)}")
        print()
        
        print("Can Run Parallel With:")
        print("-" * 70)
        for group_id, parallel in sorted(overlap['canRunParallelWith'].items()):
            if parallel:
                print(f"  {group_id:15s} ✓ {', '.join(parallel)}")
        print()

    def show_help(self):
        """Show help information"""
        active_semesters = self.data['metadata'].get('activeSemesters', [1, 3])
        sem_filters = ', '.join([f'sem{s}' for s in active_semesters])
        
        print("Usage: python3 view_scheduling_input.py [--data-dir DIR] <command> [args]")
        print()
        print("Commands:")
        print("  summary                    Show overall summary (default)")
        print("  assignments [filter]       List all assignments")
        print(f"                             Filters: {sem_filters}, theory, practical, tutorial")
        print("  assignment <id>            Show details for specific assignment")
        print("  slots                      Show all time slots by day")
        print("  combinations               Show valid slot combinations")
        print("  rooms                      Show all available rooms")
        print("  faculty                    Show faculty members and their loads")
        print("  groups                     Show student groups")
        print("  constraints                Show student group overlap constraints")
        print()
        print("Examples:")
        print("  python3 view_scheduling_input.py --data-dir ./data summary")
        print("  python3 view_scheduling_input.py assignments sem1")
        print("  python3 view_scheduling_input.py assignment TA_25MCA15_TH_B_001")
        print("  python3 view_scheduling_input.py slots")
        print()


def main():
    """Main function with command line interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="View scheduling input data")
    parser.add_argument("--data-dir", help="Data directory path (default: auto-detect)")
    parser.add_argument("command", nargs="?", help="Command to run")
    parser.add_argument("args", nargs="*", help="Additional arguments")
    
    args = parser.parse_args()
    
    try:
        viewer = SchedulingInputViewer(args.data_dir)
        
        if args.command == "summary" or not args.command:
            viewer.show_summary()
        elif args.command == "assignments":
            filter_by = args.args[0] if args.args else None
            viewer.list_assignments(filter_by)
        elif args.command == "assignment":
            if not args.args:
                print("Usage: view_scheduling_input.py assignment <assignment_id>")
                return 1
            viewer.show_assignment_details(args.args[0])
        elif args.command == "slots":
            viewer.show_time_slots()
        elif args.command == "combinations":
            viewer.show_slot_combinations()
        elif args.command == "rooms":
            viewer.show_rooms()
        elif args.command == "faculty":
            viewer.show_faculty()
        elif args.command == "groups":
            viewer.show_student_groups()
        elif args.command == "constraints":
            viewer.show_constraints()
        else:
            viewer.show_help()
            return 1
            
        return 0
        
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("   Run 'timetable build stage4' first!")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
