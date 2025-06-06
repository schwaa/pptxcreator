# PPTX Generator

A command-line tool to convert Markdown content into professional PowerPoint presentations using AI-powered layout selection and customizable templates.

## Features

- Convert Markdown to PowerPoint presentations
- AI-powered content analysis and layout selection
- Template-driven design for consistent branding
- Local processing with fallback mechanisms
- Project-based organization

## Installation

1. **Prerequisites:**
   - Python 3.13+
   - An OpenAI API key for AI features
   
2. **Clone the repository:**
   ```bash
   git clone [your-repo-url]
   cd pptx-generator
   ```

3. **Create a virtual environment:**
   ```bash
   python3.13 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up your API key:**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   # Or use --api-key when running the processor
   ```

## Project Structure

```
pptx-generator/
├── projects/                  # All presentations live here
│   └── example_presentation/
│       ├── content.md        # Your markdown content
│       ├── images/           # Images referenced in markdown
│       └── output/           # Generated files
│           ├── layouts.json
│           ├── presentation.json
│           └── final_deck.pptx
├── templates/                 # Your PowerPoint templates
│   └── default_template.pptx
└── pptx_generator/           # Core package code
    ├── analyzer.py
    ├── processor.py
    ├── generator.py
    └── main.py
```

## Usage

The conversion process happens in three steps:

### 1. Template Analysis

First, analyze your PowerPoint template to understand available layouts:

```bash
python -m pptx_generator analyze \
  --template templates/your_template.pptx \
  --output projects/your_project/output/layouts.json
```

### 2. Content Processing

Convert your Markdown into a structured presentation plan:

```bash
python -m pptx_generator process \
  --markdown projects/your_project/content.md \
  --layouts projects/your_project/output/layouts.json \
  --output projects/your_project/output/presentation.json \
  --api-key "your-api-key"
```

### 3. Presentation Generation

Generate the final PowerPoint file:

```bash
python -m pptx_generator generate \
  --presentation projects/your_project/output/presentation.json \
  --template templates/your_template.pptx \
  --output projects/your_project/output/final_deck.pptx
```

## Markdown Format

Your Markdown content should use standard formatting:

```markdown
# Title of Presentation
## Subtitle
By Author Name

---

# Section Title
- Bullet point 1
- Bullet point 2
- Bullet point 3

---

# Image Slide
![Description](images/example.png)
Additional text description

---

# Next Steps
1. First action item
2. Second action item
3. Third action item
```

## Template Requirements

- Use PowerPoint (.pptx) templates only
- Define clear layouts with named placeholders
- Include at least:
  - Title slide layout
  - Section header layout
  - Content slide layout
  - Image with caption layout

## Error Handling

The system includes robust error handling:

- Template validation during analysis
- Fallback to rule-based processing if AI fails
- Clear error messages and suggestions
- Default layouts when specific layouts unavailable

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
