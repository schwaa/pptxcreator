# PPTX Creator

A command-line tool to convert Markdown content into professional PowerPoint presentations using AI-powered layout selection.

## Features

- Convert Markdown to PowerPoint presentations.
- AI-powered content analysis and layout selection (OpenRouter LLM).
- Project-based workflow: each presentation is a project directory.
- Custom PowerPoint template support.
- Dual image support:
  - Manual: Include your own images via Markdown syntax
  - AI-Generated: Automatic image generation via Stable Diffusion Forge
- Extensible and testable Python codebase.

## Requirements

- Python 3.10+
- pip
- An OpenRouter API key (set as `OPENROUTER_API_KEY` in a `.env` file)
- Git (for cloning)

## Installation

1. **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/pptx-creator.git
    cd pptx-creator
    ```

2. **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    # For development:
    pip install -r requirements-dev.txt
    ```

4. **Set up your API key:**
    - Create a file named `.env` in the project root:
      ```
      OPENROUTER_API_KEY=your-openrouter-api-key-here
      ```

## Usage

The tool uses a project-based approach. Each presentation lives in its own directory under `projects/`.

### Image Handling

The tool supports two ways to include images in your presentations:

1. **Manual Image Inclusion**
   - Place images in your project's `images/` directory
   - Reference them in your Markdown using standard syntax:
     ```markdown
     ![Alt text](images/your_image.png)
     ```

2. **AI Image Generation** (Optional)
   - The system can automatically generate relevant images using Stable Diffusion Forge
   - During content processing, the AI analyzes your content and may generate supporting images
   - Generated images are saved to your project's `images/` directory
   - Requires Stable Diffusion Forge setup (see Configuration below)

### 1. Prepare Your PowerPoint Template

- Place your `.pptx` template in the `templates/` directory (e.g., `templates/my_template.pptx`).
- Ensure slide layouts have clearly named placeholders for best results.

### 2. Create a Project and Add Content

- Create a new directory under `projects/` (e.g., `projects/robotics/`).
- Add your Markdown content as `content.md` in the project directory.
- Place any images in `projects/<project_name>/images/` and reference them in your Markdown:  
  `![Alt text](images/my_image.png)`

### 3. Analyze the Template

```bash
python -m pptx_generator.main analyze <project_name> <template_path>
```
- Example:
  ```bash
  python -m pptx_generator.main analyze robotics templates/my_template.pptx
  ```

This generates `projects/<project_name>/output/layouts.json` describing available layouts and placeholders.

### 4. Process the Markdown Content

```bash
python -m pptx_generator.main process <project_name>
```
- Example:
  ```bash
  python -m pptx_generator.main process robotics
  ```

This generates:
- `projects/<project_name>/output/presentation.json` (slide plan)
- `projects/<project_name>/<project_name>.pptx` (final PowerPoint)

## Configuration

Create a file named `.env` in the project root with:

```env
# Required for content processing
OPENROUTER_API_KEY=your-openrouter-api-key-here
OPENROUTER_MODEL_NAME=deepseek/deepseek-chat-v3-0324:free  # Optional, this is the default

# Optional: for AI image generation
SD_FORGE_SERVER_URL=http://your-sd-forge-server:7860
FLUX_MODEL_NAME=black-forest-labs/FLUX.1-schnell  # Optional, this is the default
```

## File Structure

```
pptx-creator/
├── pptx_generator/
│   ├── __main__.py
│   ├── analyzer.py
│   ├── generator.py
│   ├── main.py
│   ├── models.py
│   ├── processor.py
│   └── utils.py
├── projects/
│   └── <project_name>/
│       ├── content.md
│       ├── images/
│       └── output/
├── templates/
│   └── <your_template>.pptx
├── scripts/
├── tests/
├── requirements.txt
├── requirements-dev.txt
├── .env
└── README.md
```

## Testing

Run all tests with:
```bash
pytest
```

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/YourFeature`).
3. Commit your changes.
4. Push to your branch.
5. Open a Pull Request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
