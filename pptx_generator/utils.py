import os
from pptx.enum.shapes import MSO_SHAPE_TYPE

def find_placeholder_by_name(slide, name):
    """
    Finds a placeholder on a slide by its name.
    Useful when you've named placeholders in your template.
    """
    for shape in slide.shapes:
        # Check if it's a placeholder (has placeholder_format) and has a name
        if shape.is_placeholder and shape.name == name:
            return shape
    return None

def find_text_placeholder_by_idx(slide, idx):
    """
    Finds a text placeholder by its index.
    Useful for standard layouts where placeholder indices are consistent.
    """
    try:
        # Placeholder 1 is typically the body, 0 is title
        if idx == 0:
            return slide.shapes.title
        return slide.placeholders[idx]
    except IndexError:
        return None
    except AttributeError: # slide.shapes.title might not exist
        return None

def find_picture_placeholder_by_type(slide):
    """
    Finds the first picture placeholder on a slide.
    """
    for shape in slide.shapes:
        if shape.is_placeholder and shape.placeholder_format.type == MSO_SHAPE_TYPE.PICTURE:
            return shape
    return None

def populate_text_placeholder(placeholder, text_content, level=0):
    """Helper to safely populate a text placeholder."""
    if placeholder and placeholder.has_text_frame:
        tf = placeholder.text_frame
        tf.clear()
        # Split content by newlines to create multiple paragraphs if needed
        paragraphs = text_content.split('\n')
        for i, para_text in enumerate(paragraphs):
            p = tf.add_paragraph()
            p.text = para_text
            p.level = level # You might want to adjust level dynamically
        # Additional formatting can be added here (font, size, bold, etc.)
    else:
        print(f"Warning: Text placeholder not found or not a text frame for content: '{text_content[:30]}...'")

def populate_image_placeholder(placeholder, image_path):
    """Helper to safely populate a picture placeholder."""
    if placeholder and placeholder.is_placeholder and placeholder.placeholder_format.type == MSO_SHAPE_TYPE.PICTURE:
        if os.path.exists(image_path):
            try:
                placeholder.insert_picture(image_path)
            except Exception as e:
                print(f"Error inserting image '{image_path}' into placeholder: {e}")
        else:
            print(f"Warning: Image file not found: {image_path}. Skipping image for this placeholder.")
    else:
        print(f"Warning: Picture placeholder not found or not a picture placeholder for image: {image_path}.")
