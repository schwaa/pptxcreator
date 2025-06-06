from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import PP_PLACEHOLDER_TYPE, MSO_SHAPE_TYPE
from pptx.enum.chart import XL_CHART_TYPE
from pptx.chart.data import CategoryChartData
import os
import json
import logging

logging.basicConfig(level=logging.INFO)

def validate_and_adjust_placeholder_bounds(shape, slide_width=9144000, slide_height=6858000):
    """Validate and adjust placeholder to stay strictly within slide boundaries"""
    # Ensure values are not None
    if shape.left is None:
        shape.left = 0
    if shape.top is None:
        shape.top = 0
    if shape.width is None:
        shape.width = slide_width
    if shape.height is None:
        shape.height = slide_height

    # Clamp left/top to [0, slide_width/height]
    shape.left = max(0, shape.left)
    shape.top = max(0, shape.top)

    # Clamp width/height to be at least 1
    shape.width = max(1, shape.width)
    shape.height = max(1, shape.height)

    # Ensure right/bottom edge does not exceed slide
    if shape.left + shape.width > slide_width:
        shape.width = max(1, slide_width - shape.left)
    if shape.top + shape.height > slide_height:
        shape.height = max(1, slide_height - shape.top)

    # If left is so large that width is forced to 1, clamp left
    if shape.left > slide_width - 1:
        shape.left = slide_width - 1
        shape.width = 1
    if shape.top > slide_height - 1:
        shape.top = slide_height - 1
        shape.height = 1

    return True

def get_placeholder(slide, layout_details=None):
    """Find placeholder by ID from layout details, or by name. No fallback logic."""
    logging.info("=== DEBUG: All placeholders on this slide ===")
    for shape in slide.placeholders:
        logging.info(
            f"  Name: '{shape.name}', Type: {shape.placeholder_format.type}, ID: {shape.placeholder_format.idx}, Text: '{getattr(shape, 'text', '')}'"
        )

    # Try by ID first (most reliable)
    if layout_details and "id" in layout_details:
        for shape in slide.placeholders:
            if shape.placeholder_format.idx == layout_details["id"]:
                logging.info(f"Selected by ID: {shape.name} (id={shape.placeholder_format.idx})")
                return shape

    # Try by name (if provided)
    if layout_details and "name" in layout_details:
        for shape in slide.placeholders:
            if shape.name == layout_details["name"]:
                logging.info(f"Selected by name: {shape.name}")
                return shape

    logging.error(f"DEBUG: No matching placeholder found for details: {layout_details}")
    return None

def set_placeholder_properties(shape, details):
    """Set position and size of placeholder if specified in details"""
    if not details or not shape:
        return
    
    # Get current values as defaults
    current = {
        "left": shape.left if shape.left is not None else 0,
        "top": shape.top if shape.top is not None else 0,
        "width": shape.width if shape.width is not None else 9144000,
        "height": shape.height if shape.height is not None else 6858000
    }
    
    # Update with new values from details, cast to int
    if "left" in details:
        shape.left = int(details["left"])
    if "top" in details:
        shape.top = int(details["top"])
    if "width" in details:
        shape.width = int(details["width"])
    if "height" in details:
        shape.height = int(details["height"])
    
    # Ensure everything stays within bounds
    validate_and_adjust_placeholder_bounds(shape)

def insert_image_to_placeholder(slide, picture_shape, image_path, details):
    """Insert image into placeholder, handling different shape types"""
    try:
        if hasattr(picture_shape, 'insert_picture'):
            picture_shape.insert_picture(image_path)
        else:
            # Get position and size from placeholder
            left = details.get("left", picture_shape.left)
            top = details.get("top", picture_shape.top)
            width = min(details.get("width", picture_shape.width), 9144000 - left)
            height = min(details.get("height", picture_shape.height), 6858000 - top)
            
            # Add picture as a shape
            pic = slide.shapes.add_picture(
                image_path,
                left, top, width, height
            )
            
            # Remove the original placeholder
            sp = picture_shape._element
            sp.getparent().remove(sp)
    except Exception as e:
        logging.warning(f"Could not insert image: {e}")

def generate_presentation(data_filepath, template_filepath, output_filepath, map_filepath=None):
    """
    Generates a PowerPoint presentation based on structured data and a template.
    
    Args:
        data_filepath (str): Path to the JSON file containing presentation data
        template_filepath (str): Path to the template PPTX file
        output_filepath (str): Path where the generated PPTX will be saved
        map_filepath (str, optional): Path to the template mapping JSON file
    """
    # Load template map if provided
    template_map = {}
    if map_filepath:
        try:
            with open(map_filepath, 'r') as f:
                template_map = json.load(f)
        except Exception as e:
            logging.error(f"Could not load template map: {e}")
            raise
        # Validate template map structure
        if "layouts" not in template_map or not isinstance(template_map["layouts"], list):
            raise ValueError("Template map is missing 'layouts' or it is not a list.")

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

    def score_layout_for_section(section, layout):
        """Score how well a layout matches the content section. Return -999 if required placeholders are missing."""
        features = layout.get("features", {})
        # Require title if needed
        if section.get("title") and not features.get("has_title"):
            return -999
        # Require subtitle if needed
        if section.get("subtitle") and not features.get("has_subtitle"):
            return -999
        # Require body if bullets or text_content/caption
        if (section.get("bullets") or section.get("text_content") or section.get("caption")) and not features.get("has_body_text"):
            return -999
        # Require picture if image is needed
        if (section.get("image_path") or section.get("product_image_path")) and features.get("num_picture_placeholders", 0) < 1:
            return -999
        # Require chart if chart_data is needed
        if section.get("chart_data") and features.get("num_chart_placeholders", 0) < 1:
            return -999

        score = 0
        # Title
        if section.get("title") and features.get("has_title"):
            score += 2
        # Subtitle
        if section.get("subtitle") and features.get("has_subtitle"):
            score += 1
        # Bullets/body
        if section.get("bullets") and features.get("has_body_text"):
            score += 2
        # Image
        if (section.get("image_path") or section.get("product_image_path")) and features.get("num_picture_placeholders", 0) > 0:
            score += 2
        # Chart
        if section.get("chart_data") and features.get("num_chart_placeholders", 0) > 0:
            score += 2
        # Caption/text_content
        if (section.get("text_content") or section.get("caption")) and (features.get("has_body_text") or features.get("num_text_placeholders", 0) > 0):
            score += 1
        # Prefer layouts with fewer extra placeholders (simpler)
        score -= abs(features.get("num_text_placeholders", 0) - (1 if section.get("text_content") or section.get("caption") else 0))
        score -= abs(features.get("num_picture_placeholders", 0) - (1 if section.get("image_path") or section.get("product_image_path") else 0))
        return score

    # Process each section in the data
    for section in data.get('sections', []):
        content_type = section.get('content_type')
        if not content_type:
            logging.warning("Section missing 'content_type'. Skipping.")
            continue

        # --- NEW: Select the best layout for this section ---
        best_layout = None
        best_score = float('-inf')
        for layout in template_map.get("layouts", []):
            score = score_layout_for_section(section, layout)
            logging.info(f"Layout '{layout['name']}' scored {score} for section '{section.get('title', content_type)}'")
            if score > best_score:
                best_score = score
                best_layout = layout

        if not best_layout or best_score < 1:
            logging.error(f"No suitable layout found for section '{section.get('title', content_type)}'. Skipping.")
            continue

        layout_details = best_layout
        slide_layout_index = layout_details["index"]
        slide_layout = prs.slide_layouts[slide_layout_index]

        # Debug: Print available placeholders
        logging.info(f"\nPlaceholders in layout '{layout_details['name']}':")
        for shape in slide_layout.placeholders:
            logging.info(f"  {shape.name}: type={shape.placeholder_format.type}, id={shape.placeholder_format.idx}")

        # Print the keys in the placeholders dict for debugging
        logging.info(f"Placeholders dict keys for layout '{layout_details['name']}': {list(layout_details['placeholders'].keys())}")

        slide = prs.slides.add_slide(slide_layout)

        # Populate placeholders based on content type
        if content_type == 'presentation_title':
            title = section.get('title')
            subtitle = section.get('subtitle')

            title_placeholder = get_placeholder(slide, layout_details["placeholders"].get("Title 1"))
            subtitle_placeholder = get_placeholder(slide, layout_details["placeholders"].get("Subtitle 2"))
            
            if title_placeholder and title:
                title_placeholder.text = str(title)
            if subtitle_placeholder and subtitle:
                subtitle_placeholder.text = str(subtitle)
            if title_placeholder:
                validate_and_adjust_placeholder_bounds(title_placeholder)
            if subtitle_placeholder:
                validate_and_adjust_placeholder_bounds(subtitle_placeholder)

        elif content_type == 'bullet_points_summary':
            title = section.get('title')
            bullets = section.get('bullets', [])

            title_placeholder = get_placeholder(slide, layout_details["placeholders"].get("Title 1"))
            # Use the actual keys from the debug output
            text_placeholder_1 = get_placeholder(slide, layout_details["placeholders"].get("Text Placeholder 8"))
            text_placeholder_2 = get_placeholder(slide, layout_details["placeholders"].get("Text Placeholder 10"))

            if title_placeholder and title:
                title_placeholder.text = str(title)
            
            if text_placeholder_1:
                set_placeholder_properties(text_placeholder_1, layout_details["placeholders"].get("Text Placeholder 8"))
            if text_placeholder_2:
                set_placeholder_properties(text_placeholder_2, layout_details["placeholders"].get("Text Placeholder 10"))

            if bullets and text_placeholder_1:
                tf = text_placeholder_1.text_frame
                tf.text = bullets[0]
                for bullet in bullets[1:]:
                    p = tf.add_paragraph()
                    p.text = str(bullet)
                    p.level = 0
                tf.word_wrap = True
                for p in tf.paragraphs:
                    p.font.size = Pt(16)
            if text_placeholder_2:
                text_placeholder_2.text = ""
            if title_placeholder:
                validate_and_adjust_placeholder_bounds(title_placeholder)
            if text_placeholder_1:
                validate_and_adjust_placeholder_bounds(text_placeholder_1)
            if text_placeholder_2:
                validate_and_adjust_placeholder_bounds(text_placeholder_2)

        elif content_type == 'image_and_description':
            title = section.get('title')
            image_path = section.get('image_path')
            text_content = section.get('text_content')

            title_placeholder = get_placeholder(slide, layout_details["placeholders"].get("Title 1"))
            image_placeholder = get_placeholder(slide, layout_details["placeholders"].get("Picture Placeholder 10"))
            text_placeholder = get_placeholder(slide, layout_details["placeholders"].get("Content Placeholder 3"))

            if title_placeholder and title:
                title_placeholder.text = str(title)
            if text_placeholder and text_content:
                set_placeholder_properties(text_placeholder, layout_details["placeholders"].get("Content Placeholder 3"))
                if hasattr(text_placeholder, "text_frame"):
                    text_placeholder.text = str(text_content)
                    tf = text_placeholder.text_frame
                    tf.word_wrap = True
                    logging.info(f"DEBUG: Set text on placeholder '{text_placeholder.name}' (id={text_placeholder.placeholder_format.idx})")
                else:
                    logging.error(f"DEBUG: Placeholder '{text_placeholder.name}' (id={text_placeholder.placeholder_format.idx}) does NOT support text_frame. Text will NOT appear. Use a BODY placeholder for text.")
                validate_and_adjust_placeholder_bounds(text_placeholder)
            if image_placeholder and image_path:
                insert_image_to_placeholder(slide, image_placeholder, image_path, layout_details["placeholders"].get("Picture Placeholder 10"))
            if title_placeholder:
                validate_and_adjust_placeholder_bounds(title_placeholder)
            if image_placeholder:
                validate_and_adjust_placeholder_bounds(image_placeholder)

        elif content_type == 'description_and_image':
            title = section.get('title')
            image_path = section.get('image_path')
            text_content = section.get('text_content')

            title_placeholder = get_placeholder(slide, layout_details["placeholders"].get("Title 1"))
            image_placeholder = get_placeholder(slide, layout_details["placeholders"].get("Picture Placeholder 8"))
            text_placeholder = get_placeholder(slide, layout_details["placeholders"].get("Content Placeholder 7"))

            if title_placeholder and title:
                title_placeholder.text = str(title)
            if text_placeholder and text_content:
                text_placeholder.text = str(text_content)
                tf = text_placeholder.text_frame
                tf.word_wrap = True
                for p in tf.paragraphs:
                    p.level = 0
                    p.font.size = Pt(14)
                    p.space_before = Pt(6)
                    p.space_after = Pt(6)
            if image_placeholder and image_path:
                insert_image_to_placeholder(slide, image_placeholder, image_path, layout_details["placeholders"].get("Picture Placeholder 8"))
            if title_placeholder:
                validate_and_adjust_placeholder_bounds(title_placeholder)
            if text_placeholder:
                validate_and_adjust_placeholder_bounds(text_placeholder)
            if image_placeholder:
                validate_and_adjust_placeholder_bounds(image_placeholder)

        elif content_type == 'product_showcase':
            title = section.get('title')
            product_image_path = section.get('product_image_path')
            caption = section.get('caption')

            title_placeholder = get_placeholder(slide, layout_details["placeholders"].get("Title 1"))
            image_placeholder = get_placeholder(slide, layout_details["placeholders"].get("Picture Placeholder 7"))
            text_placeholder = get_placeholder(slide, layout_details["placeholders"].get("Text Placeholder 3"))

            if title_placeholder and title:
                title_placeholder.text = str(title)
            if text_placeholder and caption:
                text_placeholder.text = str(caption)
            if image_placeholder and product_image_path:
                insert_image_to_placeholder(slide, image_placeholder, product_image_path, layout_details["placeholders"].get("Picture Placeholder 7"))
            if title_placeholder:
                validate_and_adjust_placeholder_bounds(title_placeholder)
            if text_placeholder:
                validate_and_adjust_placeholder_bounds(text_placeholder)
            if image_placeholder:
                validate_and_adjust_placeholder_bounds(image_placeholder)

        elif content_type == 'chart_data_slide':
            title = section.get('title')
            chart_data = section.get('chart_data')
            text_content = section.get('text_content')

            title_placeholder = get_placeholder(slide, layout_details["placeholders"].get("Title 1"))
            chart_placeholder = get_placeholder(slide, layout_details["placeholders"].get("Content Placeholder 2"))
            text_placeholder = get_placeholder(slide, layout_details["placeholders"].get("Text Placeholder 3"))

            if title_placeholder and title:
                title_placeholder.text = str(title)
            if text_placeholder and text_content:
                text_placeholder.text = str(text_content)
            if chart_placeholder and chart_data:
                try:
                    chart_data_obj = CategoryChartData()
                    chart_data_obj.categories = chart_data.get('categories', [])
                    series_data = chart_data.get('series', [])
                    if series_data:
                        for series in series_data:
                            chart_data_obj.add_series(series.get('name', ''), series.get('values', []))
                    chart_placeholder.insert_chart(
                        XL_CHART_TYPE.COLUMN_CLUSTERED,
                        chart_data_obj
                    )
                except Exception as e:
                    logging.warning(f"Could not create chart: {e}")
            if title_placeholder:
                validate_and_adjust_placeholder_bounds(title_placeholder)
            if text_placeholder:
                validate_and_adjust_placeholder_bounds(text_placeholder)
            if chart_placeholder:
                validate_and_adjust_placeholder_bounds(chart_placeholder)

    # Save the final presentation
    try:
        prs.save(output_filepath)
        logging.info(f"Presentation saved to {output_filepath}")
        return True
    except Exception as e:
        logging.error(f"Error saving presentation: {e}")
        return False
