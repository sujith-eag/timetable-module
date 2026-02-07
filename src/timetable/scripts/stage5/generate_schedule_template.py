#!/usr/bin/env python3
"""
Stage 5: Generate Schedule Template
Creates a schedule with fixed assignments filled in and blanks for AI/manual scheduling.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class ScheduleTemplateGenerator:
    def __init__(self):
        self.stage4_dir = Path(__file__).parent.parent.parent / "stage_4"
        self.stage5_dir = Path(__file__).parent.parent.parent / "stage_5"
        self.stage5_dir.mkdir(exist_ok=True)
        
    def load_scheduling_input(self) -> Dict:
        """Load Stage 4 scheduling input"""
        input_file = self.stage4_dir / "schedulingInput.json"
        with open(input_file, 'r') as f:
            return json.load(f)
    
    def generate_template(self, data: Dict) -> List[Dict]:
        """Generate schedule template with fixed assignments filled"""
        print("📋 Generating schedule template...")
        print()
        
        schedule = []
        fixed_count = 0
        unfixed_count = 0
        
        for assignment in data['assignments']:
            assignment_id = assignment['assignmentId']
            sessions_needed = assignment['sessionsPerWeek']
            
            # Check if this assignment has fixed constraints
            constraints = assignment['constraints']
            fixed_day = constraints.get('fixedDay')
            fixed_slot = constraints.get('fixedSlot')
            must_be_in_room = constraints.get('mustBeInRoom')
            
            is_fixed = bool(fixed_day and fixed_slot and must_be_in_room)
            
            for session_num in range(1, sessions_needed + 1):
                entry = {
                    "assignmentId": assignment_id,
                    "sessionNumber": session_num,
                    "day": fixed_day if is_fixed else None,
                    "slotId": fixed_slot if is_fixed else None,
                    "roomId": must_be_in_room if must_be_in_room else None
                }
                
                schedule.append(entry)
                
                if is_fixed:
                    fixed_count += 1
                else:
                    unfixed_count += 1
        
        print(f"✓ Generated {len(schedule)} session slots")
        print(f"  • Fixed (pre-scheduled): {fixed_count}")
        print(f"  • Unfixed (to be scheduled): {unfixed_count}")
        print()
        
        return schedule
    
    def save_template(self, schedule: List[Dict], metadata: Dict):
        """Save schedule template"""
        output = {
            "metadata": {
                "generatedAt": datetime.now().isoformat(),
                "generator": "generate_schedule_template.py",
                "version": "1.0",
                "totalSessions": len(schedule),
                "fixedSessions": sum(1 for s in schedule if s['day'] and s['slotId']),
                "unfixedSessions": sum(1 for s in schedule if not s['day'] or not s['slotId']),
                "description": "Schedule template with fixed assignments filled, rest blank for AI/manual scheduling"
            },
            "schedule": schedule
        }
        
        output_file = self.stage5_dir / "scheduleTemplate.json"
        
        print("💾 Saving schedule template...")
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        file_size = output_file.stat().st_size
        print(f"   ✓ Saved to: {output_file}")
        print(f"   ✓ File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        print()
        
        return output_file
    
    def generate_example_filled(self, data: Dict) -> List[Dict]:
        """Generate an example with some assignments filled for testing"""
        print("📝 Generating example filled schedule...")
        print()
        
        schedule = []
        
        # Simple greedy assignment for demonstration
        # Days and slots cycle
        days = data['configuration']['weekdays']
        
        for assignment in data['assignments']:
            assignment_id = assignment['assignmentId']
            sessions_needed = assignment['sessionsPerWeek']
            valid_slot_types = assignment['validSlotTypes']
            must_be_in_room = assignment['constraints'].get('mustBeInRoom')
            preferred_rooms = assignment.get('preferredRooms', [])
            
            # Pick room
            if must_be_in_room:
                room = must_be_in_room
            elif preferred_rooms:
                room = preferred_rooms[0]
            else:
                # Pick appropriate room type
                room_type = assignment['requiresRoomType']
                rooms = [r for r in data['rooms'] if r['type'] == room_type]
                room = rooms[0]['roomId'] if rooms else None
            
            # Pick slots based on type
            if 'single' in valid_slot_types:
                available_slots = ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7']
            else:
                available_slots = ['S1+S2', 'S3+S4', 'S5+S6']
            
            for session_num in range(1, sessions_needed + 1):
                # Simple distribution: cycle through days and slots
                day_idx = (len(schedule) // len(available_slots)) % len(days)
                slot_idx = len(schedule) % len(available_slots)
                
                entry = {
                    "assignmentId": assignment_id,
                    "sessionNumber": session_num,
                    "day": days[day_idx],
                    "slotId": available_slots[slot_idx],
                    "roomId": room
                }
                
                schedule.append(entry)
        
        print(f"✓ Generated example schedule with {len(schedule)} sessions")
        print(f"  ⚠️  This is a NAIVE example, not a valid schedule!")
        print(f"  ⚠️  It WILL have conflicts - for demonstration only")
        print()
        
        return schedule
    
    def save_example(self, schedule: List[Dict]):
        """Save example schedule"""
        output = {
            "metadata": {
                "generatedAt": datetime.now().isoformat(),
                "generator": "generate_schedule_template.py",
                "version": "1.0",
                "totalSessions": len(schedule),
                "description": "Example naive schedule for testing enrichment - WILL HAVE CONFLICTS",
                "warning": "This is not a valid schedule, just for testing the enrichment pipeline"
            },
            "schedule": schedule
        }
        
        output_file = self.stage5_dir / "scheduleExample.json"
        
        print("💾 Saving example schedule...")
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        file_size = output_file.stat().st_size
        print(f"   ✓ Saved to: {output_file}")
        print(f"   ✓ File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        print()
        
        return output_file
    
    def generate_statistics(self, schedule: List[Dict]):
        """Generate statistics about the template"""
        print("=" * 70)
        print("SCHEDULE TEMPLATE STATISTICS")
        print("=" * 70)
        print()
        
        total = len(schedule)
        fixed = sum(1 for s in schedule if s['day'] and s['slotId'])
        unfixed = total - fixed
        
        # Count by room status
        with_room = sum(1 for s in schedule if s['roomId'])
        without_room = total - with_room
        
        print(f"📊 Total Sessions: {total}")
        print(f"   • Fixed (day + slot): {fixed} ({fixed/total*100:.1f}%)")
        print(f"   • Unfixed (need scheduling): {unfixed} ({unfixed/total*100:.1f}%)")
        print()
        
        print(f"🏢 Room Allocation:")
        print(f"   • With room specified: {with_room} ({with_room/total*100:.1f}%)")
        print(f"   • Without room: {without_room} ({without_room/total*100:.1f}%)")
        print()
        
        # Group by assignment
        assignments = {}
        for session in schedule:
            aid = session['assignmentId']
            if aid not in assignments:
                assignments[aid] = {'total': 0, 'fixed': 0}
            assignments[aid]['total'] += 1
            if session['day'] and session['slotId']:
                assignments[aid]['fixed'] += 1
        
        fully_fixed = sum(1 for a in assignments.values() if a['fixed'] == a['total'])
        partially_fixed = sum(1 for a in assignments.values() if 0 < a['fixed'] < a['total'])
        unfixed_assignments = sum(1 for a in assignments.values() if a['fixed'] == 0)
        
        print(f"📚 Assignments Status:")
        print(f"   • Fully scheduled: {fully_fixed}")
        print(f"   • Partially scheduled: {partially_fixed}")
        print(f"   • Not scheduled: {unfixed_assignments}")
        print()


def main():
    try:
        generator = ScheduleTemplateGenerator()
        
        print("=" * 70)
        print("STAGE 5: GENERATE SCHEDULE TEMPLATE")
        print("=" * 70)
        print()
        
        # Load data
        print("📂 Loading scheduling input...")
        data = generator.load_scheduling_input()
        print(f"   ✓ Loaded {len(data['assignments'])} assignments")
        print()
        
        # Generate template
        template = generator.generate_template(data)
        template_file = generator.save_template(template, data['metadata'])
        
        # Generate example
        example = generator.generate_example_filled(data)
        example_file = generator.save_example(example)
        
        # Statistics
        generator.generate_statistics(template)
        
        print("=" * 70)
        print("✅ STAGE 5 TEMPLATE GENERATION COMPLETE")
        print("=" * 70)
        print()
        
        print("📄 Generated Files:")
        print(f"   1. {template_file.name}")
        print(f"      → Template with fixed assignments filled")
        print(f"      → Use this as base for AI/manual scheduling")
        print()
        print(f"   2. {example_file.name}")
        print(f"      → Example filled schedule (NAIVE, for testing only)")
        print(f"      → Use this to test enrichment script")
        print()
        
        print("Next Steps:")
        print("   1. Fill in blank slots in scheduleTemplate.json")
        print("      (or let AI schedule them)")
        print("   2. Run enrichment script to generate full timetable:")
        print("      python3 enrich_schedule.py scheduleTemplate.json")
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
