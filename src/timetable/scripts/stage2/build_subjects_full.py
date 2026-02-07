"""
Build Subjects Full - Generate subjects2Full.json

This script generates the complete subjects file for Stage 2 by:
1. Loading all Stage 1 subject files
2. Expanding credit patterns into components
3. Keeping all original fields
4. Saving to subjects2Full.json
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

from data_loader import Stage1DataLoader
from expand_components import ComponentExpander


class SubjectsFullBuilder:
    """Builds the complete subjects2Full.json file"""
    
    def __init__(self, stage1_dir: str = None, stage2_dir: str = None):
        """
        Initialize the builder
        
        Args:
            stage1_dir: Path to stage_1 directory
            stage2_dir: Path to stage_2 directory for output
        """
        self.loader = Stage1DataLoader(stage1_dir)
        
        if stage2_dir is None:
            script_dir = Path(__file__).parent
            self.stage2_dir = script_dir.parent
        else:
            self.stage2_dir = Path(stage2_dir)
        
        # Load config for component expansion
        config = self.loader.load_config()
        self.expander = ComponentExpander(config)
    
    def build_subject_full(self, subject: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a complete subject entry with components
        
        Args:
            subject: Basic subject dict from Stage 1
            
        Returns:
            Complete subject dict with components
        """
        # Start with all original fields
        subject_full = subject.copy()
        
        # Skip subjects without subjectCode (like some diff subjects)
        if 'subjectCode' not in subject:
            return subject_full
        
        # Check if components already exist (diff subjects)
        if 'components' not in subject:
            # Expand credit pattern into components
            components = self.expander.expand_components(subject)
            subject_full['components'] = components
        else:
            # Components exist, but may need enrichment
            components = []
            for comp in subject['components']:
                enriched_comp = self._enrich_component(comp, subject['subjectCode'])
                components.append(enriched_comp)
            subject_full['components'] = components
        
        return subject_full
    
    def _enrich_component(self, component: Dict[str, Any], subject_code: str) -> Dict[str, Any]:
        """
        Enrich a manually-defined component with missing fields
        
        Args:
            component: Component dict (may be incomplete)
            subject_code: Subject code for generating componentId
            
        Returns:
            Complete component dict
        """
        enriched = component.copy()
        
        # Generate componentId if missing
        if 'componentId' not in enriched:
            comp_type = enriched.get('componentType', 'unknown')
            suffix_map = {'theory': 'TH', 'tutorial': 'TU', 'practical': 'PR'}
            suffix = suffix_map.get(comp_type, 'XX')
            enriched['componentId'] = f"{subject_code}_{suffix}"
        
        # Calculate totalWeeklyMinutes if missing
        if 'totalWeeklyMinutes' not in enriched:
            sessions = enriched.get('sessionsPerWeek', 0)
            duration = enriched.get('sessionDuration', 0)
            enriched['totalWeeklyMinutes'] = sessions * duration
        
        return enriched
    
    def build_all_subjects(self) -> List[Dict[str, Any]]:
        """
        Build all subjects with components
        
        Returns:
            List of complete subject dicts
        """
        subjects = self.loader.load_all_subjects()
        subjects_full = []
        
        for subject in subjects:
            subject_full = self.build_subject_full(subject)
            subjects_full.append(subject_full)
        
        return subjects_full
    
    def save_subjects_full(self, subjects: List[Dict[str, Any]], filename: str = "subjects2Full.json"):
        """
        Save subjects to JSON file
        
        Args:
            subjects: List of complete subject dicts
            filename: Output filename
        """
        output_path = self.stage2_dir / filename
        
        output_data = {
            "subjects": subjects
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    def generate_report(self, subjects: List[Dict[str, Any]]) -> str:
        """
        Generate a summary report
        
        Args:
            subjects: List of complete subject dicts
            
        Returns:
            Report string
        """
        lines = []
        lines.append("=" * 60)
        lines.append("SUBJECTS FULL BUILD REPORT")
        lines.append("=" * 60)
        lines.append("")
        
        # Count subjects by type
        core_count = sum(1 for s in subjects if s.get('type') == 'core')
        elective_count = sum(1 for s in subjects if s.get('type') == 'elective')
        diff_count = sum(1 for s in subjects if s.get('type') == 'diff')
        
        lines.append(f"Total subjects: {len(subjects)}")
        lines.append(f"  - Core: {core_count}")
        lines.append(f"  - Elective: {elective_count}")
        lines.append(f"  - Diff: {diff_count}")
        lines.append("")
        
        # Count components
        total_components = 0
        theory_count = 0
        tutorial_count = 0
        practical_count = 0
        
        for subject in subjects:
            components = subject.get('components', [])
            total_components += len(components)
            
            for comp in components:
                comp_type = comp.get('componentType')
                if comp_type == 'theory':
                    theory_count += 1
                elif comp_type == 'tutorial':
                    tutorial_count += 1
                elif comp_type == 'practical':
                    practical_count += 1
        
        lines.append(f"Total components: {total_components}")
        lines.append(f"  - Theory: {theory_count}")
        lines.append(f"  - Tutorial: {tutorial_count}")
        lines.append(f"  - Practical: {practical_count}")
        lines.append("")
        
        # Subject details
        lines.append("Subject Details:")
        lines.append("-" * 60)
        
        for subject in subjects:
            if 'subjectCode' not in subject:
                lines.append(f"- {subject.get('title', 'UNKNOWN')}")
                lines.append(f"  Type: {subject.get('type', 'N/A')}")
                lines.append(f"  Components: N/A (special subject)")
                lines.append("")
                continue
            
            code = subject['subjectCode']
            title = subject.get('title', 'N/A')
            pattern = subject.get('creditPattern', [])
            components = subject.get('components', [])
            
            lines.append(f"- {code}: {title}")
            lines.append(f"  Credit Pattern: {pattern}")
            lines.append(f"  Total Credits: {subject.get('totalCredits', 'N/A')}")
            lines.append(f"  Type: {subject.get('type', 'N/A')}")
            lines.append(f"  Components: {len(components)}")
            
            for comp in components:
                comp_id = comp.get('componentId')
                comp_type = comp.get('componentType')
                sessions = comp.get('sessionsPerWeek')
                duration = comp.get('sessionDuration')
                
                lines.append(f"    - {comp_id} ({comp_type}): {sessions} × {duration}min")
            
            lines.append("")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)


def main():
    """Main execution"""
    print("Building subjects2Full.json...")
    print()
    
    try:
        # Build subjects
        builder = SubjectsFullBuilder()
        subjects_full = builder.build_all_subjects()
        
        # Validate components
        errors = []
        for subject in subjects_full:
            components = subject.get('components', [])
            subject_errors = builder.expander.validate_components(components)
            if subject_errors:
                errors.extend(subject_errors)
        
        if errors:
            print("✗ Validation errors found:")
            for error in errors:
                print(f"  - {error}")
            print()
            return 1
        
        # Save to file
        output_path = builder.save_subjects_full(subjects_full)
        print(f"✓ Saved to: {output_path}")
        print()
        
        # Generate and display report
        report = builder.generate_report(subjects_full)
        print(report)
        
        # Also save report to file
        report_path = builder.stage2_dir / "subjects_build_report.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✓ Report saved to: {report_path}")
        
        return 0
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
