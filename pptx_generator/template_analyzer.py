from pptx import Presentation
from pptx.enum.shapes import PP_PLACEHOLDER_TYPE, MSO_SHAPE_TYPE
import json
import os

# Mapping for common placeholder types to simpler strings
PLACEHOLDER_TYPE_MAP = {
    PP_PLACEHOLDER_TYPE.TITLE: "title",
    PP_PLACEHOLDER_TYPE.BODY: "body",
    PP_PLACEHOLDER_TYPE.SUBTITLE: "subtitle",
    PP_PLACEHOLDER_TYPE.PICTURE: "picture",
    PP_PLACEHOLDER_TYPE.CHART: "chart",
    PP_PLACEHOLDER_TYPE.TABLE: "table",
    PP_PLACEHOLDER_TYPE.OBJECT: "object", # Generic object
    # Add more as needed
}

def get_shape_type_name(shape):
    """Helper to get a human-readable type for a shape."""
    if shape.is_placeholder:
        return PLACEHOLDER_TYPE_MAP.get(shape.placeholder_format.type, "unknown_placeholder")
    elif shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
        return "picture"
    elif shape.has_text_frame:
        return "textbox"
    elif shape.has_table:
        return "table"
    elif shape.has_chart:
        return "chart"
    return "shape" # Generic shape

def analyze_template_and_create_map(template_filepath, output_map_filepath):
    """
    Analyzes a PowerPoint template and generates a JSON mapping file.
    This mapping includes layout names, placeholder details, and attempts
    to assign a semantic type to each layout based on its placeholders.
    """
    print(f"Analyzing template: {template_filepath}")
    try:
        prs = Presentation(template_filepath)
    except Exception as e:
        print(f"Error: Could not load template '{template_filepath}'. Details: {e}")
        print("Please ensure the template file exists and is a valid PPTX.")
        return

    template_map = {
        "template_filepath": template_filepath,
        "layouts": []
    }

    for layout_idx, slide_layout in enumerate(prs.slide_layouts):
        layout_info = {
            "name": slide_layout.name,
            "index": layout_idx,
            "placeholders": {},
            "semantic_type": "unknown", # Initial guess
            "features": { # For AI decision making
                "has_title": False,
                "has_subtitle": False,
                "has_body_text": False,
                "num_text_placeholders": 0,
                "num_picture_placeholders": 0,
                "num_chart_placeholders": 0,
                "num_table_placeholders": 0,
                "default_title_name": None,
                "default_body_name": None,
                "default_picture_name": None
            }
        }

        # Analyze placeholders within this layout
        for shape in slide_layout.placeholders:
            ph_name = shape.name
            ph_type = get_shape_type_name(shape)
            ph_id = shape.placeholder_format.idx # Unique ID within layout type

            layout_info["placeholders"][ph_name] = {
                "type": ph_type,
                "id": ph_id,
                "left": shape.left.inches,
                "top": shape.top.inches,
                "width": shape.width.inches,
                "height": shape.height.inches,
            }

            # Populate features for semantic typing
            if ph_type == "title":
                layout_info["features"]["has_title"] = True
                layout_info["features"]["default_title_name"] = ph_name
            elif ph_type == "subtitle":
                layout_info["features"]["has_subtitle"] = True
            elif ph_type == "body":
                layout_info["features"]["has_body_text"] = True
                layout_info["features"]["default_body_name"] = ph_name
            elif ph_type == "picture":
                layout_info["features"]["num_picture_placeholders"] += 1
                layout_info["features"]["default_picture_name"] = ph_name # Store first one found
            elif ph_type == "chart":
                layout_info["features"]["num_chart_placeholders"] += 1
            elif ph_type == "table":
                layout_info["features"]["num_table_placeholders"] += 1
            if ph_type in ["title", "subtitle", "body", "textbox"]:
                layout_info["features"]["num_text_placeholders"] += 1

        # --- Attempt to assign a semantic type based on detected features ---
        features = layout_info["features"]

        if features["has_title"] and not features["has_body_text"] and not features["num_picture_placeholders"] and not features["num_chart_placeholders"] and not features["has_subtitle"]:
            if layout_info["name"].lower() == "title only":
                layout_info["semantic_type"] = "title_only"
            else:
                layout_info["semantic_type"] = "section_header"

        elif features["has_title"] and features["has_subtitle"] and features["num_text_placeholders"] == 2:
            layout_info["semantic_type"] = "presentation_title"

        elif features["has_title"] and features["has_body_text"] and features["num_picture_placeholders"] == 0 and features["num_chart_placeholders"] == 0:
            layout_info["semantic_type"] = "bullet_points_summary"

        elif features["has_title"] and features["num_picture_placeholders"] == 1 and not features["has_body_text"]:
            layout_info["semantic_type"] = "title_and_single_image"

        elif features["has_title"] and features["num_picture_placeholders"] == 1 and features["has_body_text"]:
            # Check for specific layouts based on placeholder names
            if "imageleft" in {k.lower() for k in layout_info["placeholders"].keys()} and \
               "textright" in {k.lower() for k in layout_info["placeholders"].keys()}:
               layout_info["semantic_type"] = "image_and_description"
            elif "textleft" in {k.lower() for k in layout_info["placeholders"].keys()} and \
                 "imageright" in {k.lower() for k in layout_info["placeholders"].keys()}:
               layout_info["semantic_type"] = "description_and_image"
            elif "imagecaption" in {k.lower() for k in layout_info["placeholders"].keys()}:
                layout_info["semantic_type"] = "product_showcase"
            else:
                layout_info["semantic_type"] = "image_and_text"

        elif features["has_title"] and features["num_chart_placeholders"] == 1:
            layout_info["semantic_type"] = "chart_data_slide"

        elif layout_info["name"].lower() == "blank":
            layout_info["semantic_type"] = "blank_canvas"

        template_map["layouts"].append(layout_info)

    # Save the map to a JSON file
    output_dir = os.path.dirname(output_map_filepath)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    try:
        with open(output_map_filepath, 'w', encoding='utf-8') as f:
            json.dump(template_map, f, indent=4)
        print(f"Template map saved to: {output_map_filepath}")
    except Exception as e:
        print(f"Error saving template map to '{output_map_filepath}': {e}")
