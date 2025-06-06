import argparse
import os
from pptx_generator.generator import generate_presentation
from pptx_generator.template_analyzer import analyze_template_and_create_map
from PIL import Image # For dummy image generation

def main():
    parser = argparse.ArgumentParser(
        description="PowerPoint Generator and Template Analyzer CLI.",
        epilog="Use 'pptx-gen generate ...' or 'pptx-gen analyze ...'"
    )

    # Create subparsers for 'generate' and 'analyze' commands
    subparsers = parser.add_subparsers(dest='command', help='Available commands', required=True)

    # --- 'generate' command parser ---
    generate_parser = subparsers.add_parser('generate', help='Generate a PowerPoint presentation.')
    generate_parser.add_argument(
        "-d", "--data",
        required=True,
        help="Path to the JSON file containing presentation data."
    )
    generate_parser.add_argument(
        "-t", "--template",
        required=True,
        help="Path to the template PPTX file."
    )
    generate_parser.add_argument(
        "-m", "--map",
        required=True,
        help="Path to the generated template map JSON file."
    )
    generate_parser.add_argument(
        "-o", "--output",
        default="output/generated_presentation.pptx",
        help="Path for the output PPTX file. Defaults to 'output/generated_presentation.pptx'."
    )

    # --- 'analyze' command parser ---
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a template and create a mapping file.')
    analyze_parser.add_argument(
        "-t", "--template",
        required=True,
        help="Path to the template PPTX file to analyze."
    )
    analyze_parser.add_argument(
        "-o", "--output",
        default="template_map.json",
        help="Path for the output template map JSON file. Defaults to 'template_map.json'."
    )

    args = parser.parse_args()

    # Handle the 'analyze' command
    if args.command == 'analyze':
        print(f"Analyzing template '{args.template}' to create map file '{args.output}'...")
        analyze_template_and_create_map(args.template, args.output)
        return # Exit after analysis

    # Handle the 'generate' command
    elif args.command == 'generate':
        # Ensure output directory exists for generation
        output_dir = os.path.dirname(args.output)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")

        # Generate a dummy image if it doesn't exist for demonstration purposes
        dummy_image_path = "images/dummy_image.png"
        dummy_image_dir = os.path.dirname(dummy_image_path)
        if dummy_image_dir and not os.path.exists(dummy_image_dir):
            os.makedirs(dummy_image_dir)

        if not os.path.exists(dummy_image_path):
            try:
                img = Image.new('RGB', (600, 400), color = 'blue')
                img.save(dummy_image_path)
                print(f"Created a dummy '{dummy_image_path}' for demonstration.")
            except ImportError:
                print("Pillow library not found. Cannot create dummy image. Please install with: pip install Pillow")
            except Exception as e:
                print(f"Error creating dummy image: {e}")

        print(f"Generating presentation using data '{args.data}', template '{args.template}', map '{args.map}' to output '{args.output}'...")
        generate_presentation(args.data, args.template, args.output, args.map)
    else:
        # This case should not be reached if subparsers are 'required'
        parser.print_help()

if __name__ == "__main__":
    main()
