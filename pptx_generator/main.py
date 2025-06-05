import argparse
import os
from pptx_generator.generator import generate_presentation
from PIL import Image # For dummy image generation

def main():
    parser = argparse.ArgumentParser(
        description="Generate a PowerPoint presentation from data and a template.",
        epilog="Example: python -m pptx_generator.main --data data/example_report_data.json --template templates/default_template.pptx --output output/my_generated_report.pptx"
    )

    parser.add_argument(
        "-d", "--data",
        required=True,
        help="Path to the JSON file containing presentation data."
    )
    parser.add_argument(
        "-t", "--template",
        required=True,
        help="Path to the template PPTX file."
    )
    parser.add_argument(
        "-o", "--output",
        default="output/generated_presentation.pptx", # Default output path
        help="Path for the output PPTX file. Defaults to 'output/generated_presentation.pptx'."
    )

    args = parser.parse_args()

    # Ensure output directory exists
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
            print(f"Image slides will be empty unless you provide your own images in the '{dummy_image_dir}' directory.")
        except Exception as e:
            print(f"Error creating dummy image: {e}")

    generate_presentation(args.data, args.template, args.output)

if __name__ == "__main__":
    main()
