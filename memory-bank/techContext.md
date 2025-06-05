# Technical Context

## Technology Stack

### Core Technologies
- Python 3.13+
- python-pptx library (for PowerPoint manipulation)
- Pillow library (for image handling)
- JSON (for data input)

### Development Tools
- Virtual Environment (venv)
- Git (version control)
- Visual Studio Code (recommended IDE)

## Project Structure
```
pptx-generator/
├── pptx_generator/
│   ├── __init__.py
│   ├── main.py          # CLI entry point
│   ├── generator.py     # Core generation logic
│   ├── utils.py        # Utility functions
│   ├── data/           # Sample data files
│   ├── templates/      # Template storage
│   └── output/         # Generated presentations
├── tests/              # Test suite
├── requirements.txt    # Project dependencies
└── README.md          # Documentation
```

## Dependencies
```
python-pptx>=0.6.21    # PowerPoint file manipulation
Pillow>=10.0.0         # Image processing
click>=8.1.0           # CLI interface
pytest>=7.0.0          # Testing framework (dev dependency)
```

## Technical Constraints

### PowerPoint Template Requirements
- Must be .pptx format (not .ppt)
- Should contain named placeholders
- Must have defined layouts
- Should use master slides for consistency

### Input Data Requirements
- Valid JSON format
- Must match expected schema
- File size limitations apply
- UTF-8 encoding required

### System Requirements
- Python 3.13+ installed
- Sufficient disk space for temporary files
- Memory requirements based on presentation size
- Write permissions in output directory

## Development Setup
1. Clone repository
2. Create virtual environment: `python3.13 -m venv venv`
3. Activate virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/macOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Install dev dependencies: `pip install -r requirements-dev.txt`

## Build and Distribution
- Package built using setuptools
- Distributed via PyPI
- Supports pip installation
- Includes binary wheels

## Testing Strategy
- Unit tests with pytest
- Integration tests for core functionality
- Template validation tests
- Error handling tests
- CI/CD pipeline integration
