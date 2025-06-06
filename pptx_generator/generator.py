from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.shapes import PP_PLACEHOLDER_TYPE, MSO_SHAPE_TYPE
from pptx.enum.chart import XL_CHART_TYPE
from pptx.chart.data import CategoryChartData
import os
import json

def validate_placeholder_bounds(shape, slide_width=9144000, slide_height=6858000):
    """Validate placeholder stays within slide boundaries"""
    if shape.left < 0 or shape.top < 0:
        return False
    if (shape.left + shape.width) > slide_width:
        return False
    if (shape.top + shape.height) > slide_height:
        return False
    return True

def get_placeholder(slide, layout_details=None, fallback_type=None):
    """Find placeholder by ID from layout details, or by type as fallback"""
    type_map = {
        "title": 1,
        "center_title": 3,
        "subtitle": 4,
        "body": 2,
        "picture": 18,
        "object": 7,
        "chart": 7  # Charts use the same type as generic objects
    }

    if layout_details and "id" in layout_details:
        # Try by ID first
        for shape in slide.placeholders:
            if shape.placeholder_format.idx == layout_details["id"]:
                # Skip boundary validation for titles and subtitles
                if layout_details.get("type", "").lower() in ["title", "center_title", "subtitle"]:
                    return shape
                if validate_placeholder_bounds(shape):
                    return shape
                else:
                    print(f"Warning: Placeholder {shape.name} exceeds slide boundaries")
                    return None
    
    # Try by type if specified in layout_details
    if layout_details and "type" in layout_details:
        placeholder_type = type_map.get(layout_details["type"].lower())
        if placeholder_type:
            for shape in slide.placeholders:
                # Handle both title types (center and normal)
                if placeholder_type in [1, 3] and shape.placeholder_format.type in [1, 3]:
                    if validate_placeholder_bounds(shape):
                        return shape
                elif shape.placeholder_format.type == placeholder_type:
                    if validate_placeholder_bounds(shape):
                        return shape
                else:
                    print(f"Warning: Placeholder {shape.name} exceeds slide boundaries")
                    return None

    # Fall back to type parameter
    if fallback_type:
        for shape in slide.placeholders:
            if isinstance(fallback_type, int):
                # If fallback_type is already a numeric type
                match_type = fallback_type
            else:
                # Convert string type to numeric
                match_type = type_map.get(str(fallback_type).lower())
            
            if match_type and shape.placeholder_format.type == match_type:
                if validate_placeholder_bounds(shape):
                    return shape
                else:
                    print(f"Warning: Placeholder {shape.name} exceeds slide boundaries")
                    return None
    return None

def set_placeholder_properties(shape, details):
    """Set position and size of placeholder if specified in details"""
    if not details or not shape:
        return
    
    if "left" in details:
        shape.left = details["left"]
    if "top" in details:
        shape.top = details["top"]
    if "width" in details:
        shape.width = min(details["width"], 9144000 - shape.left)  # Ensure fits slide
    if "height" in details:
        shape.height = min(details["height"], 6858000 - shape.top)  # Ensure fits slide

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
        print(f"Warning: Could not insert image: {e}")

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
            print(f"Warning: Could not load template map: {e}")

    # Load presentation data
    try:
        with open(data_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading data file: {e}")
        return

    # Load template
    try:
        prs = Presentation(template_filepath)
        # Remove any existing slides
        for _ in range(len(prs.slides._sldIdLst)):
            rId = prs.slides._sldIdLst[0].rId
            prs.part.drop_rel(rId)
            prs.slides._sldIdLst.remove(prs.slides._sldIdLst[0])
    except Exception as e:
        print(f"Error loading template: {e}")
        return

    # Process each section in the data
    for section in data.get('sections', []):
        # [Rest of the generate_presentation implementation...]
        content_type = section.get('content_type')
        if not content_type:
            print("Warning: Section missing 'content_type'. Skipping.")
            continue

        # Determine slide layout based on content type
        if content_type == 'presentation_title':
            slide_layout_name = "Title 1"
        elif content_type == 'bullet_points_summary':
            slide_layout_name = "Two Content"
        elif content_type == 'image_and_description':
            slide_layout_name = "Title, Content Photo 1"
        elif content_type == 'description_and_image':
            slide_layout_name = "Title, Content Photo 2"
        elif content_type == 'product_showcase':
            slide_layout_name = "Picture with Caption"
        elif content_type == 'chart_data_slide':
            slide_layout_name = "Content with Caption"
        else:
            print(f"Warning: Unknown content type '{content_type}'. Skipping.")
            continue

        # Find slide layout in template map
        slide_layout = None
        if template_map and "layouts" in template_map:
            for layout in template_map["layouts"]:
                if layout["name"] == slide_layout_name:
                    slide_layout = layout
                    break

        if not slide_layout:
            print(f"Warning: Slide layout '{slide_layout_name}' not found in template map. Skipping.")
            continue

        # Add slide to presentation
        layout_details = slide_layout
        slide_layout_index = layout_details["index"]
        slide_layout = prs.slide_layouts[slide_layout_index]

        # Debug: Print available placeholders
        print(f"\nPlaceholders in layout '{slide_layout_name}':")
        for shape in slide_layout.placeholders:
            print(f"  {shape.name}: type={shape.placeholder_format.type}, id={shape.placeholder_format.idx}")

        slide = prs.slides.add_slide(slide_layout)

        # Populate placeholders based on content type
        if content_type == 'presentation_title':
            title = section.get('title')
            subtitle = section.get('subtitle')

            title_placeholder = get_placeholder(slide, layout_details["placeholders"].get("Title"))
            subtitle_placeholder = get_placeholder(slide, layout_details["placeholders"].get("Subtitle"))
            
            if title_placeholder and title:
                title_placeholder.text = str(title)
            if subtitle_placeholder and subtitle:
                subtitle_placeholder.text = str(subtitle)

        elif content_type == 'bullet_points_summary':
            title = section.get('title')
            bullets = section.get('bullets', [])

            title_placeholder = get_placeholder(slide, layout_details["placeholders"].get("Title"))
            text_placeholder_1 = get_placeholder(slide, layout_details["placeholders"].get("Left Content"))
            text_placeholder_2 = get_placeholder(slide, layout_details["placeholders"].get("Right Content"))

            if title_placeholder and title:
                title_placeholder.text = str(title)
            
            # Set placeholder properties first
            if text_placeholder_1:
                set_placeholder_properties(text_placeholder_1, layout_details["placeholders"].get("Left Content"))
            if text_placeholder_2:
                set_placeholder_properties(text_placeholder_2, layout_details["placeholders"].get("Right Content"))

                # Add all bullets to first placeholder
            if bullets and text_placeholder_1:
                tf = text_placeholder_1.text_frame
                # Set all bullets as text
                tf.text = bullets[0]  # First bullet
                for bullet in bullets[1:]:
                    p = tf.add_paragraph()
                    p.text = str(bullet)
                    p.level = 0

                # Format text frame
                tf.word_wrap = True
                for p in tf.paragraphs:
                    p.font.size = Pt(16)

            # Clear second placeholder
            if text_placeholder_2:
                text_placeholder_2.text = ""

        elif content_type in ['image_and_description', 'description_and_image']:
            title = section.get('title')
            image_path = section.get('image_path')
            text_content = section.get('text_content')

            title_placeholder = get_placeholder(slide, layout_details["placeholders"].get("Title"))
            image_placeholder = get_placeholder(slide, layout_details["placeholders"].get("Picture"))
            text_placeholder = get_placeholder(slide, layout_details["placeholders"].get("Content"))

            if title_placeholder and title:
                title_placeholder.text = str(title)
            if text_placeholder and text_content:
                # For image_and_description, find all content placeholders
                if content_type == 'image_and_description':
                    content_placeholders = []
                    for shape in slide.placeholders:
                        if shape.placeholder_format.type in [2, 7]:  # BODY or OBJECT
                            content_placeholders.append(shape)
                    
                    # Split content between available placeholders
                    if content_placeholders:
                        content_paragraphs = str(text_content).split('\n')
                        total_placeholders = len(content_placeholders)
                        mid = len(content_paragraphs) // total_placeholders
                        
                        for i, placeholder in enumerate(content_placeholders):
                            # Calculate content range for this placeholder
                            start = i * mid
                            end = (i + 1) * mid if i < total_placeholders - 1 else None
                            placeholder_content = content_paragraphs[start:end]
                            
                            # Set text and format
                            if placeholder_content:
                                placeholder.text = '\n'.join(placeholder_content)
                                tf = placeholder.text_frame
                                tf.word_wrap = True
                                for p in tf.paragraphs:
                                    p.level = 0  # Body text level
                                    p.font.size = Pt(14)
                                    p.space_before = Pt(6)
                                    p.space_after = Pt(6)
                else:
                    # Regular text handling for other content types
                    text_placeholder.text = str(text_content)
                    tf = text_placeholder.text_frame
                    tf.word_wrap = True
                    for p in tf.paragraphs:
                        p.level = 0  # Body text level
                        p.font.size = Pt(14)
                        p.space_before = Pt(6)
                        p.space_after = Pt(6)
            if image_placeholder and image_path:
                insert_image_to_placeholder(slide, image_placeholder, image_path, layout_details["placeholders"].get("Picture"))

        elif content_type == 'product_showcase':
            title = section.get('title')
            product_image_path = section.get('product_image_path')
            caption = section.get('caption')

            title_placeholder = get_placeholder(slide, layout_details["placeholders"].get("Title"))
            image_placeholder = get_placeholder(slide, layout_details["placeholders"].get("Picture"))
            text_placeholder = get_placeholder(slide, layout_details["placeholders"].get("Content"))

            if title_placeholder and title:
                title_placeholder.text = str(title)
            if text_placeholder and caption:
                text_placeholder.text = str(caption)
            if image_placeholder and product_image_path:
                insert_image_to_placeholder(slide, image_placeholder, product_image_path, layout_details["placeholders"].get("Picture"))

        elif content_type == 'chart_data_slide':
            title = section.get('title')
            chart_data = section.get('chart_data')
            text_content = section.get('text_content')

            title_placeholder = get_placeholder(slide, layout_details["placeholders"].get("Title"))
            chart_placeholder = get_placeholder(slide, layout_details["placeholders"].get("Chart"))
            text_placeholder = get_placeholder(slide, layout_details["placeholders"].get("Content"))

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
                    print(f"Warning: Could not create chart: {e}")

    # Save the final presentation
    try:
        prs.save(output_filepath)
        print(f"Presentation saved to {output_filepath}")
    except Exception as e:
        print(f"Error saving presentation: {e}")
