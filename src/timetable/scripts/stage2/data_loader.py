"""
Data Loader for Stage 1 Files

This module provides functions to load all Stage 1 JSON files.
Handles file reading, JSON parsing, and basic validation.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Setup logging
logger = logging.getLogger(__name__)


class Stage1DataLoader:
    """Loader for Stage 1 data files"""
    
    def __init__(self, stage1_dir: str = None):
        """
        Initialize the data loader
        
        Args:
            stage1_dir: Path to stage_1 directory. If None, auto-detects.
        """
        if stage1_dir is None:
            # Auto-detect stage_1 directory
            import os
            data_dir = os.environ.get('TIMETABLE_DATA_DIR')
            if data_dir:
                self.stage1_dir = Path(data_dir) / "stage_1"
            else:
                raise ValueError("stage1_dir not provided and TIMETABLE_DATA_DIR not set. Please provide explicit stage1_dir path or set TIMETABLE_DATA_DIR environment variable.")
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
            logger.warning(f"File not found: {filepath}")
            raise FileNotFoundError(f"File not found: {filepath}")
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logger.debug(f"Successfully loaded: {filename}")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {filename}: {e}")
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
    
    def load_subjects_sem2_core(self) -> List[Dict[str, Any]]:
        """Load semester 2 core subjects"""
        data = self._load_json("subjects2CoreBasic.json")
        return data.get("subjects", [])
    
    def load_subjects_sem2_elective(self) -> List[Dict[str, Any]]:
        """Load semester 2 elective subjects"""
        data = self._load_json("subjects2ElectBasic.json")
        return data.get("subjects", [])
    
    def load_subjects_sem3_core(self) -> List[Dict[str, Any]]:
        """Load semester 3 core subjects"""
        data = self._load_json("subjects3CoreBasic.json")
        return data.get("subjects", [])
    
    def load_subjects_sem3_elective(self) -> List[Dict[str, Any]]:
        """Load semester 3 elective subjects"""
        data = self._load_json("subjects3ElectBasic.json")
        return data.get("subjects", [])
    
    def load_subjects_sem4_core(self) -> List[Dict[str, Any]]:
        """Load semester 4 core subjects"""
        try:
            data = self._load_json("subjects4CoreBasic.json")
            return data.get("subjects", [])
        except FileNotFoundError:
            return []
    
    def load_subjects_sem1_diff(self) -> List[Dict[str, Any]]:
        """Load semester 1 differentiated subjects"""
        try:
            data = self._load_json("subjects1Diff.json")
            return data.get("subjects", [])
        except FileNotFoundError:
            return []
    
    def load_subjects_sem2_diff(self) -> List[Dict[str, Any]]:
        """Load semester 2 differentiated subjects"""
        try:
            data = self._load_json("subjects2Diff.json")
            return data.get("subjects", [])
        except FileNotFoundError:
            return []
    
    def load_subjects_sem3_diff(self) -> List[Dict[str, Any]]:
        """Load semester 3 differentiated subjects"""
        try:
            data = self._load_json("subjects3Diff.json")
            return data.get("subjects", [])
        except FileNotFoundError:
            return []

    def load_subjects_sem4_diff(self) -> List[Dict[str, Any]]:
        """Load semester 4 differentiated subjects (fixed schedule)"""
        try:
            data = self._load_json("subjects4Diff.json")
            return data.get("subjects", [])
        except FileNotFoundError:
            return []
    
    def load_subjects_diff(self) -> List[Dict[str, Any]]:
        """
        Load differentiated subjects from all semesters.
        
        DEPRECATED: Use semester-specific loaders instead.
        This method is kept for backward compatibility only.
        """
        all_diff = []
        all_diff.extend(self.load_subjects_sem1_diff())
        all_diff.extend(self.load_subjects_sem2_diff())
        all_diff.extend(self.load_subjects_sem3_diff())
        all_diff.extend(self.load_subjects_sem4_diff())
        return all_diff
    
    def load_all_subjects(self, active_semesters: Optional[Tuple[int, ...]] = None) -> List[Dict[str, Any]]:
        """
        Load subjects from relevant semester files only.
        
        If active_semesters is provided, only loads subject files for those semesters.
        If not provided, loads all available subject files (backward compatible behavior).
        
        Args:
            active_semesters: Tuple of semester numbers to load (e.g., (2, 4) or (1, 3)).
                            If None, loads all available subjects.
        
        Returns:
            Combined list of all subjects from relevant files
        """
        if active_semesters is None:
            # Backward compatible: load all available
            active_semesters = (1, 2, 3, 4)
        
        all_subjects = []
        
        # Load by semester, only if semester is active
        if 1 in active_semesters:
            try:
                subjects = self.load_subjects_sem1_core()
                all_subjects.extend(subjects)
                logger.info(f"Loaded {len(subjects)} Semester 1 core subjects")
            except FileNotFoundError:
                logger.debug("Semester 1 core subjects file not found")
        
        if 2 in active_semesters:
            try:
                subjects = self.load_subjects_sem2_core()
                all_subjects.extend(subjects)
                logger.info(f"Loaded {len(subjects)} Semester 2 core subjects")
            except FileNotFoundError:
                logger.debug("Semester 2 core subjects file not found")
            
            try:
                subjects = self.load_subjects_sem2_elective()
                all_subjects.extend(subjects)
                logger.info(f"Loaded {len(subjects)} Semester 2 elective subjects")
            except FileNotFoundError:
                logger.debug("Semester 2 elective subjects file not found")
        
        if 3 in active_semesters:
            try:
                subjects = self.load_subjects_sem3_core()
                all_subjects.extend(subjects)
                logger.info(f"Loaded {len(subjects)} Semester 3 core subjects")
            except FileNotFoundError:
                logger.debug("Semester 3 core subjects file not found")
            
            try:
                subjects = self.load_subjects_sem3_elective()
                all_subjects.extend(subjects)
                logger.info(f"Loaded {len(subjects)} Semester 3 elective subjects")
            except FileNotFoundError:
                logger.debug("Semester 3 elective subjects file not found")
        
        if 4 in active_semesters:
            try:
                subjects = self.load_subjects_sem4_core()
                all_subjects.extend(subjects)
                logger.info(f"Loaded {len(subjects)} Semester 4 core subjects")
            except FileNotFoundError:
                logger.debug("Semester 4 core subjects file not found")
        
        # Load diff subjects ONLY for active semesters
        # Load them individually to maintain semester boundaries
        if 1 in active_semesters:
            try:
                subjects = self.load_subjects_sem1_diff()
                all_subjects.extend(subjects)
                logger.info(f"Loaded {len(subjects)} Semester 1 differentiated subjects")
            except FileNotFoundError:
                logger.debug("Semester 1 differentiated subjects file not found")
        
        if 2 in active_semesters:
            try:
                subjects = self.load_subjects_sem2_diff()
                all_subjects.extend(subjects)
                logger.info(f"Loaded {len(subjects)} Semester 2 differentiated subjects")
            except FileNotFoundError:
                logger.debug("Semester 2 differentiated subjects file not found")
        
        if 3 in active_semesters:
            try:
                subjects = self.load_subjects_sem3_diff()
                all_subjects.extend(subjects)
                logger.info(f"Loaded {len(subjects)} Semester 3 differentiated subjects")
            except FileNotFoundError:
                logger.debug("Semester 3 differentiated subjects file not found")
        
        if 4 in active_semesters:
            try:
                subjects = self.load_subjects_sem4_diff()
                all_subjects.extend(subjects)
                logger.info(f"Loaded {len(subjects)} Semester 4 differentiated subjects")
            except FileNotFoundError:
                logger.debug("Semester 4 differentiated subjects file not found")
        
        logger.info(f"Total subjects loaded: {len(all_subjects)} from Semester(s): {', '.join(map(str, sorted(active_semesters)))}")
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
                "sem2_core": self.load_subjects_sem2_core(),
                "sem2_elective": self.load_subjects_sem2_elective(),
                "sem3_core": self.load_subjects_sem3_core(),
                "sem3_elective": self.load_subjects_sem3_elective(),
                "sem4_core": self.load_subjects_sem4_core(),
                "sem4_diff": self.load_subjects_sem4_diff(),
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
