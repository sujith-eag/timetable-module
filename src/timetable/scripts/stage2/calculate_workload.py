"""
Calculate Workload Module

This module calculates faculty workload statistics based on their assignments.
Takes faculty assignments and subject component data to compute hours per week.
"""

import json
from pathlib import Path
from typing import Dict, List, Any


class WorkloadCalculator:
    """Calculates faculty workload from assignments"""
    
    def __init__(self, subjects_full: List[Dict[str, Any]]):
        """
        Initialize the workload calculator
        
        Args:
            subjects_full: List of complete subject dicts with components
        """
        # Build subject lookup map
        self.subjects_map = {}
        for subject in subjects_full:
            if 'subjectCode' in subject:
                self.subjects_map[subject['subjectCode']] = subject
        
        # Build component lookup map
        self.components_map = {}
        for subject in subjects_full:
            if 'components' in subject:
                for comp in subject['components']:
                    comp_id = comp.get('componentId')
                    if comp_id:
                        self.components_map[comp_id] = comp
    
    def parse_assigned_subjects(
        self, 
        assigned_subjects: List[Any],
        student_groups_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Parse the assignedSubjects field into structured assignments
        
        Args:
            assigned_subjects: Raw assignedSubjects list from Stage 1
            student_groups_data: Student groups configuration (full dict with all groups)
            
        Returns:
            List of parsed assignment dicts
        """
        assignments = []
        
        for item in assigned_subjects:
            if isinstance(item, dict):
                # Format: {"24MCA31": ["A", "B"]}
                for subject_code, sections in item.items():
                    assignment = self._create_assignment(
                        subject_code, 
                        sections,
                        student_groups_data
                    )
                    if assignment:
                        assignments.append(assignment)
            elif isinstance(item, str):
                # Format: "24MCASS5" (no section specified)
                assignment = self._create_assignment(
                    item,
                    None,  # Will be determined from student groups
                    student_groups_data
                )
                if assignment:
                    assignments.append(assignment)
        
        return assignments
    
    def _create_assignment(
        self,
        subject_code: str,
        sections: List[str] = None,
        student_groups_data: Any = None
    ) -> Dict[str, Any]:
        """
        Create an assignment entry
        
        Args:
            subject_code: Subject code
            sections: List of section letters, or None
            student_groups_data: Student groups configuration (dict with all groups) or list of student groups
            
        Returns:
            Assignment dict or None if subject not found
        """
        subject = self.subjects_map.get(subject_code)
        if not subject:
            return None
        
        # Determine semester and sections
        semester = subject.get('semester')
        is_elective = subject.get('isElective', False)
        
        # Determine sections and student group IDs
        actual_sections = []
        student_group_ids = []
        
        if sections is None or len(sections) == 0:
            # For electives, fetch from electiveStudentGroups
            if is_elective and isinstance(student_groups_data, dict):
                elective_student_groups = student_groups_data.get('electiveStudentGroups', [])
                
                # Find which elective group this subject belongs to
                elective_subject_groups = student_groups_data.get('electiveSubjectGroups', [])
                parent_group = None
                
                for esg in elective_subject_groups:
                    if subject_code in esg.get('subjectCodes', []):
                        parent_group = esg.get('groupId')
                        break
                
                # Get student groups and sections for this elective
                if parent_group:
                    for esg in elective_student_groups:
                        if esg.get('parentGroupId') == parent_group:
                            student_group_ids.append(esg['studentGroupId'])
                            # Add sections from this elective student group
                            esg_sections = esg.get('sections', [])
                            for sec in esg_sections:
                                if sec not in actual_sections:
                                    actual_sections.append(sec)
        else:
            # Regular subjects with specified sections
            actual_sections = sections
            
            # Get regular student groups
            if isinstance(student_groups_data, dict):
                regular_groups = student_groups_data.get('studentGroups', [])
            elif isinstance(student_groups_data, list):
                regular_groups = student_groups_data
            else:
                regular_groups = []
            
            for section in sections:
                # Find matching student group
                for sg in regular_groups:
                    if sg.get('semester') == semester and sg.get('section') == section:
                        student_group_ids.append(sg['studentGroupId'])
        
        # Get component IDs and types
        components = subject.get('components', [])
        component_ids = [c.get('componentId') for c in components if c.get('componentId')]
        component_types = [c.get('componentType') for c in components if c.get('componentType')]
        
        # Calculate hours (now returns whole numbers)
        hours_per_section = self._calculate_hours_for_subject(subject_code)
        
        # For electives, count the number of student groups as "sections"
        effective_sections = len(student_group_ids) if is_elective else len(actual_sections)
        if effective_sections == 0:
            effective_sections = 1
        
        total_hours = hours_per_section * effective_sections
        
        # Calculate sessions
        sessions_per_section = sum(
            c.get('sessionsPerWeek', 0) 
            for c in components
        )
        total_sessions = sessions_per_section * effective_sections
        
        return {
            'subjectCode': subject_code,
            'semester': semester,
            'sections': actual_sections,
            'studentGroupIds': student_group_ids,
            'componentIds': component_ids,
            'componentTypes': component_types,
            'role': 'primary',
            'weeklyHoursPerSection': hours_per_section,
            'totalWeeklyHours': total_hours,
            'sessionsPerWeekPerSection': sessions_per_section,
            'totalSessionsPerWeek': total_sessions
        }
    
    def _calculate_hours_for_subject(self, subject_code: str) -> int:
        """
        Calculate total hours per week for one section of a subject
        
        Args:
            subject_code: Subject code
            
        Returns:
            Total hours per week (whole hours, rounded up from minutes)
        """
        subject = self.subjects_map.get(subject_code)
        if not subject:
            return 0
        
        components = subject.get('components', [])
        total_minutes = 0
        
        for comp in components:
            sessions = comp.get('sessionsPerWeek', 0)
            duration = comp.get('sessionDuration', 0)
            total_minutes += sessions * duration
        
        # Convert minutes to hours (round up to nearest hour)
        import math
        total_hours = math.ceil(total_minutes / 60.0)
        
        return total_hours
    
    def calculate_workload_stats(
        self,
        primary_assignments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate workload statistics from primary assignments
        
        Args:
            primary_assignments: List of primary assignment dicts
            
        Returns:
            Workload stats dict with whole hours
        """
        import math
        
        stats = {
            'theoryHours': 0,
            'tutorialHours': 0,
            'practicalHours': 0,
            'totalSessions': 0,
            'totalWeeklyHours': 0
        }
        
        for assignment in primary_assignments:
            subject_code = assignment['subjectCode']
            subject = self.subjects_map.get(subject_code)
            
            if not subject:
                continue
            
            # Determine the effective number of sections/groups
            # For electives, use student group count; for regular subjects, use sections
            num_sections = len(assignment.get('sections', []))
            num_student_groups = len(assignment.get('studentGroupIds', []))
            
            # Use whichever is greater (handles both regular and elective subjects)
            effective_multiplier = max(num_sections, num_student_groups)
            if effective_multiplier == 0:
                effective_multiplier = 1  # At least count once
            
            components = subject.get('components', [])
            
            for comp in components:
                comp_type = comp.get('componentType')
                sessions = comp.get('sessionsPerWeek', 0)
                duration = comp.get('sessionDuration', 0)
                
                # Calculate minutes and convert to whole hours (round up)
                total_minutes = sessions * duration * effective_multiplier
                hours = math.ceil(total_minutes / 60.0)
                
                if comp_type == 'theory':
                    stats['theoryHours'] += hours
                elif comp_type == 'tutorial':
                    stats['tutorialHours'] += hours
                elif comp_type == 'practical':
                    stats['practicalHours'] += hours
                
                stats['totalSessions'] += sessions * effective_multiplier
        
        stats['totalWeeklyHours'] = (
            stats['theoryHours'] + 
            stats['tutorialHours'] + 
            stats['practicalHours']
        )
        
        return stats


def main():
    """Test the workload calculator"""
    from data_loader import Stage1DataLoader
    
    print("Testing Workload Calculator")
    print("=" * 60)
    print()
    
    # Load data
    loader = Stage1DataLoader()
    faculty = loader.load_faculty_basic()
    student_groups_data = loader.load_student_groups()
    
    # Load subjects full
    script_dir = Path(__file__).parent
    subjects_full_path = script_dir.parent / "subjects2Full.json"
    
    with open(subjects_full_path, 'r', encoding='utf-8') as f:
        subjects_data = json.load(f)
    
    subjects_full = subjects_data.get('subjects', [])
    
    # Create calculator
    calculator = WorkloadCalculator(subjects_full)
    
    # Test with a few faculty
    test_faculty = [f for f in faculty if f['facultyId'] in ['RG', 'SA', 'MM']]
    
    for fac in test_faculty:
        print(f"Faculty: {fac['name']} ({fac['facultyId']})")
        print(f"Designation: {fac.get('designation', 'N/A')}")
        print()
        
        # Parse assignments
        assigned_subjects = fac.get('assignedSubjects', [])
        assignments = calculator.parse_assigned_subjects(
            assigned_subjects,
            student_groups_data
        )
        
        print(f"Primary Assignments: {len(assignments)}")
        for asn in assignments:
            print(f"  - {asn['subjectCode']} (Sem {asn.get('semester', 'N/A')})")
            print(f"    Sections: {asn['sections']}")
            print(f"    Components: {', '.join(asn['componentTypes'])}")
            print(f"    Hours: {asn['totalWeeklyHours']}h/week")
            print(f"    Sessions: {asn['totalSessionsPerWeek']}/week")
        print()
        
        # Calculate workload stats
        stats = calculator.calculate_workload_stats(assignments)
        
        print("Workload Stats:")
        print(f"  Theory: {stats['theoryHours']}h")
        print(f"  Tutorial: {stats['tutorialHours']}h")
        print(f"  Practical: {stats['practicalHours']}h")
        print(f"  Total Sessions: {stats['totalSessions']}")
        print(f"  Total Hours: {stats['totalWeeklyHours']}h/week")
        print()
        print("-" * 60)
        print()


if __name__ == "__main__":
    main()
