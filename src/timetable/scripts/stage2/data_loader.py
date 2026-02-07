"""
Data Loader for Stage 1 Files

This module provides functions to load all Stage 1 JSON files.
Handles file reading, JSON parsing, and basic validation.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any


class Stage1DataLoader:
    """Loader for Stage 1 data files"""
    
    def __init__(self, stage1_dir: str = None):
        """
        Initialize the data loader
        
        Args:
            stage1_dir: Path to stage_1 directory. If None, auto-detects.
        """
        if stage1_dir is None:
            # Auto-detect stage_1 directory relative to this script
            script_dir = Path(__file__).parent
            self.stage1_dir = script_dir.parent.parent / "stage_1"
        else:
            self.stage1_dir = Path(stage1_dir)
        
        if not self.stage1_dir.exists():
            raise FileNotFoundError(f"Stage 1 directory not found: {self.stage1_dir}")
    
    def _load_json(self, filename: str) -> Dict[str, Any]:
        """
        Load a JSON file from stage_1 directory
        
        Args:
            filename: Name of the JSON file
            
        Returns:
            Parsed JSON data as dictionary
        """
        filepath = self.stage1_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {filename}: {e}")
    
    def load_config(self) -> Dict[str, Any]:
        """Load config.json"""
        return self._load_json("config.json")
    
    def load_faculty_basic(self) -> List[Dict[str, Any]]:
        """Load faculty from facultyBasic.json"""
        data = self._load_json("facultyBasic.json")
        return data.get("faculty", [])
    
    def load_student_groups(self) -> Dict[str, Any]:
        """Load studentGroups.json"""
        return self._load_json("studentGroups.json")
    
    def load_room_preferences(self) -> List[Dict[str, Any]]:
        """Load room preferences from roomPreferences.json"""
        data = self._load_json("roomPreferences.json")
        return data.get("roomPreferences", [])
    
    def load_subjects_sem1_core(self) -> List[Dict[str, Any]]:
        """Load semester 1 core subjects"""
        data = self._load_json("subjects1CoreBasic.json")
        return data.get("subjects", [])
    
    def load_subjects_sem3_core(self) -> List[Dict[str, Any]]:
        """Load semester 3 core subjects"""
        data = self._load_json("subjects3CoreBasic.json")
        return data.get("subjects", [])
    
    def load_subjects_sem3_elective(self) -> List[Dict[str, Any]]:
        """Load semester 3 elective subjects"""
        data = self._load_json("subjects3ElectBasic.json")
        return data.get("subjects", [])
    
    def load_subjects_diff(self) -> List[Dict[str, Any]]:
        """Load diff subjects"""
        data = self._load_json("subjects3Diff.json")
        return data.get("subjects", [])
    
    def load_all_subjects(self) -> List[Dict[str, Any]]:
        """
        Load all subjects from all files
        
        Returns:
            Combined list of all subjects
        """
        all_subjects = []
        all_subjects.extend(self.load_subjects_sem1_core())
        all_subjects.extend(self.load_subjects_sem3_core())
        all_subjects.extend(self.load_subjects_sem3_elective())
        all_subjects.extend(self.load_subjects_diff())
        return all_subjects
    
    def load_all(self) -> Dict[str, Any]:
        """
        Load all Stage 1 data
        
        Returns:
            Dictionary with all loaded data:
            - config
            - faculty
            - studentGroups
            - roomPreferences
            - subjects (all combined)
            - subjects_by_category (separated)
        """
        return {
            "config": self.load_config(),
            "faculty": self.load_faculty_basic(),
            "studentGroups": self.load_student_groups(),
            "roomPreferences": self.load_room_preferences(),
            "subjects": self.load_all_subjects(),
            "subjects_by_category": {
                "sem1_core": self.load_subjects_sem1_core(),
                "sem3_core": self.load_subjects_sem3_core(),
                "sem3_elective": self.load_subjects_sem3_elective(),
                "diff": self.load_subjects_diff()
            }
        }


def main():
    """Test the data loader"""
    loader = Stage1DataLoader()
    
    print("Loading Stage 1 data...")
    print(f"Stage 1 directory: {loader.stage1_dir}")
    print()
    
    # Load and display summary
    try:
        config = loader.load_config()
        print(f"✓ Config loaded")
        print(f"  - Weekdays: {config['config']['weekdays']}")
        print(f"  - Time slots: {len(config['config']['timeSlots'])}")
        print()
        
        faculty = loader.load_faculty_basic()
        print(f"✓ Faculty loaded: {len(faculty)} faculty members")
        print()
        
        student_groups_data = loader.load_student_groups()
        student_groups = student_groups_data.get("studentGroups", [])
        print(f"✓ Student groups loaded: {len(student_groups)} groups")
        print()
        
        room_prefs = loader.load_room_preferences()
        print(f"✓ Room preferences loaded: {len(room_prefs)} preferences")
        print()
        
        subjects = loader.load_all_subjects()
        print(f"✓ Subjects loaded: {len(subjects)} subjects")
        
        # Show breakdown
        by_category = loader.load_all()["subjects_by_category"]
        print(f"  - Sem 1 Core: {len(by_category['sem1_core'])}")
        print(f"  - Sem 3 Core: {len(by_category['sem3_core'])}")
        print(f"  - Sem 3 Elective: {len(by_category['sem3_elective'])}")
        print(f"  - Diff: {len(by_category['diff'])}")
        print()
        
        print("✓ All Stage 1 data loaded successfully!")
        
    except Exception as e:
        print(f"✗ Error loading data: {e}")
        raise


if __name__ == "__main__":
    main()
