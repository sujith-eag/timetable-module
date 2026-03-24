"""
Calculate Workload Module

This module calculates faculty workload statistics based on their assignments.
Takes faculty assignments and subject component data to compute hours per week.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any

# Setup logging
logger = logging.getLogger(__name__)


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
        
        logger.debug(f"WorkloadCalculator initialized with {len(self.subjects_map)} subjects")
        
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
    
    def parse_supported_subjects(
        self,
        supported_subjects: List[Any],
        student_groups_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Parse the supportingSubjects field into structured assignments with ONLY practical components.
        
        Supporting staff assignments should include ONLY practical/lab components, not theory or tutorial.
        This method ensures supporting assignments are correctly filtered.
        
        Args:
            supported_subjects: Raw supportingSubjects list from Stage 1
            student_groups_data: Student groups configuration (full dict with all groups)
            
        Returns:
            List of parsed assignment dicts (supporting only) with practical components only
        """
        assignments = []
        
        for item in supported_subjects:
            if isinstance(item, dict):
                # Format: {"24MCA31": ["A", "B"]}
                for subject_code, sections in item.items():
                    assignment = self._create_assignment(
                        subject_code,
                        sections,
                        student_groups_data,
                        is_supporting=True  # Flag to filter components
                    )
                    if assignment:
                        assignments.append(assignment)
            elif isinstance(item, str):
                # Format: "24MCASS5" (no section specified)
                assignment = self._create_assignment(
                    item,
                    None,  # Will be determined from student groups
                    student_groups_data,
                    is_supporting=True  # Flag to filter components
                )
                if assignment:
                    assignments.append(assignment)
        
        return assignments
    
    def _create_assignment(
        self,
        subject_code: str,
        sections: List[str] = None,
        student_groups_data: Any = None,
        is_supporting: bool = False
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
            logger.warning(f"Subject not found in subjects_map: '{subject_code}'. Skipping assignment.")
            return None
        
        logger.debug(f"Creating assignment for subject: {subject_code}")
        
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
                
                if not parent_group:
                    logger.warning(f"Elective subject {subject_code} not found in elective subject groups. Skipping.")
                    return None
                
                # Get student groups and sections for this elective
                found_groups = False
                for esg in elective_student_groups:
                    if esg.get('parentGroupId') == parent_group:
                        found_groups = True
                        student_group_ids.append(esg['studentGroupId'])
                        # Add sections from this elective student group
                        esg_sections = esg.get('sections', [])
                        for sec in esg_sections:
                            if sec not in actual_sections:
                                actual_sections.append(sec)
                
                if not found_groups:
                    logger.warning(f"No elective student groups found for parent group {parent_group} (subject: {subject_code}). Skipping.")
                    return None
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
                found = False
                for sg in regular_groups:
                    if sg.get('semester') == semester:
                        # Handle special case: 'ALL' sections map to 'Combined' (Sem 4)
                        section_match = sg.get('section') == section
                        if section == 'ALL' and sg.get('section') == 'Combined':
                            section_match = True
                        
                        if section_match:
                            student_group_ids.append(sg['studentGroupId'])
                            found = True
                            break
                
                if not found:
                    logger.warning(f"No student group found for semester {semester}, section {section} (subject: {subject_code})")
        
        # Get component IDs and types
        # NOTE: For supporting assignments, filter to ONLY practical components
        components = subject.get('components', [])
        
        if is_supporting:
            # Supporting staff ONLY handle practical/lab components
            components = [c for c in components if c.get('componentType', '').lower() == 'practical']
            if not components:
                logger.warning(f"No practical components found for supporting subject {subject_code}. Skipping.")
                return None
        
        component_ids = [c.get('componentId') for c in components if c.get('componentId')]
        component_types = [c.get('componentType') for c in components if c.get('componentType')]
        
        if not component_ids:
            logger.warning(f"No components found for subject {subject_code}. Skipping.")
            return None
        
        # Calculate hours (now returns whole numbers)
        # If supporting, calculate hours for practical components only
        hours_per_section = self._calculate_hours_for_subject(subject_code, is_supporting=is_supporting)
        
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
        
        logger.debug(f"Assignment created: {subject_code} - {total_hours}h/week, {total_sessions} sessions/week")
        
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
    
    def _calculate_hours_for_subject(self, subject_code: str, is_supporting: bool = False) -> int:
        """
        Calculate total hours per week for one section of a subject
        
        Args:
            subject_code: Subject code
            is_supporting: If True, only calculate hours for practical components
            
        Returns:
            Total hours per week (whole hours, rounded up from minutes)
        """
        subject = self.subjects_map.get(subject_code)
        if not subject:
            return 0
        
        components = subject.get('components', [])
        
        # For supporting assignments, only count practical components
        if is_supporting:
            components = [c for c in components if c.get('componentType', '').lower() == 'practical']
        
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
        primary_assignments: List[Dict[str, Any]],
        supporting_assignments: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Calculate workload statistics from primary AND supporting assignments.
        
        Supporting assignments are typically practical/lab components where the faculty
        assists the primary instructor. Their hours count toward total workload.
        
        NOTE: This method uses component information already calculated in assignments,
        not from re-expanding subject definitions. This is crucial for supporting
        assignments which have already had non-practical components filtered out.
        
        Args:
            primary_assignments: List of primary assignment dicts
            supporting_assignments: List of supporting assignment dicts (optional)
            
        Returns:
            Workload stats dict with hours broken down by component type
        """
        if supporting_assignments is None:
            supporting_assignments = []
        
        import math
        
        stats = {
            'theoryHours': 0,
            'tutorialHours': 0,
            'practicalHours': 0,
            'totalSessions': 0,
            'totalWeeklyHours': 0
        }
        
        # Process both primary and supporting assignments
        # Use assignment's already-calculated data, don't recalculate from subject
        all_assignments = primary_assignments + supporting_assignments
        
        for assignment in all_assignments:
            # Get component types from this specific assignment
            # (not from subject definition - subject has MORE components)
            component_types = assignment.get('componentTypes', [])
            effective_sections = len(assignment.get('sections', []))
            if effective_sections == 0:
                effective_sections = len(assignment.get('studentGroupIds', []))
            if effective_sections == 0:
                effective_sections = 1
            
            # Get hours from subject for each component in THIS assignment
            subject_code = assignment['subjectCode']
            subject = self.subjects_map.get(subject_code)
            
            if not subject:
                continue
            
            subject_components = subject.get('components', [])
            
            # Only process components that are in this assignment's component list
            for comp_type in assignment['componentTypes']:
                # Find this specific component in subject
                for comp in subject_components:
                    if comp.get('componentType') == comp_type:
                        sessions = comp.get('sessionsPerWeek', 0)
                        duration = comp.get('sessionDuration', 0)
                        
                        # Calculate hours for this component's sections
                        total_minutes = sessions * duration * effective_sections
                        hours = math.ceil(total_minutes / 60.0)
                        
                        if comp_type == 'theory':
                            stats['theoryHours'] += hours
                        elif comp_type == 'tutorial':
                            stats['tutorialHours'] += hours
                        elif comp_type == 'practical':
                            stats['practicalHours'] += hours
                        
                        stats['totalSessions'] += sessions * effective_sections
                        break
        
        stats['totalWeeklyHours'] = (
            stats['theoryHours'] + 
            stats['tutorialHours'] + 
            stats['practicalHours']
        )
        
        return stats


def main(data_dir=None):
    """Test the workload calculator"""
    import argparse
    from pathlib import Path
    from timetable.scripts.stage2.data_loader import Stage1DataLoader
    
    if data_dir is None:
        parser = argparse.ArgumentParser(description="Calculate faculty workload")
        parser.add_argument("--data-dir", required=True, help="Data directory path")
        args = parser.parse_args()
        data_dir = Path(args.data_dir)
    else:
        data_dir = Path(data_dir)
    
    stage1_dir = data_dir / "stage_1"
    stage2_dir = data_dir / "stage_2"
    
    print("Testing Workload Calculator")
    print(f"Data directory: {data_dir}")
    print("=" * 60)
    print()
    
    # Load data
    loader = Stage1DataLoader(str(stage1_dir))
    faculty = loader.load_faculty_basic()
    student_groups_data = loader.load_student_groups()
    
    # Load subjects full
    subjects_full_path = stage2_dir / "subjects2Full.json"
    
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
