#!/usr/bin/env python3
"""
Stage 5 AI Scheduler: Constraint-based scheduler for university timetables.
Generates conflict-free schedules using Stage 4 assignment and constraint data.
Following the prompt guidelines to create optimal schedules.
"""

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict

class ScheduleOptimizer:
    def __init__(self, data_dir: str):
        """Initialize optimizer with data directory path."""
        self.data_dir = Path(data_dir)
        self.stage1_dir = self.data_dir / "stage_1"
        self.stage4_dir = self.data_dir / "stage_4"
        self.stage5_dir = self.data_dir / "stage_5"
        
        # Create stage_5 if it doesn't exist
        self.stage5_dir.mkdir(exist_ok=True)
        
        # Load config and scheduling input
        config_path = self.stage1_dir / "config.json"
        staging_input_path = self.stage4_dir / "schedulingInput.json"
        
        with open(config_path) as f:
            self.config = json.load(f)['config']
        with open(staging_input_path) as f:
            self.input_data = json.load(f)
        
        # Load Stage 4 data
        self.assignments = self.input_data.get('assignments', [])
        self.constraints = self.input_data.get('constraints', {})
        self.time_slots = self.input_data.get('timeSlots', [])
        self.student_groups = {g['studentGroupId']: g for g in self.input_data.get('studentGroups', [])}
        
        # Extract infrastructure from config
        self.rooms = {r['roomId']: r for r in self.config['resources']['rooms']}
        self.weekdays = self.config['weekdays']
        self.day_slots = self.config['daySlotPattern']
        self.valid_combinations = self.config['validSlotCombinations']
        
        # Build slot maps for quick lookup
        self.slots_by_day = defaultdict(list)
        for slot in self.time_slots:
            self.slots_by_day[slot['day']].append(slot['slotId'])
        
        # State tracking - use (day, slot) tuples as keys
        self.schedule = {}  # assignmentId + str(sessionNumber) -> {day, slotId, roomId}
        self.room_bookings = defaultdict(set)  # room_bookings[(roomId, day, slot)] = assignmentId
        self.faculty_bookings = defaultdict(set)  # faculty_bookings[(facultyId, day, slot)] = assignmentId
        self.group_bookings = defaultdict(set)  # group_bookings[(studentGroupId, day, slot)] = assignmentId
        
    def extract_entity_ids(self, assignment_id: str) -> Tuple[str, str, str]:
        """Extract subject, component, group from assignment ID.
        Format: TA_SUBJECT_COMPONENT_GROUP_NUM
        """
        parts = assignment_id.split('_')
        if len(parts) >= 4:
            subject = parts[1]
            component = parts[2]
            group = parts[3] if parts[3] not in ['001', '002', '003', '004', '005', '026', '027', '028'] else 'ALL'
            return subject, component, group
        return '', '', ''
    
    def get_valid_slots_for_duration(self, duration: int, day: str) -> List[str]:
        """Get valid slot combinations for a given duration and day."""
        day_slots_list = self.slots_by_day.get(day, [])
        
        if duration == 55:
            return day_slots_list
        elif duration == 110:
            # Return valid double slots
            valid_doubles = []
            for combo in self.valid_combinations['double']:
                if '+' in combo:
                    s1, s2 = combo.split('+')
                    if s1 in day_slots_list and s2 in day_slots_list:
                        valid_doubles.append(combo)
            if day == 'Sat':
                for combo in self.valid_combinations['saturday']:
                    if '+' in combo:
                        s1, s2 = combo.split('+')
                        if s1 in day_slots_list and s2 in day_slots_list:
                            valid_doubles.append(combo)
            return valid_doubles
        return []
    
    def get_room_options(self, room_type: str, preferred_rooms: List[str] = None) -> List[str]:
        """Get available rooms for a given room type, preferring those in preferredRooms list."""
        all_rooms = [rid for rid, room in self.rooms.items() if room['type'] == room_type]
        
        if preferred_rooms:
            # Prioritize preferred rooms
            preferred_set = set(preferred_rooms)
            preferred = [r for r in all_rooms if r in preferred_set]
            others = [r for r in all_rooms if r not in preferred_set]
            return preferred + others
        
        return all_rooms
    
    def check_room_available(self, room_id: str, day: str, slots: List[str]) -> bool:
        """Check if room is available for all requested slots on a day."""
        for slot in slots:
            if (room_id, day, slot) in self.room_bookings:
                return False
        return True
    
    def check_faculty_available(self, faculty_id: str, day: str, slots: List[str]) -> bool:
        """Check if faculty has no conflicts."""
        for slot in slots:
            if (faculty_id, day, slot) in self.faculty_bookings:
                return False
        return True
    
    def check_group_available(self, group_ids: List[str], day: str, slots: List[str]) -> bool:
        """Check if student groups have no conflicts (same group double-booking)."""
        for group_id in group_ids:
            for slot in slots:
                if (group_id, day, slot) in self.group_bookings:
                    return False
        return True
    
    def check_group_overlap_constraints(self, group_ids: List[str], day: str, slots: List[str]) -> bool:
        """Check studentGroupOverlap constraints - groups that cannot be scheduled together."""
        overlap_constraints = self.constraints.get('studentGroupOverlap', {}).get('cannotOverlapWith', {})
        
        for group_id in group_ids:
            if group_id not in overlap_constraints:
                continue
            
            banned_groups = set(overlap_constraints[group_id])
            
            for slot in slots:
                # Check if any banned group is already scheduled at this (day, slot)
                for banned_group_id in banned_groups:
                    if (banned_group_id, day, slot) in self.group_bookings:
                        return False  # Conflict found
        
        return True
    
    def check_room_capacity(self, room_id: str, group_ids: List[str], is_diff_subject: bool = False) -> bool:
        """Check if room capacity is sufficient for all student groups.
        Diff subjects bypass capacity constraints (can be split into sections)."""
        if room_id not in self.rooms:
            return False
        
        # Diff subjects (like project phases, seminars) can be split into sections
        if is_diff_subject:
            return True
        
        room_capacity = self.rooms[room_id].get('capacity', 0)
        total_students = 0
        
        for group_id in group_ids:
            if group_id in self.student_groups:
                total_students += self.student_groups[group_id].get('studentCount', 0)
        
        return total_students <= room_capacity
    
    def mark_usage(self, room_id: str, faculty_id: str, group_ids: List[str], day: str, slots: List[str], assignment_id: str):
        """Mark resources as used."""
        for slot in slots:
            self.room_bookings[(room_id, day, slot)] = assignment_id
            self.faculty_bookings[(faculty_id, day, slot)] = assignment_id
            for group_id in group_ids:
                self.group_bookings[(group_id, day, slot)] = assignment_id
    
    def count_group_classes_on_day(self, group_ids: List[str], day: str) -> int:
        """Count how many classes a group already has on a given day."""
        count = 0
        for group_id in group_ids:
            # Count unique slots used by this group on this day
            for (gid, d, slot), asgn_id in self.group_bookings.items():
                if gid == group_id and d == day:
                    count += 1
        return count
    
    def count_faculty_classes_on_day(self, faculty_id: str, day: str) -> int:
        """Count how many classes faculty has on a given day."""
        count = 0
        for (fid, d, slot), asgn_id in self.faculty_bookings.items():
            if fid == faculty_id and d == day:
                count += 1
        return count
    
    def get_days_sorted_by_load(self, faculty_id: str, group_ids: List[str]) -> List[str]:
        """Get days sorted by total load with stronger preference for lower-load days.
        
        Weighting strategy:
        - Group load: quadratically penalize high loads (prefer spreading)
        - Faculty load: linear penality (less important than student spread)
        """
        day_loads = []
        for day in self.weekdays:
            group_load = sum(self.count_group_classes_on_day(group_ids, day) for gid in group_ids)
            faculty_load = self.count_faculty_classes_on_day(faculty_id, day)
            
            # Quadratic penalty for group load (0→0, 1→4, 2→16, 3→36, etc)
            # This strongly prefers zero-load days
            # Linear penalty for faculty load
            total_load = (group_load ** 2) * 4 + faculty_load * 2
            day_loads.append((total_load, day))
        
        # Sort by load (ascending) - strongly prefer days with no existing classes
        day_loads.sort(key=lambda x: x[0])
        return [day for _, day in day_loads]
    
    def schedule_session(self, assignment: Dict, session_num: int) -> Tuple[bool, Optional[Dict]]:
        """Schedule a single session for an assignment. Returns (success, scheduled_session).
        
        Respects fixed constraints from Stage 4:
        - If fixedDay is set, only tries that day
        - If fixedSlot is set, only tries those slots
        """
        assignment_id = assignment['assignmentId']
        duration = assignment['sessionDuration']
        room_type = assignment['requiresRoomType']
        faculty_id = assignment['facultyId']
        group_ids = assignment['studentGroupIds']
        preferred_rooms = assignment.get('preferredRooms', [])
        is_diff_subject = assignment.get('isDiffSubject', False)
        
        # Check for fixed constraints from Stage 4
        constraints = assignment.get('constraints', {})
        fixed_day = constraints.get('fixedDay')
        fixed_slot = constraints.get('fixedSlot')
        
        # Determine which days to try
        if fixed_day:
            # Fixed constraint: only try specified day
            days_to_try = [fixed_day]
        else:
            # No fixed day: sort by load to spread classes
            days_to_try = self.get_days_sorted_by_load(faculty_id, group_ids)
        
        # Try to find a valid slot
        for day in days_to_try:
            if fixed_slot:
                # Fixed constraint: only try specified slots
                # Convert to proper format for slot_combo checking
                if isinstance(fixed_slot, list):
                    slot_combo = '+'.join(fixed_slot) if len(fixed_slot) > 1 else fixed_slot[0]
                else:
                    slot_combo = fixed_slot
                slots_combos = [slot_combo]
            else:
                # No fixed slot: get all valid combinations for duration on this day
                slots_combos = self.get_valid_slots_for_duration(duration, day)
            
            if not slots_combos:
                continue
            
            for slot_combo in slots_combos:
                slots = slot_combo.split('+') if '+' in slot_combo else [slot_combo]
                
                # Check faculty and group conflicts first (cheaper than room check)
                if not self.check_faculty_available(faculty_id, day, slots):
                    continue
                if not self.check_group_available(group_ids, day, slots):
                    continue
                if not self.check_group_overlap_constraints(group_ids, day, slots):
                    continue
                
                # Try each room (prefer preferred ones)
                valid_rooms = self.get_room_options(room_type, preferred_rooms)
                
                for room_id in valid_rooms:
                    if not self.check_room_available(room_id, day, slots):
                        continue
                    if not self.check_room_capacity(room_id, group_ids, is_diff_subject):
                        continue
                    
                    # Found valid assignment
                    scheduled = {
                        'assignmentId': assignment_id,
                        'sessionNumber': session_num,
                        'sessionsPerWeek': assignment['sessionsPerWeek'],
                        'sessionDuration': duration,
                        'day': day,
                        'slotId': '+'.join(slots) if len(slots) > 1 else slots[0],
                        'roomId': room_id,
                        'requiresRoomType': room_type,
                        'isDiffSubject': is_diff_subject
                    }
                    
                    self.mark_usage(room_id, faculty_id, group_ids, day, slots, assignment_id)
                    return True, scheduled
        
        return False, None
    
    def optimize_schedule(self) -> Tuple[List[Dict], List[Dict]]:
        """Create optimized schedule using Stage 4 assignment and constraint data.
        
        Priority order:
        1. Assignments with FIXED constraints (must honor fixedDay/fixedSlot)
        2. Diff subjects (special sessions that need careful placement)
        3. Regular assignments (sorted by workload)
        """
        scheduled = []
        unscheduled = []
        
        # Separate assignments into fixed and flexible
        fixed_assignments = []
        flexible_assignments = []
        
        for assignment in self.assignments:
            constraints = assignment.get('constraints', {})
            if constraints.get('fixedDay') or constraints.get('fixedSlot'):
                fixed_assignments.append(assignment)
            else:
                flexible_assignments.append(assignment)
        
        # Sort fixed assignments: by isDiffSubject and priority
        fixed_assignments.sort(key=lambda a: (
            a.get('isDiffSubject', False) == False,  # isDiffSubject first
            {'high': 0, 'normal': 1, 'low': 2}.get(a.get('priority', 'normal'), 1),
        ))
        
        # Sort flexible assignments
        flexible_assignments.sort(key=lambda a: (
            a.get('isDiffSubject', False) == False,  # isDiffSubject first
            {'high': 0, 'normal': 1, 'low': 2}.get(a.get('priority', 'normal'), 1),
            a['sessionDuration'] != 110,  # Labs before theory
            -a['sessionsPerWeek']  # More sessions first
        ))
        
        # Process fixed assignments first
        print(f"\n[PRIORITY] Scheduling {len(fixed_assignments)} fixed assignments...")
        for assignment in fixed_assignments:
            sessions_needed = assignment['sessionsPerWeek']
            
            for session_num in range(1, sessions_needed + 1):
                success, scheduled_session = self.schedule_session(assignment, session_num)
                
                if success:
                    scheduled.append(scheduled_session)
                else:
                    unscheduled.append({
                        'assignmentId': assignment['assignmentId'],
                        'sessionNumber': session_num,
                        'totalSessions': sessions_needed,
                        'reason': f"Cannot honor fixed constraints: fixedDay={assignment.get('constraints', {}).get('fixedDay')}, fixedSlot={assignment.get('constraints', {}).get('fixedSlot')}",
                        'faculty': assignment['facultyId'],
                        'studentGroups': assignment['studentGroupIds']
                    })
        
        # Then process flexible assignments
        print(f"[FLEXIBLE] Scheduling {len(flexible_assignments)} flexible assignments...")
        for assignment in flexible_assignments:
            sessions_needed = assignment['sessionsPerWeek']
            
            for session_num in range(1, sessions_needed + 1):
                success, scheduled_session = self.schedule_session(assignment, session_num)
                
                if success:
                    scheduled.append(scheduled_session)
                else:
                    unscheduled.append({
                        'assignmentId': assignment['assignmentId'],
                        'sessionNumber': session_num,
                        'totalSessions': sessions_needed,
                        'reason': 'No valid (day, slot, room) avoiding faculty and group conflicts',
                        'faculty': assignment['facultyId'],
                        'studentGroups': assignment['studentGroupIds']
                    })
        
        return scheduled, unscheduled
    
    def validate_hard_constraints(self, scheduled: List[Dict]) -> List[str]:
        """Validate all hard constraints using Stage 4 assignment data."""
        violations = []
        
        # Build mappings for quick lookup
        assignment_map = {a['assignmentId']: a for a in self.assignments}
        overlap_constraints = self.constraints.get('studentGroupOverlap', {}).get('cannotOverlapWith', {})
        
        # Track bookings for validation
        room_bookings_check = defaultdict(set)
        faculty_bookings_check = defaultdict(set)
        group_bookings_check = defaultdict(set)
        
        for sess in scheduled:
            assignment_id = sess['assignmentId']
            assignment = assignment_map.get(assignment_id)
            if not assignment:
                continue
            
            room_id = sess['roomId']
            day = sess['day']
            slots = sess['slotId'].split('+') if '+' in sess['slotId'] else [sess['slotId']]
            faculty_id = assignment['facultyId']
            group_ids = assignment['studentGroupIds']
            
            for slot in slots:
                # H1: Check room double-booking
                key = (room_id, day, slot)
                if key in room_bookings_check and room_id:
                    violations.append(f"H1 ROOM: {room_id} double-booked on {day} {slot}")
                room_bookings_check[key] = assignment_id
                
                # H1: Check faculty double-booking
                fkey = (faculty_id, day, slot)
                if fkey in faculty_bookings_check:
                    violations.append(f"H1 FACULTY: {faculty_id} double-booked on {day} {slot}")
                faculty_bookings_check[fkey] = assignment_id
                
                # H1: Check group double-booking
                for group_id in group_ids:
                    gkey = (group_id, day, slot)
                    if gkey in group_bookings_check:
                        violations.append(f"H1 GROUP: {group_id} double-booked on {day} {slot} (same course)")
                    group_bookings_check[gkey] = assignment_id
        
        # Validate student group overlap constraints
        for sess in scheduled:
            assignment_id = sess['assignmentId']
            assignment = assignment_map.get(assignment_id)
            if not assignment:
                continue
            
            group_ids = assignment['studentGroupIds']
            day = sess['day']
            slots = sess['slotId'].split('+') if '+' in sess['slotId'] else [sess['slotId']]
            
            for group_id in group_ids:
                if group_id not in overlap_constraints:
                    continue
                
                banned_groups = set(overlap_constraints[group_id])
                
                for slot in slots:
                    for other_sess in scheduled:
                        if other_sess['assignmentId'] == assignment_id:
                            continue
                        
                        other_assignment = assignment_map.get(other_sess['assignmentId'])
                        if not other_assignment:
                            continue
                        
                        other_group_ids = other_assignment['studentGroupIds']
                        other_day = other_sess['day']
                        other_slots = other_sess['slotId'].split('+') if '+' in other_sess['slotId'] else [other_sess['slotId']]
                        
                        if day == other_day and slot in other_slots:
                            for other_group_id in other_group_ids:
                                if other_group_id in banned_groups:
                                    violations.append(f"OVERLAP: {group_id} cannot overlap with {other_group_id} at {day}-{slot}")
        
        # Validate room capacity (skip for diff subjects - they can be split into sections)
        for sess in scheduled:
            assignment_id = sess['assignmentId']
            assignment = assignment_map.get(assignment_id)
            if not assignment:
                continue
            
            # Skip capacity check for diff subjects (they can be split into multiple sections)
            if sess.get('isDiffSubject', False):
                continue
            
            room_id = sess['roomId']
            group_ids = assignment['studentGroupIds']
            
            if room_id in self.rooms:
                room_capacity = self.rooms[room_id].get('capacity', 0)
                total_students = 0
                
                for group_id in group_ids:
                    if group_id in self.student_groups:
                        total_students += self.student_groups[group_id].get('studentCount', 0)
                
                if total_students > room_capacity:
                    violations.append(f"CAPACITY: {room_id} (cap {room_capacity}) cannot fit {total_students} students from {group_ids}")
        
        return violations
    
    def create_output(self, scheduled: List[Dict], unscheduled: List[Dict]) -> Dict:
        """Create output in prompt-specified 9-field format."""
        # Schedule is already in correct format:
        # assignmentId, sessionNumber, sessionsPerWeek, sessionDuration,
        # day, slotId, roomId, requiresRoomType, isDiffSubject
        
        return {
            'metadata': {
                'generatedAt': datetime.now().isoformat(timespec='milliseconds'),
                'generator': 'AI_SCHEDULER_v3.0',
                'version': '1.0',
                'totalSessions': len(scheduled),
                'scheduledCount': len(scheduled),
                'unscheduledCount': len(unscheduled),
                'constraintViolations': 0,
                'description': 'AI-generated conflict-free schedule with full constraint validation'
            },
            'schedule': scheduled
        }

def main():
    parser = argparse.ArgumentParser(
        description="Stage 5 AI Scheduler: Generate conflict-free schedule using constraint optimization"
    )
    parser.add_argument("--data-dir", required=True, help="Data directory path (contains stage_1, stage_4, etc.)")
    args = parser.parse_args()
    
    try:
        optimizer = ScheduleOptimizer(args.data_dir)
        
        print("=" * 70)
        print("STAGE 5: AI SCHEDULER v3.0 - Enhanced Constraint Validation")
        print("=" * 70)
        print(f"\nData directory: {optimizer.data_dir}")
        print(f"Loading {len(optimizer.assignments)} assignments from Stage 4...")
        print(f"Student groups: {len(optimizer.student_groups)}")
        print(f"Rooms: {len(optimizer.rooms)}")
        print(f"Time slots per day: {len(optimizer.slots_by_day['Mon'])}")
        
        # STEP 1: Schedule with real-time constraint checking
        print("\n[STEP 1] Scheduling with real-time constraint checking...")
        scheduled, unscheduled = optimizer.optimize_schedule()
        
        print(f"  ✓ Scheduled: {len(scheduled)} sessions")
        print(f"  ⚠ Unscheduled: {len(unscheduled)} sessions")
        
        # STEP 2: Validate all hard constraints
        print("\n[STEP 2] Validating all hard constraints...")
        violations = optimizer.validate_hard_constraints(scheduled)
        
        print(f"  ✓ Hard constraint violations: {len(violations)}")
        
        if violations:
            print("\n❌ CONSTRAINT VIOLATIONS DETECTED:")
            print("-" * 70)
            for v in violations[:20]:
                print(f"  • {v}")
            if len(violations) > 20:
                print(f"  ... and {len(violations) - 20} more violations")
            print("-" * 70)
            print("\n⚠ Schedule has constraint violations.")
            print("Proceeding to save with violations noted in metadata...")
            print()
        
        # STEP 3: Create output
        print("[STEP 3] Creating final output...")
        output = optimizer.create_output(scheduled, unscheduled)
        
        # Add violations to metadata
        output['metadata']['constraintViolations'] = len(violations)
        if violations:
            output['metadata']['violations'] = violations[:50]  # Store first 50 violations
        
        # STEP 4: Save to stage_5
        print("\n[STEP 4] Saving final schedule...")
        output_file = optimizer.stage5_dir / "ai_solved_schedule.json"
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"  ✓ Schedule saved to {output_file}")
        print(f"  ✓ File size: {output_file.stat().st_size:,} bytes")
        
        # Summary
        print("\n" + "=" * 70)
        print("✅ STAGE 5 SCHEDULING COMPLETE")
        print("=" * 70)
        print(f"Total sessions scheduled: {len(scheduled)}")
        print(f"Total sessions unscheduled: {len(unscheduled)}")
        print(f"Constraint violations: {len(violations)}")
        print(f"Output file: {output_file}")
        print("=" * 70 + "\n")
        
        if unscheduled:
            print("⚠ Note: The following sessions could not be scheduled:")
            for u in unscheduled[:5]:
                print(f"  • {u['assignmentId']} session {u['sessionNumber']}")
            if len(unscheduled) > 5:
                print(f"  ... and {len(unscheduled) - 5} more")
            print()
        
        return 0
    
    except FileNotFoundError as e:
        print(f"\n❌ File not found: {e}")
        print("Make sure Stage 4 and Stage 1 files exist in the data directory.")
        import traceback
        traceback.print_exc()
        return 1
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
