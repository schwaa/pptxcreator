import os
import json
import re
import logging
import ast # <-- Add this import
from openai import OpenAI
from dotenv import load_dotenv
from .utils import clean_text_for_presentation

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

PROMPT_TEMPLATE = """
You are an expert presentation designer's assistant. Your primary goal is to select the best possible slide layout for a given piece of content and structure the output as a JSON object.

**OUTPUT JSON STRUCTURE:**
The output MUST be a single JSON object with a root key "slides".
"slides" is a JSON array of slide objects.
Each slide object MUST have two keys:
1.  `"layout"`: (string) The name of the layout to use for this slide, chosen from the AVAILABLE LAYOUTS JSON.
2.  `"placeholders"`: (JSON object) A map where keys are placeholder names (strings from the chosen layout's "placeholders" object in AVAILABLE LAYOUTS JSON) and values are the content for those placeholders.

**LAYOUT SELECTION RULES:**
1.  Analyze the user's MARKDOWN CONTENT for a given slide (e.g., is it a title? A paragraph? A list of bullets? An image `![alt text](image.path)`)?
2.  Review the `AVAILABLE_LAYOUTS_JSON`. This file describes each layout, including the `type` (e.g., "TITLE", "BODY", "PICTURE") and percentage-based `left_pct`, `top_pct`, `width_pct`, `height_pct` of its placeholders.
3.  **Make a smart design choice.**
    - If the content is a long list of bullet points, prefer a layout with a large "BODY" or "OBJECT" type placeholder (check `height_pct` and `width_pct`).
    - If the content includes an image (e.g., `![alt text for image](image.png)`), choose a layout with a "PICTURE" placeholder. Consider the `alt text` as the content for this "PICTURE" placeholder. The actual image embedding is handled later.
    - Ensure the chosen layout can accommodate all distinct pieces of content for the slide. For example, if there's a title, body text, and an image, select a layout that has placeholders suitable for all three.
    - Do not choose a "Two Content" or similar layout (e.g., one with two "OBJECT" or "BODY" placeholders side-by-side) if the markdown content for a slide segment is clearly a single block of text and a single image. Instead, find a layout designed for one text block and one picture.
4.  Based on your choice, generate a JSON object for the slide, mapping the content to the correct placeholder names from the chosen layout in `AVAILABLE_LAYOUTS_JSON`.

**CONTENT FORMATTING RULES FOR PLACEHOLDER VALUES:**
1.  **For Bullet Points or Paragraphs:** If the content for a placeholder is a list of items or a paragraph, format its value as a JSON ARRAY of strings. Each string in the array should be a single bullet point or a concise sentence from the paragraph.
    - Example within "placeholders" map: `"Body Placeholder 1": ["First bullet point.", "Second bullet point."]`
    - Example for paragraph: `"Text Placeholder 2": ["This is the first sentence.", "This is the second sentence."]`
2.  **For Titles or Simple Text (including image alt text for PICTURE placeholders):** If the content is a title, a short phrase, or alt text for an image, format its value as a single JSON string.
    - Example within "placeholders" map: `"Title 1": "This is a Title"`
    - Example for image alt text: `"Picture Placeholder 1": "A majestic mountain range at sunset"`
3.  **Cleanup:** Ensure all text in the final JSON is clean plain text. REMOVE all markdown formatting like '-', '*', '#', or '**'.

---
**AVAILABLE LAYOUTS JSON (describes layout names, and for each layout, its placeholders with their types and dimensions):**
{layouts_json}

---
**MARKDOWN CONTENT (segment this into slides and map to layouts/placeholders based on the rules above):**
{markdown_content}
---

**YOUR TASK:**
Generate a single, valid JSON object adhering to the **OUTPUT JSON STRUCTURE**, **LAYOUT SELECTION RULES**, and **CONTENT FORMATTING RULES** above.
"""

# Fallback parser for when LLM fails or is unavailable
def fallback_parser(markdown_content, layouts_data):
    """
    Simple fallback: splits markdown into slides by '---' and uses a dynamically chosen layout.
    """
    slides = []
    
    # Determine a suitable fallback layout and its placeholders
    fallback_layout_name = "Title Slide" # Default default
    title_ph_name = "Title 1" # Default default
    content_ph_name = "Subtitle 2" # Default default

    available_layouts = layouts_data.get("layouts", [])
    
    if available_layouts:
        # The structure of l.get("placeholders", {}) is now a dictionary:
        # {"PlaceholderName1": {"type": "TITLE", ...}, "PlaceholderName2": {"type": "BODY", ...}}
        # So, len(l.get("placeholders", {})) or len(l.get("placeholders", {}).keys()) gives the count.

        # Try to find a 'Title and Content' like layout
        preferred_layouts = [
            l for l in available_layouts
            if "title" in l["name"].lower() and "content" in l["name"].lower() and len(l.get("placeholders", {}).keys()) >= 2
        ]
        if not preferred_layouts: # Try single column general layouts
            preferred_layouts = [
                l for l in available_layouts
                if "general" in l["name"].lower() and "single column" in l["name"].lower() and len(l.get("placeholders", {}).keys()) >= 2
            ]
        if not preferred_layouts: # Try any layout with at least 2 placeholders
            preferred_layouts = [l for l in available_layouts if len(l.get("placeholders", {}).keys()) >= 2]
        
        if preferred_layouts:
            chosen_layout = preferred_layouts[0] # Take the first suitable one
            fallback_layout_name = chosen_layout["name"]
            # Get placeholder names from the keys of the placeholders dictionary
            placeholder_names = list(chosen_layout.get("placeholders", {}).keys())
            if placeholder_names:
                title_ph_name = placeholder_names[0]
            if len(placeholder_names) > 1:
                content_ph_name = placeholder_names[1]
            else: # Only one placeholder, use it for title, content will be appended or ignored
                content_ph_name = None
        else: # Still no good layout, take the first one with at least one placeholder
            first_layout_with_ph = next((l for l in available_layouts if l.get("placeholders", {})), None)
            if first_layout_with_ph:
                fallback_layout_name = first_layout_with_ph["name"]
                placeholder_names = list(first_layout_with_ph.get("placeholders", {}).keys())
                if placeholder_names:
                    title_ph_name = placeholder_names[0]
                content_ph_name = None # No second placeholder for sure if we are in this block
            else: # Absolute fallback: use a generic name, generator might skip
                logging.warning("No suitable fallback layout with placeholders found in layouts_data. Using generic names.")
                fallback_layout_name = "Fallback Layout" 
                title_ph_name = "Title Placeholder"
                content_ph_name = "Content Placeholder"

    logging.info(f"Fallback parser using layout: '{fallback_layout_name}' with title placeholder: '{title_ph_name}' and content placeholder: '{content_ph_name or 'N/A'}'")

    for slide_md in markdown_content.split('---'):
        slide_md = slide_md.strip()
        if not slide_md:
            continue
        lines = slide_md.splitlines()
        title = lines[0].strip('# ').strip() if lines else "Untitled Slide"
        body_lines = [line.strip() for line in lines[1:] if line.strip()]
        
        # Ensure body is an array of strings, even if empty or single line
        if not body_lines:
            body = ["This is sample body text generated to ensure the slide is not empty. Add your own content here."]
        else:
            body = [clean_text_for_presentation(b_line) for b_line in body_lines]

        cleaned_title = clean_text_for_presentation(title)
        
        slide_content = {title_ph_name: cleaned_title}
        if content_ph_name:
            slide_content[content_ph_name] = body if body else [""] # Ensure body is always a list
        elif body: # No dedicated content placeholder, append to title if title_ph exists
             slide_content[title_ph_name] = f"{cleaned_title}\n{'\n'.join(body)}"


        slides.append({
            "layout": fallback_layout_name,
            "placeholders": slide_content
        })
    return {"slides": slides}

def extract_json_from_response(response_content):
    """
    Extracts the first JSON object from a string, even if wrapped in Markdown code fences or with extra text.
    """
    code_block = re.search(r"```(?:json)?\s*({.*?})\s*```", response_content, re.DOTALL)
    if code_block:
        json_str = code_block.group(1)
    else:
        json_match = re.search(r"({.*})", response_content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response_content
    return json_str

def call_llm(system_prompt, user_prompt): # model_name parameter removed
    """
    Calls the LLM (OpenRouter) to process the content.
    The model name is now sourced from the OPENROUTER_MODEL_NAME environment variable.
    """
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        logging.error("OPENROUTER_API_KEY not found in environment variables.")
        return None

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=openrouter_api_key,
    )
    
    default_model = "deepseek/deepseek-chat-v3-0324:free"
    chosen_model = os.getenv("OPENROUTER_MODEL_NAME", default_model)
    logging.info(f"Using OpenRouter API with model: {chosen_model}")

    try:
        completion = client.chat.completions.create(
            model=chosen_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        response_content = completion.choices[0].message.content
        json_str = extract_json_from_response(response_content)
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logging.error(f"LLM output was not valid JSON: {e}")
        logging.error(f"LLM Raw Response: {response_content}")
        return None
    except Exception as e:
        logging.error(f"Error calling OpenRouter LLM: {e}")
        return None

def process_content(markdown_filepath, layouts_filepath, output_filepath, api_key_unused=None): # model_name parameter removed
    """
    Processes markdown content to produce a structured presentation plan,
    and now reliably handles and cleans malformed list-as-string responses from the LLM.
    """
    load_dotenv()
    presentation_structure = None

    # Read markdown content
    try:
        with open(markdown_filepath, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
    except Exception as e:
        logging.error(f"Error reading markdown file '{markdown_filepath}': {e}")
        return

    # Read layouts.json
    try:
        with open(layouts_filepath, 'r', encoding='utf-8') as f:
            layouts_content = f.read()
            # Parse layouts_content to be available for fallback_parser
            layouts_data = json.loads(layouts_content) 
    except Exception as e:
        logging.error(f"Error reading or parsing layouts file '{layouts_filepath}': {e}")
        # Fallback: if layouts.json is missing, unreadable, or invalid JSON
        logging.warning(f"Layouts file '{layouts_filepath}' not found, unreadable, or invalid. Proceeding with empty layouts_data for fallback.")
        layouts_content = "{}" # For LLM prompt
        layouts_data = {"layouts": []} # For fallback_parser

    # Build prompts
    system_prompt = (
        "You are an AI assistant. Please follow the user's instructions carefully to generate the requested JSON output."
    )
    user_prompt = PROMPT_TEMPLATE.format(
        layouts_json=layouts_content, 
        markdown_content=markdown_content
    )

    llm_response = call_llm(system_prompt, user_prompt) # model_name argument removed

    if llm_response:
        # Ensure the "placeholders" key is used, not "content"
        for slide in llm_response.get("slides", []):
            if "content" in slide and "placeholders" not in slide:
                slide["placeholders"] = slide.pop("content")

        if "slides" not in llm_response or not isinstance(llm_response["slides"], list):
            logging.warning("LLM response is missing 'slides' key or is not a list. Using fallback.")
            presentation_structure = fallback_parser(markdown_content, layouts_data)
        else:
            # --- START OF DEFINITIVE FIX (incorporating ast.literal_eval) ---
            logging.info("Sanitizing and cleaning LLM response...")
            for slide in llm_response["slides"]: # Iterate over llm_response["slides"]
                # Ensure the "placeholders" key is used, not "content"
                if "content" in slide and "placeholders" not in slide:
                    slide["placeholders"] = slide.pop("content")

                if "placeholders" in slide and isinstance(slide["placeholders"], dict): # Check "placeholders"
                    for key, value in list(slide["placeholders"].items()): # Iterate over a copy
                        
                        # STEP 1: Fix stringified lists from the LLM.
                        if isinstance(value, str) and value.strip().startswith('[') and value.strip().endswith(']'):
                            try:
                                # Use ast.literal_eval for safety. It only parses simple Python literals.
                                parsed_value = ast.literal_eval(value)
                                if isinstance(parsed_value, list):
                                    value = parsed_value # The string is now a proper list
                            except (ValueError, SyntaxError) as e_ast:
                                # If it's not a valid list literal, leave it as a string for the next step.
                                logging.warning(f"Found string '{value}' that looks like a list, but could not parse with ast.literal_eval: {e_ast}. Will attempt to clean as string.")
                        
                        # STEP 2: Clean the final values (which are now correctly typed or original string).
                        if isinstance(value, str):
                            slide["placeholders"][key] = clean_text_for_presentation(value)
                        elif isinstance(value, list):
                            # Clean each string item within the list, keep non-strings as is
                            slide["placeholders"][key] = [clean_text_for_presentation(item) if isinstance(item, str) else item for item in value]
            
            # --- Post-cleanup: Handle empty placeholders ---
            for slide in llm_response["slides"]: # Iterate over llm_response["slides"]
                current_placeholders = slide.get("placeholders", {}) # Check "placeholders"
                # Removed content_ph_name from this list as it's not defined in this scope
                for placeholder_key in ["Content Placeholder 2", "Content Placeholder 6", "Content Placeholder 7"]: 
                    if placeholder_key and placeholder_key in current_placeholders: # Check if placeholder_key is not None
                        content_value = current_placeholders[placeholder_key]
                        is_empty = False
                        if isinstance(content_value, str):
                            if not content_value or not content_value.strip():
                                is_empty = True
                        elif isinstance(content_value, list):
                            if not content_value: 
                                is_empty = True
                            else: 
                                is_empty = all(not item or (isinstance(item, str) and not item.strip()) for item in content_value)
                        
                        if is_empty:
                            current_placeholders[placeholder_key] = "This is sample body text generated to ensure the slide is not empty. Add your own content here."
            presentation_structure = llm_response
            # --- END OF DEFINITIVE FIX ---
    else:
        logging.warning("LLM processing failed or no response. Using fallback parser.")
        presentation_structure = fallback_parser(markdown_content, layouts_data)
    
    if presentation_structure:
        try:
            with open(output_filepath, 'w', encoding='utf-8') as f:
                json.dump(presentation_structure, f, indent=2, ensure_ascii=False)
            logging.info(f"Clean presentation plan saved successfully to {output_filepath}")
        except Exception as e:
            logging.error(f"Error saving presentation plan to '{output_filepath}': {e}")
    else:
        logging.error(f"Failed to generate or fallback to a presentation structure. Output file '{output_filepath}' not created.")
