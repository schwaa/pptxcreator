from pptx.enum.shapes import PP_PLACEHOLDER_TYPE, MSO_SHAPE_TYPE

def find_placeholder_by_name(slide, placeholder_name):
    """Find a placeholder by its name in a slide."""
    if not placeholder_name:
        return None
        
    # Try exact match first
    for shape in slide.placeholders:
        if shape.name == placeholder_name:
            return shape
    
    # Try case-insensitive match
    for shape in slide.placeholders:
        if shape.name.lower() == placeholder_name.lower():
            return shape
            
    # Try partial match
    search_term = placeholder_name.lower()
    for shape in slide.placeholders:
        if search_term in shape.name.lower():
            return shape
    
    return None

def find_text_placeholder_by_idx(slide, idx):
    """Find a text placeholder by its index in a slide."""
    for shape in slide.placeholders:
        if shape.placeholder_format.idx == idx:
            return shape
    return None

def find_picture_placeholder_by_type(slide):
    """Find a picture placeholder in a slide."""
    # Try finding by placeholder type
    for shape in slide.placeholders:
        if shape.is_placeholder and shape.placeholder_format.type == PP_PLACEHOLDER_TYPE.PICTURE:
            return shape
    
    # Try finding by name containing "Picture"
    for shape in slide.placeholders:
        if shape.name and "picture" in shape.name.lower():
            return shape
            
    # Try finding by name containing "Image"
    for shape in slide.placeholders:
        if shape.name and "image" in shape.name.lower():
            return shape
            
    return None

def populate_text_placeholder(placeholder_shape, text):
    """Populate a text placeholder with content."""
    if not placeholder_shape:
        return
        
    if not hasattr(placeholder_shape, 'text'):
        return
        
    try:
        placeholder_shape.text = text or ""  # Handle None gracefully
    except Exception as e:
        # Silently ignore text placeholder errors
        pass

def populate_image_placeholder(placeholder_shape, image_path):
    """Populate an image placeholder with an image."""
    if not placeholder_shape or not image_path:
        return

    try:
        if not image_path.startswith("images/"):
            image_path = "images/dummy_image.png"
            
        try:
            placeholder_shape.insert_picture(image_path)
        except FileNotFoundError:
            try:
                from PIL import Image
                import os
                os.makedirs("images", exist_ok=True)
                img = Image.new('RGB', (800, 600), color='lightblue')
                img.save("images/dummy_image.png")
                placeholder_shape.insert_picture("images/dummy_image.png")
            except Exception:
                pass
    except Exception:
        pass  # Silently ignore image placeholder errors
