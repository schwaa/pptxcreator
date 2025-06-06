import argparse
import os
from pptx_generator.generator import generate_presentation
from pptx_generator.analyzer import analyze_template
from pptx_generator.processor import process_content

def main():
    parser = argparse.ArgumentParser(
        description="PowerPoint Generator CLI - Convert Markdown to PPTX.",
    )

    # A new top-level argument to define the project context
    parser.add_argument(
        '--project', 
        help="Path to a project directory (e.g., 'projects/my_talk'). Simplifies other path arguments."
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands', required=True)

    # --- 'analyze' command ---
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a template file.')
    analyze_parser.add_argument("-t", "--template", required=True, help="Path to the template PPTX file.")
    analyze_parser.add_argument("-o", "--output", help="Output path for layouts.json. Defaults to [PROJECT]/output/layouts.json")

    # --- 'process' command ---
    process_parser = subparsers.add_parser('process', help='Process markdown into a presentation plan.')
    process_parser.add_argument("-m", "--markdown", help="Path to markdown file. Defaults to [PROJECT]/content.md")
    process_parser.add_argument("-l", "--layouts", help="Path to layouts.json. Defaults to [PROJECT]/output/layouts.json")
    process_parser.add_argument("-o", "--output", help="Output path for presentation.json. Defaults to [PROJECT]/output/presentation.json")
    process_parser.add_argument("--api-key", help="(Deprecated) OpenAI API key. Not required for OpenRouter.")

    # --- 'generate' command ---
    generate_parser = subparsers.add_parser('generate', help='Generate the final PPTX file.')
    generate_parser.add_argument("-p", "--presentation", help="Path to presentation.json. Defaults to [PROJECT]/output/presentation.json")
    generate_parser.add_argument("-t", "--template", required=True, help="Path to the template PPTX file.")
    generate_parser.add_argument("-o", "--output", help="Path for the final output PPTX file.")

    args = parser.parse_args()

    # --- Path Management ---
    # Use the --project argument to set smart defaults
    project_dir = args.project
    output_dir = os.path.join(project_dir, 'output') if project_dir else None

    def get_path(arg_path, default_dir, default_filename):
        if arg_path:
            return arg_path
        if default_dir:
            os.makedirs(default_dir, exist_ok=True)
            return os.path.join(default_dir, default_filename)
        # If no project is set and the argument is not provided, this will fail.
        # We add checks for this below.
        return None 

    # --- Command Handling ---
    if args.command == 'analyze':
        # Analyze doesn't depend on a project, so its output must be explicit if no project is set.
        output_path = get_path(args.output, output_dir, 'layouts.json')
        if not output_path:
            print("Error: --output path is required when not using the --project flag.")
            return
        
        print(f"Analyzing '{args.template}' -> '{output_path}'")
        analyze_template(args.template, output_path)

    elif args.command == 'process':
        markdown_path = get_path(args.markdown, project_dir, 'content.md')
        layouts_path = get_path(args.layouts, output_dir, 'layouts.json')
        output_path = get_path(args.output, output_dir, 'presentation.json')

        if not all([markdown_path, layouts_path, output_path]):
            print("Error: --markdown, --layouts, and --output are required when not using the --project flag.")
            return
        
        # Remove the strict API key check; processor.py will handle provider logic
        # api_key = args.api_key or os.getenv("OPENAI_API_KEY")
        # if not api_key:
        #     print("Error: API Key is required via --api-key or OPENAI_API_KEY.")
        #     return

        print(f"Processing '{markdown_path}' -> '{output_path}'")
        process_content(markdown_path, layouts_path, output_path, api_key_unused=None)

    elif args.command == 'generate':
        # Note: We need to know the *final* presentation name for the output default.
        # This requires knowing the project name.
        final_pptx_name = os.path.basename(project_dir) + ".pptx" if project_dir else "output.pptx"

        presentation_path = get_path(args.presentation, output_dir, 'presentation.json')
        output_path = get_path(args.output, output_dir, final_pptx_name)

        if not all([presentation_path, output_path, args.template]):
            print("Error: --presentation, --output, and --template are required when not using the --project flag.")
            return
        
        print(f"Generating '{presentation_path}' -> '{output_path}'")
        # Ensure argument order matches the function definition
        generate_presentation(
            data_filepath=presentation_path, 
            template_filepath=args.template, 
            output_filepath=output_path
        )

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
