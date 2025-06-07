import argparse
import os
import json
from pptx_generator.generator import generate_presentation
from pptx_generator.analyzer import analyze_template
from pptx_generator.processor import process_content

BASE_PROJECTS_DIR = "projects"
BASE_TEMPLATES_DIR = "templates"

def main():
    parser = argparse.ArgumentParser(
        description="PowerPoint Generator CLI - Convert Markdown to PPTX.",
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands', required=True)

    # --- 'analyze' command ---
    analyze_parser = subparsers.add_parser('analyze', 
                                           help='Analyze a template and store its layout for a project. Creates projects/<project_name>/output/layouts.json.')
    analyze_parser.add_argument("project_name", 
                                help="Name of the project (e.g., 'robotics'). Will be created under 'projects/' if it doesn't exist.")
    analyze_parser.add_argument("template_specifier", 
                                help="Name of the template (e.g., 'default_template.pptx' to be found in 'templates/' dir) or full path to a .pptx template file.")

    # --- 'process' command ---
    process_parser = subparsers.add_parser('process', 
                                           help="Process markdown (projects/<project_name>/content.md) into a presentation plan (projects/<project_name>/output/presentation.json).")
    process_parser.add_argument("project_name", 
                                help="Name of the project (e.g., 'robotics').")

    # --- 'generate' command ---
    generate_parser = subparsers.add_parser('generate', 
                                            help="Generate the final PPTX file (projects/<project_name>/output/<project_name>.pptx) using the project's presentation plan and the stored template path from layouts.json.")
    generate_parser.add_argument("project_name", 
                                 help="Name of the project (e.g., 'robotics').")

    args = parser.parse_args()

    project_name = args.project_name
    project_dir = os.path.join(BASE_PROJECTS_DIR, project_name)
    output_dir = os.path.join(project_dir, 'output')
    
    # Ensure base project and output directories exist for all commands that use them
    if hasattr(args, 'project_name'): # All new commands have project_name
        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)


    # --- Command Handling ---
    if args.command == 'analyze':
        template_spec = args.template_specifier
        template_filepath = ""

        # Determine if template_specifier is a path or a name
        if os.path.isfile(template_spec):
            template_filepath = template_spec
        else:
            # Assume it's a name, look in BASE_TEMPLATES_DIR
            potential_path = os.path.join(BASE_TEMPLATES_DIR, template_spec)
            if os.path.isfile(potential_path):
                template_filepath = potential_path
            else:
                print(f"Error: Template '{template_spec}' not found as a direct path or in '{BASE_TEMPLATES_DIR}/'.")
                return
        
        if not os.path.exists(template_filepath):
             print(f"Error: Template file not found at '{template_filepath}'.")
             return

        layouts_output_path = os.path.join(output_dir, 'layouts.json')
        
        print(f"Analyzing '{template_filepath}' for project '{project_name}' -> '{layouts_output_path}'")
        analyze_template(template_filepath, layouts_output_path)

    elif args.command == 'process':
        markdown_path = os.path.join(project_dir, 'content.md')
        layouts_path = os.path.join(output_dir, 'layouts.json')
        presentation_output_path = os.path.join(output_dir, 'presentation.json')

        if not os.path.exists(markdown_path):
            print(f"Error: Markdown file not found at '{markdown_path}'. Please create it for project '{project_name}'.")
            return
        if not os.path.exists(layouts_path):
            print(f"Error: Layouts file not found at '{layouts_path}'. Please run 'analyze' for project '{project_name}' first.")
            return
        
        print(f"Processing '{markdown_path}' for project '{project_name}' -> '{presentation_output_path}'")
        process_content(markdown_path, layouts_path, presentation_output_path)

    elif args.command == 'generate':
        presentation_plan_path = os.path.join(output_dir, 'presentation.json')
        layouts_path = os.path.join(output_dir, 'layouts.json') # Needed to get the template path
        final_pptx_output_path = os.path.join(output_dir, f"{project_name}.pptx")

        if not os.path.exists(presentation_plan_path):
            print(f"Error: Presentation plan not found at '{presentation_plan_path}'. Please run 'process' for project '{project_name}' first.")
            return
        if not os.path.exists(layouts_path):
            print(f"Error: Layouts file not found at '{layouts_path}'. Cannot determine source template. Please run 'analyze' for project '{project_name}'.")
            return

        try:
            with open(layouts_path, 'r', encoding='utf-8') as f:
                layout_data = json.load(f)
            source_template_filepath = layout_data.get("source_template_path")
            if not source_template_filepath or not os.path.exists(source_template_filepath):
                print(f"Error: Source template path '{source_template_filepath}' from layouts.json is invalid or file not found.")
                print(f"Please re-run 'analyze' for project '{project_name}' with a valid template.")
                return
        except Exception as e:
            print(f"Error reading source template path from '{layouts_path}': {e}")
            return
        
        print(f"Generating '{presentation_plan_path}' for project '{project_name}' using template '{source_template_filepath}' -> '{final_pptx_output_path}'")
        generate_presentation(
            data_filepath=presentation_plan_path, 
            template_filepath=source_template_filepath, 
            output_filepath=final_pptx_output_path
        )

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
