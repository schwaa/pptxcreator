import json
from pprint import pprint

def analyze_template_map(map_filepath):
    """Analyze and display the contents of a template map file."""
    try:
        with open(map_filepath, 'r', encoding='utf-8') as f:
            template_map = json.load(f)
    except FileNotFoundError:
        print(f"Error: Map file '{map_filepath}' not found.")
        return
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in map file '{map_filepath}'.")
        return

    # Count layouts by semantic type
    semantic_types = {}
    for layout in template_map["layouts"]:
        semantic_type = layout["semantic_type"]
        if semantic_type not in semantic_types:
            semantic_types[semantic_type] = []
        semantic_types[semantic_type].append(layout["name"])

    # Print summary
    print("\n=== Template Map Analysis ===\n")
    print("Template File:", template_map["template_filepath"])
    print("\nLayouts by Semantic Type:")
    print("-" * 40)
    
    for semantic_type, layouts in sorted(semantic_types.items()):
        print(f"\n{semantic_type}:")
        for layout in layouts:
            print(f"  - {layout}")

    # Analyze layout features
    print("\nLayout Details:")
    print("-" * 40)
    for layout in template_map["layouts"]:
        print(f"\n{layout['name']} ({layout['semantic_type']}):")
        features = layout["features"]
        placeholders = layout["placeholders"]
        
        print("  Features:")
        for key, value in features.items():
            if value not in [None, False, 0]:  # Only show non-empty/non-zero features
                print(f"    - {key}: {value}")
        
        print("  Placeholders:")
        for name, details in placeholders.items():
            print(f"    - {name} ({details['type']})")

    # List expected content types from data
    expected_types = [
        "presentation_title",
        "bullet_points_summary",
        "image_and_description",
        "description_and_image",
        "product_showcase",
        "chart_data_slide"
    ]

    print("\nContent Type Coverage:")
    print("-" * 40)
    print("\nExpected content types vs. available semantic types:")
    for content_type in expected_types:
        status = "✅" if content_type in semantic_types else "❌"
        layouts = semantic_types.get(content_type, [])
        if layouts:
            print(f"{status} {content_type}: {', '.join(layouts)}")
        else:
            print(f"{status} {content_type}: No matching layout")

    # Suggestions for missing types
    print("\nSuggestions for Missing Types:")
    print("-" * 40)
    for content_type in expected_types:
        if content_type not in semantic_types:
            print(f"\n{content_type}:")
            if content_type == "presentation_title":
                print("  Look for layouts with both title and subtitle placeholders")
            elif content_type == "bullet_points_summary":
                print("  Look for layouts with title and body text placeholders")
            elif content_type in ["image_and_description", "description_and_image"]:
                print("  Look for layouts with both picture and text placeholders")
            elif content_type == "product_showcase":
                print("  Look for layouts with a large picture placeholder")
            elif content_type == "chart_data_slide":
                print("  Look for layouts with chart placeholders")

if __name__ == "__main__":
    analyze_template_map("template_map.json")
