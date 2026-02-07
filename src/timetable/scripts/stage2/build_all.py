#!/usr/bin/env python3
"""
Build All Stage 2 Data

Master script that builds all Stage 2 data files in the correct sequence:
1. Build subjects2Full.json (with components)
2. Build faculty2Full.json (with workload)
3. Validate all generated data

Usage:
    python3 build_all.py
    python3 build_all.py --validate-only
"""

import sys
import argparse
from pathlib import Path

# Import individual build modules
import build_subjects_full
import build_faculty_full
import validate_stage2


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description="Build all Stage 2 data files"
    )
    parser.add_argument(
        '--validate-only',
        action='store_true',
        help="Only run validation without rebuilding"
    )
    parser.add_argument(
        '--skip-validation',
        action='store_true',
        help="Skip validation after building"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("STAGE 2 BUILD PIPELINE")
    print("=" * 60)
    print()
    
    exit_code = 0
    
    if not args.validate_only:
        # Step 1: Build subjects
        print("Step 1/2: Building subjects2Full.json...")
        print("-" * 60)
        result = build_subjects_full.main()
        if result != 0:
            print("✗ Failed to build subjects2Full.json")
            return 1
        print()
        
        # Step 2: Build faculty
        print("Step 2/2: Building faculty2Full.json...")
        print("-" * 60)
        result = build_faculty_full.main()
        if result != 0:
            print("✗ Failed to build faculty2Full.json")
            return 1
        print()
    
    if not args.skip_validation:
        # Step 3: Validate
        print("Validation: Checking generated data...")
        print("-" * 60)
        result = validate_stage2.main()
        if result != 0:
            print("✗ Validation failed")
            exit_code = 1
        else:
            print("✓ Validation passed")
        print()
    
    # Final summary
    print("=" * 60)
    if exit_code == 0:
        print("✓ STAGE 2 BUILD COMPLETE")
        print()
        print("Generated files:")
        script_dir = Path(__file__).parent
        stage2_dir = script_dir.parent
        
        files = [
            "subjects2Full.json",
            "faculty2Full.json",
            "subjects_build_report.txt",
            "faculty_build_report.txt"
        ]
        
        for filename in files:
            filepath = stage2_dir / filename
            if filepath.exists():
                size = filepath.stat().st_size
                print(f"  - {filename} ({size:,} bytes)")
    else:
        print("✗ STAGE 2 BUILD FAILED")
        print()
        print("Please check the errors above and retry.")
    
    print("=" * 60)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
