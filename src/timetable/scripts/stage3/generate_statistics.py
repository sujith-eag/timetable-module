#!/usr/bin/env python3
"""
Generate comprehensive statistics from teaching assignments.
Analyzes workload distribution, resource requirements, and constraint patterns.
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Paths
STAGE_3_DIR = Path(__file__).parent.parent
ASSIGNMENTS_SEM3 = STAGE_3_DIR / "teachingAssignments_sem3.json"
ASSIGNMENTS_SEM1 = STAGE_3_DIR / "teachingAssignments_sem1.json"
OUTPUT_FILE = STAGE_3_DIR / "statistics.json"

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

def generate_combined_statistics(sem1_stats, sem3_stats):
    """Generate combined statistics across both semesters."""
    combined = {
        'totalAssignments': sem1_stats['totalAssignments'] + sem3_stats['totalAssignments'],
        'totalSessions': sem1_stats['totalSessions'] + sem3_stats['totalSessions'],
        'totalHours': round(sem1_stats['totalHours'] + sem3_stats['totalHours'], 2)
    }
    
    # Faculty workload across both semesters
    all_faculty = set(sem1_stats['facultyDistribution'].keys()) | set(sem3_stats['facultyDistribution'].keys())
    
    faculty_combined = {}
    for fid in all_faculty:
        sem1_data = sem1_stats['facultyDistribution'].get(fid, {
            'facultyName': '',
            'assignments': 0,
            'sessions': 0,
            'hours': 0,
            'subjects': [],
            'subjectCount': 0
        })
        sem3_data = sem3_stats['facultyDistribution'].get(fid, {
            'facultyName': '',
            'assignments': 0,
            'sessions': 0,
            'hours': 0,
            'subjects': [],
            'subjectCount': 0
        })
        
        faculty_combined[fid] = {
            'facultyName': sem1_data['facultyName'] or sem3_data['facultyName'],
            'sem1': {
                'assignments': sem1_data['assignments'],
                'sessions': sem1_data['sessions'],
                'hours': sem1_data['hours'],
                'subjects': sem1_data['subjects']
            },
            'sem3': {
                'assignments': sem3_data['assignments'],
                'sessions': sem3_data['sessions'],
                'hours': sem3_data['hours'],
                'subjects': sem3_data['subjects']
            },
            'total': {
                'assignments': sem1_data['assignments'] + sem3_data['assignments'],
                'sessions': sem1_data['sessions'] + sem3_data['sessions'],
                'hours': round(sem1_data['hours'] + sem3_data['hours'], 2),
                'subjects': sorted(list(set(sem1_data['subjects'] + sem3_data['subjects']))),
                'subjectCount': len(set(sem1_data['subjects'] + sem3_data['subjects']))
            }
        }
    
    combined['facultyWorkload'] = faculty_combined
    
    # Resource utilization analysis
    combined['resourceAnalysis'] = {
        'lectureRoomSessions': sem1_stats['byRoomType'].get('lecture', {}).get('sessions', 0) + 
                               sem3_stats['byRoomType'].get('lecture', {}).get('sessions', 0),
        'labSessions': sem1_stats['byRoomType'].get('lab', {}).get('sessions', 0) + 
                       sem3_stats['byRoomType'].get('lab', {}).get('sessions', 0),
        'theorySessions': sem1_stats['byComponent'].get('theory', {}).get('sessions', 0) + 
                         sem3_stats['byComponent'].get('theory', {}).get('sessions', 0),
        'practicalSessions': sem1_stats['byComponent'].get('practical', {}).get('sessions', 0) + 
                            sem3_stats['byComponent'].get('practical', {}).get('sessions', 0),
        'tutorialSessions': sem1_stats['byComponent'].get('tutorial', {}).get('sessions', 0) + 
                           sem3_stats['byComponent'].get('tutorial', {}).get('sessions', 0)
    }
    
    return combined

def main():
    print("Generating comprehensive statistics for Stage 3...")
    print("=" * 70)
    
    # Load data
    print("\n📂 Loading teaching assignments...")
    sem1_data = load_assignments(ASSIGNMENTS_SEM1)
    sem3_data = load_assignments(ASSIGNMENTS_SEM3)
    print(f"   ✓ Semester 1: {len(sem1_data['assignments'])} assignments")
    print(f"   ✓ Semester 3: {len(sem3_data['assignments'])} assignments")
    
    # Analyze each semester
    print("\n📊 Analyzing Semester 1...")
    sem1_stats = analyze_semester(sem1_data, 1)
    print(f"   ✓ {sem1_stats['totalAssignments']} assignments, {sem1_stats['totalSessions']} sessions/week")
    
    print("\n📊 Analyzing Semester 3...")
    sem3_stats = analyze_semester(sem3_data, 3)
    print(f"   ✓ {sem3_stats['totalAssignments']} assignments, {sem3_stats['totalSessions']} sessions/week")
    
    # Generate combined statistics
    print("\n🔗 Generating combined statistics...")
    combined_stats = generate_combined_statistics(sem1_stats, sem3_stats)
    print(f"   ✓ Total: {combined_stats['totalAssignments']} assignments across both semesters")
    
    # Build output
    output = {
        'metadata': {
            'generatedAt': datetime.now().isoformat(),
            'generator': 'generate_statistics.py',
            'version': '1.0'
        },
        'semester1': sem1_stats,
        'semester3': sem3_stats,
        'combined': combined_stats
    }
    
    # Save to file
    print(f"\n💾 Saving statistics to {OUTPUT_FILE.name}...")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    
    file_size = OUTPUT_FILE.stat().st_size
    print(f"   ✓ Saved ({file_size:,} bytes)")
    
    # Print summary
    print("\n" + "=" * 70)
    print("📈 STATISTICS SUMMARY")
    print("=" * 70)
    
    print(f"\n🎯 Overall:")
    print(f"   • Total Assignments: {combined_stats['totalAssignments']}")
    print(f"   • Total Sessions/Week: {combined_stats['totalSessions']}")
    print(f"   • Total Hours/Week: {combined_stats['totalHours']}h")
    
    print(f"\n👥 Faculty ({len(combined_stats['facultyWorkload'])} total):")
    for fid, data in sorted(combined_stats['facultyWorkload'].items(), 
                           key=lambda x: x[1]['total']['hours'], reverse=True):
        print(f"   • {data['facultyName']} ({fid}):")
        print(f"     - Total: {data['total']['assignments']} assignments, "
              f"{data['total']['sessions']} sessions/week, {data['total']['hours']}h/week")
        print(f"     - Sem 1: {data['sem1']['sessions']} sessions, Sem 3: {data['sem3']['sessions']} sessions")
    
    print(f"\n📚 Subjects:")
    print(f"   • Semester 1: {len(sem1_stats['subjectCoverage'])} subjects")
    print(f"   • Semester 3: {len(sem3_stats['subjectCoverage'])} subjects")
    
    print(f"\n🏫 Room Requirements:")
    print(f"   • Lecture room sessions: {combined_stats['resourceAnalysis']['lectureRoomSessions']}/week")
    print(f"   • Lab sessions: {combined_stats['resourceAnalysis']['labSessions']}/week")
    
    print(f"\n📝 Component Breakdown:")
    print(f"   • Theory: {combined_stats['resourceAnalysis']['theorySessions']} sessions/week")
    print(f"   • Practical: {combined_stats['resourceAnalysis']['practicalSessions']} sessions/week")
    print(f"   • Tutorial: {combined_stats['resourceAnalysis']['tutorialSessions']} sessions/week")
    
    print("\n✅ Statistics generation complete!")
    print(f"📄 Full details in: {OUTPUT_FILE.relative_to(STAGE_3_DIR.parent)}")

if __name__ == '__main__':
    main()
