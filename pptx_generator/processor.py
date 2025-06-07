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
You are an expert presentation designer's assistant. Your primary goal is to convert raw Markdown content into a structured JSON object.

**CONTENT FORMATTING RULES:**
1.  **For Bullet Points:** If the content for a placeholder is a list of items, format its value as a JSON ARRAY of strings.
    - Example: `"Content Placeholder 2": ["First bullet point.", "Second bullet point."]`
2.  **For Paragraphs:** If the content is a paragraph, reformat it into a JSON ARRAY of strings, where each string is a concise sentence.
3.  **For Simple Text:** If the content is a title or a short phrase, format its value as a single JSON string.
    - Example: `"Title 1": "This is a Title"`
4.  **Cleanup:** Ensure all text in the final JSON is clean plain text. REMOVE all markdown formatting like '-', '*', '#', or '**'.

---
**AVAILABLE LAYOUTS JSON:**
{layouts_json}

---
**MARKDOWN CONTENT:**
{markdown_content}
---

**YOUR TASK:**
Generate a single, valid JSON object that strictly follows all rules above. The 'content' values must be either a single JSON string or a JSON array of strings.
"""

# Fallback parser for when LLM fails or is unavailable
def fallback_parser(markdown_content):
    """
    Simple fallback: splits markdown into slides by '---' and uses a default layout.
    """
    slides = []
    for slide_md in markdown_content.split('---'):
        slide_md = slide_md.strip()
        if not slide_md:
            continue
        lines = slide_md.splitlines()
        title = lines[0].strip('# ').strip() if lines else ""
        body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
        # If body is empty, make up some content
        if not body:
            body = "This is sample body text generated to ensure the slide is not empty. Add your own content here."
        
        cleaned_title = clean_text_for_presentation(title)
        cleaned_body = clean_text_for_presentation(body)

        slides.append({
            "layout": "Title, Content 1", # Updated to a valid layout name from default_template.pptx
            "content": {
                "Title 1": cleaned_title,
                "Content Placeholder 2": cleaned_body
            }
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

def call_llm(system_prompt, user_prompt, model_name=None):
    """
    Calls the LLM (OpenRouter) to process the content.
    """
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        logging.error("OPENROUTER_API_KEY not found in environment variables.")
        return None

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=openrouter_api_key,
    )
    
    chosen_model = model_name or "deepseek/deepseek-chat-v3-0324:free" 
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

def process_content(markdown_filepath, layouts_filepath, output_filepath, api_key_unused=None, model_name=None):
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
    except Exception as e:
        logging.error(f"Error reading layouts file '{layouts_filepath}': {e}")
        # Fallback: if layouts.json is missing or unreadable, provide an empty JSON object string
        # This allows the LLM to proceed, though it won't have specific layout info.
        logging.warning(f"Layouts file '{layouts_filepath}' not found or unreadable. Proceeding without specific layout info.")
        layouts_content = "{}"

    # Build prompts
    system_prompt = (
        "You are an AI assistant. Please follow the user's instructions carefully to generate the requested JSON output."
    )
    user_prompt = PROMPT_TEMPLATE.format(
        layouts_json=layouts_content, 
        markdown_content=markdown_content
    )

    llm_response = call_llm(system_prompt, user_prompt, model_name=model_name)

    if llm_response:
        if "slides" not in llm_response or not isinstance(llm_response["slides"], list):
            logging.warning("LLM response is missing 'slides' key or is not a list. Using fallback.")
            presentation_structure = fallback_parser(markdown_content)
        else:
            # --- START OF DEFINITIVE FIX (incorporating ast.literal_eval) ---
            logging.info("Sanitizing and cleaning LLM response...")
            for slide in llm_response["slides"]:
                if "content" in slide and isinstance(slide["content"], dict):
                    for key, value in list(slide["content"].items()): # Iterate over a copy
                        
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
                            slide["content"][key] = clean_text_for_presentation(value)
                        elif isinstance(value, list):
                            # Clean each string item within the list, keep non-strings as is
                            slide["content"][key] = [clean_text_for_presentation(item) if isinstance(item, str) else item for item in value]
            
            # --- Post-cleanup: Handle empty placeholders ---
            for slide in llm_response["slides"]:
                placeholders = slide.get("content", {})
                for placeholder_key in ["Content Placeholder 2", "Content Placeholder 6", "Content Placeholder 7"]:
                    if placeholder_key in placeholders:
                        content_value = placeholders[placeholder_key]
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
                            placeholders[placeholder_key] = "This is sample body text generated to ensure the slide is not empty. Add your own content here."
            presentation_structure = llm_response
            # --- END OF DEFINITIVE FIX ---
    else:
        logging.warning("LLM processing failed or no response. Using fallback parser.")
        presentation_structure = fallback_parser(markdown_content)
    
    if presentation_structure:
        try:
            with open(output_filepath, 'w', encoding='utf-8') as f:
                json.dump(presentation_structure, f, indent=2, ensure_ascii=False)
            logging.info(f"Clean presentation plan saved successfully to {output_filepath}")
        except Exception as e:
            logging.error(f"Error saving presentation plan to '{output_filepath}': {e}")
    else:
        logging.error(f"Failed to generate or fallback to a presentation structure. Output file '{output_filepath}' not created.")
