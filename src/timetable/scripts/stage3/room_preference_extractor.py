"""
Room Preference Extractor for Stage 3
======================================

This module extracts room preferences from Stage 1 data and populates
the preferredRooms field in teaching assignments.

Author: Stage 3 Implementation
Date: October 26, 2025
"""

from typing import Dict, List, Any
from data_loader_stage2 import DataLoaderStage2


class RoomPreferenceExtractor:
    """Extracts and populates room preferences for assignments."""
    
    def __init__(self, loader: DataLoaderStage2):
        """
        Initialize the room preference extractor.
        
        Args:
            loader: DataLoaderStage2 instance with loaded data
        """
        self.loader = loader
    
    def extract_preferences(self, assignment: Dict[str, Any]) -> List[str]:
        """
        Extract room preferences for an assignment.
        
        Args:
            assignment: Teaching assignment dictionary
            
        Returns:
            List of preferred room IDs
        """
        subject_code = assignment.get("subjectCode")
        component_type = assignment.get("componentType")
        student_group_ids = assignment.get("studentGroupIds", [])
        
        preferred_rooms = []
        
        # Check each student group for room preferences
        for student_group_id in student_group_ids:
            room_pref = self.loader.get_room_preferences_for_subject(
                subject_code, component_type, student_group_id
            )
            
            if room_pref and "preferredRooms" in room_pref:
                preferred_rooms.extend(room_pref["preferredRooms"])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_rooms = []
        for room in preferred_rooms:
            if room not in seen:
                seen.add(room)
                unique_rooms.append(room)
        
        return unique_rooms
    
    def populate_room_preferences(
        self, 
        assignments: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Populate room preferences for multiple assignments.
        
        Args:
            assignments: List of teaching assignments
            
        Returns:
            List of assignments with preferredRooms field populated
        """
        for assignment in assignments:
            assignment["preferredRooms"] = self.extract_preferences(assignment)
        
        return assignments


def main():
    """Test the room preference extractor."""
    print("Testing Room Preference Extractor")
    print("=" * 80)
    
    # Load data
    print("\n1. Loading data...")
    loader = DataLoaderStage2()
    loader.load_all()
    print("   ✓ Data loaded")
    
    # Generate sample assignments
    print("\n2. Generating sample assignments...")
    from assignment_generator import AssignmentGenerator
    generator = AssignmentGenerator(loader)
    assignments = generator.generate_all_assignments(semester=3)
    print(f"   ✓ Generated {len(assignments)} assignments")
    
    # Extract room preferences
    print("\n3. Extracting room preferences...")
    extractor = RoomPreferenceExtractor(loader)
    assignments_with_rooms = extractor.populate_room_preferences(assignments)
    print(f"   ✓ Extracted preferences for {len(assignments_with_rooms)} assignments")
    
    # Show sample room preferences
    print("\n4. Sample Room Preferences:")
    print("-" * 80)
    
    for i, assignment in enumerate(assignments_with_rooms[:10], 1):
        print(f"\n   Assignment {i}: {assignment['assignmentId']}")
        print(f"      Subject: {assignment['subjectTitle']}")
        print(f"      Component: {assignment['componentType']}")
        print(f"      Room Type: {assignment['requiresRoomType']}")
        print(f"      Preferred Rooms: {assignment['preferredRooms']}")
    
    # Statistics
    print("\n5. Statistics:")
    print("-" * 80)
    
    with_preferences = sum(1 for a in assignments_with_rooms if a['preferredRooms'])
    without_preferences = len(assignments_with_rooms) - with_preferences
    
    print(f"   Assignments with room preferences: {with_preferences}")
    print(f"   Assignments without preferences: {without_preferences}")
    print(f"   Total: {len(assignments_with_rooms)}")
    
    # Group by room type
    print("\n6. Room Type Distribution:")
    print("-" * 80)
    room_types = {}
    for assignment in assignments_with_rooms:
        room_type = assignment['requiresRoomType']
        room_types[room_type] = room_types.get(room_type, 0) + 1
    
    for room_type, count in sorted(room_types.items()):
        print(f"   {room_type}: {count} assignments")
    
    print("\n" + "=" * 80)
    print("✓ Test complete!")


if __name__ == "__main__":
    main()
