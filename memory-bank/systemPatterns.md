# System Patterns

## Architecture Overview & Data Flow
The system follows a three-stage CLI-driven process: `analyze`, `process`, and `generate`.

```mermaid
flowchart TD
    UserInputMd[User Input: content.md] --> B(main.py process)
    UserInputTmpl[User Input: template.pptx] --> A(main.py analyze)
    
    A -- template_filepath --> Analyzer(analyzer.py)
    Analyzer -- layouts.json (incl. source_template_path) --> ProjectFiles1[/projects/project_name/output/layouts.json/]
    
    ProjectFiles1 --> B
    UserInputMd --> B
    B -- markdown_content, layout_definitions --> Processor(processor.py w/ LLM)
    Processor -- presentation.json --> ProjectFiles2[/projects/project_name/output/presentation.json/]

    subgraph "Processor Internals (Agentic Workflow)"
        direction LR
        MarkdownChunk[Markdown Chunk] --> PlanLLM{call_planning_llm}
        LayoutsJsonIn[layouts.json] --> PlanLLM
        PlanLLM -- SlidePlan (Pydantic) --> ExecutePlan{Execute Plan}
        ExecutePlan -- Optional ImageGenerationRequest --> ImageGen[Optional: generate_and_save_image]
        ImageGen -- Optional image_path --> DesignLLM{call_designer_llm}
        SlidePlan --> DesignLLM
        LayoutsJsonIn --> DesignLLM
        DesignLLM -- FinalSlide (Pydantic) --> FinalSlideOutput[FinalSlide.model_dump()]
        FinalSlideOutput --> Processor
    end
    
    ProjectFiles2 --> C(main.py generate)
    ProjectFiles1 -- source_template_path --> C
    C -- presentation_plan, template_filepath --> Generator(generator.py)
    Generator -- final.pptx --> Output[/projects/project_name/output/project_name.pptx/]

    subgraph "Stage 1: Analyze Template"
        direction LR
        UserInputTmpl --> A
        A --> Analyzer
        Analyzer --> ProjectFiles1
    end

    subgraph "Stage 2: Process Content"
        direction LR
        UserInputMd --> B
        ProjectFiles1 --> B
        B --> Processor
        Processor --> ProjectFiles2
    end

    subgraph "Stage 3: Generate Presentation"
        direction LR
        ProjectFiles2 --> C
        ProjectFiles1 --> C
        C --> Generator
        Generator --> Output
    end
```

## Component Specifications

### 1. Template Analyzer (`analyzer.py`)
- **Purpose:** Extract template layout information and store the source template path.
- **Input:** Path to a PPTX template file.
- **Output:** `layouts.json` file containing:
    - `source_template_path`: Path to the input PPTX template.
    - `layouts`: A list of available layouts, each with a `name` and a list of `placeholders` (names).
- **Key Logic:** Uses `python-pptx` to inspect slide masters and layouts.

### 2. Content Processor (`processor.py`)
- **Purpose:** Convert markdown content into a structured presentation plan using an agentic, multi-step LLM process with Pydantic validation, guided by available layouts.
- **Input:**
    - Path to `content.md` (processed in chunks).
    - Path to `layouts.json` (provides layout definitions).
- **Output:** `presentation.json` file containing:
    - `slides`: A list of slide definitions, each conforming to the `FinalSlide` Pydantic model structure (see Data Contracts below).
- **Key Logic (Agentic Workflow):**
    - The `process_content` function iterates through markdown chunks (separated by `---`).
    - **Step 1: Planning Agent (`call_planning_llm`)**
        - Input: A markdown chunk, `layouts_json`.
        - LLM (e.g., GPT-4 Turbo via OpenRouter) is called with a focused prompt.
        - Output: A `SlidePlan` Pydantic model, validated directly with Pydantic. This model includes `slide_topic`, `content_type`, `raw_content`, and an optional `image_request` (which itself is an `ImageGenerationRequest` Pydantic model detailing an image prompt).
    - **Step 2: Tool Use (Image Generation - Optional)**
        - If `SlidePlan.image_request` is present, the `generate_and_save_image` helper function is called with the prompt from `ImageGenerationRequest`.
        - Output: Path to the generated image.
    - **Step 3: Designer Agent (`call_designer_llm`)**
        - Input: The `SlidePlan`, the optional `image_path` from Step 2, and `layouts_json`.
        - LLM is called with a prompt focused on generating the final slide structure.
        - Output: A `FinalSlide` Pydantic model, validated directly with Pydantic. This model contains the chosen `layout` (string) and `placeholders` (dictionary mapping placeholder names to content, which can be text, lists of text, or an image path).
    - The `FinalSlide.model_dump()` is appended to the `slides` list in `presentation.json`.
    - Pydantic is used directly to ensure LLM outputs conform to the expected models (`SlidePlan`, `FinalSlide`).
    - A new `pptx_generator/models.py` file defines these Pydantic models: `ImageGenerationRequest`, `SlidePlan`, `FinalSlide`.
    - Fallback parsing logic might be adjusted or simplified due to Pydantic validation.

### 3. Presentation Generator (`generator.py`)
- **Purpose:** Create the final PPTX presentation by populating a template with content from the presentation plan.
- **Input:**
    - Path to `presentation.json`.
    - Path to the source PPTX template file.
- **Output:** Final `.pptx` file.
- **Key Logic:**
    - Uses `python-pptx` to add slides based on layout names from `presentation.json`.
    - Populates placeholders on each slide by matching names from the `placeholders` dictionary in `presentation.json` to `shape.name`.
    - Handles text and list-of-text content. Basic image handling (uses string as alt-text if image file not found).

## Data Contracts

### 1. `layouts.json`
**Purpose:** Define available template layouts, placeholders, and the source template path.
```json
{
  "source_template_path": "templates/default_template.pptx",
  "layouts": [
    {
      "name": "Title Slide",
      "placeholders": [
        "Title 1",
        "Subtitle 2"
      ]
    },
    {
      "name": "Title and Content",
      "placeholders": [
        "Title 1",
        "Content Placeholder 2"
      ]
    }
    // ... more layouts
  ]
}
```

### 2. `presentation.json`
**Purpose:** Define presentation content and structure, mapping content to specific placeholders in chosen layouts. This structure will reflect the `FinalSlide.model_dump()` output from the new agentic processor.
```json
{
  "slides": [
    {
      "layout": "Title Slide", // From FinalSlide.layout
      "placeholders": {        // From FinalSlide.placeholders
        "Title 1": "The Future of AI",
        "Subtitle 2": "A Presentation by Jane Doe"
      }
    },
    {
      "layout": "Title and Content",
      "placeholders": {
        "Title 1": "Key Developments",
        "Content Placeholder 2": [
            "Rise of Transformers",
            "Open Source Models",
            "Multimodal Capabilities"
        ],
        "ImagePlaceholder1": "path/to/generated_or_existing_image.jpg" // Example if image was part of FinalSlide
      }
    }
    // ... more slides
  ]
}
```
*Note: The key for the content map per slide is `placeholders`. The structure of each slide object will conform to the `FinalSlide` Pydantic model.*

## Design Patterns
- **CLI Facade (`main.py`):** Simplifies user interaction with the three-stage process.
- **Agentic Workflow (in `processor.py`):** A multi-step process where an "agent" (the `process_content` function) uses specialized LLM calls (Planning Agent, Designer Agent) and Pydantic models to make decisions, execute actions (like image generation), and format outputs for each slide.
- **Pydantic Models (in `models.py`):** Used for data validation and to define clear, structured inputs and outputs for LLM interactions, enforced directly by Pydantic.
- **Strategy Pattern (in `processor.py` - potentially evolving):** The LLM-based processing is primary. The rule-based fallback might be re-evaluated or simplified given the robustness introduced by Pydantic validation at each LLM step.
- **Data-Driven Configuration:** `layouts.json` and `presentation.json` drive the generation process.

## Error Handling Strategy
- Input validation at each stage (file existence, basic format checks).
- `try-except` blocks for file I/O and LLM communication.
- Fallback parser in `processor.py` if LLM fails or returns malformed data.
- Logging for warnings and errors.
