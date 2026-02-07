"""
Build Faculty Full - Generate faculty2Full.json

This script generates the complete faculty file for Stage 2 by:
1. Loading faculty from Stage 1
2. Loading subjects from Stage 2 (subjects2Full.json)
3. Parsing assignments and calculating workload
4. Saving to faculty2Full.json
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

from data_loader import Stage1DataLoader
from calculate_workload import WorkloadCalculator


class FacultyFullBuilder:
    """Builds the complete faculty2Full.json file"""
    
    def __init__(self, stage1_dir: str = None, stage2_dir: str = None):
        """
        Initialize the builder
        
        Args:
            stage1_dir: Path to stage_1 directory
            stage2_dir: Path to stage_2 directory
        """
        self.loader = Stage1DataLoader(stage1_dir)
        
        if stage2_dir is None:
            script_dir = Path(__file__).parent
            self.stage2_dir = script_dir.parent
        else:
            self.stage2_dir = Path(stage2_dir)
        
        # Load subjects2Full.json
        subjects_full_path = self.stage2_dir / "subjects2Full.json"
        with open(subjects_full_path, 'r', encoding='utf-8') as f:
            subjects_data = json.load(f)
        
        self.subjects_full = subjects_data.get('subjects', [])
        self.calculator = WorkloadCalculator(self.subjects_full)
        
        # Load student groups for assignment parsing
        self.student_groups_data = self.loader.load_student_groups()
    
    def build_faculty_full(self, faculty: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build a complete faculty entry with assignments and workload
        
        Args:
            faculty: Basic faculty dict from Stage 1
            
        Returns:
            Complete faculty dict
        """
        faculty_full = {
            'facultyId': faculty['facultyId'],
            'name': faculty['name'],
            'designation': faculty.get('designation', ''),
            'department': 'MCA'  # Default for now
        }
        
        # Parse primary assignments
        assigned_subjects = faculty.get('assignedSubjects', [])
        primary_assignments = self.calculator.parse_assigned_subjects(
            assigned_subjects,
            self.student_groups_data
        )
        
        faculty_full['primaryAssignments'] = primary_assignments
        
        # Parse supporting assignments
        supporting_subjects = faculty.get('supportingSubjects', [])
        supporting_assignments = []
        
        for subject_code in supporting_subjects:
            # Get subject details
            subject = self.calculator.subjects_map.get(subject_code)
            if subject:
                supporting_assignments.append({
                    'subjectCode': subject_code,
                    'semester': subject.get('semester'),
                    'role': 'supporting'
                })
        
        faculty_full['supportingAssignments'] = supporting_assignments
        
        # Calculate workload stats
        workload_stats = self.calculator.calculate_workload_stats(primary_assignments)
        faculty_full['workloadStats'] = workload_stats
        
        return faculty_full
    
    def build_all_faculty(self) -> List[Dict[str, Any]]:
        """
        Build all faculty with complete data
        
        Returns:
            List of complete faculty dicts
        """
        faculty_list = self.loader.load_faculty_basic()
        faculty_full_list = []
        
        for faculty in faculty_list:
            faculty_full = self.build_faculty_full(faculty)
            faculty_full_list.append(faculty_full)
        
        return faculty_full_list
    
    def save_faculty_full(self, faculty: List[Dict[str, Any]], filename: str = "faculty2Full.json"):
        """
        Save faculty to JSON file
        
        Args:
            faculty: List of complete faculty dicts
            filename: Output filename
        """
        output_path = self.stage2_dir / filename
        
        output_data = {
            "faculty": faculty
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    def generate_report(self, faculty: List[Dict[str, Any]]) -> str:
        """
        Generate a summary report
        
        Args:
            faculty: List of complete faculty dicts
            
        Returns:
            Report string
        """
        lines = []
        lines.append("=" * 60)
        lines.append("FACULTY FULL BUILD REPORT")
        lines.append("=" * 60)
        lines.append("")
        
        lines.append(f"Total faculty: {len(faculty)}")
        lines.append("")
        
        # Calculate aggregates
        total_hours = sum(f['workloadStats']['totalWeeklyHours'] for f in faculty)
        avg_hours = total_hours / len(faculty) if faculty else 0
        
        lines.append(f"Total teaching hours: {total_hours:.1f}h/week")
        lines.append(f"Average per faculty: {avg_hours:.1f}h/week")
        lines.append("")
        
        # Faculty details
        lines.append("Faculty Details:")
        lines.append("-" * 60)
        
        for fac in faculty:
            lines.append(f"- {fac['name']} ({fac['facultyId']})")
            lines.append(f"  Designation: {fac.get('designation', 'N/A')}")
            
            # Primary assignments
            primary = fac.get('primaryAssignments', [])
            lines.append(f"  Primary Assignments: {len(primary)}")
            
            for asn in primary:
                sections_str = ', '.join(asn['sections']) if asn['sections'] else 'N/A'
                comp_types_str = ', '.join(asn['componentTypes'])
                student_groups_str = ', '.join(asn.get('studentGroupIds', [])) if asn.get('studentGroupIds') else 'N/A'
                
                lines.append(f"    - {asn['subjectCode']} (Sem {asn.get('semester', 'N/A')})")
                lines.append(f"      Sections: {sections_str}")
                lines.append(f"      Student Groups: {student_groups_str}")
                lines.append(f"      Components: {comp_types_str}")
                lines.append(f"      Hours: {asn['totalWeeklyHours']:.1f}h, Sessions: {asn['totalSessionsPerWeek']}")
            
            # Supporting assignments
            supporting = fac.get('supportingAssignments', [])
            if supporting:
                lines.append(f"  Supporting Assignments: {len(supporting)}")
                for asn in supporting:
                    lines.append(f"    - {asn['subjectCode']} (Sem {asn.get('semester', 'N/A')})")
            
            # Workload stats
            stats = fac.get('workloadStats', {})
            lines.append(f"  Workload:")
            lines.append(f"    Theory: {stats.get('theoryHours', 0)}h")
            lines.append(f"    Tutorial: {stats.get('tutorialHours', 0)}h")
            lines.append(f"    Practical: {stats.get('practicalHours', 0)}h")
            lines.append(f"    Total: {stats.get('totalWeeklyHours', 0)}h/week")
            lines.append(f"    Sessions: {stats.get('totalSessions', 0)}/week")
            lines.append("")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)


def main():
    """Main execution"""
    print("Building faculty2Full.json...")
    print()
    
    try:
        # Check if subjects2Full.json exists
        script_dir = Path(__file__).parent
        subjects_path = script_dir.parent / "subjects2Full.json"
        
        if not subjects_path.exists():
            print("✗ Error: subjects2Full.json not found!")
            print("  Run build_subjects_full.py first.")
            return 1
        
        # Build faculty
        builder = FacultyFullBuilder()
        faculty_full = builder.build_all_faculty()
        
        # Save to file
        output_path = builder.save_faculty_full(faculty_full)
        print(f"✓ Saved to: {output_path}")
        print()
        
        # Generate and display report
        report = builder.generate_report(faculty_full)
        print(report)
        
        # Also save report to file
        report_path = builder.stage2_dir / "faculty_build_report.txt"
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
