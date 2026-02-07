"""
Constraint Builder for Stage 3
===============================

This module builds constraint objects for each teaching assignment.
Constraints include:
- Student group conflicts (from global overlap matrix)
- Faculty conflicts (same faculty cannot be in two places)
- Fixed timing (for diff subjects with specific day/slot)
- Room allocation (pre-allocated rooms)

Author: Stage 3 Implementation
Date: October 26, 2025
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from data_loader_stage2 import DataLoaderStage2


class ConstraintBuilder:
    """Builds constraint objects for teaching assignments."""
    
    def __init__(self, loader: DataLoaderStage2, overlap_matrix_path: Path):
        """
        Initialize the constraint builder.
        
        Args:
            loader: DataLoaderStage2 instance with loaded data
            overlap_matrix_path: Path to studentGroupOverlapConstraints.json
        """
        self.loader = loader
        self.overlap_matrix = self._load_overlap_matrix(overlap_matrix_path)
    
    def _load_overlap_matrix(self, matrix_path: Path) -> Dict[str, Any]:
        """Load the student group overlap constraint matrix."""
        with open(matrix_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def build_constraints(self, assignment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build constraints for a single assignment.
        
        Args:
            assignment: Teaching assignment dictionary
            
        Returns:
            Constraints dictionary with:
            - studentGroupConflicts: List of conflicting student groups
            - facultyConflicts: List of conflicting faculty (just the assignment's own faculty)
            - fixedDay: Day if fixed timing (e.g., "Tue")
            - fixedSlot: Slot if fixed timing (e.g., "S6")
            - mustBeInRoom: Specific room if pre-allocated
        """
        constraints = {
            "studentGroupConflicts": self._get_student_group_conflicts(assignment),
            "facultyConflicts": [assignment["facultyId"]],
            "fixedDay": None,
            "fixedSlot": None,
            "mustBeInRoom": None
        }
        
        # Check for fixed timing (diff subjects)
        if assignment.get("isDiffSubject"):
            fixed_timing = self._get_fixed_timing(assignment)
            if fixed_timing:
                constraints["fixedDay"] = fixed_timing.get("day")
                constraints["fixedSlot"] = fixed_timing.get("slots")
        
        # Check for pre-allocated room
        must_be_in_room = self._get_pre_allocated_room(assignment)
        if must_be_in_room:
            constraints["mustBeInRoom"] = must_be_in_room
        
        return constraints
    
    def _get_student_group_conflicts(self, assignment: Dict[str, Any]) -> List[str]:
        """
        Get list of student groups that conflict with this assignment.
        
        Uses the global overlap matrix to find all groups that cannot
        overlap with any of the student groups in this assignment.
        
        Args:
            assignment: Teaching assignment
            
        Returns:
            List of conflicting student group IDs
        """
        student_group_ids = assignment.get("studentGroupIds", [])
        conflicts = set()
        
        cannot_overlap = self.overlap_matrix.get("cannotOverlapWith", {})
        
        for group_id in student_group_ids:
            if group_id in cannot_overlap:
                conflicts.update(cannot_overlap[group_id])
        
        return sorted(list(conflicts))
    
    def _get_fixed_timing(self, assignment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get fixed timing for diff subjects.
        
        Args:
            assignment: Teaching assignment
            
        Returns:
            Fixed timing dictionary or None
        """
        subject_code = assignment.get("subjectCode")
        subject = self.loader.get_subject_by_code(subject_code)
        
        if subject and "fixedTiming" in subject:
            return subject["fixedTiming"]
        
        return None
    
    def _get_pre_allocated_room(self, assignment: Dict[str, Any]) -> Optional[str]:
        """
        Get pre-allocated room if exists.
        
        Args:
            assignment: Teaching assignment
            
        Returns:
            Room ID if pre-allocated, None otherwise
        """
        subject_code = assignment.get("subjectCode")
        component_type = assignment.get("componentType")
        student_group_ids = assignment.get("studentGroupIds", [])
        
        # Check each student group for room allocation
        for student_group_id in student_group_ids:
            room_pref = self.loader.get_room_preferences_for_subject(
                subject_code, component_type, student_group_id
            )
            
            if room_pref and "roomAllocations" in room_pref:
                # Build component key
                component_id = assignment.get("componentId")
                section = assignment.get("sections", [])[0] if assignment.get("sections") else ""
                
                # Try different key formats
                allocations = room_pref["roomAllocations"]
                
                # Try component_id_section format (e.g., "24MCA32_PR_A")
                if component_id and section:
                    key = f"{component_id}_{section}"
                    if key in allocations:
                        return allocations[key]
                
                # Try direct component_id
                if component_id in allocations:
                    return allocations[component_id]
        
        return None
    
    def build_constraints_for_assignments(
        self, 
        assignments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Build constraints for multiple assignments.
        
        Args:
            assignments: List of teaching assignments
            
        Returns:
            List of assignments with constraints field populated
        """
        for assignment in assignments:
            assignment["constraints"] = self.build_constraints(assignment)
        
        return assignments


def main():
    """Test the constraint builder."""
    print("Testing Constraint Builder")
    print("=" * 80)
    
    # Load data
    print("\n1. Loading data...")
    loader = DataLoaderStage2()
    loader.load_all()
    print("   ✓ Data loaded")
    
    # Load overlap matrix
    matrix_path = loader.base_path / "stage_3" / "studentGroupOverlapConstraints.json"
    
    # Generate sample assignments
    print("\n2. Generating sample assignments...")
    from assignment_generator import AssignmentGenerator
    generator = AssignmentGenerator(loader)
    assignments = generator.generate_all_assignments(semester=3)
    print(f"   ✓ Generated {len(assignments)} assignments")
    
    # Build constraints
    print("\n3. Building constraints...")
    builder = ConstraintBuilder(loader, matrix_path)
    assignments_with_constraints = builder.build_constraints_for_assignments(assignments)
    print(f"   ✓ Built constraints for {len(assignments_with_constraints)} assignments")
    
    # Show sample constraints
    print("\n4. Sample Constraints:")
    print("-" * 80)
    
    for i, assignment in enumerate(assignments_with_constraints[:5], 1):
        print(f"\n   Assignment {i}: {assignment['assignmentId']}")
        print(f"      Subject: {assignment['subjectTitle']}")
        print(f"      Student Groups: {assignment['studentGroupIds']}")
        
        constraints = assignment['constraints']
        print(f"      Student Conflicts: {constraints['studentGroupConflicts']}")
        print(f"      Faculty Conflicts: {constraints['facultyConflicts']}")
        print(f"      Fixed Day: {constraints['fixedDay']}")
        print(f"      Fixed Slot: {constraints['fixedSlot']}")
        print(f"      Must Be In Room: {constraints['mustBeInRoom']}")
    
    # Statistics
    print("\n5. Constraint Statistics:")
    print("-" * 80)
    
    with_fixed_timing = sum(1 for a in assignments_with_constraints if a['constraints']['fixedDay'])
    with_room_allocation = sum(1 for a in assignments_with_constraints if a['constraints']['mustBeInRoom'])
    
    print(f"   Assignments with fixed timing: {with_fixed_timing}")
    print(f"   Assignments with pre-allocated rooms: {with_room_allocation}")
    print(f"   Total assignments: {len(assignments_with_constraints)}")
    
    # Check for assignment with room allocation
    print("\n6. Assignments with Pre-allocated Rooms:")
    print("-" * 80)
    for assignment in assignments_with_constraints:
        if assignment['constraints']['mustBeInRoom']:
            print(f"   {assignment['assignmentId']}: {assignment['subjectTitle']}")
            print(f"      Room: {assignment['constraints']['mustBeInRoom']}")
            print(f"      Student Groups: {assignment['studentGroupIds']}")
    
    print("\n" + "=" * 80)
    print("✓ Test complete!")


if __name__ == "__main__":
    main()
