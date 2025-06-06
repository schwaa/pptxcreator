import argparse
import os
from pptx_generator.generator import generate_presentation
from pptx_generator.analyzer import analyze_template_and_create_map
from pptx_generator.processor import process_content

def main():
    parser = argparse.ArgumentParser(
        description="PowerPoint Generator CLI - Convert Markdown to PPTX.",
        epilog="Example: pptx-gen analyze template.pptx && pptx-gen process content.md && pptx-gen generate"
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(dest='command', help='Available commands', required=True)

    # --- 'analyze' command parser ---
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a template and create a layout mapping file.')
    analyze_parser.add_argument(
        "-t", "--template",
        required=True,
        help="Path to the template PPTX file to analyze."
    )
    analyze_parser.add_argument(
        "-o", "--output",
        help="Path for the output layouts.json file. Defaults to PROJECT/output/layouts.json",
    )

    # --- 'process' command parser ---
    process_parser = subparsers.add_parser('process', help='Process markdown content into presentation structure.')
    process_parser.add_argument(
        "-m", "--markdown",
        required=True,
        help="Path to the input markdown file."
    )
    process_parser.add_argument(
        "-l", "--layouts",
        help="Path to the layouts.json file. Defaults to PROJECT/output/layouts.json"
    )
    process_parser.add_argument(
        "-o", "--output",
        help="Path for the output presentation.json file. Defaults to PROJECT/output/presentation.json"
    )
    process_parser.add_argument(
        "--api-key",
        help="OpenAI API key. Can also be set via OPENAI_API_KEY environment variable."
    )

    # --- 'generate' command parser ---
    generate_parser = subparsers.add_parser('generate', help='Generate the final PowerPoint presentation.')
    generate_parser.add_argument(
        "-p", "--presentation",
        help="Path to the presentation.json file. Defaults to PROJECT/output/presentation.json"
    )
    generate_parser.add_argument(
        "-t", "--template",
        required=True,
        help="Path to the template PPTX file."
    )
    generate_parser.add_argument(
        "-o", "--output",
        help="Path for the output PPTX file. Defaults to PROJECT/output/final_deck.pptx"
    )

    args = parser.parse_args()

    # Determine project directory from markdown path or presentation path
    if args.command == 'process' and args.markdown:
        project_dir = os.path.dirname(os.path.dirname(args.markdown))
    elif args.command == 'generate' and args.presentation:
        project_dir = os.path.dirname(os.path.dirname(args.presentation))
    else:
        project_dir = os.path.join('projects', 'example_presentation')

    # Set default output paths based on project structure
    output_dir = os.path.join(project_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)

    # Handle commands
    if args.command == 'analyze':
        output_path = args.output or os.path.join(output_dir, 'layouts.json')
        print(f"Analyzing template '{args.template}' to create layout map '{output_path}'...")
        analyze_template_and_create_map(args.template, output_path)

    elif args.command == 'process':
        layouts_path = args.layouts or os.path.join(output_dir, 'layouts.json')
        output_path = args.output or os.path.join(output_dir, 'presentation.json')
        
        if not os.path.exists(layouts_path):
            print(f"Error: layouts file not found at '{layouts_path}'")
            print("Have you run 'analyze' first to generate the layouts file?")
            return

        api_key = args.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Error: OpenAI API key is required. Provide with --api-key or set OPENAI_API_KEY")
            return

        print(f"Processing markdown '{args.markdown}' using layouts from '{layouts_path}'...")
        process_content(args.markdown, layouts_path, output_path, api_key)

    elif args.command == 'generate':
        presentation_path = args.presentation or os.path.join(output_dir, 'presentation.json')
        output_path = args.output or os.path.join(output_dir, 'final_deck.pptx')

        if not os.path.exists(presentation_path):
            print(f"Error: presentation file not found at '{presentation_path}'")
            print("Have you run 'process' first to generate the presentation file?")
            return

        print(f"Generating presentation using content from '{presentation_path}'...")
        generate_presentation(args.template, presentation_path, output_path)

    else:
        parser.print_help()

if __name__ == "__main__":
    main()
