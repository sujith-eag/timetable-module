#!/usr/bin/env python3
"""
Build Assignments for Semester 2
=================================

This script orchestrates the complete generation of teaching assignments
for Semester 2 by coordinating all Phase 2 modules:
- Assignment generation
- Constraint building
- Room preference extraction

Output: teachingAssignments_sem2.json

Author: Stage 3 Implementation
Date: March 15, 2026
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from timetable.scripts.stage3.data_loader_stage2 import DataLoaderStage2
from timetable.scripts.stage3.assignment_generator import AssignmentGenerator
from timetable.scripts.stage3.constraint_builder import ConstraintBuilder
from timetable.scripts.stage3.room_preference_extractor import RoomPreferenceExtractor


class AssignmentBuilder:
    """Orchestrates the building of teaching assignments."""
    
    def __init__(self, semester: int, data_dir: Optional[str] = None):
        """
        Initialize the assignment builder.
        
        Args:
            semester: Semester number (2)
            data_dir: Path to data directory. If None, uses current directory detection.
        """
        self.semester = semester
        self.loader = DataLoaderStage2(data_dir)
        self.base_path = self.loader.base_path / "stage_3"
        
    def build(self) -> Dict[str, Any]:
        """
        Build complete teaching assignments for the semester.
        
        Returns:
            Dictionary containing:
            - metadata: Build information
            - assignments: List of teaching assignments
            - statistics: Summary statistics
        """
        print(f"\nBuilding Teaching Assignments for Semester {self.semester}")
        print("=" * 80)
        
        # Step 1: Load data
        print("\n1. Loading data...")
        self.loader.load_all()
        print("   ✓ Data loaded")
        
        # Step 2: Generate assignments
        print("\n2. Generating assignments...")
        generator = AssignmentGenerator(self.loader, semester=self.semester)
        assignments = generator.generate_all_assignments(semester=self.semester)
        print(f"   ✓ Generated {len(assignments)} assignments")
        
        # Step 3: Build constraints
        print("\n3. Building constraints...")
        overlap_matrix_path = self.base_path / "studentGroupOverlapConstraints.json"
        constraint_builder = ConstraintBuilder(self.loader, overlap_matrix_path)
        assignments = constraint_builder.build_constraints_for_assignments(assignments)
        print(f"   ✓ Built constraints for {len(assignments)} assignments")
        
        # Step 4: Extract room preferences
        print("\n4. Extracting room preferences...")
        room_extractor = RoomPreferenceExtractor(self.loader)
        assignments = room_extractor.populate_room_preferences(assignments)
        print(f"   ✓ Extracted room preferences for {len(assignments)} assignments")
        
        # Step 5: Calculate statistics
        print("\n5. Calculating statistics...")
        statistics = self._calculate_statistics(assignments)
        print("   ✓ Statistics calculated")
        
        # Build output structure
        output = {
            "metadata": {
                "semester": self.semester,
                "generatedAt": datetime.now().isoformat(),
                "totalAssignments": len(assignments),
                "generator": "build_assignments_sem2.py"
            },
            "assignments": assignments,
            "statistics": statistics
        }
        
        return output
    
    def _calculate_statistics(self, assignments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for assignments."""
        stats = {
            "totalAssignments": len(assignments),
            "byAssignmentType": {
                "primary": 0,
                "supporting": 0
            },
            "byType": {
                "core": 0,
                "elective": 0,
                "diff": 0
            },
            "byComponentType": {
                "theory": 0,
                "practical": 0,
                "tutorial": 0
            },
            "byPriority": {
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "totalSessions": 0,
            "totalWeeklyHours": 0,
            "facultyAssignments": {},
            "roomRequirements": {
                "lecture": 0,
                "lab": 0
            },
            "withFixedTiming": 0,
            "withPreAllocatedRooms": 0,
            "withRoomPreferences": 0
        }
        
        for assignment in assignments:
            # Count by assignment type (primary vs supporting)
            assignment_type = assignment.get("assignmentType", "primary")
            if assignment_type in stats["byAssignmentType"]:
                stats["byAssignmentType"][assignment_type] += 1
            
            # Count by type
            if assignment.get("isDiffSubject"):
                stats["byType"]["diff"] += 1
            elif assignment.get("isElective"):
                stats["byType"]["elective"] += 1
            else:
                stats["byType"]["core"] += 1
            
            # Count by component type
            comp_type = assignment.get("componentType", "theory")
            stats["byComponentType"][comp_type] = stats["byComponentType"].get(comp_type, 0) + 1
            
            # Count by priority
            priority = assignment.get("priority", "medium")
            stats["byPriority"][priority] = stats["byPriority"].get(priority, 0) + 1
            
            # Total sessions and hours
            sessions = assignment.get("sessionsPerWeek", 0)
            duration = assignment.get("sessionDuration", 0)
            stats["totalSessions"] += sessions
            stats["totalWeeklyHours"] += (sessions * duration) / 60.0
            
            # Faculty assignments
            faculty_id = assignment.get("facultyId")
            if faculty_id:
                stats["facultyAssignments"][faculty_id] = stats["facultyAssignments"].get(faculty_id, 0) + 1
            
            # Room requirements
            room_type = assignment.get("requiresRoomType")
            if room_type in stats["roomRequirements"]:
                stats["roomRequirements"][room_type] += 1
            
            # Fixed timing
            if assignment.get("constraints", {}).get("fixedDay"):
                stats["withFixedTiming"] += 1
            
            # Pre-allocated rooms
            if assignment.get("constraints", {}).get("mustBeInRoom"):
                stats["withPreAllocatedRooms"] += 1
            
            # Room preferences
            if assignment.get("preferredRooms"):
                stats["withRoomPreferences"] += 1
        
        # Round hours
        stats["totalWeeklyHours"] = round(stats["totalWeeklyHours"], 1)
        
        return stats
    
    def save(self, output: Dict[str, Any], filename: str) -> Path:
        """
        Save assignments to JSON file.
        
        Args:
            output: Output dictionary
            filename: Output filename
            
        Returns:
            Path to saved file
        """
        output_path = self.base_path / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2)
        
        return output_path
    
    def print_summary(self, statistics: Dict[str, Any]):
        """Print summary of generated assignments."""
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total assignments: {statistics['totalAssignments']}")
        print(f"  - Core: {statistics['byType']['core']}")
        print(f"  - Elective: {statistics['byType']['elective']}")
        print(f"  - Diff: {statistics['byType']['diff']}")
        print(f"\nComponent Types:")
        print(f"  - Theory: {statistics['byComponentType']['theory']}")
        print(f"  - Practical: {statistics['byComponentType'].get('practical', 0)}")
        print(f"  - Tutorial: {statistics['byComponentType'].get('tutorial', 0)}")
        print(f"\nPriority Distribution:")
        print(f"  - High: {statistics['byPriority']['high']}")
        print(f"  - Medium: {statistics['byPriority']['medium']}")
        print(f"  - Low: {statistics['byPriority']['low']}")
        print(f"\nTotal Weekly Hours: {statistics['totalWeeklyHours']}")
        print(f"Total Sessions: {statistics['totalSessions']}")
        print("=" * 80)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Build teaching assignments for Semester 2")
    parser.add_argument(
        "--data-dir",
        type=str,
        default=None,
        help="Path to data directory (e.g., src/timetable/stages). If not provided, uses default detection."
    )
    args = parser.parse_args()
    
    print("=" * 80)
    print("🚀 Stage 3 - Building Teaching Assignments for Semester 2")
    print("=" * 80)
    
    try:
        builder = AssignmentBuilder(semester=2, data_dir=args.data_dir)
        output = builder.build()
        
        # Save to file
        output_path = builder.save(output, "teachingAssignments_sem2.json")
        print(f"\n✅ Assignments saved to: {output_path}")
        
        # Print summary
        builder.print_summary(output["statistics"])
        
        # Also print faculty assignments
        print("\nFaculty Assignments:")
        for faculty_id, count in sorted(output["statistics"]["facultyAssignments"].items()):
            print(f"  - {faculty_id}: {count} assignments")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
