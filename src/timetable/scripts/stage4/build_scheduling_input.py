#!/usr/bin/env python3
"""
Stage 4: Build Scheduling Input for AI
Generates a self-contained JSON file with all data needed for AI-based scheduling.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class SchedulingInputBuilder:
    def __init__(self):
        self.stage1_dir = Path(__file__).parent.parent.parent / "stage_1"
        self.stage3_dir = Path(__file__).parent.parent.parent / "stage_3"
        self.output_dir = Path(__file__).parent.parent
        
    def load_json(self, filepath: Path) -> Dict:
        """Load JSON file"""
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def load_stage1_data(self) -> Dict[str, Any]:
        """Load all Stage 1 configuration data"""
        print("📂 Loading Stage 1 configuration...")
        
        config = self.load_json(self.stage1_dir / "config.json")
        student_groups = self.load_json(self.stage1_dir / "studentGroups.json")
        
        print("   ✓ Loaded config.json")
        print("   ✓ Loaded studentGroups.json")
        
        return {
            "config": config["config"],
            "studentGroups": student_groups["studentGroups"]
        }
    
    def load_stage3_data(self) -> Dict[str, Any]:
        """Load Stage 3 teaching assignments"""
        print("📂 Loading Stage 3 teaching assignments...")
        
        sem1 = self.load_json(self.stage3_dir / "teachingAssignments_sem1.json")
        sem3 = self.load_json(self.stage3_dir / "teachingAssignments_sem3.json")
        overlap = self.load_json(self.stage3_dir / "studentGroupOverlapConstraints.json")
        
        print(f"   ✓ Loaded Semester 1: {len(sem1['assignments'])} assignments")
        print(f"   ✓ Loaded Semester 3: {len(sem3['assignments'])} assignments")
        print("   ✓ Loaded overlap constraints")
        
        return {
            "sem1_assignments": sem1["assignments"],
            "sem3_assignments": sem3["assignments"],
            "overlap_constraints": overlap
        }
    
    def build_time_slots(self, config: Dict) -> List[Dict]:
        """Build complete time slot information for all days"""
        print("🕐 Building time slot structure...")
        
        slots = []
        day_slot_pattern = config["daySlotPattern"]
        time_slots_info = {slot["slotId"]: slot for slot in config["timeSlots"]}
        
        for day, slot_ids in day_slot_pattern.items():
            for slot_id in slot_ids:
                slot_info = time_slots_info[slot_id]
                slots.append({
                    "day": day,
                    "slotId": slot_id,
                    "start": slot_info["start"],
                    "end": slot_info["end"],
                    "durationMinutes": slot_info["lengthMinutes"]
                })
        
        print(f"   ✓ Generated {len(slots)} total time slots")
        return slots
    
    def build_valid_slot_combinations(self, config: Dict) -> List[Dict]:
        """Build valid slot combinations for double-period sessions"""
        print("🔗 Building valid slot combinations...")
        
        combinations = []
        valid_combos = config["validSlotCombinations"]
        
        # Single slots
        for slot_id in valid_combos["single"]:
            combinations.append({
                "type": "single",
                "slots": [slot_id],
                "durationMinutes": 55
            })
        
        # Double slots (for tutorials/practicals)
        for combo in valid_combos["double"]:
            slot1, slot2 = combo.split("+")
            combinations.append({
                "type": "double",
                "slots": [slot1, slot2],
                "durationMinutes": 110,
                "requiresContiguous": True
            })
        
        print(f"   ✓ Generated {len(combinations)} slot combinations")
        return combinations
    
    def build_rooms(self, config: Dict) -> List[Dict]:
        """Build room information"""
        print("🏢 Building room information...")
        
        rooms = config["resources"]["rooms"]
        print(f"   ✓ Loaded {len(rooms)} rooms")
        return rooms
    
    def build_constraints(self, assignments: List[Dict], overlap: Dict) -> Dict:
        """Build global constraint information"""
        print("⚖️ Building constraint information...")
        
        # Extract all unique faculty
        faculty_ids = list(set(a["facultyId"] for a in assignments))
        
        # Extract all unique student groups
        student_group_ids = list(set(
            sg for a in assignments for sg in a["studentGroupIds"]
        ))
        
        constraints = {
            "studentGroupOverlap": overlap,
            "facultyList": sorted(faculty_ids),
            "studentGroupList": sorted(student_group_ids),
            "hardConstraints": {
                "noFacultyConflict": True,
                "noStudentGroupConflict": True,
                "respectRoomType": True,
                "respectSessionDuration": True,
                "respectContiguousRequirement": True
            },
            "softConstraints": {
                "preferPreAllocatedRooms": True,
                "minimizeGapsForFaculty": True,
                "minimizeGapsForStudents": True,
                "balanceLoadAcrossDays": True
            }
        }
        
        print(f"   ✓ {len(faculty_ids)} faculty members")
        print(f"   ✓ {len(student_group_ids)} student groups")
        return constraints
    
    def transform_assignments(self, assignments: List[Dict]) -> List[Dict]:
        """Transform assignments into AI-friendly format"""
        transformed = []
        
        for a in assignments:
            # Determine valid slot types based on duration
            if a["sessionDuration"] == 55:
                valid_slot_types = ["single"]
            else:
                valid_slot_types = ["double"]
            
            transformed.append({
                "assignmentId": a["assignmentId"],
                "subjectCode": a["subjectCode"],
                "shortCode": a.get("shortCode", a["subjectCode"]),
                "subjectTitle": a["subjectTitle"],
                "componentType": a["componentType"],
                "semester": a["semester"],
                "facultyId": a["facultyId"],
                "facultyName": a["facultyName"],
                "studentGroupIds": a["studentGroupIds"],
                "sections": a["sections"],
                "sessionDuration": a["sessionDuration"],
                "sessionsPerWeek": a["sessionsPerWeek"],
                "totalSessionsNeeded": a["sessionsPerWeek"],
                "requiresRoomType": a["requiresRoomType"],
                "preferredRooms": a.get("preferredRooms", []),
                "requiresContiguous": a["requiresContiguous"],
                "validSlotTypes": valid_slot_types,
                "priority": a["priority"],
                "isElective": a["isElective"],
                "constraints": a["constraints"]
            })
        
        return transformed
    
    def build(self) -> Dict:
        """Build complete scheduling input"""
        print("=" * 70)
        print("STAGE 4: BUILDING SCHEDULING INPUT FOR AI")
        print("=" * 70)
        print()
        
        # Load data
        stage1 = self.load_stage1_data()
        stage3 = self.load_stage3_data()
        
        print()
        
        # Combine all assignments
        all_assignments = (
            stage3["sem1_assignments"] + 
            stage3["sem3_assignments"]
        )
        
        # Build components
        time_slots = self.build_time_slots(stage1["config"])
        slot_combinations = self.build_valid_slot_combinations(stage1["config"])
        rooms = self.build_rooms(stage1["config"])
        constraints = self.build_constraints(all_assignments, stage3["overlap_constraints"])
        
        # Transform assignments
        print("🔄 Transforming assignments to AI format...")
        transformed_assignments = self.transform_assignments(all_assignments)
        print(f"   ✓ Transformed {len(transformed_assignments)} assignments")
        
        print()
        
        # Build final structure
        scheduling_input = {
            "metadata": {
                "generatedAt": datetime.now().isoformat(),
                "generator": "build_scheduling_input.py",
                "version": "1.0",
                "totalAssignments": len(transformed_assignments),
                "semester1Assignments": len(stage3["sem1_assignments"]),
                "semester3Assignments": len(stage3["sem3_assignments"]),
                "totalTimeSlots": len(time_slots),
                "totalRooms": len(rooms),
                "description": "Self-contained scheduling input for AI-based timetable generation"
            },
            "configuration": {
                "weekdays": stage1["config"]["weekdays"],
                "dayStart": stage1["config"]["dayStart"],
                "dayEnd": stage1["config"]["dayEnd"],
                "breakWindows": stage1["config"]["breakWindows"],
                "sessionTypes": stage1["config"]["sessionTypes"],
                "resourceConstraints": stage1["config"]["resourceConstraints"]
            },
            "timeSlots": time_slots,
            "slotCombinations": slot_combinations,
            "rooms": rooms,
            "studentGroups": stage1["studentGroups"],
            "constraints": constraints,
            "assignments": transformed_assignments
        }
        
        return scheduling_input
    
    def save(self, data: Dict):
        """Save scheduling input to file"""
        output_file = self.output_dir / "schedulingInput.json"
        
        print("💾 Saving scheduling input...")
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        file_size = output_file.stat().st_size
        print(f"   ✓ Saved to: {output_file}")
        print(f"   ✓ File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        
        return output_file
    
    def generate_summary(self, data: Dict):
        """Generate summary statistics"""
        print()
        print("=" * 70)
        print("SCHEDULING INPUT SUMMARY")
        print("=" * 70)
        print()
        
        print(f"📊 Assignments: {data['metadata']['totalAssignments']}")
        print(f"   • Semester 1: {data['metadata']['semester1Assignments']}")
        print(f"   • Semester 3: {data['metadata']['semester3Assignments']}")
        print()
        
        print(f"🕐 Time Slots: {data['metadata']['totalTimeSlots']}")
        days = set(ts["day"] for ts in data["timeSlots"])
        for day in data["configuration"]["weekdays"]:
            day_slots = [ts for ts in data["timeSlots"] if ts["day"] == day]
            print(f"   • {day}: {len(day_slots)} slots")
        print()
        
        print(f"🏢 Rooms: {data['metadata']['totalRooms']}")
        room_types = {}
        for room in data["rooms"]:
            room_type = room["type"]
            room_types[room_type] = room_types.get(room_type, 0) + 1
        for room_type, count in sorted(room_types.items()):
            print(f"   • {room_type.capitalize()}: {count}")
        print()
        
        print(f"👥 Faculty: {len(data['constraints']['facultyList'])}")
        print(f"🎓 Student Groups: {len(data['constraints']['studentGroupList'])}")
        print()
        
        print("📝 Assignment Breakdown:")
        by_component = {}
        by_priority = {}
        by_duration = {}
        for a in data["assignments"]:
            comp = a["componentType"]
            by_component[comp] = by_component.get(comp, 0) + 1
            
            prio = a["priority"]
            by_priority[prio] = by_priority.get(prio, 0) + 1
            
            dur = a["sessionDuration"]
            by_duration[dur] = by_duration.get(dur, 0) + a["sessionsPerWeek"]
        
        print("   By Component Type:")
        for comp, count in sorted(by_component.items()):
            print(f"      • {comp.capitalize()}: {count} assignments")
        
        print("   By Priority:")
        for prio, count in sorted(by_priority.items()):
            print(f"      • {prio.capitalize()}: {count} assignments")
        
        print("   By Session Duration:")
        for dur, count in sorted(by_duration.items()):
            print(f"      • {dur} min sessions: {count} sessions/week")
        print()
        
        total_sessions = sum(a["sessionsPerWeek"] for a in data["assignments"])
        print(f"📅 Total Sessions to Schedule: {total_sessions} per week")
        print()
        
        print("=" * 70)
        print("✅ STAGE 4 BUILD COMPLETE!")
        print("=" * 70)


def main():
    try:
        builder = SchedulingInputBuilder()
        data = builder.build()
        output_file = builder.save(data)
        builder.generate_summary(data)
        
        print()
        print(f"🎉 Scheduling input ready for AI at:")
        print(f"   {output_file}")
        print()
        print("Next steps:")
        print("   1. Review the generated schedulingInput.json")
        print("   2. Use this file as input to your AI scheduling algorithm")
        print("   3. AI should output minimal Stage 5 format:")
        print("      [assignmentId, day, slotId, roomId]")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
