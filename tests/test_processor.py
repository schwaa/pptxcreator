import pytest
import os
import json
import requests
from unittest.mock import patch, MagicMock, mock_open

from pptx_generator.processor import (
    call_planning_llm,
    call_designer_llm,
    generate_and_save_image,
    process_content
)
from pptx_generator.models import SlidePlan, FinalSlide, ImageGenerationRequest

# --- Fixtures ---
@pytest.fixture
def mock_env_vars(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_api_key")
    monkeypatch.setenv("OPENROUTER_MODEL_NAME", "test_model")
    monkeypatch.setenv("SD_FORGE_SERVER_URL", "http://fake-sd-forge.com")
    monkeypatch.setenv("FLUX_MODEL_NAME", "test_flux_model")

@pytest.fixture
def sample_layouts_json_str():
    return json.dumps({
        "source_template_path": "dummy.pptx",
        "layouts": [
            {"name": "Title Slide", "placeholders": ["Title 1", "Subtitle 2"]},
            {"name": "Title and Content", "placeholders": ["Title 1", "Content Placeholder 1"]},
            {"name": "Image with Caption", "placeholders": ["Title 1", "Picture Placeholder 1", "Caption Placeholder 1"]}
        ]
    })

@pytest.fixture
def sample_slide_plan_no_image():
    return SlidePlan(
        slide_topic="Test Topic No Image",
        content_type="paragraph",
        raw_content=["This is test content.", "It has two lines."]
    )

@pytest.fixture
def sample_slide_plan_with_image_request():
    return SlidePlan(
        slide_topic="Test Topic With Image",
        content_type="image_with_caption",
        image_request=ImageGenerationRequest(prompt="A test image prompt"),
        raw_content=["Caption for the image."]
    )

@pytest.fixture
def sample_final_slide_text():
    return FinalSlide(
        layout="Title and Content",
        placeholders={
            "Title 1": "Test Topic No Image",
            "Content Placeholder 1": ["This is test content.", "It has two lines."]
        }
    )

@pytest.fixture
def sample_final_slide_image():
    return FinalSlide(
        layout="Image with Caption",
        placeholders={
            "Title 1": "Test Topic With Image",
            "Picture Placeholder 1": "images/slide_1_test_topic_with_image.png",
            "Caption Placeholder 1": "Caption for the image."
        }
    )

# --- Tests for call_planning_llm ---
@patch('pptx_generator.processor.client.chat.completions.create') # Keep patch for consistency
def test_call_planning_llm_handles_not_implemented(mock_create, mock_env_vars, sample_layouts_json_str, caplog):
    markdown_chunk = "## Test Topic\n\nThis is test content."
    result = call_planning_llm(markdown_chunk, sample_layouts_json_str)
    
    assert result is None # Function should catch NotImplementedError and return None
    mock_create.assert_not_called() # The actual LLM call should not be reached
    
    # Check for the specific NotImplementedError being logged
    found_log = False
    for record in caplog.records:
        if record.levelname == "ERROR" and "Error in call_planning_llm: call_planning_llm is not yet implemented with pydantic-ai" in record.message:
            found_log = True
            break
    assert found_log, "Expected NotImplementedError log message for call_planning_llm not found."

# --- Tests for call_designer_llm ---
@patch('pptx_generator.processor.client.chat.completions.create') # Keep patch for consistency
def test_call_designer_llm_handles_not_implemented(mock_create, mock_env_vars, sample_slide_plan_no_image, sample_layouts_json_str, caplog):
    result = call_designer_llm(sample_slide_plan_no_image, None, sample_layouts_json_str)
    
    assert result is None # Function should catch NotImplementedError and return None
    mock_create.assert_not_called() # The actual LLM call should not be reached

    # Check for the specific NotImplementedError being logged
    found_log = False
    for record in caplog.records:
        if record.levelname == "ERROR" and "Error in call_designer_llm: call_designer_llm is not yet implemented with pydantic-ai" in record.message:
            found_log = True
            break
    assert found_log, "Expected NotImplementedError log message for call_designer_llm not found."

# --- Tests for generate_and_save_image ---
@patch('pptx_generator.processor.requests.post')
@patch('pptx_generator.processor.os.makedirs')
@patch('builtins.open', new_callable=mock_open)
def test_generate_and_save_image_success(mock_file_open, mock_makedirs, mock_post, mock_env_vars):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"images": ["dGVzdF9pbWFnZV9kYXRh"]} # base64 for "test_image_data"
    mock_post.return_value = mock_response
    
    sd_forge_url = os.getenv("SD_FORGE_SERVER_URL")
    success = generate_and_save_image("test prompt", "output/images/test.png", "test_model", sd_forge_url)
    
    assert success is True
    mock_makedirs.assert_called_once_with("output/images", exist_ok=True)
    mock_file_open.assert_called_once_with("output/images/test.png", 'wb')
    mock_post.assert_called_once()

@patch('pptx_generator.processor.requests.post')
def test_generate_and_save_image_api_error(mock_post, mock_env_vars):
    mock_post.side_effect = requests.exceptions.RequestException("API Down")
    sd_forge_url = os.getenv("SD_FORGE_SERVER_URL")
    success = generate_and_save_image("test prompt", "output/images/test.png", "test_model", sd_forge_url)
    assert success is False

def test_generate_and_save_image_no_sd_forge_url(mock_env_vars, monkeypatch):
    monkeypatch.setenv("SD_FORGE_SERVER_URL", "") # Unset or empty
    success = generate_and_save_image("test prompt", "output/images/test.png", "test_model", "")
    assert success is False

# --- Tests for process_content (Orchestration) ---
@patch('pptx_generator.processor.call_planning_llm')
@patch('pptx_generator.processor.call_designer_llm')
@patch('pptx_generator.processor.generate_and_save_image')
@patch('builtins.open', new_callable=mock_open)
@patch('pptx_generator.processor.os.makedirs')
def test_process_content_success_no_images(
    mock_os_makedirs, mock_file_open_global, mock_gen_img, mock_designer_llm, mock_planning_llm,
    mock_env_vars, sample_layouts_json_str, sample_slide_plan_no_image, sample_final_slide_text,
    tmp_path
):
    # Setup mocks
    mock_planning_llm.return_value = sample_slide_plan_no_image
    mock_designer_llm.return_value = sample_final_slide_text
    mock_gen_img.return_value = False # Should not be called if no image_request

    # Prepare dummy files
    md_path = tmp_path / "content.md"
    md_path.write_text("## Slide 1\nContent for slide 1.")
    
    layouts_path = tmp_path / "layouts.json"
    layouts_path.write_text(sample_layouts_json_str)
    
    output_path = tmp_path / "presentation.json"

    # Mock open for reading markdown and layouts, and writing output
    def mock_open_side_effect(filepath, *args, **kwargs):
        if str(filepath) == str(md_path):
            return mock_open(read_data="## Slide 1\nContent for slide 1.").return_value
        elif str(filepath) == str(layouts_path):
            return mock_open(read_data=sample_layouts_json_str).return_value
        elif str(filepath) == str(output_path): # This is for the final write
             return mock_file_open_global.return_value
        raise FileNotFoundError(f"Unexpected file open: {filepath}")

    with patch('builtins.open', side_effect=mock_open_side_effect):
        process_content(str(md_path), str(layouts_path), str(output_path))

    mock_planning_llm.assert_called_once()
    mock_designer_llm.assert_called_once_with(sample_slide_plan_no_image, None, sample_layouts_json_str)
    mock_gen_img.assert_not_called() 
    
    mock_os_makedirs.assert_called_with(os.path.dirname(str(output_path)), exist_ok=True)
    
    with patch('json.dump') as mock_json_dump:
         with patch('builtins.open', side_effect=mock_open_side_effect): 
            process_content(str(md_path), str(layouts_path), str(output_path))
         
         expected_output_structure = {"slides": [sample_final_slide_text.model_dump(exclude_none=True)]}
         args, kwargs = mock_json_dump.call_args_list[-1]
         assert args[0] == expected_output_structure

@patch('pptx_generator.processor.call_planning_llm')
@patch('pptx_generator.processor.call_designer_llm')
@patch('pptx_generator.processor.generate_and_save_image')
@patch('pptx_generator.processor.os.makedirs')
@patch('json.dump') 
def test_process_content_success_with_image_generation(
    mock_json_dump, mock_os_makedirs, mock_gen_img, mock_designer_llm, mock_planning_llm,
    mock_env_vars, sample_layouts_json_str, 
    sample_slide_plan_with_image_request, sample_final_slide_image,
    tmp_path
):
    mock_planning_llm.return_value = sample_slide_plan_with_image_request
    mock_designer_llm.return_value = sample_final_slide_image
    mock_gen_img.return_value = True 

    md_path = tmp_path / "content_img.md"
    md_path.write_text("## Slide Image\nNeeds an image.")
    
    layouts_path = tmp_path / "layouts_img.json"
    layouts_path.write_text(sample_layouts_json_str)
    
    output_path = tmp_path / "presentation_img.json"

    def mock_open_side_effect(filepath, *args, **kwargs):
        if str(filepath) == str(md_path):
            return mock_open(read_data="## Slide Image\nNeeds an image.").return_value
        elif str(filepath) == str(layouts_path):
            return mock_open(read_data=sample_layouts_json_str).return_value
        elif str(filepath) == str(output_path): 
             m = MagicMock()
             m.__enter__.return_value = MagicMock() 
             m.__exit__.return_value = None
             return m
        raise FileNotFoundError(f"Unexpected file open: {filepath}")

    with patch('builtins.open', side_effect=mock_open_side_effect):
        process_content(str(md_path), str(layouts_path), str(output_path), regenerate_images=True)

    mock_planning_llm.assert_called_once()
    
    expected_image_filename = "slide_1_test_topic_with_image.png"
    expected_image_path_for_json = os.path.join("images", expected_image_filename)
    
    project_dir = os.path.dirname(os.path.abspath(str(md_path)))
    images_output_dir = os.path.join(project_dir, "images")
    expected_abs_image_save_path = os.path.join(images_output_dir, expected_image_filename)

    mock_gen_img.assert_called_once_with(
        sample_slide_plan_with_image_request.image_request.prompt,
        expected_abs_image_save_path,
        os.getenv("FLUX_MODEL_NAME"),
        os.getenv("SD_FORGE_SERVER_URL")
    )
    
    mock_designer_llm.assert_called_once_with(
        sample_slide_plan_with_image_request, 
        expected_image_path_for_json,
        sample_layouts_json_str
    )
    
    expected_output_structure = {"slides": [sample_final_slide_image.model_dump(exclude_none=True)]}
    mock_json_dump.assert_called_once()
    args_dump, kwargs_dump = mock_json_dump.call_args
    assert args_dump[0] == expected_output_structure

def test_process_content_file_not_found(mock_env_vars, tmp_path, caplog):
    process_content("non_existent.md", "layouts.json", "output.json")
    assert "Markdown file not found: non_existent.md" in caplog.text
    caplog.clear()
    
    md_path = tmp_path / "content.md"
    md_path.write_text("Test")
    process_content(str(md_path), "non_existent_layouts.json", "output.json")
    assert f"Layouts file not found: non_existent_layouts.json" in caplog.text
