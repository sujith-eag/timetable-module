"""
Component Expansion Module

This module handles the expansion of credit patterns into detailed components.
Takes a subject with creditPattern [theory, tutorial, practical] and generates
component objects with all necessary fields.
"""

from typing import Dict, List, Any


class ComponentExpander:
    """Expands credit patterns into detailed component objects"""
    
    # Component type mappings
    COMPONENT_TYPES = ['theory', 'tutorial', 'practical']
    COMPONENT_SUFFIXES = ['TH', 'TU', 'PR']
    ROOM_TYPE_MAP = {
        'theory': 'lecture',
        'tutorial': 'lab',
        'practical': 'lab'
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the component expander
        
        Args:
            config: Configuration dict from config.json
        """
        self.config = config['config']
        self.credit_to_hours = self.config['creditToHours']
        self.session_types = self.config['sessionTypes']
    
    def expand_components(self, subject: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Expand a subject's credit pattern into components
        
        Args:
            subject: Subject dict with creditPattern [T, Tu, P]
            
        Returns:
            List of component dicts
        """
        credit_pattern = subject.get('creditPattern', [0, 0, 0])
        subject_code = subject['subjectCode']
        components = []
        
        for i, credits in enumerate(credit_pattern):
            if credits > 0:
                component_type = self.COMPONENT_TYPES[i]
                component = self._create_component(
                    subject_code=subject_code,
                    component_type=component_type,
                    credits=credits,
                    suffix=self.COMPONENT_SUFFIXES[i]
                )
                components.append(component)
        
        return components
    
    def _create_component(
        self, 
        subject_code: str, 
        component_type: str, 
        credits: int,
        suffix: str
    ) -> Dict[str, Any]:
        """
        Create a single component object
        
        Args:
            subject_code: Subject code (e.g., "24MCA32")
            component_type: "theory", "tutorial", or "practical"
            credits: Number of credits
            suffix: Component suffix (TH, TU, PR)
            
        Returns:
            Component dict with all fields
        """
        # Get session duration for this component type
        session_duration = self.session_types[component_type]['duration']
        
        # Calculate sessions per week
        # Formula: credits × creditToHours × 60 minutes ÷ sessionDuration
        hours_per_credit = self.credit_to_hours[component_type]
        total_minutes = credits * hours_per_credit * 60
        sessions_per_week = total_minutes // session_duration
        
        # Get contiguous requirement
        must_be_contiguous = self.session_types[component_type]['requiresContiguous']
        
        # Calculate block size (number of slots needed)
        block_size_slots = 2 if must_be_contiguous else 1
        
        # Determine room type requirement
        must_be_in_room_type = self.ROOM_TYPE_MAP[component_type]
        
        return {
            'componentId': f"{subject_code}_{suffix}",
            'componentType': component_type,
            'credits': credits,
            'sessionDuration': session_duration,
            'sessionsPerWeek': sessions_per_week,
            'totalWeeklyMinutes': sessions_per_week * session_duration,
            'mustBeInRoomType': must_be_in_room_type,
            'blockSizeSlots': block_size_slots,
            'mustBeContiguous': must_be_contiguous
        }
    
    def validate_components(self, components: List[Dict[str, Any]]) -> List[str]:
        """
        Validate generated components
        
        Args:
            components: List of component dicts
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        for comp in components:
            # Check required fields
            required_fields = [
                'componentId', 'componentType', 'credits', 
                'sessionDuration', 'sessionsPerWeek', 'totalWeeklyMinutes',
                'mustBeInRoomType', 'blockSizeSlots', 'mustBeContiguous'
            ]
            
            for field in required_fields:
                if field not in comp:
                    errors.append(f"Component {comp.get('componentId', 'UNKNOWN')} missing field: {field}")
            
            # Check valid component type
            if comp.get('componentType') not in self.COMPONENT_TYPES:
                errors.append(f"Invalid component type: {comp.get('componentType')}")
            
            # Check sessions per week > 0
            if comp.get('sessionsPerWeek', 0) <= 0:
                errors.append(f"Component {comp.get('componentId')} has invalid sessionsPerWeek: {comp.get('sessionsPerWeek')}")
            
            # Check total minutes calculation
            expected_total = comp.get('sessionsPerWeek', 0) * comp.get('sessionDuration', 0)
            if comp.get('totalWeeklyMinutes') != expected_total:
                errors.append(
                    f"Component {comp.get('componentId')} totalWeeklyMinutes mismatch: "
                    f"expected {expected_total}, got {comp.get('totalWeeklyMinutes')}"
                )
        
        return errors


def main():
    """Test the component expander"""
    from data_loader import Stage1DataLoader
    
    print("Testing Component Expansion")
    print("=" * 50)
    print()
    
    # Load data
    loader = Stage1DataLoader()
    config = loader.load_config()
    subjects = loader.load_all_subjects()
    
    # Create expander
    expander = ComponentExpander(config)
    
    # Test with a few subjects
    test_subjects = [
        s for s in subjects 
        if s.get('subjectCode') in ['24MCA32', '24MCA31', '24MCAAD1']
    ]
    
    for subject in test_subjects:
        print(f"Subject: {subject['subjectCode']} - {subject['title']}")
        print(f"Credit Pattern: {subject.get('creditPattern', [])}")
        print()
        
        components = expander.expand_components(subject)
        
        print(f"Generated {len(components)} component(s):")
        for comp in components:
            print(f"  - {comp['componentId']}")
            print(f"    Type: {comp['componentType']}")
            print(f"    Credits: {comp['credits']}")
            print(f"    Duration: {comp['sessionDuration']} min")
            print(f"    Sessions/week: {comp['sessionsPerWeek']}")
            print(f"    Total/week: {comp['totalWeeklyMinutes']} min")
            print(f"    Room: {comp['mustBeInRoomType']}")
            print(f"    Block size: {comp['blockSizeSlots']} slot(s)")
            print(f"    Contiguous: {comp['mustBeContiguous']}")
            print()
        
        # Validate
        errors = expander.validate_components(components)
        if errors:
            print("  ✗ Validation errors:")
            for error in errors:
                print(f"    - {error}")
        else:
            print("  ✓ Components validated successfully")
        
        print("-" * 50)
        print()


if __name__ == "__main__":
    main()
