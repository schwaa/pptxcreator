from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import PP_PLACEHOLDER_TYPE, MSO_SHAPE_TYPE
from pptx.enum.chart import XL_CHART_TYPE
from pptx.chart.data import CategoryChartData
import os
import json
import logging

logging.basicConfig(level=logging.INFO)

# ... (helper functions unchanged) ...

def generate_presentation(data_filepath, template_filepath, output_filepath):
    """
    Generates a PowerPoint presentation based on structured data and a template.
    
    Args:
        data_filepath (str): Path to the JSON file containing presentation data
        template_filepath (str): Path to the template PPTX file
        output_filepath (str): Path where the generated PPTX will be saved
    """
    # Load presentation data
    try:
        with open(data_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logging.error(f"Error loading data file: {e}")
        raise

    # Load template
    try:
        prs = Presentation(template_filepath)
        # Remove any existing slides (private API, fragile: see python-pptx docs)
        for _ in range(len(prs.slides._sldIdLst)):
            rId = prs.slides._sldIdLst[0].rId
            prs.part.drop_rel(rId)
            prs.slides._sldIdLst.remove(prs.slides._sldIdLst[0])
    except Exception as e:
        logging.error(f"Error loading template: {e}")
        raise

    # --- NEW: Use the new presentation.json format ---
    # Each slide is described by its layout name and a content dict mapping placeholder names to values
    for slide_idx, slide_plan in enumerate(data.get("slides", [])):
        layout_name = slide_plan.get("layout")
        content = slide_plan.get("content", {})
        logging.info(f"Processing slide {slide_idx} with layout: '{layout_name}'")

        # Find the layout by name
        slide_layout = None
        for layout in prs.slide_layouts:
            if layout.name == layout_name:
                slide_layout = layout
                break
        if not slide_layout:
            logging.warning(f"  Layout '{layout_name}' not found in template. Skipping slide.")
            continue

        slide = prs.slides.add_slide(slide_layout)
        
        # Log all placeholder names available in this chosen layout
        available_ph_names = [ph.name for ph in slide.placeholders]
        logging.info(f"  Layout '{layout_name}' has placeholders: {available_ph_names}")

        # Fill placeholders by name
        for placeholder_name_from_json, value in content.items():
            found = False
            for shape in slide.placeholders:
                # Exact match, case-sensitive, whitespace stripped (as per test)
                if shape.name.strip() == placeholder_name_from_json.strip():
                    found = True
                    logging.info(f"    Found placeholder '{shape.name.strip()}' in layout. Attempting to fill.")
                    # Handle images
                    if isinstance(value, str) and (value.lower().endswith('.png') or value.lower().endswith('.jpg') or value.lower().endswith('.jpeg')):
                        try:
                            # Ensure image path is relative to project root or an absolute path
                            image_path = value
                            if not os.path.isabs(image_path) and "projects/" in data_filepath:
                                project_dir = data_filepath.split("projects/")[0] # Get base path before "projects/"
                                image_path = os.path.join(project_dir, value) # Assume image path is relative to project root if not absolute

                            if not os.path.exists(image_path):
                                # Try path relative to the project's images folder
                                # e.g. if data_filepath is projects/first_test_run/output/presentation.json
                                # and value is "images/test_image.png"
                                # then image_path becomes projects/first_test_run/images/test_image.png
                                base_project_path = os.path.dirname(os.path.dirname(data_filepath)) # e.g. projects/first_test_run
                                potential_path = os.path.join(base_project_path, value)
                                if os.path.exists(potential_path):
                                    image_path = potential_path
                                else:
                                     logging.warning(f"      Image file not found at '{value}' or '{image_path}' or '{potential_path}'. Skipping image.")
                                     continue # Skip this placeholder if image not found

                            logging.info(f"      Inserting image '{image_path}' into '{shape.name.strip()}'")
                            # Remove the placeholder and insert the image at its position/size
                            left, top, width, height = shape.left, shape.top, shape.width, shape.height
                            sp = shape._element
                            sp.getparent().remove(sp)
                            slide.shapes.add_picture(image_path, left, top, width, height)
                        except Exception as e:
                            logging.warning(f"      Could not insert image '{value}' into '{placeholder_name_from_json}': {e}")
                    else:
                        # Handle text
                        try:
                            shape.text = str(value)
                            logging.info(f"      Set text for '{placeholder_name_from_json}'.")
                        except Exception as e:
                            logging.warning(f"      Could not set text for '{placeholder_name_from_json}': {e}")
                    break
            if not found:
                logging.warning(f"    Placeholder '{placeholder_name_from_json}' (from JSON) not found in layout '{layout_name}' actual placeholders: {available_ph_names}.")

    # Save the final presentation
    try:
        prs.save(output_filepath)
        logging.info(f"Presentation saved to {output_filepath}")
        return True
    except Exception as e:
        logging.error(f"Error saving presentation: {e}")
        return False
