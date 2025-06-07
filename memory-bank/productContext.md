# Product Context

## Purpose
The PPTX Generator automates PowerPoint presentation creation from markdown content, ensuring consistency in branding and layout through a template-driven approach. It serves users who need to generate multiple presentations efficiently.

**Current Status:**
The tool now successfully implements a three-stage process:
1.  **Analyze:** A PPTX template is analyzed to produce a `layouts.json` file, which details its available layouts, placeholders, and stores the path to the source template.
2.  **Process:** Markdown content (`content.md`) is processed along with the `layouts.json` (for layout definitions) using an LLM (OpenRouter, model: `deepseek/deepseek-chat-v3-0324:free`) to create a structured `presentation.json`. This JSON file maps content to specific placeholders within chosen layouts.
3.  **Generate:** The `presentation.json` and the original template (path retrieved from `layouts.json`) are used to generate the final PPTX file with content populated.

## Problems Solved
1.  **Manual PowerPoint Creation Overhead:**
    *   Automates slide creation and content population from markdown.
    *   Reduces human error.
    *   Saves time for frequent presentation generation.
2.  **Consistency Management:**
    *   Ensures brand and layout consistency via templates.
    *   Standardizes presentation structure.
3.  **Content Structuring and Integration:**
    *   Converts unstructured markdown into a structured presentation plan (`presentation.json`).
    *   Bridges markdown content with visual presentation layouts.

## User Experience Goals
1.  **Simplicity:**
    *   Clear three-step CLI workflow (`analyze`, `process`, `generate`).
    *   User provides markdown and a template; the system handles the rest.
    *   Informative feedback during execution.
2.  **Reliability:**
    *   Consistent output based on inputs.
    *   Improved error handling and data validation.
3.  **Flexibility:**
    *   Supports various template designs (as long as they have identifiable layouts and placeholders).
    *   Handles text content, including bulleted lists. (Image handling is basic, next focus area).
4.  **Efficiency:**
    *   Automates the core generation process.
    *   Reduces manual intervention significantly.
