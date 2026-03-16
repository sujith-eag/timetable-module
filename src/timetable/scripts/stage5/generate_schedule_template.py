#!/usr/bin/env python3
"""
Stage 5: Generate Schedule Template (Phase 1 Enhanced)

Simple, clean template format for scheduling:
- Anchored sessions: Fully fixed assignments (diff subjects, etc.)
- Unfixed sessions: Blank slots with minimal room guidance

Minimal and lean - no bloat, just what's needed.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any


class ScheduleTemplateGenerator:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.stage4_dir = self.data_dir / "stage_4"
        self.stage5_dir = self.data_dir / "stage_5"
        self.stage5_dir.mkdir(exist_ok=True)
        
    def load_scheduling_input(self) -> Dict:
        """Load Stage 4 scheduling input"""
        input_file = self.stage4_dir / "schedulingInput.json"
        with open(input_file, 'r') as f:
            return json.load(f)
    
    def build_anchored_sessions(self, data: Dict) -> List[Dict]:
        """
        Extract fully anchored/fixed assignments.
        An assignment is anchored if it has: fixedDay AND fixedSlot
        These are typically diff subjects or special schedules that cannot be moved.
        
        NOTE: fixedSlot can be a list of contiguous slots for ONE session.
        Do NOT enumerate - all slots go into ONE entry.
        """
        print("📌 Building anchored sessions (fixed/immutable)...")
        anchored = []
        
        for assignment in data['assignments']:
            constraints = assignment['constraints']
            
            # Check if fixed in time: needs fixedDay AND fixedSlot
            fixed_day = constraints.get('fixedDay')
            fixed_slot = constraints.get('fixedSlot')
            
            if fixed_day and fixed_slot:
                # fixedSlot can be a string or list of slots (all for ONE session)
                slots = fixed_slot if isinstance(fixed_slot, list) else [fixed_slot]
                fixed_room = constraints.get('mustBeInRoom')  # Room constraint if any
                
                # Create ONE entry per session (sessionsPerWeek determines count)
                for session_num in range(1, assignment['sessionsPerWeek'] + 1):
                    anchored.append({
                        "assignmentId": assignment['assignmentId'],
                        "sessionNumber": session_num,
                        "sessionsPerWeek": assignment['sessionsPerWeek'],  # Scheduling scope
                        "sessionDuration": assignment['sessionDuration'],   # Minutes (for config lookup)
                        "dayFixed": fixed_day,
                        "slotsIdFixed": slots,  # All slots as array (can be 1 or more)
                        "roomIdFixed": fixed_room,  # Can be None
                        "requiresRoomType": assignment.get('requiresRoomType'),  # lecture/lab type
                        "isDiffSubject": assignment.get('isDiffSubject', False)
                    })
        
        print(f"   ✓ Found {len(anchored)} anchored sessions (with fixed day/slot)")
        return anchored
    
    def build_unfixed_sessions(self, data: Dict, anchored_ids: set) -> List[Dict]:
        """
        Build unfixed/blank sessions (those not anchored).
        These need scheduling and go to AI/manual scheduler.
        
        Include essential metadata fields that AI needs to make scheduling decisions.
        """
        print("📋 Building unfixed sessions (blank, to be scheduled)...")
        unfixed = []
        
        anchored_assignment_ids = anchored_ids
        
        for assignment in data['assignments']:
            # Skip if anchored
            if assignment['assignmentId'] in anchored_assignment_ids:
                continue
            
            # Create session entry for each session needed
            for session_num in range(1, assignment['sessionsPerWeek'] + 1):
                session_entry = {
                    "assignmentId": assignment['assignmentId'],
                    "sessionNumber": session_num,
                    "sessionsPerWeek": assignment['sessionsPerWeek'],          # Scheduling scope
                    "sessionDuration": assignment['sessionDuration'],          # Minutes (for config lookup)
                    "dayFixed": None,
                    "slotsIdFixed": None,
                    "roomIdFixed": None,
                    "requiresRoomType": assignment.get('requiresRoomType'),    # lecture/lab type
                    "isDiffSubject": assignment.get('isDiffSubject', False)
                }
                
                unfixed.append(session_entry)
        
        print(f"   ✓ Created {len(unfixed)} unfixed sessions")
        return unfixed
    
    def generate_template(self, data: Dict) -> Dict:
        """Generate clean, simple schedule template (Phase 1 Enhanced)"""
        print()
        print("=" * 70)
        print("GENERATING SCHEDULE TEMPLATE (Phase 1 Enhanced - Minimal)")
        print("=" * 70)
        print()
        
        # Find anchored sessions
        anchored_sessions = self.build_anchored_sessions(data)
        anchored_assignment_ids = {
            s['assignmentId'] for s in anchored_sessions
        }
        
        # Find unfixed sessions
        unfixed_sessions = self.build_unfixed_sessions(data, anchored_assignment_ids)
        
        print()
        print("Summary:")
        print(f"   • Anchored sessions (fixed): {len(anchored_sessions)}")
        print(f"   • Unfixed sessions (to schedule): {len(unfixed_sessions)}")
        print(f"   • Total sessions: {len(anchored_sessions) + len(unfixed_sessions)}")
        print()
        
        # Build output structure - simple and clean
        output = {
            "metadata": {
                "generatedAt": datetime.now().isoformat(),
                "generator": "generate_schedule_template.py",
                "version": "1.3",
                "description": "Schedule template - reference-based with room type guidance",
                "note": "AI receives: config.json (infrastructure) + this template. Stage 4 kept internal for Stage 6 enrichment.",
                "requiredFiles": ["config.json"],
                "activeSemesters": data['metadata'].get('activeSemesters', [1, 3]),
                "totalSessions": len(anchored_sessions) + len(unfixed_sessions),
                "fixedSessions": len(anchored_sessions),
                "unfixedSessions": len(unfixed_sessions)
            },
            "schedule": anchored_sessions + unfixed_sessions
        }
        
        return output
    
    def save_template(self, output: Dict) -> Path:
        """Save generated template"""
        output_file = self.stage5_dir / "scheduleTemplate.json"
        
        print("💾 Saving schedule template...")
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        file_size = output_file.stat().st_size
        print(f"   ✓ Saved to: {output_file}")
        print(f"   ✓ File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        print()
        
        return output_file

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate schedule template")
    parser.add_argument("--data-dir", required=True, help="Data directory path")
    args = parser.parse_args()
    
    try:
        generator = ScheduleTemplateGenerator(args.data_dir)
        
        print("=" * 70)
        print("STAGE 5: GENERATE SCHEDULE TEMPLATE (Phase 1 Enhanced)")
        print("=" * 70)
        print()
        
        # Load data
        print("📂 Loading scheduling input...")
        data = generator.load_scheduling_input()
        print(f"   ✓ Loaded {len(data['assignments'])} assignments")
        print(f"   ✓ Active semesters: {data['metadata'].get('activeSemesters', [1, 3])}")
        print()
        
        # Generate template
        output = generator.generate_template(data)
        template_file = generator.save_template(output)
        
        print("=" * 70)
        print("✅ STAGE 5 TEMPLATE GENERATION COMPLETE")
        print("=" * 70)
        print()
        
        print("📄 Generated File:")
        print(f"   {template_file.name}")
        print()
        
        print("Template Format (Phase 1 Enhanced):")
        print("   ✓ Anchored sessions: Fixed assignments (diff subjects, fixed times)")
        print("   ✓ Unfixed sessions: Blank slots with room type/preferences")
        print("   ✓ Minimal: No bloat, no enumeration matrices")
        print()
        
        print("File size:", template_file.stat().st_size / 1024, "KB")
        print()
        
        print("Next Steps:")
        print("   1. AI/Manual scheduler fills in blanks")
        print("   2. Output saved back to scheduleTemplate.json or as ai_solved_schedule.json")
        print("   3. Stage 6 enriches to create final timetable")
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())