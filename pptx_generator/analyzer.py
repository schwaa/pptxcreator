import json
import os
import argparse
from pptx import Presentation

def analyze_template(template_filepath: str, output_filepath: str):
    """
    Analyzes a PowerPoint template and creates a simple JSON file listing
    each layout and its placeholder names. This version instantiates each
    layout to get the most accurate placeholder names.

    Args:
        template_filepath (str): Path to the template PPTX file.
        output_filepath (str): Path to save the output layouts.json file.
    """
    print(f"Analyzing template: {template_filepath}")
    
    layout_data = {"layouts": []}

    # We need a fresh Presentation object for each layout analysis to avoid issues
    # with slide indices if we were to add/remove them from a single prs object.
    # Since we only read, this is fine.

    for i in range(len(Presentation(template_filepath).slide_layouts)):
        # Load a fresh presentation object for each layout to get its placeholders
        # This is to ensure we get the placeholder names as they appear on an *instantiated* slide
        try:
            prs_temp = Presentation(template_filepath)
        except Exception as e:
            print(f"Error: Could not load template '{template_filepath}' for layout analysis. Details: {e}")
            return

        if i >= len(prs_temp.slide_layouts):
            print(f"Error: Layout index {i} out of bounds.")
            continue
            
        slide_layout = prs_temp.slide_layouts[i]
        
        # Add a temporary slide from this layout to inspect its placeholders
        # This is more reliable as placeholder names can sometimes differ from the master
        try:
            temp_slide_for_analysis = prs_temp.slides.add_slide(slide_layout)
            placeholders = [shape.name for shape in temp_slide_for_analysis.placeholders]
            # No need to delete the slide as prs_temp is discarded after this iteration
        except Exception as e:
            print(f"Warning: Could not add temporary slide for layout '{slide_layout.name}'. Error: {e}. Falling back to layout placeholders.")
            # Fallback to the direct layout placeholders if adding a slide fails for some reason
            placeholders = [shape.name for shape in slide_layout.placeholders]

        layout_info = {
            "name": slide_layout.name,
            "placeholders": placeholders
        }
        layout_data["layouts"].append(layout_info)
        print(f"  Analyzed layout: '{slide_layout.name}', Found Placeholders: {placeholders}")


    # Ensure the output directory exists
    output_dir = os.path.dirname(output_filepath)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    try:
        with open(output_filepath, 'w', encoding='utf-8') as f:
            json.dump(layout_data, f, indent=2)
        print(f"Layouts map saved successfully to: {output_filepath}")
    except Exception as e:
        print(f"Error saving layouts map to '{output_filepath}': {e}")

def main():
    """Main entry point for the analyzer script."""
    parser = argparse.ArgumentParser(description="Analyze a PowerPoint template and create a layouts.json file.")
    parser.add_argument('-t', '--template', required=True, help="Path to the template PPTX file to analyze.")
    parser.add_argument('-o', '--output', required=True, help="Path for the output layouts.json file.")
    args = parser.parse_args()
    
    analyze_template(args.template, args.output)

if __name__ == '__main__':
    main()
