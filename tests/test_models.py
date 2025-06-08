import pytest
from pydantic import ValidationError
from pptx_generator.models import ImageGenerationRequest, SlidePlan, FinalSlide

# Test ImageGenerationRequest
def test_image_generation_request_valid():
    data = {"prompt": "A beautiful sunset over mountains."}
    req = ImageGenerationRequest(**data)
    assert req.prompt == data["prompt"]

def test_image_generation_request_missing_prompt():
    with pytest.raises(ValidationError):
        ImageGenerationRequest() # prompt is required

def test_image_generation_request_invalid_prompt_type():
    with pytest.raises(ValidationError):
        ImageGenerationRequest(prompt=123) # prompt should be a string

# Test SlidePlan
def test_slide_plan_valid_no_image():
    data = {
        "slide_topic": "Introduction to AI",
        "content_type": "paragraph",
        "raw_content": ["AI is transforming the world.", "It has many applications."]
    }
    plan = SlidePlan(**data)
    assert plan.slide_topic == data["slide_topic"]
    assert plan.content_type == data["content_type"]
    assert plan.raw_content == data["raw_content"]
    assert plan.image_request is None

def test_slide_plan_valid_with_image():
    data = {
        "slide_topic": "AI in Art",
        "content_type": "image_with_caption",
        "image_request": {"prompt": "A robot painting a masterpiece."},
        "raw_content": ["AI can also be creative."]
    }
    plan = SlidePlan(**data)
    assert plan.slide_topic == data["slide_topic"]
    assert plan.image_request is not None
    assert plan.image_request.prompt == data["image_request"]["prompt"]
    assert plan.raw_content == data["raw_content"]

def test_slide_plan_missing_required_fields():
    with pytest.raises(ValidationError):
        SlidePlan(slide_topic="Topic Only") # content_type and raw_content are required

    with pytest.raises(ValidationError):
        SlidePlan(content_type="paragraph", raw_content=["Test"]) # slide_topic is required

    with pytest.raises(ValidationError):
        SlidePlan(slide_topic="Topic", content_type="paragraph") # raw_content is required

def test_slide_plan_invalid_content_type():
    data = {
        "slide_topic": "Invalid Type",
        "content_type": "invalid_enum_value", # Not in Literal
        "raw_content": ["This should fail."]
    }
    with pytest.raises(ValidationError):
        SlidePlan(**data)

def test_slide_plan_invalid_image_request_structure():
    data = {
        "slide_topic": "Bad Image Request",
        "content_type": "image_with_caption",
        "image_request": {"not_a_prompt": "A robot painting a masterpiece."}, # Incorrect key
        "raw_content": ["This should fail."]
    }
    with pytest.raises(ValidationError):
        SlidePlan(**data)

# Test FinalSlide
def test_final_slide_valid_text_only():
    data = {
        "layout": "Title and Content",
        "placeholders": {
            "Title 1": "Final Slide Title",
            "Content Placeholder 1": ["Bullet point 1.", "Bullet point 2."]
        }
    }
    final_slide = FinalSlide(**data)
    assert final_slide.layout == data["layout"]
    assert final_slide.placeholders["Title 1"] == data["placeholders"]["Title 1"]
    assert final_slide.placeholders["Content Placeholder 1"] == data["placeholders"]["Content Placeholder 1"]

def test_final_slide_valid_with_image_path():
    data = {
        "layout": "Image with Caption",
        "placeholders": {
            "Title 1": "Image Slide",
            "Picture Placeholder 1": "images/generated_image.png",
            "Caption Placeholder 1": "This is a generated image."
        }
    }
    final_slide = FinalSlide(**data)
    assert final_slide.layout == data["layout"]
    assert final_slide.placeholders["Picture Placeholder 1"] == data["placeholders"]["Picture Placeholder 1"]

def test_final_slide_missing_required_fields():
    with pytest.raises(ValidationError):
        FinalSlide(layout="Title Slide") # placeholders is required

    with pytest.raises(ValidationError):
        FinalSlide(placeholders={"Title 1": "Test"}) # layout is required

def test_final_slide_invalid_placeholder_value_type():
    # Example: placeholder value is a dict when it should be str or List[str]
    data = {
        "layout": "Title and Content",
        "placeholders": {
            "Title 1": {"text": "This is wrong structure"}
        }
    }
    with pytest.raises(ValidationError):
        FinalSlide(**data)

def test_final_slide_placeholder_content_types():
    # String value
    data_str = {
        "layout": "Title Slide",
        "placeholders": {"Title 1": "A Simple Title"}
    }
    slide_str = FinalSlide(**data_str)
    assert isinstance(slide_str.placeholders["Title 1"], str)

    # List of strings value
    data_list = {
        "layout": "Content Slide",
        "placeholders": {"Body": ["Line 1", "Line 2"]}
    }
    slide_list = FinalSlide(**data_list)
    assert isinstance(slide_list.placeholders["Body"], list)
    assert all(isinstance(item, str) for item in slide_list.placeholders["Body"])

    # Image path (string)
    data_img = {
        "layout": "Image Slide",
        "placeholders": {"Image Placeholder": "path/to/image.png"}
    }
    slide_img = FinalSlide(**data_img)
    assert isinstance(slide_img.placeholders["Image Placeholder"], str)
