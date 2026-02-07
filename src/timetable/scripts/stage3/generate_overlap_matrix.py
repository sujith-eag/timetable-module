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
from typing import Dict, List, Set, Any
from data_loader_stage2 import DataLoaderStage2


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
        
        # Check if they have the same parent (same section, same elective category)
        parent_of_1 = self._get_parent(group1)
        parent_of_2 = self._get_parent(group2)
        if parent_of_1 and parent_of_2 and parent_of_1 == parent_of_2:
            # Same parent AND same elective category means overlap
            # (but we already checked different categories above)
            return True
        
        # Check if either group is a mixed group (has multiple parents)
        parents_of_1 = self._get_parents(group1)
        parents_of_2 = self._get_parents(group2)
        
        # If group1 is mixed (SS) and group2 is any of its parents
        if len(parents_of_1) > 1:
            if group2 in parents_of_1:
                return True
            # Check if group2 is a child of any of group1's parents
            # BUT only if they're from the SAME elective category or group2 is not an elective
            for parent in parents_of_1:
                if group2 in self._get_children(parent):
                    # group2 is a sibling - check if same elective category
                    if not cat2 or cat1 == cat2:
                        return True
        
        # If group2 is mixed (SS) and group1 is any of its parents
        if len(parents_of_2) > 1:
            if group1 in parents_of_2:
                return True
            # Check if group1 is a child of any of group2's parents
            # BUT only if they're from the SAME elective category or group1 is not an elective
            for parent in parents_of_2:
                if group1 in self._get_children(parent):
                    # group1 is a sibling - check if same elective category
                    if not cat1 or cat1 == cat2:
                        return True
        
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
        
        # Check specific cases for different sections
        # MCA_SEM3_A can run parallel with MCA_SEM3_B
        if (group1, group2) in [("MCA_SEM3_A", "MCA_SEM3_B"), ("MCA_SEM3_B", "MCA_SEM3_A")]:
            return True
        
        # ELEC_AD_A1 can run parallel with ELEC_AD_B1 (different sections, same category)
        if (group1, group2) in [("ELEC_AD_A1", "ELEC_AD_B1"), ("ELEC_AD_B1", "ELEC_AD_A1")]:
            return True
        
        # AD and SS are disjoint categories - can run in parallel
        cat1 = self._get_elective_category(group1)
        cat2 = self._get_elective_category(group2)
        if cat1 and cat2 and cat1 != cat2:
            # Different elective categories = can run parallel
            return True
        
        # Same logic for Sem 1
        if (group1, group2) in [("MCA_SEM1_A", "MCA_SEM1_B"), ("MCA_SEM1_B", "MCA_SEM1_A")]:
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


def main():
    """Generate the overlap constraint matrix."""
    print("Generating Student Group Overlap Constraint Matrix")
    print("=" * 80)
    
    # Load data
    print("\n1. Loading data...")
    loader = DataLoaderStage2()
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
