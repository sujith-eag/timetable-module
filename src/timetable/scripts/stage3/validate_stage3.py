"""
Validate Stage 3 Teaching Assignments
======================================

This script validates the generated teaching assignments to ensure:
- All required fields are present
- Data types are correct
- Constraints are valid
- Relationships are consistent

Author: Stage 3 Implementation
Date: October 26, 2025
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Tuple

from timetable.core.semester_detector import detect_active_semesters


class Stage3Validator:
    """Validates Stage 3 teaching assignments."""
    
    def __init__(self, base_path: Path):
        """
        Initialize the validator.
        
        Args:
            base_path: Path to V4 directory
        """
        self.base_path = base_path
        self.errors = []
        self.warnings = []
    
    def validate_file(self, filename: str) -> bool:
        """
        Validate a teaching assignments file.
        
        Args:
            filename: Name of file to validate
            
        Returns:
            True if validation passed, False otherwise
        """
        file_path = self.base_path / "stage_3" / filename
        
        if not file_path.exists():
            self.errors.append(f"File not found: {filename}")
            return False
        
        # Load file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            self.errors.append(f"Invalid JSON in {filename}: {e}")
            return False
        
        # Validate structure
        if not self._validate_structure(data, filename):
            return False
        
        # Validate assignments
        assignments = data.get("assignments", [])
        for i, assignment in enumerate(assignments, 1):
            self._validate_assignment(assignment, i, filename)
        
        return len(self.errors) == 0
    
    def _validate_structure(self, data: Dict[str, Any], filename: str) -> bool:
        """Validate top-level structure."""
        required_keys = ["metadata", "assignments", "statistics"]
        
        for key in required_keys:
            if key not in data:
                self.errors.append(f"{filename}: Missing required key '{key}'")
                return False
        
        # Validate metadata
        metadata = data["metadata"]
        if "semester" not in metadata:
            self.errors.append(f"{filename}: Metadata missing 'semester'")
        if "totalAssignments" not in metadata:
            self.errors.append(f"{filename}: Metadata missing 'totalAssignments'")
        
        # Check assignment count matches
        if metadata.get("totalAssignments") != len(data.get("assignments", [])):
            self.warnings.append(
                f"{filename}: Metadata totalAssignments ({metadata.get('totalAssignments')}) "
                f"doesn't match actual count ({len(data.get('assignments', []))})"
            )
        
        return True
    
    def _validate_assignment(self, assignment: Dict[str, Any], index: int, filename: str):
        """Validate a single assignment."""
        prefix = f"{filename} - Assignment {index}"
        
        # Required fields
        required_fields = [
            "assignmentId", "subjectCode", "subjectTitle", "componentId",
            "componentType", "semester", "facultyId", "facultyName",
            "studentGroupIds", "sections", "sessionDuration", "sessionsPerWeek",
            "requiresRoomType", "preferredRooms", "requiresContiguous",
            "blockSizeSlots", "priority", "isElective", "isDiffSubject", "constraints"
        ]
        
        for field in required_fields:
            if field not in assignment:
                self.errors.append(f"{prefix}: Missing required field '{field}'")
        
        # Validate data types
        if "sessionDuration" in assignment and not isinstance(assignment["sessionDuration"], int):
            self.errors.append(f"{prefix}: sessionDuration must be an integer")
        
        if "sessionsPerWeek" in assignment and not isinstance(assignment["sessionsPerWeek"], int):
            self.errors.append(f"{prefix}: sessionsPerWeek must be an integer")
        
        if "studentGroupIds" in assignment and not isinstance(assignment["studentGroupIds"], list):
            self.errors.append(f"{prefix}: studentGroupIds must be a list")
        
        if "sections" in assignment and not isinstance(assignment["sections"], list):
            self.errors.append(f"{prefix}: sections must be a list")
        
        if "preferredRooms" in assignment and not isinstance(assignment["preferredRooms"], list):
            self.errors.append(f"{prefix}: preferredRooms must be a list")
        
        # Validate constraints
        if "constraints" in assignment:
            self._validate_constraints(assignment["constraints"], prefix)
        
        # Validate component type
        valid_components = ["theory", "practical", "tutorial"]
        if assignment.get("componentType") not in valid_components:
            self.errors.append(
                f"{prefix}: Invalid componentType '{assignment.get('componentType')}'"
            )
        
        # Validate priority
        valid_priorities = ["high", "medium", "low"]
        if assignment.get("priority") not in valid_priorities:
            self.errors.append(f"{prefix}: Invalid priority '{assignment.get('priority')}'")
        
        # Validate room type
        valid_room_types = ["lecture", "lab"]
        if assignment.get("requiresRoomType") not in valid_room_types:
            self.errors.append(
                f"{prefix}: Invalid requiresRoomType '{assignment.get('requiresRoomType')}'"
            )
        
        # Logical validations
        if assignment.get("sessionsPerWeek", 0) <= 0:
            self.errors.append(f"{prefix}: sessionsPerWeek must be > 0")
        
        if assignment.get("sessionDuration", 0) <= 0:
            self.errors.append(f"{prefix}: sessionDuration must be > 0")
        
        if not assignment.get("studentGroupIds"):
            self.errors.append(f"{prefix}: studentGroupIds cannot be empty")
        
        if not assignment.get("sections"):
            self.errors.append(f"{prefix}: sections cannot be empty")
    
    def _validate_constraints(self, constraints: Dict[str, Any], prefix: str):
        """Validate constraints object."""
        required_constraint_fields = [
            "studentGroupConflicts", "facultyConflicts",
            "fixedDay", "fixedSlot", "mustBeInRoom"
        ]
        
        for field in required_constraint_fields:
            if field not in constraints:
                self.errors.append(f"{prefix}: Constraints missing field '{field}'")
        
        # Validate types
        if "studentGroupConflicts" in constraints:
            if not isinstance(constraints["studentGroupConflicts"], list):
                self.errors.append(f"{prefix}: studentGroupConflicts must be a list")
        
        if "facultyConflicts" in constraints:
            if not isinstance(constraints["facultyConflicts"], list):
                self.errors.append(f"{prefix}: facultyConflicts must be a list")
            elif not constraints["facultyConflicts"]:
                self.warnings.append(f"{prefix}: facultyConflicts is empty")
    
    def print_report(self):
        """Print validation report."""
        print("\n" + "=" * 80)
        print("STAGE 3 VALIDATION REPORT")
        print("=" * 80)
        
        if self.errors:
            print(f"\n❌ ERRORS: {len(self.errors)}")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print(f"\n⚠ WARNINGS: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✓ All validations passed!")
        elif not self.errors:
            print("\n✓ Validation passed with warnings")
        else:
            print("\n✗ Validation failed")
        
        print("\n" + "=" * 80)


def get_active_semesters(base_path: Path) -> List[int]:
    """Get active semesters from DataLoader (single source of truth).
    
    Uses DataLoader to detect active semesters, which reads from
    studentGroups.json as the system of record.
    
    Args:
        base_path: Base data directory path
        
    Returns:
        List of active semester numbers found
    """
    try:
        from timetable.core.loader import DataLoader
        loader = DataLoader(base_path)
        # DataLoader auto-detects from studentGroups.json on init
        return list(loader.active_semesters)
    except Exception:
        # Fallback to file-based detection if DataLoader fails
        stage_3_path = base_path / "stage_3"
        if stage_3_path.exists():
            active_semesters = []
            for i in range(1, 5):  # Semesters 1-4
                if (stage_3_path / f"teachingAssignments_sem{i}.json").exists():
                    active_semesters.append(i)
            return sorted(active_semesters) if active_semesters else [1, 3]
        return [1, 3]  # Fallback default


def main(data_dir=None):
    """Main validation function."""
    import argparse
    
    if data_dir is None:
        parser = argparse.ArgumentParser(description="Validate Stage 3 teaching assignments")
        parser.add_argument("--data-dir", required=True, help="Data directory path")
        args = parser.parse_args()
        data_dir = args.data_dir
    
    print("=" * 80)
    print("STAGE 3: VALIDATE TEACHING ASSIGNMENTS")
    print("=" * 80)
    print(f"Data directory: {data_dir}")
    print()
    
    # Determine base path
    base_path = Path(data_dir)
    
    # Get active semesters dynamically
    active_semesters = get_active_semesters(base_path)
    print(f"Active semesters: {active_semesters}")
    print()
    
    validator = Stage3Validator(base_path)
    
    # Validate all active semester files
    results = {}
    for i, semester in enumerate(active_semesters, 1):
        filename = f"teachingAssignments_sem{semester}.json"
        print(f"{i}. Validating Semester {semester} assignments...")
        results[semester] = validator.validate_file(filename)
        print(f"   {'✓' if results[semester] else '✗'} Semester {semester} validation {'passed' if results[semester] else 'failed'}")
    
    # Print report
    validator.print_report()
    
    # Exit code
    if validator.errors:
        exit(1)
    else:
        exit(0)


if __name__ == "__main__":
    main()
