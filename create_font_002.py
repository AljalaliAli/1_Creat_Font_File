"""
create_font.py

This script is designed to run on both Windows and Linux platforms, either directly using Python
or as a standalone executable. It checks if the required modules `fontforge` and `psMat` are available.
If not, it attempts to run the script using `ffpython.exe` on Windows or `fontforge` on Linux.

Usage:
    On Windows:
        pyinstaller --onefile create_font.py
        ./create_font.exe
        python create_font.py

    On Linux:
        python3 create_font.py
"""

import os
import sys
import subprocess
import tempfile
import platform

# The main script code that we want to run in ffpython or fontforge environments
SCRIPT_CONTENT = """
import os
import fontforge
import psMat
import configparser

class CaseSensitiveConfigParser(configparser.ConfigParser):
    def optionxform(self, optionstr):
        return optionstr

def read_config(config_file='config.ini'):
    config = CaseSensitiveConfigParser()
    config.read(config_file)
    return config

def create_font(config):
    fontname = config['FONT_PROPERTIES']['fontname']
    fullname = config['FONT_PROPERTIES']['fullname']
    familyname = config['FONT_PROPERTIES']['familyname']
    font = fontforge.font()
    font.fontname = fontname
    font.fullname = fullname
    font.familyname = familyname
    return font

def import_and_trace_glyph(font, char, image_path):
    unicode_int = ord(char)
    glyph = font.createChar(unicode_int)
    if not os.path.exists(image_path):
        print(f"Image for character '{char}' not found. Skipping this glyph.")
        return None
    glyph.importOutlines(image_path)
    glyph.autoTrace()
    if glyph.foreground.isEmpty():
        print(f"The image for character '{char}' was imported, but the autotrace did not create contours.")
    else:
        print(f"The image for character '{char}' was imported and autotraced successfully.")
    return glyph

def scale_glyph(glyph, scaling_factor):
    glyph.transform(psMat.scale(scaling_factor))
    print(f"Glyph scaled by factor: {scaling_factor}")

def center_and_align_glyph(glyph, alignment='bottom', vertical_offset=0):
    min_x, min_y, max_x, max_y = glyph.boundingBox()
    glyph_width = max_x - min_x
    advance_width = glyph.width
    center_x_offset = (advance_width - glyph_width) // 2 - min_x
    if alignment == 'bottom':
        y_offset = -min_y + vertical_offset
    elif alignment == 'top':
        total_height = glyph.font.ascent + glyph.font.descent
        y_offset = (glyph.font.ascent - max_y) + vertical_offset
    else:
        raise ValueError("Invalid alignment option. Use 'top' or 'bottom'.")
    glyph.transform(psMat.translate(center_x_offset, y_offset))
    left_side_bearing = (advance_width - glyph_width) // 2
    right_side_bearing = advance_width - glyph_width - left_side_bearing
    glyph.left_side_bearing = int(left_side_bearing)
    glyph.right_side_bearing = int(right_side_bearing)
    print(f"Glyph centered horizontally and aligned to the {alignment} with a vertical offset of {vertical_offset}.")

def save_font_files(font, sfd_path, ttf_path):
    font.save(sfd_path)
    font.generate(ttf_path)
    print(f"SFD file saved to {sfd_path}")
    print(f"TTF file generated at {ttf_path}")

def main():
    config = read_config()
    common_image_path = config['PATHS']['common_image_path']
    sfd_path = config['PATHS']['sfd_path']
    ttf_path = config['PATHS']['ttf_path']
    scaling_factor = float(config['FONT_PROPERTIES']['scaling_factor'])
    alignment = config['FONT_PROPERTIES'].get('alignment', 'bottom')
    vertical_offset = int(config['FONT_PROPERTIES'].get('vertical_offset', 0))
    print("FontForge version:", fontforge.version())
    font = create_font(config)
    for char, image_name in config['GLYPHS'].items():
        image_path = os.path.join(common_image_path, image_name)
        glyph = import_and_trace_glyph(font, char, image_path)
        if glyph:
            scale_glyph(glyph, scaling_factor)
            center_and_align_glyph(glyph, alignment, vertical_offset)
            print(f"Processed character: {char}")
    save_font_files(font, sfd_path, ttf_path)
    font.close()

if __name__ == "__main__":
    main()
"""

def run_main_script():
    """
    Writes the embedded script content to a temporary file and runs it using ffpython.exe on Windows
    or fontforge on Linux. After execution, the temporary file is removed.
    """
    # Write the SCRIPT_CONTENT to a temporary file and run it using the appropriate interpreter
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_script:
        temp_script.write(SCRIPT_CONTENT.encode('utf-8'))
        temp_script_path = temp_script.name

    if platform.system() == 'Windows':
        fontforge_path = r"FontForgeBuilds\bin\ffpython.exe"
        if os.path.exists(fontforge_path):
            subprocess.call([fontforge_path, temp_script_path] + sys.argv[1:])
        else:
            print(f"ffpython.exe not found at {fontforge_path}. Please check the path.")
    elif platform.system() == 'Linux':
        subprocess.call(['fontforge', '-script', temp_script_path] + sys.argv[1:])
    else:
        print("Unsupported operating system.")
        sys.exit(1)

    # Clean up the temporary script file after execution
    os.remove(temp_script_path)
    sys.exit()

def try_import_fontforge():
    """
    Try to import the required fontforge and psMat modules. If unavailable, trigger the
    external execution using ffpython.exe or fontforge.
    """
    try:
        import fontforge
        import psMat
        return True
    except ImportError:
        return False

if __name__ == "__main__":
    is_frozen = getattr(sys, 'frozen', False)
    if is_frozen:
        run_main_script()
    else:
        if try_import_fontforge():
            # If the import succeeds, run the main logic directly
            exec(SCRIPT_CONTENT)
        else:
            # If the import fails, try running in the FontForge environment
            run_main_script()
