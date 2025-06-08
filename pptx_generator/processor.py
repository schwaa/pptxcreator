import os
import json
import re
import logging
import requests # For image generation
from openai import OpenAI
from dotenv import load_dotenv
# import instructor # TODO: Replace with pydantic-ai imports

from .utils import clean_text_for_presentation # Assuming this is still needed for some raw_content processing
from .models import SlidePlan, FinalSlide, ImageGenerationRequest # Pydantic models

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize OpenAI client
load_dotenv()
# Ensure API key is loaded before initializing client
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    logging.critical("OPENROUTER_API_KEY not found in environment. LLM calls will fail.")
    # You might want to raise an exception here or handle it gracefully
    # For now, proceeding will likely cause errors later if client is used without key.
client = OpenAI( # Renamed from base_openai_client
    base_url=os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1"),
    api_key=OPENROUTER_API_KEY
)
# TODO: Integrate pydantic-ai with the client if necessary, or use pydantic-ai specific functions for LLM calls.
LLM_MODEL_NAME = os.getenv("OPENROUTER_MODEL_NAME", "gpt-4-turbo") # Default to a capable model

# --- Helper Functions ---
def generate_and_save_image(prompt: str, save_path: str, model_name: str, sd_forge_url: str | None) -> bool:
    """
    Generates an image using SD Forge and saves it.
    Returns True on success, False on failure.
    """
    if not sd_forge_url:
        logging.error("SD_FORGE_SERVER_URL is not configured for image generation.")
        return False

    api_endpoint = f"{sd_forge_url.rstrip('/')}/sdapi/v1/txt2img"
    # Standard payload, can be customized further if needed
    payload = {
        "prompt": prompt,
        "steps": 25,
        "width": 1024,
        "height": 768,
        "cfg_scale": 7,
        "sampler_name": "Euler a", # A common sampler
        "override_settings": {
            "sd_model_checkpoint": model_name 
        }
    }
    logging.info(f"Requesting image generation for prompt: '{prompt}' (Model: '{model_name}') -> Save path: '{save_path}'")
    try:
        response = requests.post(api_endpoint, json=payload, timeout=180) # 3 min timeout
        response.raise_for_status()  # Raises HTTPError for bad responses (4XX or 5XX)
        r_json = response.json()

        if r_json.get('images') and r_json['images'][0]:
            import base64
            image_data_base64 = r_json['images'][0]
            # Some APIs might include data:image/png;base64, prefix
            if "," in image_data_base64:
                image_data_base64 = image_data_base64.split(',', 1)[1]
            
            image_bytes = base64.b64decode(image_data_base64)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, 'wb') as f:
                f.write(image_bytes)
            logging.info(f"Image successfully generated and saved to {save_path}")
            return True
        else:
            logging.error(f"Image generation failed: No image data in response. Response: {r_json}")
            return False
    except requests.exceptions.Timeout:
        logging.error(f"Image generation timed out for prompt: '{prompt}'")
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"API Error during image generation ({api_endpoint}): {e}")
        if e.response is not None:
            logging.error(f"API Response: {e.response.status_code} - {e.response.text}")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred during image generation: {e}")
        return False

# --- New Agentic LLM Caller Functions ---
def call_planning_llm(markdown_chunk: str, layouts_json_str: str) -> SlidePlan | None:
    """
    Calls the LLM to generate a high-level plan for a slide.
    Returns a SlidePlan object or None if an error occurs.
    """
    if not OPENROUTER_API_KEY: # Check again in case it wasn't set at module load
        logging.error("OPENROUTER_API_KEY not available for call_planning_llm.")
        return None

    system_prompt = """
You are an AI assistant tasked with planning a single presentation slide based on a chunk of markdown content.
Your goal is to create a high-level plan for the slide, including its topic, the type of content,
the raw text content (cleaned and broken into sentences or bullets), and an optional request for image generation if it would significantly enhance the slide.

Output Format:
You MUST respond with a JSON object that strictly adheres to the `SlidePlan` Pydantic model.
The `raw_content` should be a list of strings (sentences or bullet points). Clean out markdown formatting (like #, *, -) from this text.
If you decide an image is needed, provide a detailed `prompt` for an image generation model within the `image_request` object.
Do not request an image if the markdown already implies an image (e.g., `![alt](path)` - though this specific markdown is not directly processed by you for image paths, consider its intent).
Choose `content_type` from: 'paragraph', 'bullet_list', 'title_only', 'image_with_caption'.
"""
    user_prompt = f"""
Available Layouts Information (for context, you don't choose the final layout here):
```json
{layouts_json_str}
```

Markdown Content Chunk for this Slide:
---
{markdown_chunk}
---

Based on the markdown chunk, generate a `SlidePlan` JSON object.
Focus on:
1.  `slide_topic`: A concise topic for this slide.
2.  `content_type`: The primary nature of the content.
3.  `raw_content`: The essential text, cleaned and listified. Ensure markdown syntax (like '#', '*', '-') is removed from the text.
4.  `image_request` (optional): If a new image would be highly beneficial, define `ImageGenerationRequest` with a `prompt`.
"""
    logging.info(f"Calling Planning LLM for markdown chunk:\n{markdown_chunk[:200]}...")
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Extract the JSON from the response
        try:
            content = response.choices[0].message.content
            # Log the actual response for debugging
            logging.info(f"LLM Response: {content}")
            # Strip JSON code block markers if present
            if content.startswith("```json\n") and content.endswith("\n```"):
                content = content[8:-4]  # Remove ```json\n and \n```
            plan_data = json.loads(content)
            plan = SlidePlan(**plan_data)
            if plan.raw_content:
                plan.raw_content = [clean_text_for_presentation(text) for text in plan.raw_content]
            logging.info(f"Planning LLM successful. Slide topic: {plan.slide_topic}")
            return plan
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse LLM response as JSON: {e}")
            return None
        except Exception as e:
            logging.error(f"Failed to create SlidePlan from LLM response: {e}")
            return None
    except Exception as e: # This will now catch the NotImplementedError or any other unexpected error
        logging.error(f"Error in call_planning_llm: {e}")
        return None

def call_designer_llm(slide_plan: SlidePlan, image_path: str | None, layouts_json_str: str) -> FinalSlide | None:
    """
    Calls the LLM to generate the final JSON structure for a slide,
    including layout selection and placeholder mapping.
    Returns a FinalSlide object or None if an error occurs.
    """
    if not OPENROUTER_API_KEY:
        logging.error("OPENROUTER_API_KEY not available for call_designer_llm.")
        return None

    system_prompt = """
You are an AI presentation designer. Your task is to take a high-level slide plan (including content and an optional image path)
and select the best PowerPoint layout from the provided list. Then, map all content (text and the image if provided)
to the appropriate placeholders in the chosen layout.

Output Format:
You MUST respond with a JSON object that strictly adheres to the `FinalSlide` Pydantic model.
The `layout` field must be one of the layout names from the "Available Layouts JSON".
The `placeholders` field must be a dictionary where keys are placeholder names from the chosen layout,
and values are the content (string, list of strings for bullets, or the provided image path for an image placeholder).

Ensure all text content is clean and ready for presentation (no markdown).
If an `image_path` is provided, you MUST include it in a suitable "Picture" or "Image" type placeholder in your chosen layout.
If the `slide_plan.content_type` is 'image_with_caption' and an image_path is provided, ensure the image and some caption/text from `slide_plan.raw_content` are placed.
If `slide_plan.content_type` is 'title_only', the `raw_content` might be empty or just a title; ensure the title placeholder is filled.
If `slide_plan.raw_content` is a list of one item, it's likely a title or single paragraph. If multiple items, it's a list.
"""

    user_prompt = f"""
Slide Plan:
```json
{slide_plan.model_dump_json(indent=2)}
```

Generated Image Path (if any, otherwise None):
{image_path if image_path else "No image was generated for this slide."}

Available Layouts JSON (Choose one and map content to its placeholders):
```json
{layouts_json_str}
```

Based on the Slide Plan, the optional image path, and the Available Layouts, generate a `FinalSlide` JSON object.
Select the most appropriate layout.
Map all `slide_plan.raw_content` and the `image_path` (if provided and applicable for the chosen layout) to the placeholders of your chosen layout.
If `image_path` is provided, ensure it's assigned to a placeholder designed for images (e.g., name containing "Picture", "Image", "Photo").
The `slide_plan.slide_topic` should generally go into a "Title" placeholder.
The `slide_plan.raw_content` should go into "Content", "Body", or similar text placeholders.
"""
    logging.info(f"Calling Designer LLM for slide topic: {slide_plan.slide_topic}")
    try:
        response = client.chat.completions.create(
            model=LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Extract the JSON from the response
        try:
            content = response.choices[0].message.content
            # Log the actual response for debugging
            logging.info(f"LLM Response: {content}")
            # Strip JSON code block markers if present
            if content.startswith("```json\n") and content.endswith("\n```"):
                content = content[8:-4]  # Remove ```json\n and \n```
            slide_data = json.loads(content)
            final_slide = FinalSlide(**slide_data)
            logging.info(f"Designer LLM successful. Chosen layout: {final_slide.layout}")
            return final_slide
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse LLM response as JSON: {e}")
            return None
        except Exception as e:
            logging.error(f"Failed to create FinalSlide from LLM response: {e}")
            return None
    except Exception as e: # This will now catch the NotImplementedError or any other unexpected error
        logging.error(f"Error in call_designer_llm: {e}")
        return None

# --- Main Processing Function (Agentic Workflow) ---
def process_content(markdown_filepath: str, layouts_filepath: str, output_filepath: str, regenerate_images: bool = False):
    """
    Processes markdown content using an agentic workflow to generate a presentation.json file.
    """
    # load_dotenv() is called at module level, but good to ensure critical vars are checked
    if not OPENROUTER_API_KEY:
        logging.critical("process_content cannot proceed: OPENROUTER_API_KEY is not set.")
        return

    sd_forge_url = os.getenv("SD_FORGE_SERVER_URL")
    flux_model_name = os.getenv("FLUX_MODEL_NAME", "stabilityai/stable-diffusion-3-medium") 

    try:
        with open(markdown_filepath, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
    except FileNotFoundError:
        logging.error(f"Markdown file not found: {markdown_filepath}")
        return
    except Exception as e:
        logging.error(f"Error reading markdown file '{markdown_filepath}': {e}")
        return

    try:
        with open(layouts_filepath, 'r', encoding='utf-8') as f:
            layouts_json_str = f.read() 
            # layouts_data = json.loads(layouts_json_str) # Not strictly needed if only passing string to LLM
    except FileNotFoundError:
        logging.error(f"Layouts file not found: {layouts_filepath}")
        return
    except Exception as e:
        logging.error(f"Error reading/parsing layouts file '{layouts_filepath}': {e}")
        return

    final_presentation = {"slides": []}
    markdown_chunks = markdown_content.split('---')
    project_dir = os.path.dirname(os.path.abspath(markdown_filepath)) # Use abspath for robustness
    images_output_dir = os.path.join(project_dir, "images") 

    for i, chunk in enumerate(markdown_chunks):
        chunk = chunk.strip()
        if not chunk:
            continue

        logging.info(f"--- Starting Agentic Process for Slide {i+1} ---")

        # 1. Planning Agent
        logging.info(f"  Step 1 (Slide {i+1}): Analyzing content and creating a high-level plan...")
        slide_plan: SlidePlan | None = call_planning_llm(chunk, layouts_json_str)
        
        if not slide_plan:
            logging.warning(f"  [Failed] Could not create a plan for slide {i+1}. Skipping.")
            continue
            
        image_path_for_slide = None
        # 2. Tool Use: Image Generation (if requested)
        if slide_plan.image_request and slide_plan.image_request.prompt:
            img_prompt = slide_plan.image_request.prompt
            logging.info(f"  Step 2 (Slide {i+1}): Plan requires image generation. Prompt: '{img_prompt}'")
            
            if not sd_forge_url:
                logging.warning(f"  SD_FORGE_SERVER_URL not configured. Cannot generate image for slide {i+1}.")
            else:
                safe_topic = re.sub(r'[^a-zA-Z0-9_.-]', '_', slide_plan.slide_topic.lower())[:50]
                img_filename = f"slide_{i+1}_{safe_topic}.png" 
                abs_image_save_path = os.path.join(images_output_dir, img_filename)
                image_path_for_json = os.path.join("images", img_filename) # Relative path for presentation.json

                should_generate_this_image = regenerate_images or not os.path.exists(abs_image_save_path)

                if should_generate_this_image:
                    logging.info(f"  Generating image for slide {i+1} at {abs_image_save_path}")
                    success = generate_and_save_image(img_prompt, abs_image_save_path, flux_model_name, sd_forge_url)
                    if success:
                        image_path_for_slide = image_path_for_json
                        logging.info(f"  Image generated successfully: {image_path_for_slide}")
                    else:
                        logging.warning(f"  Failed to generate image for slide {i+1}.")
                else:
                    logging.info(f"  Image for slide {i+1} already exists and regenerate_images is False. Using existing: {abs_image_save_path}")
                    image_path_for_slide = image_path_for_json
        
        # 3. Designer Agent
        logging.info(f"  Step 3 (Slide {i+1}): Generating final layout and placeholder mapping...")
        final_slide: FinalSlide | None = call_designer_llm(
            slide_plan, 
            image_path_for_slide, 
            layouts_json_str
        )
        
        if not final_slide:
            logging.warning(f"  [Failed] Could not generate final slide structure for slide {i+1}. Skipping.")
            continue
            
        final_presentation["slides"].append(final_slide.model_dump(exclude_none=True)) # exclude_none for cleaner JSON
        logging.info(f"--- Successfully processed slide {i+1} ---")

    if final_presentation["slides"]:
        try:
            os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
            with open(output_filepath, 'w', encoding='utf-8') as f:
                json.dump(final_presentation, f, indent=2, ensure_ascii=False)
            logging.info(f"Presentation structure successfully saved to {output_filepath}")
        except Exception as e:
            logging.error(f"Error saving presentation structure to '{output_filepath}': {e}")
    else:
        logging.warning(f"No slides were processed. Output file '{output_filepath}' will be empty or not created.")

if __name__ == '__main__':
    logging.info("Running processor.py directly for testing (conceptual).")
    
    # Create dummy files for testing
    # Ensure this script is in the pptx_generator directory for relative paths to work,
    # or adjust paths accordingly.
    test_project_dir = "test_project_processor"
    os.makedirs(test_project_dir, exist_ok=True)
    os.makedirs(os.path.join(test_project_dir, "images"), exist_ok=True)

    dummy_md_path = os.path.join(test_project_dir, "content.md")
    dummy_layouts_path = os.path.join(test_project_dir, "layouts.json")
    dummy_output_path = os.path.join(test_project_dir, "presentation.json")

    with open(dummy_md_path, "w", encoding='utf-8') as f:
        f.write("## Slide 1: Introduction\n\nWelcome to this amazing presentation about AI.\n\n* Bullet point 1\n* Bullet point 2\n\n---\n\n## Slide 2: The Future\n\nThis slide discusses the future of AI and could really use an image of a futuristic robot.\n\n---\n\n## Slide 3: Conclusion\n\nAI is transformative.")
    
    dummy_layout_data = {
        "source_template_path": "dummy_template.pptx", # Added as per layouts.json structure
        "layouts": [
            {"name": "Title Slide", "placeholders": ["Title 1", "Subtitle 2"]},
            {"name": "Title and Content", "placeholders": ["Title 1", "Content Placeholder 1"]},
            {"name": "Image with Caption", "placeholders": ["Title 1", "Picture Placeholder 1", "Caption Placeholder 1"]},
            {"name": "Blank", "placeholders": []}
        ]
    }
    with open(dummy_layouts_path, "w", encoding='utf-8') as f:
        json.dump(dummy_layout_data, f, indent=2)

    if not OPENROUTER_API_KEY:
        logging.error("CRITICAL: OPENROUTER_API_KEY not set for test run. LLM calls will fail.")
    
    # Set SD_FORGE_SERVER_URL in .env or environment if you want to test image generation
    # e.g. SD_FORGE_SERVER_URL=http://localhost:7860 
    # And FLUX_MODEL_NAME, e.g. FLUX_MODEL_NAME=JuggernautXL_v9_RunDiffusionPhoto_v2.safetensors

    process_content(dummy_md_path, dummy_layouts_path, dummy_output_path, regenerate_images=False)

    logging.info(f"Test run finished. Check {dummy_output_path} and the {os.path.join(test_project_dir, 'images')} folder.")
    # To clean up, you might manually delete the test_project_processor directory.
