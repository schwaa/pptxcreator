# PPTX Creator

A command-line tool to convert Markdown content into professional PowerPoint presentations using AI-powered layout selection (via OpenRouter) and customizable templates.

## Features

-   Convert Markdown to PowerPoint presentations.
-   AI-powered content analysis and layout selection using OpenRouter (model: `deepseek/deepseek-chat-v3-0324:free`).
-   Template-driven design for consistent branding.
-   Project-based organization for managing multiple presentations.
-   Three-step CLI process: `analyze` template, `process` content, `generate` presentation.

## Requirements

-   Python 3.13+
-   An OpenRouter API key (set as `OPENROUTER_API_KEY` in a `.env` file).
-   Git (for cloning).

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/pptx-creator.git # Replace with your actual repo URL
    cd pptx-creator
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3.13 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    # For development (e.g., running tests), also install:
    # pip install -r requirements-dev.txt
    ```

4.  **Set up your API key:**
    Create a file named `.env` in the root of the `pptx-creator` directory with your OpenRouter API key:
    ```env
    OPENROUTER_API_KEY="your-openrouter-api-key-here"
    ```
    This file is already in `.gitignore` to prevent accidental commits of your key.

## Project Structure

The tool uses a project-based approach. Each presentation you create will reside in its own directory under `projects/`.

```
pptx-creator/
├── pptx_generator/           # Core package code
│   ├── main.py               # CLI entry point
│   ├── analyzer.py           # Template analysis logic
│   ├── processor.py          # Content processing (LLM)
│   └── generator.py          # PPTX generation
├── projects/                  # Your presentations live here
│   └── <your_project_name>/   # A specific presentation project (e.g., "robotics_report")
│       ├── content.md        # Your markdown content for this project
│       ├── images/           # (Optional) Store images referenced in content.md here
│       └── output/           # Generated files for this project
│           ├── layouts.json      # Analysis of the template used
│           ├── presentation.json # Structured plan from your markdown
│           └── <your_project_name>.pptx # The final PowerPoint file
├── templates/                 # Store your PowerPoint (.pptx) templates here
│   └── default_template.pptx # An example template
├── .env                       # Stores your API key (you create this)
├── requirements.txt           # Dependencies
└── README.md                  # This file
```

## Usage Workflow

The process involves three main commands, all run from the root `pptx-creator` directory:

**Step 0: Prepare Your Content and Template**

1.  **Create a PowerPoint Template (`.pptx`):**
    *   Design your template with various slide layouts (e.g., Title Slide, Title and Content, Section Header, Content with Picture).
    *   Ensure placeholders within these layouts have distinct names if possible (View -> Slide Master -> Select Layout -> Click on placeholder -> Selection Pane to see/edit name). This helps with accurate content mapping.
    *   Place your template in the `templates/` directory (e.g., `templates/my_custom_template.pptx`) or note its full path.

2.  **Prepare Your Markdown (`content.md`):**
    *   For a new presentation, decide on a `project_name` (e.g., `annual_review`). The tool will create `projects/<project_name>/` if it doesn't exist.
    *   Create a `projects/<project_name>/content.md` file with your presentation content using standard Markdown.
    *   **Images:** If you use images, you can use standard Markdown syntax: `![Alt text for image](images/my_image.png)`.
        *   Place the actual image files (e.g., `my_image.png`) inside `projects/<project_name>/images/`.
        *   The `generator.py` script will attempt to find images relative to this `images/` folder within your project. The LLM currently uses the alt text or image description from the markdown for the `presentation.json`. (Future improvements will aim for the LLM to pass through the actual image path).

**Step 1: Analyze Your Template**

This step inspects your `.pptx` template and creates a `layouts.json` file for your project. This file tells the system about the available slide layouts and their placeholders, and also stores the path to the template that was analyzed.

```bash
python -m pptx_generator.main analyze <project_name> <template_specifier>
```

*   `<project_name>`: The name of your project (e.g., `annual_review`).
*   `<template_specifier>`:
    *   Either the name of a template file in the `templates/` directory (e.g., `default_template.pptx`).
    *   Or the full path to a `.pptx` template file (e.g., `/path/to/your/custom_template.pptx`).

**Example:**
```bash
python -m pptx_generator.main analyze annual_review default_template.pptx
```
This will create `projects/annual_review/output/layouts.json`.

**Step 2: Process Your Markdown Content**

This step takes your `projects/<project_name>/content.md` and the `layouts.json` (for layout definitions) and uses an LLM to create a structured `presentation.json`. This JSON file outlines which content goes into which placeholder on which slide layout.

```bash
python -m pptx_generator.main process <project_name>
```

*   `<project_name>`: The name of your project (must match the one used in the `analyze` step).

**Example:**
```bash
python -m pptx_generator.main process annual_review
```
This requires `projects/annual_review/content.md` and `projects/annual_review/output/layouts.json` to exist. It will create `projects/annual_review/output/presentation.json`.

**Step 3: Generate the PowerPoint Presentation**

This final step uses the `presentation.json` and the original template (whose path was stored in `layouts.json`) to generate the final `.pptx` file.

```bash
python -m pptx_generator.main generate <project_name>
```

*   `<project_name>`: The name of your project.

**Example:**
```bash
python -m pptx_generator.main generate annual_review
```
This requires `projects/annual_review/output/presentation.json` and `projects/annual_review/output/layouts.json` to exist. It will create `projects/annual_review/output/annual_review.pptx`.

## Key Data Files Explained

*   **`projects/<project_name>/content.md` (Input):** Your raw presentation content in Markdown.
*   **`templates/<template_name>.pptx` (Input):** Your PowerPoint template.
*   **`projects/<project_name>/output/layouts.json` (Intermediate):**
    *   Generated by the `analyze` command.
    *   Contains `source_template_path` (path to the PPTX template used).
    *   Contains `layouts`: an array of available slide layouts from the template, each with its `name` and an array of its `placeholders` (names of placeholder shapes).
*   **`projects/<project_name>/output/presentation.json` (Intermediate):**
    *   Generated by the `process` command.
    *   Contains `slides`: an array of slide plans. Each slide plan specifies the `layout` name to use and a `placeholders` dictionary. This dictionary maps placeholder names (e.g., "Title 1", "Content Placeholder 2") to the content (string or list of strings for text, or a descriptive string for images that `generator.py` tries to resolve).
*   **`projects/<project_name>/output/<project_name>.pptx` (Output):** The final generated PowerPoint presentation.

## Troubleshooting & Known Issues

*   **API Key:** Ensure `OPENROUTER_API_KEY` is correctly set in your `.env` file in the project root.
*   **Template Placeholders:** For best results, ensure your PPTX template layouts have clearly named placeholders. Unnamed or generically named placeholders might lead to less predictable content mapping.
*   **Image Handling:**
    *   The system currently relies on the LLM to interpret image references in markdown. The `generator.py` script then attempts to find image files based on the string provided by the LLM for picture placeholders.
    *   Place images in `projects/<project_name>/images/` and reference them like `![alt text](images/my_image.png)` in your `content.md`.
    *   If an image file is not found, the picture placeholder will likely remain empty (descriptive text will not be inserted into picture placeholders).
*   **LLM Output:** The quality of the `presentation.json` (and thus the final PPTX) depends on the LLM's ability to structure the content appropriately. The `processor.py` includes a basic fallback parser if the LLM output is unusable.

## Contributing

Contributions are welcome! Please follow these steps:
1.  Fork the repository.
2.  Create a feature branch (`git checkout -b feature/AmazingFeature`).
3.  Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4.  Push to the branch (`git push origin feature/AmazingFeature`).
5.  Open a Pull Request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
