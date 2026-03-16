"""
Generate Student Group Overlap Constraint Matrix
================================================

This script generates the global constraint matrix for student group overlaps
based on the parent-child hierarchy defined in studentGroups.json.

The matrix defines which student groups CANNOT overlap (have scheduling conflicts)
and which groups CAN run in parallel.

Rules:
1. Same group cannot overlap with itself
2. Parent groups cannot overlap with their child groups
3. Groups with shared students cannot overlap
4. Mixed groups (SS) cannot overlap with ANY semester 3 group

Author: Stage 3 Implementation
Date: October 26, 2025
"""

import json
from pathlib import Path
from typing import Dict, List, Set, Any, Optional
from timetable.scripts.stage3.data_loader_stage2 import DataLoaderStage2


class OverlapMatrixGenerator:
    """Generates student group overlap constraint matrix."""
    
    def __init__(self, loader: DataLoaderStage2):
        """
        Initialize the generator.
        
        Args:
            loader: DataLoaderStage2 instance with loaded data
        """
        self.loader = loader
        self.hierarchy = loader.get_student_group_hierarchy()
        self.regular_groups = loader.get_regular_student_groups()
        self.elective_groups = loader.get_elective_student_groups()
        
        # Build list of all group IDs
        self.all_group_ids = self._get_all_group_ids()
    
    def _get_all_group_ids(self) -> List[str]:
        """Get list of all student group IDs."""
        group_ids = []
        
        # Regular groups
        for group in self.regular_groups:
            group_ids.append(group["studentGroupId"])
        
        # Elective groups
        for group in self.elective_groups:
            group_ids.append(group["studentGroupId"])
        
        return group_ids
    
    def _get_children(self, group_id: str) -> List[str]:
        """Get children of a group from hierarchy."""
        if group_id in self.hierarchy:
            return self.hierarchy[group_id].get("children", [])
        return []
    
    def _get_parent(self, group_id: str) -> str:
        """Get parent of a group from hierarchy."""
        if group_id in self.hierarchy:
            parent = self.hierarchy[group_id].get("parent")
            if parent:
                return parent
        return None
    
    def _get_parents(self, group_id: str) -> List[str]:
        """Get all parents of a group (for mixed groups with multiple parents)."""
        if group_id in self.hierarchy:
            # Check for single parent
            if "parent" in self.hierarchy[group_id]:
                return [self.hierarchy[group_id]["parent"]]
            # Check for multiple parents
            if "parents" in self.hierarchy[group_id]:
                return self.hierarchy[group_id]["parents"]
        return []
    
    def _get_elective_category(self, group_id: str) -> str:
        """
        Get the elective category for a group (AD or SS).
        
        Args:
            group_id: Student group ID
            
        Returns:
            'AD' if Advanced Development, 'SS' if Systems & Security, None otherwise
        """
        if "ELEC_AD" in group_id:
            return "AD"
        elif "ELEC_SS" in group_id:
            return "SS"
        return None
    
    def _shares_students_with(self, group1: str, group2: str) -> bool:
        """
        Check if two groups share students.
        
        CRITICAL: AD and SS electives are DISJOINT sets - students take EITHER AD OR SS, not both!
        
        Args:
            group1: First group ID
            group2: Second group ID
            
        Returns:
            True if groups share students, False otherwise
        """
        # Same group
        if group1 == group2:
            return True
        
        # Check if they're from different elective categories (AD vs SS)
        # AD and SS are disjoint - a student cannot be in both
        cat1 = self._get_elective_category(group1)
        cat2 = self._get_elective_category(group2)
        if cat1 and cat2 and cat1 != cat2:
            # Different elective categories = disjoint sets
            return False
        
        # Check if group1 is parent of group2
        children_of_1 = self._get_children(group1)
        if group2 in children_of_1:
            return True
        
        # Check if group2 is parent of group1
        children_of_2 = self._get_children(group2)
        if group1 in children_of_2:
            return True
        
        # Check if they have the same single parent (same section, same elective category)
        parent_of_1 = self._get_parent(group1)
        parent_of_2 = self._get_parent(group2)
        if parent_of_1 and parent_of_2 and parent_of_1 == parent_of_2:
            # Same single parent means overlap
            return True
        
        # Check if either group is a mixed group (has multiple parents)
        parents_of_1 = self._get_parents(group1)
        parents_of_2 = self._get_parents(group2)
        
        # If both groups have multiple parents (mixed groups)
        if len(parents_of_1) > 1 and len(parents_of_2) > 1:
            # Check if they have the same set of parents (this would indicate they're the same group)
            if set(parents_of_1) == set(parents_of_2):
                # Same parents - they could share students unless they're different elective categories
                # Check if they're different elective groups (same semester, different elective)
                # If they're siblings in the elective hierarchy, they don't share
                # This is handled by returning False - they partition the same parent set
                return False
            # Different parent sets = different groups = don't share
            return False
        
        # If only group1 is mixed and group2 is a child of any of group1's parents
        if len(parents_of_1) > 1:
            if group2 in parents_of_1:
                return True
            # Check if group2 is a child of any of group1's parents
            for parent in parents_of_1:
                if group2 in self._get_children(parent):
                    # group2 is a sibling of group1 - they share the parent but may partition students
                    # If they're both electives, they don't share (they partition the parent)
                    if not (cat1 and cat2) and not cat2:
                        # Not electives or cat2 is None: return True (sharing)
                        return True
                    # Both are electives: they partition, so don't share
                    return False
            return False
        
        # If only group2 is mixed and group1 is a child of any of group2's parents
        if len(parents_of_2) > 1:
            if group1 in parents_of_2:
                return True
            # Check if group1 is a child of any of group2's parents
            for parent in parents_of_2:
                if group1 in self._get_children(parent):
                    # group1 is a sibling of group2 - they share the parent but may partition students
                    # If they're both electives, they don't share (they partition the parent)
                    if not (cat1 and cat2) and not cat1:
                        # Not electives or cat1 is None: return True (sharing)
                        return True
                    # Both are electives: they partition, so don't share
                    return False
            return False
        
        return False
    
    def _can_run_parallel(self, group1: str, group2: str) -> bool:
        """
        Check if two groups can run in parallel (no student overlap).
        
        Args:
            group1: First group ID
            group2: Second group ID
            
        Returns:
            True if groups can run in parallel, False otherwise
        """
        # Cannot run parallel if they share students
        if self._shares_students_with(group1, group2):
            return False
        
        # If they don't share students, they CAN run in parallel
        # unless there are specific constraints
        
        # Extract semester numbers from group IDs dynamically
        # Pattern: MCA_SEM{N}_{SECTION} or MCA_SEM{N}_ALL
        def extract_sem_and_section(group_id: str):
            """Extract semester number and section from group ID."""
            # Pattern: MCA_SEM2_A -> (2, 'A')
            parts = group_id.split('_')
            if len(parts) >= 3 and parts[1].startswith('SEM'):
                try:
                    sem = int(parts[1][3:])  # Extract number from "SEM2"
                    section = '_'.join(parts[2:])  # Handle ALL or letters
                    return sem, section
                except ValueError:
                    return None, None
            return None, None
        
        sem1, sec1 = extract_sem_and_section(group1)
        sem2, sec2 = extract_sem_and_section(group2)
        
        # Core groups from same semester but different sections can run parallel
        # (e.g., MCA_SEM2_A can run parallel with MCA_SEM2_B)
        if (sem1 is not None and sem2 is not None and 
            sem1 == sem2 and  # Same semester
            sec1 != sec2 and  # Different sections
            sec1 not in ['ALL'] and sec2 not in ['ALL']):  # Not global sections
            return True
        
        # AD and SS elective categories are disjoint sets - can run in parallel
        cat1 = self._get_elective_category(group1)
        cat2 = self._get_elective_category(group2)
        if cat1 and cat2 and cat1 != cat2:
            # Different elective categories = can run parallel
            return True
        
        # Elective groups that don't share students can run parallel
        # (e.g., ELEC_AI_G1 and ELEC_CS_G1 partition students, so they can run in parallel)
        if 'ELEC' in group1 and 'ELEC' in group2:
            # Both are elective groups and don't share students (checked above)
            return True
        
        return False
    
    def generate_matrix(self) -> Dict[str, Any]:
        """
        Generate the complete overlap constraint matrix.
        
        Returns:
            Dictionary with cannotOverlapWith and canRunParallelWith mappings
        """
        cannot_overlap = {}
        can_run_parallel = {}
        
        for group_id in self.all_group_ids:
            # Find all groups that cannot overlap
            conflicts = []
            parallel = []
            
            for other_id in self.all_group_ids:
                if self._shares_students_with(group_id, other_id):
                    conflicts.append(other_id)
                elif self._can_run_parallel(group_id, other_id):
                    parallel.append(other_id)
            
            cannot_overlap[group_id] = sorted(conflicts)
            can_run_parallel[group_id] = sorted(parallel)
        
        return {
            "cannotOverlapWith": cannot_overlap,
            "canRunParallelWith": can_run_parallel
        }
    
    def save_matrix(self, output_path: Path):
        """
        Generate and save the constraint matrix to a JSON file.
        
        Args:
            output_path: Path to save the JSON file
        """
        matrix = self.generate_matrix()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(matrix, f, indent=2)
        
        print(f"✓ Saved constraint matrix to: {output_path}")
        return matrix
    
    def print_matrix_summary(self, matrix: Dict[str, Any]):
        """Print a summary of the constraint matrix."""
        print("\nConstraint Matrix Summary")
        print("=" * 80)
        
        print("\nCannot Overlap With:")
        print("-" * 80)
        for group_id, conflicts in matrix["cannotOverlapWith"].items():
            print(f"  {group_id:15} ⊗ {', '.join(conflicts)}")
        
        print("\nCan Run Parallel With:")
        print("-" * 80)
        for group_id, parallel in matrix["canRunParallelWith"].items():
            if parallel:
                print(f"  {group_id:15} ✓ {', '.join(parallel)}")
            else:
                print(f"  {group_id:15} ✓ (none)")
        
        print("\n" + "=" * 80)


def main(data_dir=None):
    """Generate the overlap constraint matrix."""
    import argparse
    
    if data_dir is None:
        parser = argparse.ArgumentParser(description="Generate student group overlap constraint matrix")
        parser.add_argument("--data-dir", required=True, help="Data directory path")
        args = parser.parse_args()
        data_dir = args.data_dir
    
    print("Generating Student Group Overlap Constraint Matrix")
    print("=" * 80)
    print(f"Data directory: {data_dir}")
    print()
    
    # Load data
    print("\n1. Loading data...")
    loader = DataLoaderStage2(data_dir)
    loader.load_all()
    print("   ✓ Data loaded successfully")
    
    # Generate matrix
    print("\n2. Generating constraint matrix...")
    generator = OverlapMatrixGenerator(loader)
    
    # Determine output path
    output_path = loader.base_path / "stage_3" / "studentGroupOverlapConstraints.json"
    
    # Save matrix
    print("\n3. Saving matrix...")
    matrix = generator.save_matrix(output_path)
    
    # Print summary
    print("\n4. Matrix Summary:")
    generator.print_matrix_summary(matrix)
    
    # Validation
    print("\n5. Validation:")
    print("-" * 80)
    total_groups = len(matrix["cannotOverlapWith"])
    print(f"   ✓ Total student groups: {total_groups}")
    
    # Check specific rules
    print("\n   Checking specific rules:")
    
    # Rule 1: Self-conflict
    all_self_conflict = all(
        group_id in conflicts 
        for group_id, conflicts in matrix["cannotOverlapWith"].items()
    )
    print(f"   {'✓' if all_self_conflict else '✗'} All groups conflict with themselves")
    
    # Rule 2: Parent-child conflicts
    if "MCA_SEM3_A" in matrix["cannotOverlapWith"]:
        conflicts_a = matrix["cannotOverlapWith"]["MCA_SEM3_A"]
        has_children = "ELEC_AD_A1" in conflicts_a and "ELEC_SS_G1" in conflicts_a
        print(f"   {'✓' if has_children else '✗'} MCA_SEM3_A conflicts with its children")
    
    # Rule 3: Cross-section parallel
    if "ELEC_AD_A1" in matrix["canRunParallelWith"]:
        parallel_ad = matrix["canRunParallelWith"]["ELEC_AD_A1"]
        can_parallel = "ELEC_AD_B1" in parallel_ad
        print(f"   {'✓' if can_parallel else '✗'} AD electives from different sections can run parallel")
    
    # Rule 4: SS mixed group conflicts with all
    if "ELEC_SS_G1" in matrix["cannotOverlapWith"]:
        ss_conflicts = matrix["cannotOverlapWith"]["ELEC_SS_G1"]
        conflicts_all = len(ss_conflicts) == total_groups
        print(f"   {'✓' if conflicts_all else '✗'} SS mixed group conflicts with all groups")
    
    print("\n" + "=" * 80)
    print("✓ Matrix generation complete!")


if __name__ == "__main__":
    main()
