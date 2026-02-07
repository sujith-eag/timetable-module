"""
Data Loader for Stage 3 - Load Stage 2 and Stage 1 Data
========================================================

This module loads all necessary data from Stage 1 and Stage 2:
- Faculty data (from Stage 2 faculty2Full.json)
- Subject data (from Stage 2 subjects2Full.json)
- Student groups (from Stage 1 studentGroups.json)
- Room preferences (from Stage 1 roomPreferences.json)
- Config data (from Stage 1 config.json)

Author: Stage 3 Implementation
Date: October 26, 2025
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional


class DataLoaderStage2:
    """Loads all required data from Stage 1 and Stage 2 for Stage 3 processing."""
    
    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize the data loader.
        
        Args:
            base_path: Base path to V4 directory. If None, auto-detects from script location.
        """
        if base_path is None:
            # Auto-detect base path (assumes script is in V4/stage_3/scripts/)
            script_dir = Path(__file__).parent
            self.base_path = script_dir.parent.parent
        else:
            self.base_path = Path(base_path)
        
        self.stage_1_path = self.base_path / "stage_1"
        self.stage_2_path = self.base_path / "stage_2"
        
        # Data containers
        self.faculty_data: List[Dict[str, Any]] = []
        self.subjects_data: List[Dict[str, Any]] = []
        self.student_groups: Dict[str, Any] = {}
        self.room_preferences: List[Dict[str, Any]] = []
        self.config: Dict[str, Any] = {}
    
    def _load_json(self, file_path: Path) -> Any:
        """
        Load JSON file with error handling.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Parsed JSON data
            
        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Required file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def load_faculty(self) -> List[Dict[str, Any]]:
        """
        Load faculty data from Stage 2.
        
        Returns:
            List of faculty dictionaries with full teaching assignments and workload
        """
        faculty_file = self.stage_2_path / "faculty2Full.json"
        data = self._load_json(faculty_file)
        self.faculty_data = data.get("faculty", [])
        return self.faculty_data
    
    def load_subjects(self) -> List[Dict[str, Any]]:
        """
        Load subject data from Stage 2.
        
        Returns:
            List of subject dictionaries with full component information
        """
        subjects_file = self.stage_2_path / "subjects2Full.json"
        data = self._load_json(subjects_file)
        self.subjects_data = data.get("subjects", [])
        return self.subjects_data
    
    def load_student_groups(self) -> Dict[str, Any]:
        """
        Load student groups from Stage 1.
        
        Returns:
            Dictionary containing studentGroups, electiveStudentGroups, and groupHierarchy
        """
        groups_file = self.stage_1_path / "studentGroups.json"
        self.student_groups = self._load_json(groups_file)
        return self.student_groups
    
    def load_room_preferences(self) -> List[Dict[str, Any]]:
        """
        Load room preferences from Stage 1.
        
        Returns:
            List of room preference dictionaries
        """
        rooms_file = self.stage_1_path / "roomPreferences.json"
        data = self._load_json(rooms_file)
        self.room_preferences = data.get("roomPreferences", [])
        return self.room_preferences
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from Stage 1.
        
        Returns:
            Configuration dictionary with time slots and settings
        """
        config_file = self.stage_1_path / "config.json"
        self.config = self._load_json(config_file)
        return self.config
    
    def load_all(self) -> Dict[str, Any]:
        """
        Load all data at once.
        
        Returns:
            Dictionary containing all loaded data:
            {
                "faculty": List[Dict],
                "subjects": List[Dict],
                "studentGroups": Dict,
                "roomPreferences": List[Dict],
                "config": Dict
            }
        """
        return {
            "faculty": self.load_faculty(),
            "subjects": self.load_subjects(),
            "studentGroups": self.load_student_groups(),
            "roomPreferences": self.load_room_preferences(),
            "config": self.load_config()
        }
    
    def get_faculty_by_id(self, faculty_id: str) -> Optional[Dict[str, Any]]:
        """
        Get faculty member by ID.
        
        Args:
            faculty_id: Faculty identifier (e.g., "SA")
            
        Returns:
            Faculty dictionary or None if not found
        """
        for faculty in self.faculty_data:
            if faculty.get("facultyId") == faculty_id:
                return faculty
        return None
    
    def get_subject_by_code(self, subject_code: str) -> Optional[Dict[str, Any]]:
        """
        Get subject by code.
        
        Args:
            subject_code: Subject code (e.g., "24MCA31")
            
        Returns:
            Subject dictionary or None if not found
        """
        for subject in self.subjects_data:
            if subject.get("subjectCode") == subject_code:
                return subject
        return None
    
    def get_subjects_by_semester(self, semester: int) -> List[Dict[str, Any]]:
        """
        Get all subjects for a specific semester.
        
        Args:
            semester: Semester number (1 or 3)
            
        Returns:
            List of subject dictionaries for that semester
        """
        return [s for s in self.subjects_data if s.get("semester") == semester]
    
    def get_room_preferences_for_subject(
        self, 
        subject_code: str, 
        component_type: str, 
        student_group_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get room preferences for a specific subject component and student group.
        
        Args:
            subject_code: Subject code
            component_type: Component type (theory, practical, tutorial)
            student_group_id: Student group ID
            
        Returns:
            Room preference dictionary or None if not found
        """
        for pref in self.room_preferences:
            if (pref.get("subjectCode") == subject_code and 
                pref.get("componentType") == component_type and
                pref.get("studentGroupId") == student_group_id):
                return pref
        return None
    
    def get_student_group_hierarchy(self) -> Dict[str, Any]:
        """
        Get student group hierarchy for overlap constraint calculation.
        
        Returns:
            Group hierarchy dictionary mapping parents to children
        """
        return self.student_groups.get("groupHierarchy", {})
    
    def get_elective_student_groups(self) -> List[Dict[str, Any]]:
        """
        Get all elective student groups.
        
        Returns:
            List of elective student group dictionaries
        """
        return self.student_groups.get("electiveStudentGroups", [])
    
    def get_regular_student_groups(self) -> List[Dict[str, Any]]:
        """
        Get all regular (non-elective) student groups.
        
        Returns:
            List of regular student group dictionaries
        """
        return self.student_groups.get("studentGroups", [])


def main():
    """Test the data loader."""
    print("Testing DataLoaderStage2...")
    print("=" * 60)
    
    loader = DataLoaderStage2()
    
    # Load all data
    print("\n1. Loading all data...")
    all_data = loader.load_all()
    
    print(f"   ✓ Loaded {len(all_data['faculty'])} faculty members")
    print(f"   ✓ Loaded {len(all_data['subjects'])} subjects")
    print(f"   ✓ Loaded {len(all_data['studentGroups'].get('studentGroups', []))} student groups")
    print(f"   ✓ Loaded {len(all_data['studentGroups'].get('electiveStudentGroups', []))} elective groups")
    print(f"   ✓ Loaded {len(all_data['roomPreferences'])} room preferences")
    print(f"   ✓ Loaded config with {len(all_data['config'].get('timeSlots', []))} time slots")
    
    # Test faculty lookup
    print("\n2. Testing faculty lookup...")
    faculty = loader.get_faculty_by_id("SA")
    if faculty:
        print(f"   ✓ Found faculty: {faculty['name']}")
        print(f"     Total hours: {faculty['workloadStats']['totalWeeklyHours']}h")
        print(f"     Total sessions: {faculty['workloadStats']['totalSessions']}")
    
    # Test subject lookup
    print("\n3. Testing subject lookup...")
    subject = loader.get_subject_by_code("24MCA31")
    if subject:
        print(f"   ✓ Found subject: {subject['title']}")
        print(f"     Components: {len(subject.get('components', []))}")
    
    # Test semester filter
    print("\n4. Testing semester filter...")
    sem3_subjects = loader.get_subjects_by_semester(3)
    print(f"   ✓ Found {len(sem3_subjects)} Semester 3 subjects")
    
    # Test room preferences
    print("\n5. Testing room preferences...")
    room_pref = loader.get_room_preferences_for_subject("24MCA32", "practical", "MCA_SEM3_A")
    if room_pref:
        print(f"   ✓ Found room preference: {room_pref['preferredRooms']}")
        if "roomAllocations" in room_pref:
            print(f"     Pre-allocated: {room_pref['roomAllocations']}")
    
    # Test hierarchy
    print("\n6. Testing group hierarchy...")
    hierarchy = loader.get_student_group_hierarchy()
    print(f"   ✓ Group hierarchy has {len(hierarchy)} parent groups")
    for parent, info in hierarchy.items():
        print(f"     {parent} → {info.get('children', [])}")
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")


if __name__ == "__main__":
    main()
