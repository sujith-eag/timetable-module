#!/usr/bin/env python3
"""
Generate comprehensive statistics from teaching assignments.
Analyzes workload distribution, resource requirements, and constraint patterns.
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Optional

def load_assignments(filepath):
    """Load teaching assignments from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def analyze_semester(data, semester_num):
    """Analyze assignments for a single semester."""
    assignments = data['assignments']
    
    stats = {
        'semester': semester_num,
        'totalAssignments': len(assignments),
        'totalSessions': sum(a['sessionsPerWeek'] for a in assignments),
        'totalHours': round(sum(a['sessionsPerWeek'] * a['sessionDuration'] / 60 for a in assignments), 2)
    }
    
    # By type
    by_type = defaultdict(lambda: {'count': 0, 'sessions': 0, 'hours': 0})
    for a in assignments:
        type_key = 'elective' if a['isElective'] else ('diff' if a['isDiffSubject'] else 'core')
        by_type[type_key]['count'] += 1
        by_type[type_key]['sessions'] += a['sessionsPerWeek']
        by_type[type_key]['hours'] += round(a['sessionsPerWeek'] * a['sessionDuration'] / 60, 2)
    stats['byType'] = dict(by_type)
    
    # By assignment type (primary vs supporting)
    by_assignment_type = {'primary': 0, 'supporting': 0}
    for a in assignments:
        assignment_type = a.get('assignmentType', 'primary')
        if assignment_type in by_assignment_type:
            by_assignment_type[assignment_type] += 1
    stats['byAssignmentType'] = by_assignment_type
    
    # By component
    by_component = defaultdict(lambda: {'count': 0, 'sessions': 0, 'hours': 0})
    for a in assignments:
        comp = a['componentType']
        by_component[comp]['count'] += 1
        by_component[comp]['sessions'] += a['sessionsPerWeek']
        by_component[comp]['hours'] += round(a['sessionsPerWeek'] * a['sessionDuration'] / 60, 2)
    stats['byComponent'] = dict(by_component)
    
    # By priority
    by_priority = defaultdict(lambda: {'count': 0, 'sessions': 0})
    for a in assignments:
        by_priority[a['priority']]['count'] += 1
        by_priority[a['priority']]['sessions'] += a['sessionsPerWeek']
    stats['byPriority'] = dict(by_priority)
    
    # By room type
    by_room = defaultdict(lambda: {'count': 0, 'sessions': 0})
    for a in assignments:
        by_room[a['requiresRoomType']]['count'] += 1
        by_room[a['requiresRoomType']]['sessions'] += a['sessionsPerWeek']
    stats['byRoomType'] = dict(by_room)
    
    # Faculty distribution
    faculty_load = defaultdict(lambda: {
        'assignments': 0,
        'sessions': 0,
        'hours': 0,
        'subjects': set(),
        'components': defaultdict(int)
    })
    
    for a in assignments:
        fid = a['facultyId']
        faculty_load[fid]['assignments'] += 1
        faculty_load[fid]['sessions'] += a['sessionsPerWeek']
        faculty_load[fid]['hours'] += round(a['sessionsPerWeek'] * a['sessionDuration'] / 60, 2)
        faculty_load[fid]['subjects'].add(a['subjectCode'])
        faculty_load[fid]['components'][a['componentType']] += 1
    
    # Convert sets to lists and defaultdict to dict for JSON
    faculty_stats = {}
    for fid, data in faculty_load.items():
        faculty_stats[fid] = {
            'facultyName': next((a['facultyName'] for a in assignments if a['facultyId'] == fid), ''),
            'assignments': data['assignments'],
            'sessions': data['sessions'],
            'hours': data['hours'],
            'subjects': sorted(list(data['subjects'])),
            'subjectCount': len(data['subjects']),
            'components': dict(data['components'])
        }
    stats['facultyDistribution'] = faculty_stats
    
    # Subject coverage
    subject_coverage = defaultdict(lambda: {
        'title': '',
        'faculty': set(),
        'components': [],
        'totalSessions': 0,
        'sections': set()
    })
    
    for a in assignments:
        scode = a['subjectCode']
        subject_coverage[scode]['title'] = a['subjectTitle']
        subject_coverage[scode]['faculty'].add(a['facultyId'])
        subject_coverage[scode]['components'].append(a['componentType'])
        subject_coverage[scode]['totalSessions'] += a['sessionsPerWeek']
        subject_coverage[scode]['sections'].update(a['sections'])
    
    subject_stats = {}
    for scode, data in subject_coverage.items():
        subject_stats[scode] = {
            'title': data['title'],
            'faculty': sorted(list(data['faculty'])),
            'facultyCount': len(data['faculty']),
            'components': data['components'],
            'componentCount': len(data['components']),
            'totalSessions': data['totalSessions'],
            'sections': sorted(list(data['sections']))
        }
    stats['subjectCoverage'] = subject_stats
    
    # Student group analysis
    student_groups = defaultdict(lambda: {
        'assignments': 0,
        'sessions': 0,
        'hours': 0,
        'subjects': set()
    })
    
    for a in assignments:
        for group in a['studentGroupIds']:
            student_groups[group]['assignments'] += 1
            student_groups[group]['sessions'] += a['sessionsPerWeek']
            student_groups[group]['hours'] += round(a['sessionsPerWeek'] * a['sessionDuration'] / 60, 2)
            student_groups[group]['subjects'].add(a['subjectCode'])
    
    group_stats = {}
    for group, data in student_groups.items():
        group_stats[group] = {
            'assignments': data['assignments'],
            'sessions': data['sessions'],
            'hours': data['hours'],
            'subjects': sorted(list(data['subjects'])),
            'subjectCount': len(data['subjects'])
        }
    stats['studentGroups'] = group_stats
    
    # Constraint analysis
    constraints = {
        'withStudentConflicts': 0,
        'withFacultyConflicts': 0,
        'withFixedTiming': 0,
        'withRoomAllocation': 0,
        'withRoomPreferences': 0,
        'withContiguousRequirement': 0
    }
    
    conflict_patterns = defaultdict(int)
    
    for a in assignments:
        c = a['constraints']
        if c['studentGroupConflicts']:
            constraints['withStudentConflicts'] += 1
            conflict_patterns[len(c['studentGroupConflicts'])] += 1
        if c['facultyConflicts']:
            constraints['withFacultyConflicts'] += 1
        if c['fixedDay'] or c['fixedSlot']:
            constraints['withFixedTiming'] += 1
        if c['mustBeInRoom']:
            constraints['withRoomAllocation'] += 1
        if a['preferredRooms']:
            constraints['withRoomPreferences'] += 1
        if a['requiresContiguous']:
            constraints['withContiguousRequirement'] += 1
    
    stats['constraints'] = constraints
    stats['conflictPatterns'] = dict(conflict_patterns)
    
    # Room requirements
    room_needs = {
        'uniqueRoomsNeeded': len(set(r for a in assignments for r in a['preferredRooms'])),
        'preAllocatedRooms': list(set(a['constraints']['mustBeInRoom'] for a in assignments if a['constraints']['mustBeInRoom'])),
        'preferredRoomsList': list(set(r for a in assignments for r in a['preferredRooms']))
    }
    stats['roomRequirements'] = room_needs
    
    return stats

def generate_combined_statistics(stats_dict, semesters):
    """Generate combined statistics across multiple semesters dynamically.
    
    Args:
        stats_dict: Dictionary mapping semester -> stats (e.g., {2: stat_obj, 4: stat_obj})
        semesters: List of semester numbers in order (e.g., [2, 4])
    """
    # Calculate totals
    combined = {
        'totalAssignments': sum(stats_dict[sem]['totalAssignments'] for sem in semesters),
        'totalSessions': sum(stats_dict[sem]['totalSessions'] for sem in semesters),
        'totalHours': round(sum(stats_dict[sem]['totalHours'] for sem in semesters), 2)
    }
    
    # Faculty workload across all semesters
    all_faculty = set()
    for sem in semesters:
        all_faculty.update(stats_dict[sem]['facultyDistribution'].keys())
    
    faculty_combined = {}
    for fid in all_faculty:
        faculty_data_by_sem = {}
        faculty_name = ''
        
        # Collect data for each semester
        for sem in semesters:
            sem_data = stats_dict[sem]['facultyDistribution'].get(fid, {
                'facultyName': '',
                'assignments': 0,
                'sessions': 0,
                'hours': 0,
                'subjects': [],
                'subjectCount': 0
            })
            faculty_data_by_sem[f'sem{sem}'] = {
                'assignments': sem_data['assignments'],
                'sessions': sem_data['sessions'],
                'hours': sem_data['hours'],
                'subjects': sem_data['subjects']
            }
            if not faculty_name and sem_data.get('facultyName'):
                faculty_name = sem_data['facultyName']
        
        faculty_combined[fid] = {
            'facultyName': faculty_name,
            **faculty_data_by_sem,
            'total': {
                'assignments': sum(
                    stats_dict[sem]['facultyDistribution'].get(fid, {}).get('assignments', 0)
                    for sem in semesters
                ),
                'sessions': sum(
                    stats_dict[sem]['facultyDistribution'].get(fid, {}).get('sessions', 0)
                    for sem in semesters
                ),
                'hours': round(sum(
                    stats_dict[sem]['facultyDistribution'].get(fid, {}).get('hours', 0)
                    for sem in semesters
                ), 2),
                'subjects': sorted(list(set(
                    subject
                    for sem in semesters
                    for subject in stats_dict[sem]['facultyDistribution'].get(fid, {}).get('subjects', [])
                ))),
                'subjectCount': len(set(
                    subject
                    for sem in semesters
                    for subject in stats_dict[sem]['facultyDistribution'].get(fid, {}).get('subjects', [])
                ))
            }
        }
    
    combined['facultyWorkload'] = faculty_combined
    
    # Resource utilization analysis
    resource_analysis = {}
    for sem in semesters:
        by_room = stats_dict[sem]['byRoomType']
        by_comp = stats_dict[sem]['byComponent']
        
        resource_analysis.setdefault('lectureRoomSessions', 0)
        resource_analysis.setdefault('labSessions', 0)
        resource_analysis.setdefault('theorySessions', 0)
        resource_analysis.setdefault('practicalSessions', 0)
        resource_analysis.setdefault('tutorialSessions', 0)
        
        resource_analysis['lectureRoomSessions'] += by_room.get('lecture', {}).get('sessions', 0)
        resource_analysis['labSessions'] += by_room.get('lab', {}).get('sessions', 0)
        resource_analysis['theorySessions'] += by_comp.get('theory', {}).get('sessions', 0)
        resource_analysis['practicalSessions'] += by_comp.get('practical', {}).get('sessions', 0)
        resource_analysis['tutorialSessions'] += by_comp.get('tutorial', {}).get('sessions', 0)
    
    combined['resourceAnalysis'] = resource_analysis
    
    return combined

def main(data_dir=None):
    """Generate comprehensive statistics for Stage 3."""
    import argparse
    
    if data_dir is None:
        parser = argparse.ArgumentParser(description="Generate statistics for Stage 3 assignments")
        parser.add_argument("--data-dir", required=True, help="Data directory path")
        args = parser.parse_args()
        data_dir = Path(args.data_dir)
    else:
        data_dir = Path(data_dir)
    
    # Construct paths
    stage_3_dir = data_dir / "stage_3"
    output_file = stage_3_dir / "statistics.json"
    
    print("Generating comprehensive statistics for Stage 3...")
    print("=" * 70)
    print(f"Data directory: {data_dir}")
    print()
    
    # Dynamically discover which assignment files exist
    print("\n📂 Discovering assignment files...")
    semester_data = {}
    for sem in [1, 2, 3, 4]:
        filepath = stage_3_dir / f"teachingAssignments_sem{sem}.json"
        if filepath.exists():
            try:
                semester_data[sem] = load_assignments(filepath)
                print(f"   ✓ Semester {sem}: {len(semester_data[sem]['assignments'])} assignments")
            except Exception as e:
                print(f"   ✗ Semester {sem}: Error loading file - {e}")
        else:
            print(f"   - Semester {sem}: File not found (not needed for this project)")
    
    if not semester_data:
        print("\n❌ No assignment files found in stage_3/")
        return 1
    
    # Analyze each semester
    print("\n📊 Analyzing statistics...")
    semester_stats = {}
    for sem in sorted(semester_data.keys()):
        print(f"   Analyzing Semester {sem}...")
        semester_stats[sem] = analyze_semester(semester_data[sem], sem)
        print(f"   ✓ {semester_stats[sem]['totalAssignments']} assignments, "
              f"{semester_stats[sem]['totalSessions']} sessions/week")
    
    # Generate combined statistics if multiple semesters
    print("\n🔗 Generating combined statistics...")
    if len(semester_stats) > 1:
        # Use all available semesters for combined stats
        available_sems = sorted(semester_stats.keys())
        combined_stats = generate_combined_statistics(
            semester_stats, 
            available_sems
        )
        print(f"   ✓ Total across Semesters {', '.join(map(str, available_sems))}: "
              f"{combined_stats['totalAssignments']} assignments")
    else:
        # Single semester - create simple combined
        only_sem = list(semester_stats.keys())[0]
        combined_stats = {
            'totalAssignments': semester_stats[only_sem]['totalAssignments'],
            'totalSessions': semester_stats[only_sem]['totalSessions'],
            'totalHours': semester_stats[only_sem]['totalHours'],
            'facultyWorkload': semester_stats[only_sem]['facultyWorkload'],
            'resourceAnalysis': semester_stats[only_sem]['resourceAnalysis']
        }
        print(f"   ✓ Total for Semester {only_sem}: {combined_stats['totalAssignments']} assignments")
    
    # Build output with dynamic semester data
    output = {
        'metadata': {
            'generatedAt': datetime.now().isoformat(),
            'generator': 'generate_statistics.py',
            'version': '1.0',
            'activeSemesters': sorted(semester_stats.keys())
        },
        'combined': combined_stats
    }
    
    # Add individual semester stats
    for sem in sorted(semester_stats.keys()):
        output[f'semester{sem}'] = semester_stats[sem]
    
    # Save to file
    print(f"\n💾 Saving statistics to {output_file.name}...")
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    
    file_size = output_file.stat().st_size
    print(f"   ✓ Saved ({file_size:,} bytes)")
    
    # Print summary
    print("\n" + "=" * 70)
    print("📈 STATISTICS SUMMARY")
    print("=" * 70)
    
    print(f"\n🎯 Overall:")
    print(f"   • Total Assignments: {combined_stats['totalAssignments']}")
    print(f"   • Total Sessions/Week: {combined_stats['totalSessions']}")
    print(f"   • Total Hours/Week: {combined_stats['totalHours']}h")
    print(f"   • Active Semesters: {', '.join(map(str, sorted(semester_stats.keys())))}")
    
    print(f"\n👥 Faculty ({len(combined_stats['facultyWorkload'])} total):")
    for fid, data in sorted(combined_stats['facultyWorkload'].items(), 
                           key=lambda x: x[1]['total']['hours'], reverse=True):
        print(f"   • {data['facultyName']} ({fid}):")
        print(f"     - Total: {data['total']['assignments']} assignments, "
              f"{data['total']['sessions']} sessions/week, {data['total']['hours']}h/week")
        # Show breakdown by semester
        for sem in sorted(semester_stats.keys()):
            sem_key = f'sem{sem}'
            if sem_key in data:
                print(f"     - Sem {sem}: {data[sem_key]['sessions']} sessions")
    
    print(f"\n📚 Subjects:")
    for sem in sorted(semester_stats.keys()):
        num_subjects = len(semester_stats[sem].get('subjectCoverage', {}))
        print(f"   • Semester {sem}: {num_subjects} subjects")
    
    print(f"\n🏫 Room Requirements:")
    print(f"   • Lecture room sessions: {combined_stats['resourceAnalysis']['lectureRoomSessions']}/week")
    print(f"   • Lab sessions: {combined_stats['resourceAnalysis']['labSessions']}/week")
    
    print(f"\n📝 Component Breakdown:")
    print(f"   • Theory: {combined_stats['resourceAnalysis']['theorySessions']} sessions/week")
    print(f"   • Practical: {combined_stats['resourceAnalysis']['practicalSessions']} sessions/week")
    print(f"   • Tutorial: {combined_stats['resourceAnalysis']['tutorialSessions']} sessions/week")
    
    print("\n✅ Statistics generation complete!")
    print(f"📄 Full details in: {output_file.relative_to(stage_3_dir.parent)}")

if __name__ == '__main__':
    main()
