# Active Context

## Current Work Focus
The core functionality of the three-component architecture (analyze, process, generate) is stable. The current focus is an **Architectural Refactoring: Implementing an Agentic Workflow for `processor.py`**. This change is foundational for improving system intelligence, reliability, and will provide a more robust framework for future enhancements like advanced image handling.

### Current Implementation Phase: Agentic Refactoring
- Define Pydantic models for structured LLM interaction (`SlidePlan`, `FinalSlide`, `ImageGenerationRequest`) in `pptx_generator/models.py`.
- Refactor `processor.py` to use a two-pass LLM approach:
    1. `call_planning_llm` to generate a `SlidePlan`.
    2. `call_designer_llm` to generate a `FinalSlide` based on the plan and any generated assets (e.g., images).
- Integrate `pydantic-ai` (or relevant Pydantic AI modules) to ensure LLM outputs conform to these Pydantic models.
- Update `presentation.json` structure to reflect `FinalSlide.model_dump()`.

```mermaid
graph TD
    A[Current Focus] --> B[Architectural Refactoring: Agentic Workflow]
    B --> C[Define Pydantic Models (models.py)]
    B --> D[Refactor processor.py (Agentic Loop)]
    D --> D1[call_planning_llm -> SlidePlan]
    D --> D2[Optional Image Generation]
    D --> D3[call_designer_llm -> FinalSlide]
    B --> E[Integrate 'pydantic-ai']
    B --> F[Update presentation.json Structure]
    B --> G[Update Memory Bank (SystemPatterns, TechContext, etc.)]
```

## Component Architecture & Data Flow (Confirmed)

### 1. Template Analysis (`analyzer.py`)
- **Input:** Template PPTX path.
- **Output:** `projects/<project_name>/output/layouts.json` containing `source_template_path` and layout definitions (name, list of placeholder names).
- **Command:** `python -m pptx_generator.main analyze <project_name> <template_path_or_name>`

### 2. Content Processing (`processor.py`)
- **Input:** `projects/<project_name>/content.md` (processed in chunks), `projects/<project_name>/output/layouts.json` (provides layout definitions).
- **Output:** `projects/<project_name>/output/presentation.json` where each slide object is a `FinalSlide.model_dump()`.
- **LLM Interaction (Agentic):**
    - Uses OpenRouter (e.g., `gpt-4-turbo` or preferred model) via `openai` client, integrated with `pydantic-ai`.
    - **`call_planning_llm`:** Takes markdown chunk and layout definitions, returns `SlidePlan` Pydantic model using `pydantic-ai`.
    - **`call_designer_llm`:** Takes `SlidePlan`, optional image path, and layout definitions, returns `FinalSlide` Pydantic model using `pydantic-ai`.
- **Key Logic:**
    - New `pptx_generator/models.py` defines `ImageGenerationRequest`, `SlidePlan`, `FinalSlide` Pydantic models.
    - `process_content` orchestrates the agentic loop: plan -> (optional tool use/image gen) -> design.
    - `pydantic-ai` ensures LLM outputs adhere to Pydantic models.
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
- **Refactor `processor.py` to an agentic workflow using Pydantic models (`SlidePlan`, `FinalSlide`) and `pydantic-ai` (or relevant Pydantic AI modules) for improved reliability, intelligence, and structured LLM interaction.**
- **Update `presentation.json` structure to directly reflect `FinalSlide.model_dump()` output for each slide.**
- Maintain current JSON structure for `layouts.json`.

## Current Considerations
- **Prompt Engineering for Agentic Calls:** Crafting effective prompts for `call_planning_llm` and `call_designer_llm` will be crucial for accurate Pydantic model population.
- **Image Handling within Agentic Flow:** The `SlidePlan` (with `ImageGenerationRequest`) and `FinalSlide` models will provide the structure for deciding when to generate images and how to include their paths in the final slide data. Robust path resolution in `generator.py` will still be needed.
- **Testing the Agentic Workflow:** New tests will be required for `models.py`, the new LLM calling functions, and the overall `process_content` loop in `processor.py`.
- **Error Handling with Pydantic/pydantic-ai:** Leverage Pydantic's validation errors and `pydantic-ai`'s retry/error handling mechanisms for robust error handling during LLM calls.

## Immediate Next Steps
1.  **Memory Bank Update:** (This update) Document the planned agentic architecture.
2.  **Implement Agentic Workflow in `processor.py` (Primary Focus):**
    *   Create `pptx_generator/models.py` with `ImageGenerationRequest`, `SlidePlan`, and `FinalSlide` Pydantic models.
    *   Implement `call_planning_llm` in `processor.py` to return a `SlidePlan`.
    *   Implement `call_designer_llm` in `processor.py` to return a `FinalSlide`.
    *   Refactor the `process_content` loop in `processor.py` to orchestrate the agentic flow.
    *   Ensure `pydantic-ai` is used with the OpenAI client to validate LLM responses against these models.
    *   Update `presentation.json` saving logic to use `FinalSlide.model_dump()`.
3.  **Image Handling Refinement (Post-Agentic Refactor):**
    *   Leverage the `ImageGenerationRequest` in `SlidePlan` and image path handling in `FinalSlide`.
    *   Enhance `generator.py` for robust image file location and embedding.
4.  **Expand Test Suite:**
    *   Add unit tests for `models.py`.
    *   Add unit tests for `call_planning_llm` and `call_designer_llm` (possibly with mocked LLM responses).
    *   Update integration tests for the `process` command.
5.  **Error Handling and UX Refinements:**
    *   Integrate Pydantic validation errors into user feedback.

## Open Questions
- What are the optimal prompt designs for `call_planning_llm` (to generate `SlidePlan`) and `call_designer_llm` (to generate `FinalSlide`) to ensure accurate Pydantic model population by the LLM?
- How will `pydantic-ai`'s retry mechanisms (if available) be configured for handling transient LLM issues?
- How should image filenames be uniquely generated if `generate_and_save_image` is called multiple times within a single `process` run?

## Blockers
None currently. The main functionality is working.
