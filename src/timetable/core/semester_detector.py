"""
Semester detection utility for dynamic file selection.

This module provides functions to detect which semesters are active
in a project based on studentGroups.json configuration, enabling
dynamic and selective loading of semester-specific files.

The core principle: studentGroups.json is the single source of truth
for determining which semesters are active in the build.
"""

from typing import Tuple, List, Dict, Any
from pathlib import Path


def detect_active_semesters(student_groups_data: Dict[str, Any]) -> Tuple[int, ...]:
    """
    Detect which semesters are active from studentGroups.json data.
    
    Analyzes both regular and elective student groups to determine
    which semesters are configured for the current project.
    
    Args:
        student_groups_data: Loaded studentGroups.json data (dict format)
        
    Returns:
        Tuple of active semester numbers, sorted.
        Examples: (2, 4) or (1, 3)
        
    Raises:
        ValueError: If studentGroups data is invalid or missing semester info
    """
    semesters = set()
    
    # Check regular student groups
    student_groups = student_groups_data.get('studentGroups', [])
    if not student_groups:
        raise ValueError("No studentGroups found in studentGroups.json")
    
    for group in student_groups:
        if 'semester' not in group:
            raise ValueError(f"Student group missing 'semester' field: {group}")
        semesters.add(group['semester'])
    
    # Check elective student groups (supplementary, not required)
    elective_groups = student_groups_data.get('electiveStudentGroups', [])
    for group in elective_groups:
        if 'semester' in group:
            semesters.add(group['semester'])
    
    if not semesters:
        raise ValueError("Could not detect any active semesters from studentGroups.json")
    
    return tuple(sorted(semesters))


def is_semester_active(semester: int, active_semesters: Tuple[int, ...]) -> bool:
    """
    Check if a specific semester is in the active set.
    
    Args:
        semester: Semester number to check (1, 2, 3, or 4)
        active_semesters: Tuple of active semester numbers
        
    Returns:
        True if semester is active, False otherwise
    """
    return semester in active_semesters


def get_subject_files_for_semesters(active_semesters: Tuple[int, ...]) -> List[str]:
    """
    Get list of subject file names needed for active semesters.
    
    This determines which subject files should be loaded based on
    which semesters are active. Only semester-specific files are returned.
    
    Args:
        active_semesters: Tuple of active semester numbers
        
    Returns:
        List of filenames to load from stage_1/
        
    Example:
        >>> get_subject_files_for_semesters((2, 4))
        ['subjects2CoreBasic.json', 'subjects2ElectBasic.json', 
         'subjects4CoreBasic.json', 'subjects4ElectBasic.json']
    """
    files = []
    
    for sem in sorted(active_semesters):
        if sem == 1:
            files.extend([
                'subjects1CoreBasic.json',
                'subjects1Diff.json'
            ])
        elif sem == 2:
            files.extend([
                'subjects2CoreBasic.json',
                'subjects2ElectBasic.json',
                'subjects2Diff.json'
            ])
        elif sem == 3:
            files.extend([
                'subjects3CoreBasic.json',
                'subjects3ElectBasic.json',
                'subjects3Diff.json'
            ])
        elif sem == 4:
            files.extend([
                'subjects4CoreBasic.json',
                'subjects4ElectBasic.json',
                'subjects4Diff.json'
            ])
    
    return files


def get_elective_differentiation_files(active_semesters: Tuple[int, ...]) -> List[str]:
    """
    Get elective differentiation file names for active semesters.
    
    These files define how electives are differentiated/mapped for each semester.
    
    Args:
        active_semesters: Tuple of active semester numbers
        
    Returns:
        List of elective differentiation filenames
        
    Example:
        >>> get_elective_differentiation_files((2, 4))
        ['elective2Differentiation.json']
    """
    files = []
    
    if 2 in active_semesters:
        files.append('elective2Differentiation.json')
    
    if 3 in active_semesters:
        files.append('elective3Differentiation.json')
    
    return files


def describe_active_semesters(active_semesters: Tuple[int, ...]) -> str:
    """
    Generate a human-readable description of active semesters.
    
    Args:
        active_semesters: Tuple of active semester numbers
        
    Returns:
        Descriptive string
        
    Example:
        >>> describe_active_semesters((2, 4))
        'Semester 2 & 4'
    """
    if not active_semesters:
        return "No semesters"
    
    sems = sorted(active_semesters)
    if len(sems) == 1:
        return f"Semester {sems[0]}"
    else:
        return "Semester " + " & ".join(map(str, sems))


__all__ = [
    'detect_active_semesters',
    'is_semester_active',
    'get_subject_files_for_semesters',
    'get_elective_differentiation_files',
    'describe_active_semesters',
]
