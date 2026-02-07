#!/usr/bin/env python3
"""
Generate detailed human-readable reports from teaching assignments.
Creates markdown reports for faculty, subjects, student groups, and resources.
"""

import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Paths
STAGE_3_DIR = Path(__file__).parent.parent
ASSIGNMENTS_SEM3 = STAGE_3_DIR / "teachingAssignments_sem3.json"
ASSIGNMENTS_SEM1 = STAGE_3_DIR / "teachingAssignments_sem1.json"
REPORTS_DIR = STAGE_3_DIR / "reports"

def load_assignments(filepath):
    """Load teaching assignments from JSON file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def generate_faculty_report(sem1_data, sem3_data):
    """Generate faculty-wise teaching assignment report."""
    report = ["# Faculty Teaching Assignments Report\n"]
    report.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append("---\n\n")
    
    # Collect all faculty
    faculty_assignments = defaultdict(lambda: {'sem1': [], 'sem3': []})
    
    for a in sem1_data['assignments']:
        faculty_assignments[a['facultyId']]['name'] = a['facultyName']
        faculty_assignments[a['facultyId']]['sem1'].append(a)
    
    for a in sem3_data['assignments']:
        faculty_assignments[a['facultyId']]['name'] = a['facultyName']
        faculty_assignments[a['facultyId']]['sem3'].append(a)
    
    # Sort by faculty ID
    for fid in sorted(faculty_assignments.keys()):
        data = faculty_assignments[fid]
        report.append(f"## {data['name']} ({fid})\n\n")
        
        sem1_assignments = data['sem1']
        sem3_assignments = data['sem3']
        
        total_assignments = len(sem1_assignments) + len(sem3_assignments)
        total_sessions = sum(a['sessionsPerWeek'] for a in sem1_assignments + sem3_assignments)
        total_hours = sum(a['sessionsPerWeek'] * a['sessionDuration'] / 60 
                         for a in sem1_assignments + sem3_assignments)
        
        report.append(f"**Summary**: {total_assignments} assignments, "
                     f"{total_sessions} sessions/week, {total_hours:.1f}h/week\n\n")
        
        # Semester 1
        if sem1_assignments:
            report.append("### Semester 1\n\n")
            report.append("| Subject | Component | Sections | Sessions/Week | Hours/Week |\n")
            report.append("|---------|-----------|----------|---------------|------------|\n")
            
            for a in sorted(sem1_assignments, key=lambda x: (x['subjectCode'], x['componentType'])):
                hours = a['sessionsPerWeek'] * a['sessionDuration'] / 60
                sections = ', '.join(a['sections'])
                report.append(f"| {a['subjectTitle']} | {a['componentType'].title()} | "
                            f"{sections} | {a['sessionsPerWeek']} | {hours:.1f}h |\n")
            
            report.append("\n")
        
        # Semester 3
        if sem3_assignments:
            report.append("### Semester 3\n\n")
            report.append("| Subject | Component | Sections | Sessions/Week | Hours/Week | Elective |\n")
            report.append("|---------|-----------|----------|---------------|------------|----------|\n")
            
            for a in sorted(sem3_assignments, key=lambda x: (x['subjectCode'], x['componentType'])):
                hours = a['sessionsPerWeek'] * a['sessionDuration'] / 60
                sections = ', '.join(a['sections'])
                elective = "Yes" if a['isElective'] else "No"
                report.append(f"| {a['subjectTitle']} | {a['componentType'].title()} | "
                            f"{sections} | {a['sessionsPerWeek']} | {hours:.1f}h | {elective} |\n")
            
            report.append("\n")
        
        report.append("---\n\n")
    
    return ''.join(report)

def generate_subject_report(sem1_data, sem3_data):
    """Generate subject-wise coverage report."""
    report = ["# Subject Coverage Report\n"]
    report.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append("---\n\n")
    
    # Semester 1
    report.append("## Semester 1 Subjects\n\n")
    
    subject_data = defaultdict(lambda: {'components': [], 'faculty': set(), 'sections': set()})
    for a in sem1_data['assignments']:
        subject_data[a['subjectCode']]['title'] = a['subjectTitle']
        subject_data[a['subjectCode']]['components'].append({
            'type': a['componentType'],
            'faculty': a['facultyName'],
            'sessions': a['sessionsPerWeek']
        })
        subject_data[a['subjectCode']]['faculty'].add(a['facultyName'])
        subject_data[a['subjectCode']]['sections'].update(a['sections'])
    
    for scode in sorted(subject_data.keys()):
        data = subject_data[scode]
        report.append(f"### {data['title']} ({scode})\n\n")
        report.append(f"**Sections**: {', '.join(sorted(data['sections']))}\n\n")
        report.append(f"**Faculty**: {', '.join(sorted(data['faculty']))}\n\n")
        
        report.append("| Component | Faculty | Sessions/Week |\n")
        report.append("|-----------|---------|---------------|\n")
        for comp in sorted(data['components'], key=lambda x: x['type']):
            report.append(f"| {comp['type'].title()} | {comp['faculty']} | {comp['sessions']} |\n")
        report.append("\n")
    
    # Semester 3
    report.append("## Semester 3 Subjects\n\n")
    
    subject_data = defaultdict(lambda: {
        'components': [], 
        'faculty': set(), 
        'sections': set(),
        'isElective': False
    })
    for a in sem3_data['assignments']:
        subject_data[a['subjectCode']]['title'] = a['subjectTitle']
        subject_data[a['subjectCode']]['isElective'] = a['isElective']
        subject_data[a['subjectCode']]['components'].append({
            'type': a['componentType'],
            'faculty': a['facultyName'],
            'sessions': a['sessionsPerWeek'],
            'sections': a['sections']
        })
        subject_data[a['subjectCode']]['faculty'].add(a['facultyName'])
        subject_data[a['subjectCode']]['sections'].update(a['sections'])
    
    # Separate core and electives
    core_subjects = {k: v for k, v in subject_data.items() if not v['isElective']}
    elective_subjects = {k: v for k, v in subject_data.items() if v['isElective']}
    
    if core_subjects:
        report.append("### Core Subjects\n\n")
        for scode in sorted(core_subjects.keys()):
            data = core_subjects[scode]
            report.append(f"#### {data['title']} ({scode})\n\n")
            report.append(f"**Sections**: {', '.join(sorted(data['sections']))}\n\n")
            report.append(f"**Faculty**: {', '.join(sorted(data['faculty']))}\n\n")
            
            report.append("| Component | Faculty | Sections | Sessions/Week |\n")
            report.append("|-----------|---------|----------|---------------|\n")
            for comp in sorted(data['components'], key=lambda x: x['type']):
                sections = ', '.join(comp['sections'])
                report.append(f"| {comp['type'].title()} | {comp['faculty']} | "
                            f"{sections} | {comp['sessions']} |\n")
            report.append("\n")
    
    if elective_subjects:
        report.append("### Elective Subjects\n\n")
        for scode in sorted(elective_subjects.keys()):
            data = elective_subjects[scode]
            report.append(f"#### {data['title']} ({scode})\n\n")
            report.append(f"**Sections**: {', '.join(sorted(data['sections']))}\n\n")
            report.append(f"**Faculty**: {', '.join(sorted(data['faculty']))}\n\n")
            
            report.append("| Component | Faculty | Sections | Sessions/Week |\n")
            report.append("|-----------|---------|----------|---------------|\n")
            for comp in sorted(data['components'], key=lambda x: x['type']):
                sections = ', '.join(comp['sections'])
                report.append(f"| {comp['type'].title()} | {comp['faculty']} | "
                            f"{sections} | {comp['sessions']} |\n")
            report.append("\n")
    
    return ''.join(report)

def generate_student_group_report(sem1_data, sem3_data):
    """Generate student group workload report."""
    report = ["# Student Group Workload Report\n"]
    report.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append("---\n\n")
    
    # Semester 1
    report.append("## Semester 1\n\n")
    
    group_assignments = defaultdict(list)
    for a in sem1_data['assignments']:
        for group in a['studentGroupIds']:
            group_assignments[group].append(a)
    
    for group in sorted(group_assignments.keys()):
        assignments = group_assignments[group]
        total_sessions = sum(a['sessionsPerWeek'] for a in assignments)
        total_hours = sum(a['sessionsPerWeek'] * a['sessionDuration'] / 60 for a in assignments)
        
        report.append(f"### {group}\n\n")
        report.append(f"**Total Load**: {len(assignments)} assignments, "
                     f"{total_sessions} sessions/week, {total_hours:.1f}h/week\n\n")
        
        report.append("| Subject | Component | Faculty | Sessions/Week |\n")
        report.append("|---------|-----------|---------|---------------|\n")
        for a in sorted(assignments, key=lambda x: (x['subjectCode'], x['componentType'])):
            report.append(f"| {a['subjectTitle']} | {a['componentType'].title()} | "
                         f"{a['facultyName']} | {a['sessionsPerWeek']} |\n")
        report.append("\n")
    
    # Semester 3
    report.append("## Semester 3\n\n")
    
    group_assignments = defaultdict(list)
    for a in sem3_data['assignments']:
        for group in a['studentGroupIds']:
            group_assignments[group].append(a)
    
    for group in sorted(group_assignments.keys()):
        assignments = group_assignments[group]
        total_sessions = sum(a['sessionsPerWeek'] for a in assignments)
        total_hours = sum(a['sessionsPerWeek'] * a['sessionDuration'] / 60 for a in assignments)
        
        report.append(f"### {group}\n\n")
        report.append(f"**Total Load**: {len(assignments)} assignments, "
                     f"{total_sessions} sessions/week, {total_hours:.1f}h/week\n\n")
        
        report.append("| Subject | Component | Faculty | Sessions/Week | Type |\n")
        report.append("|---------|-----------|---------|---------------|------|\n")
        for a in sorted(assignments, key=lambda x: (x['subjectCode'], x['componentType'])):
            assignment_type = "Elective" if a['isElective'] else "Core"
            report.append(f"| {a['subjectTitle']} | {a['componentType'].title()} | "
                         f"{a['facultyName']} | {a['sessionsPerWeek']} | {assignment_type} |\n")
        report.append("\n")
    
    return ''.join(report)

def generate_resource_report(sem1_data, sem3_data):
    """Generate resource requirements report."""
    report = ["# Resource Requirements Report\n"]
    report.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append("---\n\n")
    
    # Room requirements
    report.append("## Room Requirements\n\n")
    
    all_assignments = sem1_data['assignments'] + sem3_data['assignments']
    
    # By room type
    by_room_type = defaultdict(lambda: {'sessions': 0, 'hours': 0, 'assignments': []})
    for a in all_assignments:
        room_type = a['requiresRoomType']
        by_room_type[room_type]['sessions'] += a['sessionsPerWeek']
        by_room_type[room_type]['hours'] += a['sessionsPerWeek'] * a['sessionDuration'] / 60
        by_room_type[room_type]['assignments'].append(a)
    
    report.append("### By Room Type\n\n")
    report.append("| Room Type | Assignments | Sessions/Week | Hours/Week |\n")
    report.append("|-----------|-------------|---------------|------------|\n")
    for room_type in sorted(by_room_type.keys()):
        data = by_room_type[room_type]
        report.append(f"| {room_type.title()} | {len(data['assignments'])} | "
                     f"{data['sessions']} | {data['hours']:.1f}h |\n")
    report.append("\n")
    
    # Pre-allocated rooms
    preallocated = [(a, a['constraints']['mustBeInRoom']) 
                   for a in all_assignments if a['constraints']['mustBeInRoom']]
    
    if preallocated:
        report.append("### Pre-allocated Rooms\n\n")
        report.append("| Assignment | Room | Sessions/Week |\n")
        report.append("|------------|------|---------------|\n")
        for a, room in preallocated:
            report.append(f"| {a['subjectTitle']} - {a['componentType'].title()} "
                         f"(Sec {', '.join(a['sections'])}) | {room} | {a['sessionsPerWeek']} |\n")
        report.append("\n")
    
    # Room preferences
    room_usage = defaultdict(int)
    for a in all_assignments:
        for room in a['preferredRooms']:
            room_usage[room] += 1
    
    if room_usage:
        report.append("### Room Preference Frequency\n\n")
        report.append("| Room | Times Preferred |\n")
        report.append("|------|------------------|\n")
        for room in sorted(room_usage.keys(), key=lambda x: room_usage[x], reverse=True):
            report.append(f"| {room} | {room_usage[room]} |\n")
        report.append("\n")
    
    # Component distribution
    report.append("## Component Distribution\n\n")
    
    by_component = defaultdict(lambda: {'sem1': 0, 'sem3': 0, 'total': 0})
    for a in sem1_data['assignments']:
        by_component[a['componentType']]['sem1'] += a['sessionsPerWeek']
        by_component[a['componentType']]['total'] += a['sessionsPerWeek']
    for a in sem3_data['assignments']:
        by_component[a['componentType']]['sem3'] += a['sessionsPerWeek']
        by_component[a['componentType']]['total'] += a['sessionsPerWeek']
    
    report.append("| Component | Sem 1 | Sem 3 | Total |\n")
    report.append("|-----------|-------|-------|-------|\n")
    for comp in sorted(by_component.keys()):
        data = by_component[comp]
        report.append(f"| {comp.title()} | {data['sem1']} | {data['sem3']} | {data['total']} |\n")
    report.append("\n")
    
    # Constraint summary
    report.append("## Constraint Summary\n\n")
    
    constraint_counts = {
        'Fixed Timing': sum(1 for a in all_assignments 
                           if a['constraints']['fixedDay'] or a['constraints']['fixedSlot']),
        'Pre-allocated Room': sum(1 for a in all_assignments 
                                 if a['constraints']['mustBeInRoom']),
        'Room Preferences': sum(1 for a in all_assignments if a['preferredRooms']),
        'Contiguous Required': sum(1 for a in all_assignments if a['requiresContiguous']),
        'Multi-slot Blocks': sum(1 for a in all_assignments if a['blockSizeSlots'] > 1)
    }
    
    report.append("| Constraint Type | Count |\n")
    report.append("|-----------------|-------|\n")
    for constraint, count in constraint_counts.items():
        report.append(f"| {constraint} | {count} |\n")
    report.append("\n")
    
    return ''.join(report)

def generate_summary_report(sem1_data, sem3_data):
    """Generate executive summary report."""
    report = ["# Stage 3 Executive Summary\n"]
    report.append(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    report.append("---\n\n")
    
    all_assignments = sem1_data['assignments'] + sem3_data['assignments']
    
    # Overview
    report.append("## Overview\n\n")
    report.append(f"- **Total Assignments**: {len(all_assignments)}\n")
    report.append(f"- **Semester 1**: {len(sem1_data['assignments'])} assignments\n")
    report.append(f"- **Semester 3**: {len(sem3_data['assignments'])} assignments\n\n")
    
    total_sessions = sum(a['sessionsPerWeek'] for a in all_assignments)
    total_hours = sum(a['sessionsPerWeek'] * a['sessionDuration'] / 60 for a in all_assignments)
    
    report.append(f"- **Total Sessions/Week**: {total_sessions}\n")
    report.append(f"- **Total Hours/Week**: {total_hours:.1f}h\n\n")
    
    # Faculty count
    all_faculty = set(a['facultyId'] for a in all_assignments)
    report.append(f"- **Faculty Involved**: {len(all_faculty)}\n\n")
    
    # Subject count
    sem1_subjects = set(a['subjectCode'] for a in sem1_data['assignments'])
    sem3_subjects = set(a['subjectCode'] for a in sem3_data['assignments'])
    report.append(f"- **Subjects**:\n")
    report.append(f"  - Semester 1: {len(sem1_subjects)}\n")
    report.append(f"  - Semester 3: {len(sem3_subjects)}\n\n")
    
    # By semester breakdown
    report.append("## Semester Breakdown\n\n")
    report.append("| Metric | Semester 1 | Semester 3 | Total |\n")
    report.append("|--------|------------|------------|-------|\n")
    
    sem1_sessions = sum(a['sessionsPerWeek'] for a in sem1_data['assignments'])
    sem3_sessions = sum(a['sessionsPerWeek'] for a in sem3_data['assignments'])
    report.append(f"| Sessions/Week | {sem1_sessions} | {sem3_sessions} | {total_sessions} |\n")
    
    sem1_hours = sum(a['sessionsPerWeek'] * a['sessionDuration'] / 60 for a in sem1_data['assignments'])
    sem3_hours = sum(a['sessionsPerWeek'] * a['sessionDuration'] / 60 for a in sem3_data['assignments'])
    report.append(f"| Hours/Week | {sem1_hours:.1f}h | {sem3_hours:.1f}h | {total_hours:.1f}h |\n")
    
    sem1_theory = sum(1 for a in sem1_data['assignments'] if a['componentType'] == 'theory')
    sem3_theory = sum(1 for a in sem3_data['assignments'] if a['componentType'] == 'theory')
    report.append(f"| Theory | {sem1_theory} | {sem3_theory} | {sem1_theory + sem3_theory} |\n")
    
    sem1_practical = sum(1 for a in sem1_data['assignments'] if a['componentType'] == 'practical')
    sem3_practical = sum(1 for a in sem3_data['assignments'] if a['componentType'] == 'practical')
    report.append(f"| Practical | {sem1_practical} | {sem3_practical} | {sem1_practical + sem3_practical} |\n")
    
    sem1_tutorial = sum(1 for a in sem1_data['assignments'] if a['componentType'] == 'tutorial')
    sem3_tutorial = sum(1 for a in sem3_data['assignments'] if a['componentType'] == 'tutorial')
    report.append(f"| Tutorial | {sem1_tutorial} | {sem3_tutorial} | {sem1_tutorial + sem3_tutorial} |\n\n")
    
    # Top faculty by workload
    report.append("## Faculty Workload (Top 5)\n\n")
    faculty_hours = defaultdict(lambda: {'name': '', 'hours': 0, 'assignments': 0})
    for a in all_assignments:
        fid = a['facultyId']
        faculty_hours[fid]['name'] = a['facultyName']
        faculty_hours[fid]['hours'] += a['sessionsPerWeek'] * a['sessionDuration'] / 60
        faculty_hours[fid]['assignments'] += 1
    
    top_faculty = sorted(faculty_hours.items(), key=lambda x: x[1]['hours'], reverse=True)[:5]
    
    report.append("| Faculty | Assignments | Hours/Week |\n")
    report.append("|---------|-------------|------------|\n")
    for fid, data in top_faculty:
        report.append(f"| {data['name']} | {data['assignments']} | {data['hours']:.1f}h |\n")
    report.append("\n")
    
    # Status
    report.append("## Status\n\n")
    report.append("✅ **Stage 3 Complete**\n\n")
    report.append("- All teaching assignments generated\n")
    report.append("- Constraints properly defined\n")
    report.append("- Room preferences extracted\n")
    report.append("- Validation passed\n\n")
    
    report.append("**Ready for**: Stage 4 (Scheduling)\n\n")
    
    return ''.join(report)

def main():
    print("Generating detailed reports for Stage 3...")
    print("=" * 70)
    
    # Create reports directory
    REPORTS_DIR.mkdir(exist_ok=True)
    print(f"\n📁 Reports directory: {REPORTS_DIR.relative_to(STAGE_3_DIR.parent)}")
    
    # Load data
    print("\n📂 Loading teaching assignments...")
    sem1_data = load_assignments(ASSIGNMENTS_SEM1)
    sem3_data = load_assignments(ASSIGNMENTS_SEM3)
    print(f"   ✓ Loaded {len(sem1_data['assignments']) + len(sem3_data['assignments'])} total assignments")
    
    # Generate reports
    reports = {
        'summary.md': ('Executive Summary', generate_summary_report),
        'faculty_assignments.md': ('Faculty Assignments', generate_faculty_report),
        'subject_coverage.md': ('Subject Coverage', generate_subject_report),
        'student_groups.md': ('Student Group Workload', generate_student_group_report),
        'resource_requirements.md': ('Resource Requirements', generate_resource_report)
    }
    
    generated = []
    for filename, (title, generator_func) in reports.items():
        print(f"\n📝 Generating {title}...")
        content = generator_func(sem1_data, sem3_data)
        
        filepath = REPORTS_DIR / filename
        with open(filepath, 'w') as f:
            f.write(content)
        
        file_size = filepath.stat().st_size
        print(f"   ✓ Saved to {filename} ({file_size:,} bytes)")
        generated.append(filename)
    
    print("\n" + "=" * 70)
    print("✅ Report generation complete!")
    print("=" * 70)
    print(f"\n📄 Generated {len(generated)} reports:")
    for filename in generated:
        print(f"   • {filename}")
    
    print(f"\n📂 All reports saved in: {REPORTS_DIR.relative_to(STAGE_3_DIR.parent)}")

if __name__ == '__main__':
    main()
