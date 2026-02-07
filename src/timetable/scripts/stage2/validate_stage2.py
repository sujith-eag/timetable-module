"""
Validate Stage 2 Data

This script validates the generated Stage 2 data files for consistency and correctness.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple


class Stage2Validator:
    """Validates Stage 2 generated data"""
    
    def __init__(self, stage2_dir: str = None):
        """
        Initialize validator
        
        Args:
            stage2_dir: Path to stage_2 directory
        """
        if stage2_dir is None:
            script_dir = Path(__file__).parent
            self.stage2_dir = script_dir.parent
        else:
            self.stage2_dir = Path(stage2_dir)
        
        self.errors = []
        self.warnings = []
    
    def load_data(self) -> Tuple[List[Dict], List[Dict]]:
        """
        Load Stage 2 data files
        
        Returns:
            Tuple of (subjects, faculty)
        """
        subjects_path = self.stage2_dir / "subjects2Full.json"
        faculty_path = self.stage2_dir / "faculty2Full.json"
        
        if not subjects_path.exists():
            raise FileNotFoundError(f"subjects2Full.json not found at {subjects_path}")
        
        if not faculty_path.exists():
            raise FileNotFoundError(f"faculty2Full.json not found at {faculty_path}")
        
        with open(subjects_path, 'r', encoding='utf-8') as f:
            subjects_data = json.load(f)
        
        with open(faculty_path, 'r', encoding='utf-8') as f:
            faculty_data = json.load(f)
        
        return subjects_data.get('subjects', []), faculty_data.get('faculty', [])
    
    def validate_subjects(self, subjects: List[Dict[str, Any]]) -> bool:
        """
        Validate subjects data
        
        Args:
            subjects: List of subject dicts
            
        Returns:
            True if valid, False otherwise
        """
        print("Validating subjects...")
        valid = True
        
        subject_codes = set()
        
        for subject in subjects:
            # Skip subjects without subjectCode
            if 'subjectCode' not in subject:
                continue
            
            code = subject['subjectCode']
            
            # Check for duplicate codes
            if code in subject_codes:
                self.errors.append(f"Duplicate subject code: {code}")
                valid = False
            subject_codes.add(code)
            
            # Check required fields
            required = ['title', 'creditPattern', 'totalCredits', 'semester', 'type']
            for field in required:
                if field not in subject:
                    self.errors.append(f"Subject {code} missing field: {field}")
                    valid = False
            
            # Validate components
            components = subject.get('components', [])
            if not components:
                self.warnings.append(f"Subject {code} has no components")
            
            for comp in components:
                # Check required component fields
                comp_required = [
                    'componentId', 'componentType', 'credits',
                    'sessionDuration', 'sessionsPerWeek', 'totalWeeklyMinutes',
                    'mustBeInRoomType', 'blockSizeSlots', 'mustBeContiguous'
                ]
                
                for field in comp_required:
                    if field not in comp:
                        self.errors.append(
                            f"Component {comp.get('componentId', 'UNKNOWN')} "
                            f"missing field: {field}"
                        )
                        valid = False
                
                # Validate totalWeeklyMinutes calculation
                if 'sessionsPerWeek' in comp and 'sessionDuration' in comp:
                    expected = comp['sessionsPerWeek'] * comp['sessionDuration']
                    actual = comp.get('totalWeeklyMinutes')
                    if expected != actual:
                        self.errors.append(
                            f"Component {comp.get('componentId')}: "
                            f"totalWeeklyMinutes mismatch (expected {expected}, got {actual})"
                        )
                        valid = False
        
        return valid
    
    def validate_faculty(self, faculty: List[Dict[str, Any]], subjects: List[Dict[str, Any]]) -> bool:
        """
        Validate faculty data
        
        Args:
            faculty: List of faculty dicts
            subjects: List of subject dicts (for reference checking)
            
        Returns:
            True if valid, False otherwise
        """
        print("Validating faculty...")
        valid = True
        
        # Build subject code set for validation
        subject_codes = {s['subjectCode'] for s in subjects if 'subjectCode' in s}
        
        faculty_ids = set()
        
        for fac in faculty:
            fac_id = fac.get('facultyId')
            
            # Check for duplicate IDs
            if fac_id in faculty_ids:
                self.errors.append(f"Duplicate faculty ID: {fac_id}")
                valid = False
            faculty_ids.add(fac_id)
            
            # Check required fields
            required = ['name', 'designation', 'primaryAssignments', 'workloadStats']
            for field in required:
                if field not in fac:
                    self.errors.append(f"Faculty {fac_id} missing field: {field}")
                    valid = False
            
            # Validate primary assignments
            primary = fac.get('primaryAssignments', [])
            for asn in primary:
                subject_code = asn.get('subjectCode')
                
                # Check if subject exists
                if subject_code not in subject_codes:
                    self.errors.append(
                        f"Faculty {fac_id} assigned to non-existent subject: {subject_code}"
                    )
                    valid = False
            
            # Validate workload stats
            stats = fac.get('workloadStats', {})
            required_stats = ['theoryHours', 'tutorialHours', 'practicalHours', 
                            'totalSessions', 'totalWeeklyHours']
            
            for field in required_stats:
                if field not in stats:
                    self.errors.append(f"Faculty {fac_id} workloadStats missing: {field}")
                    valid = False
            
            # Check workload sum
            if all(field in stats for field in required_stats):
                calculated_total = (
                    stats['theoryHours'] + 
                    stats['tutorialHours'] + 
                    stats['practicalHours']
                )
                actual_total = stats['totalWeeklyHours']
                
                # Allow small floating point differences
                if abs(calculated_total - actual_total) > 0.1:
                    self.errors.append(
                        f"Faculty {fac_id}: workload sum mismatch "
                        f"(calculated {calculated_total}, reported {actual_total})"
                    )
                    valid = False
        
        return valid
    
    def validate(self) -> bool:
        """
        Run all validations
        
        Returns:
            True if all validations pass, False otherwise
        """
        try:
            subjects, faculty = self.load_data()
            
            subjects_valid = self.validate_subjects(subjects)
            faculty_valid = self.validate_faculty(faculty, subjects)
            
            return subjects_valid and faculty_valid
            
        except Exception as e:
            self.errors.append(f"Validation error: {e}")
            return False
    
    def print_report(self):
        """Print validation report"""
        print()
        print("=" * 60)
        print("STAGE 2 VALIDATION REPORT")
        print("=" * 60)
        print()
        
        if self.errors:
            print(f"✗ Errors: {len(self.errors)}")
            for error in self.errors:
                print(f"  - {error}")
            print()
        
        if self.warnings:
            print(f"⚠ Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"  - {warning}")
            print()
        
        if not self.errors and not self.warnings:
            print("✓ All validations passed!")
            print()
        
        print("=" * 60)


def main():
    """Main execution"""
    print("Validating Stage 2 data...")
    print()
    
    validator = Stage2Validator()
    
    try:
        is_valid = validator.validate()
        validator.print_report()
        
        return 0 if is_valid else 1
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
