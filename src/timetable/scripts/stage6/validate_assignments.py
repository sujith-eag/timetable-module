#!/usr/bin/env python3
"""
Stage 6: Assignment Validation Script

This script validates the assignments in a final timetable against the
foundational rules defined in Stage 1. It specifically checks if any faculty
member is assigned to teach a subject they are not authorized for according
to facultyBasic.json.
"""

import json
import sys
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import datetime

class AssignmentValidator:
    """Validates timetable assignments against Stage 1 rules."""

    def __init__(self, timetable_path: Path):
        """
        Initializes the validator by loading necessary data files.
        """
        self.timetable_path = timetable_path
        self.base_dir = timetable_path.parent.parent
        
        print("📂 Loading data files...")
        self.timetable_data = self._load_json(self.timetable_path)
        self.faculty_basic = self._load_json(self.base_dir / "stage_1/facultyBasic.json")
        
        # Intelligently find the session list
        session_keys = ['timetable_A', 'timetable', 'sessions']
        self.sessions = []
        for key in session_keys:
            if key in self.timetable_data:
                self.sessions = self.timetable_data[key]
                print(f"   ✓ Found session data under key: '{key}'")
                break
        
        if not self.sessions:
            print(f"❌ FATAL: Could not find session data in {self.timetable_path.name}")
            sys.exit(1)
            
        self.faculty_rules = self._build_faculty_rules()
        print("   ✓ Built faculty assignment rules map.")

    def _load_json(self, path: Path) -> dict:
        """Loads a JSON file."""
        if not path.exists():
            print(f"❌ FATAL: File not found at {path}")
            sys.exit(1)
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _build_faculty_rules(self) -> dict:
        """
        Builds a map of faculty IDs to a set of their allowed subject codes.
        """
        rules = defaultdict(set)
        for faculty in self.faculty_basic['faculty']:
            fac_id = faculty['facultyId']
            
            # Handle assigned subjects
            for subj in faculty.get('assignedSubjects', []):
                if isinstance(subj, str):
                    rules[fac_id].add(subj)
                elif isinstance(subj, dict):
                    # It's a dict like {"24MCA31": ["A"]}, key is the subject code
                    subject_code = list(subj.keys())[0]
                    rules[fac_id].add(subject_code)
            
            # Handle supporting subjects
            for subj in faculty.get('supportingSubjects', []):
                if isinstance(subj, str):
                    rules[fac_id].add(subj)
                elif isinstance(subj, dict):
                    subject_code = list(subj.keys())[0]
                    rules[fac_id].add(subject_code)
        return rules

    def validate(self) -> str:
        """
        Runs the validation check and returns a formatted Markdown report.
        """
        print("⚙️ Validating faculty-subject assignments...")
        mismatches = []

        for session in self.sessions:
            fac_id = session.get('facultyId')
            subject_code = session.get('subjectCode')

            # Skip special, non-personnel assignments
            if fac_id in ['ALL_FACULTY', 'EXTERNAL']:
                continue

            if not fac_id or not subject_code:
                continue

            allowed_subjects = self.faculty_rules.get(fac_id)
            if allowed_subjects is None:
                mismatches.append(
                    f"**Faculty Not Found:** Faculty ID `{fac_id}` from session `{session['sessionId']}` does not exist in `facultyBasic.json`."
                )
                continue

            if subject_code not in allowed_subjects:
                mismatches.append(
                    f"**Invalid Assignment:** Faculty `{fac_id}` is assigned to subject `{subject_code}` in session `{session['sessionId']}`, but is not authorized to teach it in `facultyBasic.json`."
                )
        
        print(f"   ✓ Validation complete. Found {len(mismatches)} mismatches.")
        return self._generate_report(mismatches)

    def _generate_report(self, mismatches: list) -> str:
        """Formats the list of mismatches into a Markdown report."""
        report_parts = ["# Assignment Validation Report"]
        report_parts.append(f"> Validated against: `{self.timetable_path.name}`")
        report_parts.append(f"> Generated on: {datetime.now().isoformat()}\n")

        report_parts.append("## 📋 Summary")
        if not mismatches:
            report_parts.append("✅ **No assignment mismatches found.** All faculty assignments in the timetable are consistent with the rules in `facultyBasic.json`.")
        else:
            report_parts.append(f"❌ **Found {len(mismatches)} assignment mismatches!** The following sessions are invalid:")
        
        if mismatches:
            report_parts.append("\n### Mismatch Details")
            for issue in mismatches:
                report_parts.append(f"- {issue}")
        
        return "\n".join(report_parts)

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Validate timetable assignments against Stage 1 rules.")
    parser.add_argument(
        "timetable_file",
        type=Path,
        help="Path to the enriched timetable JSON file (e.g., ../timetable_enriched.json)"
    )
    args = parser.parse_args()

    try:
        validator = AssignmentValidator(args.timetable_file)
        report_content = validator.validate()
        
        output_dir = Path(__file__).parent.parent / "reports"
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / "assignment_validation_report.md"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
            
        print(f"\n✅ Validation report successfully generated at: {output_path}")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
