from pptx import Presentation
from pptx.util import Inches
from pptx.enum.chart import XL_CHART_TYPE
from pptx.chart.data import CategoryChartData
import os
import json

from .utils import (
    find_placeholder_by_name,
    find_text_placeholder_by_idx,
    find_picture_placeholder_by_type,
    populate_text_placeholder,
    populate_image_placeholder
)

def generate_presentation(data_filepath, template_filepath, output_filepath):
    """
    Generates a PowerPoint presentation based on structured data and a template.

    Args:
        data_filepath (str): Path to the JSON file containing presentation data.
        template_filepath (str): Path to the template PPTX file.
        output_filepath (str): Path where the generated PPTX will be saved.
    """
    print(f"Loading data from: {data_filepath}")
    try:
        with open(data_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Data file not found at '{data_filepath}'.")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in '{data_filepath}'.")
        return

    print(f"Loading template from: {template_filepath}")
    try:
        prs = Presentation(template_filepath)
    except Exception as e:
        print(f"Error: Could not load template '{template_filepath}'. Details: {e}")
        print("Please ensure the template file exists and is a valid PPTX.")
        return

    available_layouts = {layout.name: layout for layout in prs.slide_layouts}
    print(f"Available layouts in template: {list(available_layouts.keys())}")

    for i, section in enumerate(data.get("sections", [])):
        slide_layout_name = section.get("layout_name")
        layout = available_layouts.get(slide_layout_name)

        if not layout:
            print(f"Warning: Slide {i+1}: Layout '{slide_layout_name}' not found in template. Skipping this section.")
            continue

        slide = prs.slides.add_slide(layout)
        print(f"Adding slide {i+1}: Layout='{slide_layout_name}' - Title='{section.get('title', 'N/A')}'")

        # --- General Title for most slides ---
        # Attempt to find by name first, then fallback to default title shape
        title_ph = find_placeholder_by_name(slide, "Title Placeholder") # Standard name
        if not title_ph:
            try:
                title_ph = slide.shapes.title
            except AttributeError: # Some layouts might not have a default title shape
                title_ph = None
        populate_text_placeholder(title_ph, section.get("title", ""))

        # --- Handle specific layouts based on the layout_name ---
        if slide_layout_name == "Title Slide": # Default PowerPoint layout name
            subtitle_ph = find_placeholder_by_name(slide, "Subtitle Placeholder")
            if not subtitle_ph:
                subtitle_ph = find_text_placeholder_by_idx(slide, 1) # Common fallback
            populate_text_placeholder(subtitle_ph, section.get("subtitle", ""))

        elif slide_layout_name == "Title and Content": # Default PowerPoint layout name
            body_ph = find_placeholder_by_name(slide, "Content Placeholder")
            if not body_ph:
                body_ph = find_text_placeholder_by_idx(slide, 1) # Common fallback

            if body_ph and body_ph.has_text_frame:
                tf = body_ph.text_frame
                tf.clear()
                for bullet in section.get("bullets", []):
                    p = tf.add_paragraph()
                    p.text = bullet
                    p.level = 0

        # --- Custom Layouts (Requires specific naming in your template) ---
        elif slide_layout_name == "Image Left, Text Right":
            image_left_ph = find_placeholder_by_name(slide, "ImageLeft")
            populate_image_placeholder(image_left_ph, section.get("image_path", ""))

            text_right_ph = find_placeholder_by_name(slide, "TextRight")
            populate_text_placeholder(text_right_ph, section.get("text_content", ""))

        elif slide_layout_name == "Text Left, Image Right":
            text_left_ph = find_placeholder_by_name(slide, "TextLeft")
            populate_text_placeholder(text_left_ph, section.get("text_content", ""))

            image_right_ph = find_placeholder_by_name(slide, "ImageRight")
            populate_image_placeholder(image_right_ph, section.get("image_path", ""))

        elif slide_layout_name == "Full Width Image with Caption":
            full_image_ph = find_placeholder_by_name(slide, "FullWidthImage")
            populate_image_placeholder(full_image_ph, section.get("image_path", ""))

            caption_ph = find_placeholder_by_name(slide, "ImageCaption")
            populate_text_placeholder(caption_ph, section.get("caption", ""))

        elif slide_layout_name == "Blank" and "chart_data" in section:
            chart_data = CategoryChartData()
            chart_data.categories = section["chart_data"]["categories"]
            for series_data in section["chart_data"]["series"]:
                chart_data.add_series(series_data["name"], series_data["values"])

            x, y, cx, cy = Inches(1), Inches(1.5), Inches(8), Inches(4.5)
            slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, x, y, cx, cy, chart_data)
            # For blank charts, ensure title is handled if not in a placeholder
            if not title_ph and section.get("title"): # If title wasn't placed
                # Add a new text box for the title if desired
                left, top, width, height = Inches(0.5), Inches(0.5), Inches(9), Inches(1)
                textbox = slide.shapes.add_textbox(left, top, width, height)
                textbox.text_frame.text = section.get("title")

    print(f"Saving presentation to: {output_filepath}")
    try:
        prs.save(output_filepath)
        print("Presentation generation complete!")
    except Exception as e:
        print(f"Error saving presentation to '{output_filepath}': {e}")
        print("Please ensure the output path is valid and you have write permissions.")
