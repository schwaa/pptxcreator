import os
import zipfile

template_path = 'templates/default_template.pptx'

print(f"--- Checking file: {template_path} ---")

# Get absolute path for clarity
abs_template_path = os.path.abspath(template_path)
print(f"Attempting to access: {abs_template_path}")

# Check if file exists
if not os.path.exists(template_path):
    print(f"ERROR: File does NOT exist at: {abs_template_path}")
    print("This indicates a path or filename mismatch.")
else:
    print(f"SUCCESS: File exists at: {abs_template_path}")
    try:
        file_size = os.path.getsize(template_path)
        print(f"File size: {file_size} bytes")
        if file_size == 0:
            print("WARNING: File size is 0 bytes. This is an empty file and not a valid PPTX.")
    except Exception as e:
        print(f"WARNING: Could not get file size: {e}")

    # Try to open it as a ZIP file (which a .pptx is)
    try:
        with zipfile.ZipFile(template_path, 'r') as zf:
            print(f"SUCCESS: File can be opened as a ZIP archive.")
            if zf.namelist():
                print(f"Contents (first 5): {zf.namelist()[:5]}...")
                # Try to read a common XML part to ensure it's not just an empty zip
                try:
                    # This is a key internal file within a PPTX structure
                    zf.read('ppt/presentation.xml')
                    print("SUCCESS: Found 'ppt/presentation.xml' inside the ZIP. This is a good sign.")
                except KeyError:
                    print("WARNING: 'ppt/presentation.xml' not found inside ZIP. This might indicate an invalid PPTX structure for python-pptx, or a very unusual PPTX.")
                except Exception as e:
                    print(f"ERROR: Problem reading 'ppt/presentation.xml' from ZIP: {e}")
            else:
                print("WARNING: ZIP archive is empty. This is not a valid PPTX.")

    except zipfile.BadZipFile:
        print("CRITICAL ERROR: File is NOT a valid ZIP archive (`zipfile.BadZipFile`).")
        print("This means the .pptx file itself is corrupted, incomplete, or not a proper ZIP structure.")
        print("Solution: Re-download or re-save the PPTX file very carefully.")
    except Exception as e:
        print(f"CRITICAL ERROR: Could not open file as ZIP. Other unexpected error: {e}")

print("--- Check complete ---")
