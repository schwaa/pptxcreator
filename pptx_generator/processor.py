import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

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
        slides.append({
            "layout": "Title and Content",
            "content": {
                "Title 1": title,
                "Content Placeholder 2": body
            }
        })
    return {"slides": slides}

def extract_json_from_response(response_content):
    """
    Extracts the first JSON object from a string, even if wrapped in Markdown code fences or with extra text.
    """
    # Try to find a JSON code block
    code_block = re.search(r"```(?:json)?\s*({.*?})\s*```", response_content, re.DOTALL)
    if code_block:
        json_str = code_block.group(1)
    else:
        # Fallback: find the first {...} block
        json_match = re.search(r"({.*})", response_content, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response_content  # Last resort, try the whole thing
    return json_str

def call_llm(system_prompt, user_prompt, model_name=None):
    """
    Calls the LLM (OpenRouter) to process the content.
    """
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

    if not openrouter_api_key:
        print("Error: OPENROUTER_API_KEY not found in environment variables.")
        print("Please ensure it's set in your .env file or environment.")
        return None

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=openrouter_api_key,
    )
    
    chosen_model = model_name or "nousresearch/nous-hermes-2-mixtral-8x7b-dpo"
    print(f"Using OpenRouter API with model: {chosen_model}")

    try:
        completion = client.chat.completions.create(
            model=chosen_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        response_content = completion.choices[0].message.content
        # Try to extract JSON robustly
        json_str = extract_json_from_response(response_content)
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"LLM output was not valid JSON: {e}")
        print(f"LLM Raw Response: {response_content}")
        return None
    except Exception as e:
        print(f"Error calling OpenRouter LLM: {e}")
        return None

def process_content(markdown_filepath, layouts_filepath, output_filepath, api_key_unused=None, model_name=None):
    """
    Processes markdown content and a layouts map to produce a structured
    presentation plan using an LLM (OpenRouter).
    """
    load_dotenv()  # Load .env file

    # Read markdown content
    try:
        with open(markdown_filepath, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
    except Exception as e:
        print(f"Error reading markdown file: {e}")
        return

    # Read layouts.json
    try:
        with open(layouts_filepath, 'r', encoding='utf-8') as f:
            layouts_content = f.read()
    except Exception as e:
        print(f"Error reading layouts file: {e}")
        return

    # Build prompts
    system_prompt = (
        "You are an expert presentation designer. "
        "Given a markdown document and a list of available PowerPoint slide layouts (with their placeholder names), "
        "your job is to create a JSON plan for a presentation. "
        "For each slide, select the most appropriate layout and map content to the correct placeholders by name. "
        "For any slide that has a content/body placeholder (such as 'Content Placeholder 2', 'Content Placeholder 6', or 'Content Placeholder 7'), "
        "ALWAYS provide meaningful body text, even if you have to make it up. "
        "If the original markdown is brief, elaborate or invent relevant details to ensure every slide is full and engaging. "
        "Output a JSON object with a 'slides' array, where each slide has a 'layout' and a 'content' dict mapping placeholder names to values. "
        "Respond ONLY with the JSON object, no explanation or markdown formatting."
    )
    user_prompt = (
        f"Markdown Content:\n{markdown_content}\n\n"
        f"Available Layouts:\n{layouts_content}\n\n"
        "Please generate the presentation plan as described."
    )

    llm_response = call_llm(system_prompt, user_prompt, model_name=model_name)

    if llm_response:
        # Ensure the output structure is {"slides": [...]}
        if "slides" not in llm_response:
            print("LLM response is missing the 'slides' key. Using fallback.")
            presentation_structure = fallback_parser(markdown_content)
        else:
            # Enhance: If any slide is missing body text, make up something
            for slide in llm_response.get("slides", []):
                placeholders = slide.get("content", {})
                # Check for common content placeholders
                for key in ["Content Placeholder 2", "Content Placeholder 6", "Content Placeholder 7"]:
                    if key in placeholders and (not placeholders[key] or not placeholders[key].strip()):
                        placeholders[key] = "This is sample body text generated to ensure the slide is not empty. Add your own content here."
            presentation_structure = llm_response
    else:
        print("LLM processing failed. Falling back to simple parser.")
        presentation_structure = fallback_parser(markdown_content)
    
    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(presentation_structure, f, indent=2)
        print(f"Presentation plan saved to {output_filepath}")
    except Exception as e:
        print(f"Error saving presentation plan: {e}")
