# Timetable Builder

[![PyPI Version](https://img.shields.io/pypi/v/timetable-builder.svg)](https://pypi.org/project/timetable-builder/)
[![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)](https://github.com/sujith-eag/timetable-builder)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A comprehensive, modular data pipeline system for transforming academic configuration data into AI-ready scheduling inputs and enriched timetable outputs. The system implements a six-stage progressive data enrichment model with robust validation and type safety.

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [CLI Reference](#cli-reference)
- [Stage Descriptions](#stage-descriptions)
- [API Usage](#api-usage)
- [Configuration](#configuration)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Overview

The Timetable Builder System is designed to streamline the complex process of academic timetable generation. It transforms basic institutional data—faculty rosters, subject definitions, student groups, and scheduling constraints—into comprehensive, validated datasets suitable for AI-driven scheduling algorithms.

The system employs a modular, six-stage pipeline architecture that ensures data integrity, maintainability, and scalability. Each stage builds upon validated outputs from previous stages, creating a robust foundation for automated timetable generation.

## Key Features

### 🔧 **Modular Architecture**
- Six-stage progressive data enrichment pipeline
- Independent, testable components
- Clear separation of concerns

### ✅ **Data Validation**
- Pydantic model validation throughout the pipeline
- JSON Schema validation for data integrity
- Comprehensive error reporting and debugging

### 🚀 **CLI Interface**
- Unified command-line interface for all operations
- Intuitive commands for building, validation, and data management
- Rich output with progress indicators and detailed reporting

### 📊 **Comprehensive Reporting**
- Human-readable reports and summaries
- Multiple export formats (CSV, JSON, Markdown)
- Detailed analytics and conflict detection

### 🔄 **Type Safety**
- Full type annotations throughout the codebase
- Runtime validation with Pydantic models
- Compile-time type checking support

### 🧪 **Testing Framework**
- Comprehensive test suite (278+ tests)
- Unit and integration test coverage
- Automated validation and regression testing

## System Architecture

### Design Philosophy

The system implements a **progressive data enrichment model** where each stage transforms and enhances data from the previous stage. This approach ensures:

- **Data Integrity**: Each stage validates its inputs and outputs
- **Modularity**: Stages can be developed, tested, and modified independently
- **Traceability**: Clear data lineage from configuration to final output
- **Maintainability**: Isolated components reduce coupling and complexity

### Data Flow Pipeline

```
Stage 1: Configuration Layer
        ↓ (Validation + Enrichment)
Stage 2: Data Building
        ↓ (Assignment Generation)
Stage 3: Teaching Assignments
        ↓ (Consolidation)
Stage 4: AI Scheduling Input
        ↓ (AI Processing)
Stage 5: AI Schedule Output
        ↓ (Enrichment + Analysis)
Stage 6: Enriched Timetable
```

### Core Components

- **DataLoader**: Centralized data access with automatic validation
- **Pydantic Models**: Type-safe data structures for all entities
- **CLI Framework**: Command-line interface built with Click
- **Schema Validation**: JSON Schema validation for data integrity
- **Build System**: Modular stage-specific build processors

## Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager

### PyPI Installation (Recommended)

Install the latest stable version from PyPI:

```bash
pip install timetable-builder
```

### Development Installation

For development, testing, or the latest features:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sujith-eag/timetable-builder.git
   cd timetable-builder
   ```

2. **Install in development mode:**
   ```bash
   pip install -e .
   ```

3. **Verify installation:**
   ```bash
   timetable --version
   ```

For development with all dependencies:

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .
```

## Quick Start

### 1. Initialize a New Project

```bash
# Create a new timetable project
timetable init --data-dir ./my_timetable_project

# Navigate to the project directory
cd my_timetable_project
```

### 2. Configure Stage 1 Data

Edit the template files in `stage_1/` with your institutional data:
- `config.json` - Time slots, rooms, and scheduling parameters
- `facultyBasic.json` - Faculty roster
- `subjects*.json` - Subject definitions
- `studentGroups.json` - Student group configurations

### 3. Build and Validate

```bash
# Validate Stage 1 data
timetable validate --stage 1

# Build Stage 2 enriched data
timetable build stage2

# Validate Stage 2 data
timetable validate --stage 2

# Build complete pipeline
timetable build all
```

### 4. View Results

```bash
# Check pipeline status
timetable status

# View data summaries
timetable info all

# Export data
timetable export csv
```

## Project Structure

```
timetable-builder/
├── src/timetable/              # Main package
│   ├── cli/                    # Command-line interface
│   │   ├── __init__.py         # CLI entry point
│   │   ├── build.py            # Build commands
│   │   ├── validate.py         # Validation commands
│   │   ├── info.py             # Information display
│   │   ├── load.py             # Data loading
│   │   ├── export.py           # Data export
│   │   └── schema.py           # Schema validation
│   ├── core/                   # Core functionality
│   │   ├── loader.py           # DataLoader class
│   │   ├── schema.py           # Schema validation
│   │   └── exceptions.py       # Custom exceptions
│   ├── models/                 # Pydantic data models
│   │   ├── stage1.py           # Stage 1 models
│   │   ├── stage2.py           # Stage 2 models
│   │   └── stage6.py           # Stage 6 models
│   ├── scripts/                # Stage-specific scripts
│   │   ├── stage2/             # Stage 2 build scripts
│   │   ├── stage3/             # Stage 3 build scripts
│   │   └── stage6/             # Stage 6 processing scripts
│   └── stages/                 # Template data files
│       └── stage_1/            # Stage 1 templates
├── schemas/                    # JSON schemas
│   ├── stage1/                 # Stage 1 schemas
│   ├── stage2/                 # Stage 2 schemas
│   └── stage6/                 # Stage 6 schemas
├── tests/                      # Test suite
│   ├── unit/                   # Unit tests
│   └── integration/            # Integration tests
├── docs/                       # Documentation
└── pyproject.toml              # Package configuration
```

## CLI Reference

### Core Commands

#### Project Management
```bash
timetable init --data-dir <path>    # Initialize new project
timetable status                    # Show pipeline status
```

#### Data Validation
```bash
timetable validate --all            # Validate all stages
timetable validate --stage <1-6>    # Validate specific stage
timetable schema list               # List available schemas
timetable schema validate <name>    # Validate against schema
```

#### Build Pipeline
```bash
timetable build all                 # Build all stages
timetable build stage<N>            # Build specific stage
timetable build check               # Check build readiness
```

#### Data Inspection
```bash
timetable info all                  # Complete data summary
timetable info faculty              # Faculty information
timetable info subjects             # Subject information
timetable load faculty --stage 2    # Load and display data
```

#### Data Export
```bash
timetable export csv                # Export to CSV
timetable export json               # Export to JSON
timetable export markdown           # Export reports
```

### Command Groups

| Group | Commands | Purpose |
|-------|----------|---------|
| **build** | `all`, `stage2-6`, `check` | Build pipeline stages |
| **validate** | `--all`, `--stage` | Data validation |
| **info** | `all`, `faculty`, `subjects`, etc. | Data inspection |
| **load** | `faculty`, `subjects`, `config` | Data loading |
| **export** | `csv`, `json`, `markdown` | Data export |
| **schema** | `list`, `validate` | Schema validation |

## Stage Descriptions

### Stage 1: Configuration Layer

**Purpose**: Define institutional constraints, resources, and scheduling rules.

**Input Files**:
- `config.json` - Time slots, days, rooms, and scheduling parameters
- `facultyBasic.json` - Faculty roster with basic information
- `subjects1CoreBasic.json` - Semester 1 core subject definitions
- `subjects3CoreBasic.json` - Semester 3 core subject definitions
- `subjects3ElectBasic.json` - Semester 3 elective subjects
- `studentGroups.json` - Student group and section definitions
- `roomPreferences.json` - Room preferences and constraints

**Validation**: Pydantic models with JSON Schema validation.

### Stage 2: Data Enrichment

**Purpose**: Transform basic Stage 1 data into enriched, component-level representations.

**Processes**:
- Expand subject credit patterns into detailed components
- Calculate faculty workload statistics
- Generate comprehensive subject and faculty profiles

**Output Files**:
- `subjects2Full.json` - Subjects with expanded components
- `faculty2Full.json` - Faculty with workload calculations
- Build reports with human-readable summaries

**Scripts**: `build_subjects_full.py`, `build_faculty_full.py`, `build_all.py`

### Stage 3: Teaching Assignment Generation

**Purpose**: Generate optimized teaching assignments based on institutional rules.

**Processes**:
- Assign faculty to subjects based on qualifications and availability
- Generate teaching assignments for all semesters
- Create constraint matrices and overlap analysis

**Output Files**:
- `teachingAssignments_sem1.json` - Semester 1 assignments
- `teachingAssignments_sem3.json` - Semester 3 assignments
- `statistics.json` - Assignment statistics and summaries
- `reports/` - Detailed Markdown reports

**Scripts**: `assignment_generator.py`, `generate_statistics.py`, `build_all.py`

### Stage 4: AI Scheduling Input Consolidation

**Purpose**: Consolidate all data into a single, self-contained input for AI scheduling.

**Process**: Aggregate data from Stages 1-3 into a comprehensive scheduling input file.

**Output File**: `schedulingInput.json` - Complete AI scheduling input

**Scripts**: `build_scheduling_input.py`, `view_scheduling_input.py`

### Stage 5: AI Schedule Output

**Purpose**: Store and validate AI-generated schedule outputs.

**Input**: AI solver output (typically `ai_solved_schedule.json`)

**Validation**: Schema validation against expected AI output format

**Scripts**: `generate_schedule_template.py` (utility for testing)

### Stage 6: Enriched Timetable Generation

**Purpose**: Transform AI schedule into comprehensive, human-readable timetable.

**Processes**:
- Enrich schedule with detailed faculty, subject, and room information
- Generate conflict analysis and validation reports
- Create faculty and student schedule views

**Output Files**:
- `timetable_enriched.json` - Complete enriched timetable
- `schedule_analysis_report.md` - Conflict analysis
- `views/` - Individual faculty and student schedules

**Scripts**: `enrich_schedule.py`, `analyze_schedule.py`, `generate_*_views.py`

## API Usage

### DataLoader Class

The `DataLoader` provides type-safe data access with automatic validation:

```python
from timetable.core import DataLoader

# Initialize loader
loader = DataLoader("/path/to/project")

# Load Stage 1 data
config = loader.load_config()
faculty = loader.load_faculty()
subjects = loader.load_subjects(semester=1)

# Load Stage 2 data
faculty_full = loader.load_faculty_full()
subjects_full = loader.load_subjects_full()

# Load Stage 3 data
assignments = loader.load_teaching_assignments(semester=1)
statistics = loader.load_statistics()
```

### Pydantic Models

All data structures are defined as Pydantic models for type safety:

```python
from timetable.models.stage1 import Faculty, Subject
from timetable.models.stage2 import FacultyFull, SubjectFull

# Models provide validation and type hints
faculty: Faculty = loader.load_faculty()[0]
# Type checking and validation automatic
```

## Configuration

### Environment Variables

```bash
# Project configuration
TIMETABLE_DATA_DIR=/path/to/project
TIMETABLE_LOG_LEVEL=INFO
TIMETABLE_STRICT_MODE=false

# Development settings
TIMETABLE_DEBUG=true
TIMETABLE_VERBOSE=true
```

### Project Configuration

Each project contains a `.env` file with project-specific settings and a `stage_1/config.json` with scheduling parameters.

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=timetable

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
```

### Code Quality

```bash
# Linting
ruff check .

# Formatting
ruff format .

# Type checking
mypy src/timetable/
```

### Building Documentation

```bash
# Generate documentation
sphinx-build docs/ docs/_build/

# Serve documentation locally
sphinx-autobuild docs/ docs/_build/
```

## Contributing

We welcome contributions to the Timetable Builder System! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes with tests
4. Run the test suite: `pytest`
5. Submit a pull request

### Code Standards

- **Type Hints**: All functions and methods must have type annotations
- **Docstrings**: Comprehensive docstrings for all public APIs
- **Testing**: Unit tests for all new functionality
- **Linting**: Code must pass `ruff` checks

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions, issues, or contributions:

- **Issues**: [GitHub Issues](https://github.com/sujith-eag/timetable-builder/issues)
- **Discussions**: [GitHub Discussions](https://github.com/sujith-eag/timetable-builder/discussions)
- **Documentation**: [Full Documentation](docs/)

---

**Timetable Builder System** - Transforming academic data into optimized schedules through intelligent automation.
