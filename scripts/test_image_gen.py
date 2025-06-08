import os
import sys
from dotenv import load_dotenv

# Add project root to sys.path to allow importing from pptx_generator
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))

# --- DEBUG PRINTS START ---
print(f"DEBUG: Calculated script_dir: {script_dir}")
print(f"DEBUG: Calculated project_root: {project_root}")
# --- DEBUG PRINTS END ---

# Ensure project_root is at the beginning of sys.path
# and remove script_dir if it's different and present, to avoid confusion.
if script_dir in sys.path and script_dir != project_root:
    sys.path.remove(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)
elif sys.path[0] != project_root: # If it is in sys.path but not at the start
    sys.path.remove(project_root)
    sys.path.insert(0, project_root)

# --- DEBUG PRINTS START ---
print(f"DEBUG: sys.path after targeted modification: {sys.path}")
# --- DEBUG PRINTS END ---

# --- MODIFIED IMPORT BLOCK START ---
processor_module = None
generate_and_save_image_func = None # Will hold the function if successfully imported

try:
    print("Attempting: import pptx_generator.processor as PGP_module_alias") # Using a more unique alias
    import pptx_generator.processor as PGP_module_alias
    processor_module = PGP_module_alias
    print("Successfully imported pptx_generator.processor as PGP_module_alias.")
    
    print("\n--- dir(PGP_module_alias) ---")
    # Ensure PGP_module_alias is not None before calling dir
    if PGP_module_alias:
        print(dir(PGP_module_alias))
    else:
        print("PGP_module_alias is None, cannot call dir(). This should not happen if import succeeded.")
    print("--- end dir(PGP_module_alias) ---")

    if hasattr(PGP_module_alias, 'generate_and_save_image'):
        print("\nAttempting to access PGP_module_alias.generate_and_save_image")
        generate_and_save_image_func = PGP_module_alias.generate_and_save_image
        print("Successfully accessed PGP_module_alias.generate_and_save_image.")
    else:
        print("\nError: 'generate_and_save_image' not found as an attribute of pptx_generator.processor.")
        print("This suggests the function might not be defined, or not defined at the top level of the module, or an earlier error in processor.py prevented its definition.")
        sys.exit(1)

except ImportError as e_mod:
    print(f"Error: Could not import the module 'pptx_generator.processor'. ImportError: {e_mod}")
    print("Ensure you are running this script from the project root or that the pptx_generator package is correctly installed/discoverable.")
    print("Check for typos in 'pptx_generator' or 'processor'.")
    print("Also, check 'pptx_generator/__init__.py' for any issues.")
    sys.exit(1)
except Exception as e_gen:
    print(f"An unexpected error occurred during the import process: {e_gen}")
    sys.exit(1)
# --- MODIFIED IMPORT BLOCK END ---

def main():
    """
    Tests the image generation setup by calling generate_and_save_image directly.
    """
    global generate_and_save_image_func # Ensure main uses the globally set function
    if generate_and_save_image_func is None:
        # This check is a bit redundant given the sys.exit(1) calls above, but good for safety.
        print("Critical Error: generate_and_save_image_func is not available for use in main(). This should have been caught by earlier checks. Exiting.")
        return

    load_dotenv()

    sd_forge_url = os.getenv("SD_FORGE_SERVER_URL")
    flux_model_name = os.getenv("FLUX_MODEL_NAME", "black-forest-labs/FLUX.1-schnell")

    if not sd_forge_url:
        print("Error: SD_FORGE_SERVER_URL is not set in your .env file.")
        print("Please set it to your Stable Diffusion Forge server URL (e.g., http://localhost:7860).")
        return

    test_prompt = "A vibrant red apple on a rustic wooden table, detailed, 4k"
    # Save in a dedicated test output directory within projects
    test_save_dir = os.path.join(project_root, "projects", "test_image_output")
    os.makedirs(test_save_dir, exist_ok=True)
    test_save_path = os.path.join(test_save_dir, "test_generated_image.jpg")

    print(f"\nAttempting to generate image with prompt: '{test_prompt}'")
    print(f"Model: {flux_model_name}")
    print(f"Server URL: {sd_forge_url}")
    print(f"Saving to: {test_save_path}")

    success = generate_and_save_image_func( # Use the globally resolved function
        prompt=test_prompt,
        save_path=test_save_path,
        model_name=flux_model_name,
        sd_forge_url=sd_forge_url
    )

    if success:
        print(f"\nSUCCESS: Image generation test passed!")
        print(f"Image saved to: {test_save_path}")
        print("Please verify the image visually.")
    else:
        print(f"\nFAILURE: Image generation test failed.")
        print("Check the console output above for error messages from the API or script.")
        print("Ensure your SD Forge server is running and accessible at the configured URL.")
        print("Verify your .env file has SD_FORGE_SERVER_URL set correctly.")

if __name__ == "__main__":
    main()
