import os
import json
import argparse
import logging
from openai import OpenAI

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# This prompt template is critical for guiding the LLM's response format
PROMPT_TEMPLATE = """
You are an expert presentation designer's assistant. Your task is to convert raw Markdown content into a structured JSON object for a PowerPoint generator.

You will be given the user's Markdown content and a JSON object describing the available slide layouts in the PowerPoint template.

Your goal is to:
1.  Read the Markdown and split it into logical slides.
2.  For each slide, choose the most appropriate layout from the available layouts.
3.  Create a JSON object for each slide that specifies the chosen layout and maps the slide's content to the correct placeholder names for that layout.

**RULES FOR YOUR RESPONSE:**
- Your entire output MUST be a single, valid JSON object and nothing else. Do not include any introductory text, explanations, or code formatting like ```json.
- The root of the JSON object must be a key named "slides", which is an array of slide objects.
- Each slide object in the array must have two keys: "layout" and "content".
- The "layout" value must be a string that EXACTLY matches one of the layout names from the provided available layouts.
- The "content" value must be a dictionary. The keys of this dictionary MUST EXACTLY match the placeholder names (e.g., "Title 1", "Content Placeholder 2", "Picture Placeholder 7") available for the chosen layout.
- If the Markdown references an image (e.g., ![alt text](path/to/image.png)), the value for the corresponding picture placeholder should be the image path string: "path/to/image.png".

---
**AVAILABLE LAYOUTS:**
{layouts_json}

---
**MARKDOWN CONTENT:**
{markdown_content}
---

Now, generate the JSON object based on the rules and content above.
"""

def simple_fallback_parser(markdown_content: str, layouts: dict) -> dict:
    """
    A non-AI fallback that splits Markdown by '---' and uses a default layout.
    This makes the tool more robust if the LLM fails.
    """
    logging.warning("LLM processing failed. Falling back to simple parser.")
    
    # Try to find a "Title and Content" layout, otherwise grab the second layout available
    default_layout_name = "Title and Content"
    title_placeholder = "Title 1"
    body_placeholder = "Content Placeholder 2"

    layout_found = False
    for layout in layouts.get('layouts', []):
        if layout['name'] == default_layout_name:
            # Find the most common placeholder names
            for p_name in layout['placeholders']:
                if 'title' in p_name.lower():
                    title_placeholder = p_name
                elif 'content' in p_name.lower() or 'body' in p_name.lower():
                    body_placeholder = p_name
            layout_found = True
            break
    
    if not layout_found and len(layouts.get('layouts', [])) > 1:
        # Fallback to just using the second layout in the list (first is often title-only)
        default_layout_name = layouts['layouts'][1]['name']
        title_placeholder = layouts['layouts'][1]['placeholders'][0]
        body_placeholder = layouts['layouts'][1]['placeholders'][1]

    presentation_data = {"slides": []}
    slides = markdown_content.split('\n---\n') # Split by horizontal rule

    for slide_md in slides:
        lines = slide_md.strip().split('\n')
        title = lines[0].lstrip('# ').strip()
        body = "\n".join(lines[1:]).strip()

        slide_obj = {
            "layout": default_layout_name,
            "content": {
                title_placeholder: title,
                body_placeholder: body
            }
        }
        presentation_data["slides"].append(slide_obj)
        
    logging.info(f"Fallback parser created {len(presentation_data['slides'])} slides.")
    return presentation_data

def process_content(markdown_file: str, layouts_file: str, output_file: str, api_key: str):
    """
    Reads markdown and layout files, calls an LLM to generate a presentation plan,
    and saves it as a JSON file.
    """
    try:
        with open(markdown_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
    except FileNotFoundError:
        logging.error(f"Markdown file not found: {markdown_file}")
        return

    try:
        with open(layouts_file, 'r', encoding='utf-8') as f:
            layouts_data = json.load(f)
    except FileNotFoundError:
        logging.error(f"Layouts file not found: {layouts_file}")
        return

    layouts_json_str = json.dumps(layouts_data, indent=2)

    # 1. Construct the prompt
    prompt = PROMPT_TEMPLATE.format(
        layouts_json=layouts_json_str,
        markdown_content=markdown_content
    )

    presentation_data = None
    try:
        # 2. Call the LLM
        logging.info("Sending request to LLM. This may take a moment...")
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4-turbo",  # Or another model like "gpt-3.5-turbo"
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2, # Lower temperature for more deterministic, structured output
            response_format={"type": "json_object"} # Use JSON mode if available
        )
        response_content = response.choices[0].message.content
        logging.info("LLM response received.")

        # 3. Parse and validate the response
        presentation_data = json.loads(response_content)
        # Basic validation
        if 'slides' not in presentation_data or not isinstance(presentation_data['slides'], list):
            raise ValueError("LLM output is missing 'slides' array.")
        logging.info(f"LLM successfully generated {len(presentation_data['slides'])} slides.")

    except Exception as e:
        logging.error(f"An error occurred during LLM processing: {e}")
        # 4. Use the fallback if the LLM fails
        presentation_data = simple_fallback_parser(markdown_content, layouts_data)

    # 5. Write the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(presentation_data, f, indent=2, ensure_ascii=False)
    
    logging.info(f"Presentation plan saved successfully to {output_file}")

def main():
    """Main entry point for the processor script."""
    parser = argparse.ArgumentParser(description="Process Markdown content into a presentation.json file using an LLM.")
    parser.add_argument('--markdown', required=True, help="Path to the input Markdown file.")
    parser.add_argument('--layouts', required=True, help="Path to the layouts.json file.")
    parser.add_argument('--output', default='presentation.json', help="Path for the output presentation.json file.")
    parser.add_argument('--api-key', help="Your OpenAI API key. Can also be set via OPENAI_API_KEY environment variable.")
    
    args = parser.parse_args()

    # Get API key from argument or environment variable
    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        logging.error("API Key is required. Please provide it with --api-key or set OPENAI_API_KEY.")
    else:
        process_content(args.markdown, args.layouts, args.output, api_key)

if __name__ == '__main__':
    main()
