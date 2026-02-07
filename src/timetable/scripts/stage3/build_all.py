#!/usr/bin/env python3
"""
Master script to generate all Stage 3 outputs, statistics, and reports.
Run this after any changes to teaching assignments.
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

SCRIPTS_DIR = Path(__file__).parent

def run_script(script_name, description):
    """Run a Python script and report results."""
    print(f"\n{'='*70}")
    print(f"🔄 {description}")
    print(f"{'='*70}")
    
    script_path = SCRIPTS_DIR / script_name
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=SCRIPTS_DIR,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print(result.stdout)
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(result.stdout)
            print(result.stderr)
            print(f"❌ {description} failed with exit code {result.returncode}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"❌ {description} timed out (>60s)")
        return False
    except Exception as e:
        print(f"❌ {description} failed: {e}")
        return False

def main():
    print("=" * 70)
    print("🚀 STAGE 3 - COMPREHENSIVE GENERATION")
    print("=" * 70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    tasks = [
        ("generate_overlap_matrix.py", "Generating student group overlap matrix"),
        ("build_assignments_sem3.py", "Building Semester 3 teaching assignments"),
        ("build_assignments_sem1.py", "Building Semester 1 teaching assignments"),
        ("validate_stage3.py", "Validating all teaching assignments"),
        ("generate_statistics.py", "Generating comprehensive statistics"),
        ("generate_reports.py", "Generating detailed reports")
    ]
    
    results = []
    for script, description in tasks:
        success = run_script(script, description)
        results.append((description, success))
    
    # Final summary
    print("\n" + "=" * 70)
    print("📊 EXECUTION SUMMARY")
    print("=" * 70)
    
    all_success = all(success for _, success in results)
    
    for description, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {description}")
    
    print("\n" + "=" * 70)
    
    if all_success:
        print("✅ ALL TASKS COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("\n📂 Generated Files:")
        print("   • stage_3/studentGroupOverlapConstraints.json")
        print("   • stage_3/teachingAssignments_sem3.json")
        print("   • stage_3/teachingAssignments_sem1.json")
        print("   • stage_3/statistics.json")
        print("   • stage_3/reports/summary.md")
        print("   • stage_3/reports/faculty_assignments.md")
        print("   • stage_3/reports/subject_coverage.md")
        print("   • stage_3/reports/student_groups.md")
        print("   • stage_3/reports/resource_requirements.md")
        print("\n🎉 Stage 3 is complete and ready for Stage 4!")
        return 0
    else:
        print("❌ SOME TASKS FAILED")
        print("=" * 70)
        print("\nPlease check the error messages above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
