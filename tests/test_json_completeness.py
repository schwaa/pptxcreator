import unittest
import json
import os

class TestPresentationJsonCompleteness(unittest.TestCase):

    def setUp(self):
        self.presentation_json_path = "projects/first_test_run/output/presentation.json"
        self.layouts_json_path = "projects/first_test_run/output/layouts.json"

        if not os.path.exists(self.presentation_json_path):
            raise FileNotFoundError(f"Test file not found: {self.presentation_json_path}. Run the 'process' command first.")
        if not os.path.exists(self.layouts_json_path):
            raise FileNotFoundError(f"Layouts file not found: {self.layouts_json_path}. Run the 'analyze' command first.")

        with open(self.presentation_json_path, 'r') as f:
            self.presentation_data = json.load(f)
        with open(self.layouts_json_path, 'r') as f:
            self.layouts_data = json.load(f)
        
        # We want to perform an exact, case-sensitive match, just like the generator does.
        self.layout_placeholders_map = {
            layout['name']: [p.strip() for p in layout['placeholders']]
            for layout in self.layouts_data.get('layouts', [])
        }

    def test_slides_structure(self):
        self.assertIn("slides", self.presentation_data)
        self.assertIsInstance(self.presentation_data["slides"], list)
        self.assertTrue(len(self.presentation_data["slides"]) > 0, "Presentation should have at least one slide.")

    def test_slide_content_completeness_and_placeholder_match(self):
        errors = []
        for i, slide in enumerate(self.presentation_data.get("slides", [])):
            layout_name = slide.get("layout")
            content = slide.get("content", {})
            
            # Use a simple get() to avoid crashing if the layout name from the LLM is wrong
            expected_placeholders_for_layout = self.layout_placeholders_map.get(layout_name)
            
            if expected_placeholders_for_layout is None:
                errors.append(f"Slide {i}: Layout '{layout_name}' from presentation.json not found in layouts.json.")
                continue

            for placeholder_from_content in content.keys():
                if placeholder_from_content.strip() not in expected_placeholders_for_layout:
                    errors.append(
                        f"Slide {i} (Layout: '{layout_name}'): Placeholder '{placeholder_from_content}' not found.\n"
                        f"  >> Expected one of: {expected_placeholders_for_layout}"
                    )

        if errors:
            # This will now fail with a beautiful, precise list of all the case-mismatched placeholders.
            self.fail("Placeholder validation failed with the following errors:\n" + "\n".join(errors))

if __name__ == '__main__':
    unittest.main()
