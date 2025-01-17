import fontforge
import psMat  # Import the psMat module for transformations
import configparser
import os  # Import os module to handle file paths

# Make ConfigParser case-sensitive
class CaseSensitiveConfigParser(configparser.ConfigParser):
    def optionxform(self, optionstr):
        return optionstr

# Function to read the configuration file
def read_config(config_file='config.ini'):
    config = CaseSensitiveConfigParser()
    config.read(config_file)
    return config

# Function to create and configure the font
def create_font(config):
    # Extract font properties from config
    fontname = config['FONT_PROPERTIES']['fontname']
    fullname = config['FONT_PROPERTIES']['fullname']
    familyname = config['FONT_PROPERTIES']['familyname']

    # Create a new font and set properties
    font = fontforge.font()
    font.fontname = fontname
    font.fullname = fullname
    font.familyname = familyname
    return font

# Function to import image and autotrace glyph using character values
def import_and_trace_glyph(font, char, image_path):
    unicode_int = ord(char)  # Get the Unicode code point for the character
    glyph = font.createChar(unicode_int)  # Create glyph using the character's Unicode value
    
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

# Function to scale the glyph based on a scaling factor
def scale_glyph(glyph, scaling_factor):
    # Scale the glyph using the scaling factor from the config file
    glyph.transform(psMat.scale(scaling_factor))
    print(f"Glyph scaled by factor: {scaling_factor}")

def center_and_align_glyph(glyph, alignment='bottom', vertical_offset=0):
    # Get the bounding box of the glyph
    min_x, min_y, max_x, max_y = glyph.boundingBox()

    # Calculate the width of the glyph
    glyph_width = max_x - min_x

    # Calculate the total width allocated for the glyph
    advance_width = glyph.width

    # Calculate the offset to center the glyph horizontally
    center_x_offset = (advance_width - glyph_width) // 2 - min_x

    # Determine vertical alignment and apply the offset
    if alignment == 'bottom':
        # Align the glyph to the bottom by translating the y-coordinate
        y_offset = -min_y + vertical_offset
    elif alignment == 'top':
        # Align the glyph to the top by translating the y-coordinate
        total_height = glyph.font.ascent + glyph.font.descent
        y_offset = (glyph.font.ascent - max_y) + vertical_offset
    else:
        raise ValueError("Invalid alignment option. Use 'top' or 'bottom'.")

    # Apply the transformation to center the glyph horizontally and align it vertically
    glyph.transform(psMat.translate(center_x_offset, y_offset))

    # Recalculate the left and right side bearings to ensure the glyph is centered
    left_side_bearing = (advance_width - glyph_width) // 2
    right_side_bearing = advance_width - glyph_width - left_side_bearing

    glyph.left_side_bearing = int(left_side_bearing)
    glyph.right_side_bearing = int(right_side_bearing)

    print(f"Glyph centered horizontally and aligned to the {alignment} with a vertical offset of {vertical_offset}.")



# Function to save font files
def save_font_files(font, sfd_path, ttf_path):
    font.save(sfd_path)
    font.generate(ttf_path)
    print(f"SFD file saved to {sfd_path}")
    print(f"TTF file generated at {ttf_path}")

# Main function to run the script
def main():
    config = read_config()
    common_image_path = config['PATHS']['common_image_path']
    sfd_path = config['PATHS']['sfd_path']
    ttf_path = config['PATHS']['ttf_path']
    scaling_factor = float(config['FONT_PROPERTIES']['scaling_factor'])
    alignment = config['FONT_PROPERTIES'].get('alignment', 'bottom')  # Default to 'bottom'
    vertical_offset = int(config['FONT_PROPERTIES'].get('vertical_offset', 0))  # Default to 0

    print("FontForge version:", fontforge.version())

    font = create_font(config)

    # Iterate over each character in the GLYPHS section
    for char, image_name in config['GLYPHS'].items():
        # Construct the full image path
        image_path = os.path.join(common_image_path, image_name)
        glyph = import_and_trace_glyph(font, char, image_path)
        if glyph:  # Only proceed if the glyph was successfully created
            scale_glyph(glyph, scaling_factor)
            center_and_align_glyph(glyph, alignment, vertical_offset)

            print(f"Processed character: {char}")

    save_font_files(font, sfd_path, ttf_path)
    font.close()

if __name__ == "__main__":
    main()
