# Active Context

## Current Work Focus
The core functionality of the three-component architecture (analyze, process, generate) is now largely in place and producing presentations with content. Current focus is on ensuring robustness, refining image handling, and preparing for more comprehensive testing.

### Current Implementation Phase: Stabilization and Refinement
- Verification of data flow between components.
- Ensuring `presentation.json` structure is consistently produced and consumed.
- Basic image placeholder handling (text description populates placeholder if image file not found).

```mermaid
graph TD
    A[Current Focus] --> B[System Stability & Refinement]
    B --> C[Verify Data Contracts (layouts.json, presentation.json)]
    B --> D[Refine Image Handling in Generator]
    B --> E[Comprehensive Testing]
    B --> F[Memory Bank Update - In Progress]
```

## Component Architecture & Data Flow (Confirmed)

### 1. Template Analysis (`analyzer.py`)
- **Input:** Template PPTX path.
- **Output:** `projects/<project_name>/output/layouts.json` containing `source_template_path` and layout definitions (name, list of placeholder names).
- **Command:** `python -m pptx_generator.main analyze <project_name> <template_path_or_name>`

### 2. Content Processing (`processor.py`)
- **Input:** `projects/<project_name>/content.md`, `projects/<project_name>/output/layouts.json` (provides layout definitions to LLM).
- **Output:** `projects/<project_name>/output/presentation.json` containing slide plans (layout name, `placeholders` dictionary mapping placeholder name to content).
- **LLM Interaction:** Uses OpenRouter (model: `deepseek/deepseek-chat-v3-0324:free`) via `openai` library.
- **Key Logic:** `ast.literal_eval` for stringified lists, fallback parser.
- **Command:** `python -m pptx_generator.main process <project_name>`

### 3. Presentation Generation (`generator.py`)
- **Input:** `projects/<project_name>/output/presentation.json`, Template PPTX path (sourced from `layouts.json` by `main.py`).
- **Output:** `projects/<project_name>/output/<project_name>.pptx`.
- **Key Logic:** Reads `"placeholders"` key from `presentation.json` for content.
- **Command:** `python -m pptx_generator.main generate <project_name>`

## Recent Key Fixes & Learnings
1.  **`processor.py`:**
    *   Implemented `ast.literal_eval` to correctly parse stringified lists from LLM output.
    *   Updated `fallback_parser` to use a valid layout name (e.g., `"Title, Content 1"` for `default_template.pptx`).
    *   Ensured `layouts.json` content (layout definitions) is passed to LLM, not the path.
2.  **`generator.py`:**
    *   Corrected key access in `presentation.json` from `slide_plan.get("content", {})` to `slide_plan.get("placeholders", {})`. This was the primary fix for blank slides.
    *   Added detailed logging for placeholder matching and content filling.
    *   Improved text handling (clearing text_frame, list iteration).
    *   Basic image insertion logic (uses string as alt-text if image file not found).
3.  **`main.py` Data Flow:**
    *   Confirmed `generate` command correctly sources `template_filepath` from `layouts.json`'s `source_template_path` key.
4.  **Overall:** The system now successfully generates presentations with text content based on markdown input, LLM processing, and template analysis.

## Active Decisions
- Continue with the three-component CLI structure (`analyze`, `process`, `generate`).
- Maintain current JSON structures for `layouts.json` and `presentation.json`.

## Current Considerations
- **Image Handling:** The current image path resolution in `generator.py` is basic. Needs to be more robust (e.g., handling paths relative to `content.md`, project's `images/` folder, or absolute paths). The LLM also needs to be prompted to provide actual image file names/paths rather than descriptions if images are to be embedded.
- **Testing:** Need to expand test coverage, especially for integration tests across the three commands and for different template structures.
- **Error Handling:** While improved, continue to refine error messages and recovery paths.

## Immediate Next Steps
1.  **Finalize Memory Bank Update:** Complete updates for all memory bank files.
2.  **Image Handling Refinement (Next Major Task):**
    *   Decide on a strategy for how image paths are specified in `content.md` and represented in `presentation.json`.
    *   Update `processor.py` (LLM prompt) if necessary to extract image filenames.
    *   Enhance `generator.py` to robustly find and embed images.
3.  **Expand Test Suite:** Add more test cases.

## Open Questions
- How should users specify image paths in `content.md` for them to be correctly processed and embedded?
- What level of detail should the LLM provide for image placeholders? (Filename vs. description).

## Blockers
None currently. The main functionality is working.
