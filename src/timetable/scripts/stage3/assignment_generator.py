"""
Assignment Generator for Stage 3
=================================

This module generates teaching assignments from Stage 2 faculty data.
Each assignment represents a single teaching responsibility that needs to be scheduled.

For example, if Dr. Ajitha teaches Software Engineering Theory to Section B (3 sessions/week),
this generates ONE assignment that will later be scheduled into 3 time slots.

Author: Stage 3 Implementation
Date: October 26, 2025
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from data_loader_stage2 import DataLoaderStage2


class AssignmentGenerator:
    """Generates teaching assignments from Stage 2 data."""
    
    def __init__(self, loader: DataLoaderStage2):
        """
        Initialize the assignment generator.
        
        Args:
            loader: DataLoaderStage2 instance with loaded data
        """
        self.loader = loader
        self.assignment_counter = 0
        self.elective_differentiation_rules = self._load_differentiation_rules()
    
    def _generate_assignment_id(
        self, 
        subject_code: str, 
        component_type: str, 
        section: str
    ) -> str:
        """
        Generate a unique assignment ID.
        
        Args:
            subject_code: Subject code (e.g., "24MCA31")
            component_type: Component type (theory, practical, tutorial)
            section: Section (A, B, or mixed like "A,B")
            
        Returns:
            Unique assignment ID (e.g., "TA_24MCA31_TH_B_001")
        """
        self.assignment_counter += 1
        comp_abbrev = component_type[:2].upper()  # TH, PR, TU
        section_clean = section.replace(",", "")  # AB for mixed
        return f"TA_{subject_code}_{comp_abbrev}_{section_clean}_{self.assignment_counter:03d}"
    
    def _get_component_id(self, subject_code: str, component_type: str) -> str:
        """
        Get component ID.
        
        Args:
            subject_code: Subject code
            component_type: Component type
            
        Returns:
            Component ID (e.g., "24MCA31_TH")
        """
        comp_abbrev = component_type[:2].upper()
        return f"{subject_code}_{comp_abbrev}"
    
    def _determine_priority(self, subject: Dict[str, Any]) -> str:
        """
        Determine assignment priority.
        
        Args:
            subject: Subject dictionary
            
        Returns:
            Priority level: 'high', 'medium', or 'low'
        """
        # Diff subjects with fixed timing are high priority
        if subject.get("type") == "diff":
            return subject.get("priority", "medium")
        
        # Core subjects are high priority
        if not subject.get("isElective", False):
            return "high"
        
        # Electives are medium priority
        return "medium"
    
    def generate_assignment_from_faculty_assignment(
        self,
        faculty: Dict[str, Any],
        faculty_assignment: Dict[str, Any],
        assignment_type: str  # 'primary' or 'supporting'
    ) -> List[Dict[str, Any]]:
        """
        Generate teaching assignment(s) from a faculty assignment.
        
        A faculty assignment may map to multiple teaching assignments if it covers
        multiple sections or student groups.
        
        Args:
            faculty: Faculty dictionary
            faculty_assignment: Faculty assignment from Stage 2
            assignment_type: 'primary' or 'supporting'
            
        Returns:
            List of teaching assignment dictionaries
        """
        assignments = []
        
        subject_code = faculty_assignment["subjectCode"]
        subject = self.loader.get_subject_by_code(subject_code)
        
        if not subject:
            print(f"Warning: Subject {subject_code} not found in subjects data")
            return assignments
        
        semester = faculty_assignment["semester"]
        sections = faculty_assignment["sections"]
        student_group_ids = faculty_assignment.get("studentGroupIds", [])
        component_ids = faculty_assignment.get("componentIds", [])
        component_types = faculty_assignment.get("componentTypes", [])
        
        # Get subject details
        subject_title = subject.get("title", "")
        is_elective = subject.get("isElective", False)
        is_diff = subject.get("type") == "diff"
        
        # For each component in this assignment
        for component_type in set(component_types):
            component_id = self._get_component_id(subject_code, component_type)
            
            # Find the component details from subject
            component_details = self._get_component_details(subject, component_type)
            if not component_details:
                continue
            
            session_duration = component_details.get("sessionDuration", 55)
            sessions_per_week = component_details.get("sessionsPerWeek", 1)
            requires_contiguous = component_details.get("mustBeContiguous", False)
            block_size_slots = component_details.get("blockSizeSlots", 1)
            room_type = component_details.get("mustBeInRoomType", "lecture")
            
            # Generate assignment for each student group
            # (For core subjects, there's one group per section)
            # (For electives, there may be multiple groups)
            if len(student_group_ids) == 1:
                # Single student group - generate one assignment
                assignment = self._create_assignment(
                    faculty=faculty,
                    subject_code=subject_code,
                    subject_title=subject_title,
                    component_id=component_id,
                    component_type=component_type,
                    semester=semester,
                    sections=sections,
                    student_group_ids=student_group_ids,
                    session_duration=session_duration,
                    sessions_per_week=sessions_per_week,
                    requires_contiguous=requires_contiguous,
                    block_size_slots=block_size_slots,
                    room_type=room_type,
                    is_elective=is_elective,
                    is_diff=is_diff,
                    subject=subject
                )
                assignments.append(assignment)
            else:
                # Multiple student groups - determine if should separate by section
                # CORE SUBJECTS: Always separate by section (each section gets its own class)
                # ELECTIVES: Follow differentiation rules (some combined, some separate)
                
                if not is_elective:
                    # Core subject - always create separate assignments for each section
                    should_separate = True
                else:
                    # Elective - check differentiation rules
                    elective_category = self._get_elective_category(subject_code)
                    should_separate = self._should_separate_by_section(
                        elective_category, component_type
                    )
                
                if should_separate:
                    # Create separate assignment for each group (e.g., AD practicals)
                    for student_group_id in student_group_ids:
                        # Find the section for this group
                        section = self._get_section_for_group(student_group_id)
                        
                        assignment = self._create_assignment(
                            faculty=faculty,
                            subject_code=subject_code,
                            subject_title=subject_title,
                            component_id=component_id,
                            component_type=component_type,
                            semester=semester,
                            sections=[section] if section else sections,
                            student_group_ids=[student_group_id],
                            session_duration=session_duration,
                            sessions_per_week=sessions_per_week,
                            requires_contiguous=requires_contiguous,
                            block_size_slots=block_size_slots,
                            room_type=room_type,
                            is_elective=is_elective,
                            is_diff=is_diff,
                            subject=subject
                        )
                        assignments.append(assignment)
                else:
                    # Combined assignment for multiple groups (e.g., AD theory/tutorial, SS all)
                    assignment = self._create_assignment(
                        faculty=faculty,
                        subject_code=subject_code,
                        subject_title=subject_title,
                        component_id=component_id,
                        component_type=component_type,
                        semester=semester,
                        sections=sections,
                        student_group_ids=student_group_ids,
                        session_duration=session_duration,
                        sessions_per_week=sessions_per_week,
                        requires_contiguous=requires_contiguous,
                        block_size_slots=block_size_slots,
                        room_type=room_type,
                        is_elective=is_elective,
                        is_diff=is_diff,
                        subject=subject
                    )
                    assignments.append(assignment)
        
        return assignments
    
    def _create_assignment(
        self,
        faculty: Dict[str, Any],
        subject_code: str,
        subject_title: str,
        component_id: str,
        component_type: str,
        semester: int,
        sections: List[str],
        student_group_ids: List[str],
        session_duration: int,
        sessions_per_week: int,
        requires_contiguous: bool,
        block_size_slots: int,
        room_type: str,
        is_elective: bool,
        is_diff: bool,
        subject: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a single teaching assignment."""
        section_str = ",".join(sections)
        assignment_id = self._generate_assignment_id(subject_code, component_type, section_str)
        
        priority = self._determine_priority(subject)
        
        assignment = {
            "assignmentId": assignment_id,
            "subjectCode": subject_code,
            "shortCode": subject.get("shortCode", subject_code),
            "subjectTitle": subject_title,
            "componentId": component_id,
            "componentType": component_type,
            "semester": semester,
            "facultyId": faculty["facultyId"],
            "facultyName": faculty["name"],
            "studentGroupIds": student_group_ids,
            "sections": sections,
            "sessionDuration": session_duration,
            "sessionsPerWeek": sessions_per_week,
            "requiresRoomType": room_type,
            "preferredRooms": [],  # Will be filled by room_preference_extractor
            "requiresContiguous": requires_contiguous,
            "blockSizeSlots": block_size_slots,
            "priority": priority,
            "isElective": is_elective,
            "isDiffSubject": is_diff,
            "constraints": {}  # Will be filled by constraint_builder
        }
        
        return assignment
    
    def _get_component_details(
        self, 
        subject: Dict[str, Any], 
        component_type: str
    ) -> Optional[Dict[str, Any]]:
        """Get component details from subject."""
        components = subject.get("components", [])
        for component in components:
            if component.get("componentType") == component_type:
                return component
        return None
    
    def _get_elective_category(self, subject_code: str) -> Optional[str]:
        """Get elective category (AD or SS) from subject code."""
        if "MCAAD" in subject_code:
            return "AD"
        elif "MCASS" in subject_code:
            return "SS"
        return None
    
    def _load_differentiation_rules(self) -> Dict[str, Any]:
        """Load elective differentiation rules from Stage 1."""
        try:
            stage1_path = Path(__file__).parent.parent.parent / "stage_1"
            rules_file = stage1_path / "electiveDifferentiation.json"
            
            if rules_file.exists():
                with open(rules_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert to easier lookup format
                    rules = {}
                    for rule in data.get("rules", []):
                        category = rule["electiveCategory"]
                        rules[category] = rule["differentiation"]
                    return rules
            else:
                print(f"Warning: electiveDifferentiation.json not found at {rules_file}")
                # Default fallback: AD splits everything, SS combines everything
                return {
                    "AD": {
                        "theory": {"separateSections": True},
                        "tutorial": {"separateSections": True},
                        "practical": {"separateSections": True}
                    },
                    "SS": {
                        "theory": {"separateSections": False},
                        "tutorial": {"separateSections": False},
                        "practical": {"separateSections": False}
                    }
                }
        except Exception as e:
            print(f"Error loading differentiation rules: {e}")
            return {}
    
    def _should_separate_by_section(
        self, 
        elective_category: Optional[str], 
        component_type: str
    ) -> bool:
        """
        Determine if this component should be separated by section.
        
        Args:
            elective_category: "AD" or "SS" or None
            component_type: "theory", "tutorial", or "practical"
            
        Returns:
            True if should create separate assignments per section, False if combined
        """
        if not elective_category or elective_category not in self.elective_differentiation_rules:
            return False
        
        category_rules = self.elective_differentiation_rules[elective_category]
        component_rule = category_rules.get(component_type, {})
        
        return component_rule.get("separateSections", False)
    
    def _get_section_for_group(self, student_group_id: str) -> Optional[str]:
        """Get section letter from student group ID."""
        # ELEC_AD_A1 -> A, ELEC_AD_B1 -> B, ELEC_SS_G1 -> Mixed (returns None)
        # Check last character more precisely
        if student_group_id.endswith("_A1") or student_group_id.endswith("_A"):
            return "A"
        elif student_group_id.endswith("_B1") or student_group_id.endswith("_B"):
            return "B"
        # For mixed groups like ELEC_SS_G1, return None to indicate mixed sections
        return None
    
    def generate_all_assignments(self, semester: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Generate all teaching assignments for a semester.
        
        Args:
            semester: Semester number (1 or 3). If None, generates for all semesters.
            
        Returns:
            List of all teaching assignments
        """
        all_assignments = []
        
        for faculty in self.loader.faculty_data:
            faculty_id = faculty["facultyId"]
            
            # Process primary assignments
            for faculty_assignment in faculty.get("primaryAssignments", []):
                if semester and faculty_assignment["semester"] != semester:
                    continue
                
                assignments = self.generate_assignment_from_faculty_assignment(
                    faculty, faculty_assignment, "primary"
                )
                all_assignments.extend(assignments)
            
            # Skip supporting assignments for Stage 3 (deferred to Stage 5)
            # Supporting faculty will be assigned after main schedule is complete
        
        return all_assignments


def main():
    """Test the assignment generator."""
    print("Testing Assignment Generator")
    print("=" * 80)
    
    # Load data
    print("\n1. Loading data...")
    loader = DataLoaderStage2()
    loader.load_all()
    print("   ✓ Data loaded")
    
    # Generate assignments
    print("\n2. Generating assignments for Semester 3...")
    generator = AssignmentGenerator(loader)
    assignments_sem3 = generator.generate_all_assignments(semester=3)
    
    print(f"   ✓ Generated {len(assignments_sem3)} assignments")
    
    # Show sample assignments
    print("\n3. Sample Assignments:")
    print("-" * 80)
    
    for i, assignment in enumerate(assignments_sem3[:5], 1):
        print(f"\n   Assignment {i}:")
        print(f"      ID: {assignment['assignmentId']}")
        print(f"      Subject: {assignment['subjectTitle']}")
        print(f"      Faculty: {assignment['facultyName']}")
        print(f"      Groups: {assignment['studentGroupIds']}")
        print(f"      Sessions: {assignment['sessionsPerWeek']} × {assignment['sessionDuration']}min")
        print(f"      Priority: {assignment['priority']}")
        print(f"      Elective: {assignment['isElective']}")
    
    # Statistics
    print("\n4. Statistics:")
    print("-" * 80)
    core_count = sum(1 for a in assignments_sem3 if not a['isElective'])
    elective_count = sum(1 for a in assignments_sem3 if a['isElective'])
    diff_count = sum(1 for a in assignments_sem3 if a['isDiffSubject'])
    
    print(f"   Core assignments: {core_count}")
    print(f"   Elective assignments: {elective_count}")
    print(f"   Diff assignments: {diff_count}")
    print(f"   Total: {len(assignments_sem3)}")
    
    print("\n" + "=" * 80)
    print("✓ Test complete!")


if __name__ == "__main__":
    main()
