from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal

class ImageGenerationRequest(BaseModel):
    """The AI's decision to generate an image."""
    prompt: str = Field(description="A detailed, descriptive prompt for an image generation model.")

class SlidePlan(BaseModel):
    """The AI's high-level plan for a single slide AFTER analyzing the markdown."""
    slide_topic: str = Field(description="A brief topic or title for the slide.")
    content_type: Literal['paragraph', 'bullet_list', 'title_only', 'image_with_caption'] = Field(description="The primary type of content on the slide.")
    image_request: Optional[ImageGenerationRequest] = Field(default=None, description="An optional request to generate an image for this slide.")
    raw_content: List[str] = Field(description="The raw text content, broken into a list of strings (sentences or bullets).")

class FinalSlide(BaseModel):
    """The final, validated JSON structure for a single slide, ready for the generator."""
    layout: str = Field(description="The name of the PowerPoint layout to use for this slide.")
    placeholders: Dict[str, List[str] | str] = Field(description="A dictionary mapping placeholder names (keys) to their content (values). Content can be a string or a list of strings for bullets/paragraphs. For images, the value will be the path to the image file.")
