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
    def __init__(self, input_file: Path):
        with open(input_file, 'r') as f:
            self.data = json.load(f)
    
    def show_summary(self):
        """Show overall summary"""
        print("=" * 70)
        print("SCHEDULING INPUT SUMMARY")
        print("=" * 70)
        print()
        
        meta = self.data['metadata']
        print(f"📊 Total Assignments: {meta['totalAssignments']}")
        print(f"   • Semester 1: {meta['semester1Assignments']}")
        print(f"   • Semester 3: {meta['semester3Assignments']}")
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


def main():
    input_file = Path(__file__).parent.parent / "schedulingInput.json"
    
    if not input_file.exists():
        print(f"❌ Error: {input_file} not found")
        print("   Run build_scheduling_input.py first!")
        return 1
    
    viewer = SchedulingInputViewer(input_file)
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "summary":
            viewer.show_summary()
        elif command == "assignments":
            filter_by = sys.argv[2] if len(sys.argv) > 2 else None
            viewer.list_assignments(filter_by)
        elif command == "assignment":
            if len(sys.argv) < 3:
                print("Usage: view_scheduling_input.py assignment <assignment_id>")
                return 1
            viewer.show_assignment_details(sys.argv[2])
        elif command == "slots":
            viewer.show_time_slots()
        elif command == "combinations":
            viewer.show_slot_combinations()
        elif command == "rooms":
            viewer.show_rooms()
        elif command == "faculty":
            viewer.show_faculty()
        elif command == "groups":
            viewer.show_student_groups()
        elif command == "constraints":
            viewer.show_constraint_matrix()
        else:
            print(f"Unknown command: {command}")
            print_usage()
            return 1
    else:
        print_usage()
        viewer.show_summary()
    
    return 0


def print_usage():
    print("=" * 70)
    print("SCHEDULING INPUT VIEWER")
    print("=" * 70)
    print()
    print("Usage: python3 view_scheduling_input.py <command> [args]")
    print()
    print("Commands:")
    print("  summary                    Show overall summary (default)")
    print("  assignments [filter]       List all assignments")
    print("                             Filters: sem1, sem3, theory, practical, tutorial")
    print("  assignment <id>            Show details for specific assignment")
    print("  slots                      Show all time slots by day")
    print("  combinations               Show valid slot combinations")
    print("  rooms                      Show all available rooms")
    print("  faculty                    Show faculty members and their loads")
    print("  groups                     Show student groups")
    print("  constraints                Show student group overlap constraints")
    print()
    print("Examples:")
    print("  python3 view_scheduling_input.py summary")
    print("  python3 view_scheduling_input.py assignments sem1")
    print("  python3 view_scheduling_input.py assignment TA_25MCA15_TH_B_001")
    print("  python3 view_scheduling_input.py slots")
    print()


if __name__ == "__main__":
    sys.exit(main())
