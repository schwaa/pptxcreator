import json
import os
import argparse
from pptx import Presentation

def analyze_template(template_filepath: str, output_filepath: str = None): # output_filepath is now optional
    """
    Analyzes a PowerPoint template.
    If output_filepath is provided, saves a JSON file listing each layout
    and its placeholder names.
    Always returns a dictionary of the layout data.
    This version instantiates each layout to get the most accurate placeholder names.

    Args:
        template_filepath (str): Path to the template PPTX file.
        output_filepath (str, optional): Path to save the output layouts.json file. Defaults to None.

    Returns:
        dict: A dictionary containing the layout data.
              Example: {"layouts": [{"name": "Layout Name", "placeholders": ["PH1", "PH2"]}]}
                       or {"layouts": [], "error": "Error message"} if loading fails.
    """
    print(f"Analyzing template: {template_filepath}")
    
    # Get the absolute path of the template to store it
    try:
        abs_template_filepath = os.path.abspath(template_filepath)
    except Exception as e:
        # If abspath fails for some reason (e.g. on a non-existent file before Presentation() checks)
        print(f"Warning: Could not determine absolute path for '{template_filepath}'. Storing as provided. Error: {e}")
        abs_template_filepath = template_filepath # Store as is

    layout_data = {
        "source_template_path": abs_template_filepath, # Store the path
        "layouts": []
    }

    try:
        # Load the presentation once to get the number of layouts
        # This also serves as an initial check if the template can be loaded
        initial_prs = Presentation(template_filepath)
        num_layouts = len(initial_prs.slide_layouts)
    except Exception as e:
        error_message = f"Error: Could not load template '{template_filepath}' for initial analysis. Details: {e}"
        print(error_message)
        return {"layouts": [], "error": error_message} # Return error structure

    # We need a fresh Presentation object for each layout analysis to avoid issues
    # with slide indices if we were to add/remove them from a single prs object.
    # Since we only read, this is fine.

    for i in range(num_layouts): # Use num_layouts from the initial load
        # Load a fresh presentation object for each layout to get its placeholders
        # This is to ensure we get the placeholder names as they appear on an *instantiated* slide
        try:
            prs_temp = Presentation(template_filepath) # Reload for each layout to be safe
        except Exception as e:
            # This specific error might be redundant if initial load succeeded, but good for safety
            error_detail = f"Error: Could not re-load template '{template_filepath}' for layout {i}. Details: {e}"
            print(error_detail)
            # Add error info for this specific layout and continue
            layout_data["layouts"].append({
                "name": f"Layout index {i} (Load Error)",
                "placeholders": [],
                "error": error_detail
            })
            continue

        if i >= len(prs_temp.slide_layouts): # Should ideally not be hit if num_layouts is correct
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


    if output_filepath:
        # Ensure the output directory exists
        output_dir = os.path.dirname(output_filepath)
        if output_dir: # Check if output_dir is not an empty string (e.g. if output_filepath is just a filename)
            os.makedirs(output_dir, exist_ok=True)

        try:
            with open(output_filepath, 'w', encoding='utf-8') as f:
                json.dump(layout_data, f, indent=2)
            print(f"Success! Layouts map saved to: {output_filepath}")
        except Exception as e:
            save_error_message = f"Error saving layouts map to '{output_filepath}': {e}"
            print(save_error_message)
            # Add a general error key if not present, or a specific one for saving
            if "analysis_errors" not in layout_data: # Using a more general error key
                layout_data["analysis_errors"] = []
            layout_data["analysis_errors"].append(save_error_message)
            
    return layout_data

def main():
    """Main entry point for the analyzer script."""
    parser = argparse.ArgumentParser(description="Analyze a PowerPoint template and create a layouts.json file.")
    parser.add_argument('-t', '--template', required=True, help="Path to the template PPTX file to analyze.")
    parser.add_argument('-o', '--output', required=True, help="Path for the output layouts.json file.")
    args = parser.parse_args()
    
    analyze_template(args.template, args.output)

if __name__ == '__main__':
    main()
