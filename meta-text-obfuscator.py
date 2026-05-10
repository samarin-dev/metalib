#-----------------
# {meta}lib
# make your content unique
#-----------------
# Image Text Obfuscation Processor script
#-----------------
# Copyright (C) 2026 by Mykhailo Samarin
# All rights reserved worldwide
#-----------------
# Under General Public License
#-----------------
# Visit http://github.com/samarin-dev for more information
#-----------------

import configparser
import shutil
import textwrap
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from meta_utils import load_dictionary, generate_phrase, ANCHOR_MAP


def load_text_config():
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    return config


def get_system_font(size):
    # Attempt to load a system font; fall back to PIL default if none found
    candidates = [
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        # macOS
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial.ttf",
        # Windows
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            continue
    # PIL built-in bitmap fallback (no size control)
    return ImageFont.load_default()


def draw_text_on_image(img, text, cfg_section):
    cfg = cfg_section
    draw = ImageDraw.Draw(img, "RGBA")

    w, h = img.size

    # Read TEXT config values
    pad_x_ratio  = float(cfg.get('TEXT', 'padding_x_ratio',  fallback='0.05'))
    pad_y_ratio  = float(cfg.get('TEXT', 'padding_y_ratio',  fallback='0.05'))
    wrap_ratio   = float(cfg.get('TEXT', 'wrap_width_ratio', fallback='0.7'))
    opacity      = int(float(cfg.get('TEXT', 'opacity',      fallback='0.85')) * 255)
    stroke_width = int(cfg.get('TEXT', 'stroke_width',       fallback='2'))
    font_size    = int(cfg.get('TEXT', 'font_size',          fallback='32'))
    word_count   = int(cfg.get('TEXT', 'word_count',         fallback='5'))
    anchor_key   = cfg.get('TEXT', 'anchor',                 fallback='BL').upper()

    # Wrap text to fit wrap_ratio of image width
    avg_char_px = font_size * 0.55          # rough average character width
    max_chars   = max(1, int((w * wrap_ratio) / avg_char_px))
    wrapped     = textwrap.fill(text, width=max_chars)

    font = get_system_font(font_size)
    anchor_info = ANCHOR_MAP.get(anchor_key, ANCHOR_MAP["BL"])

    # Compute anchor point with padding applied inward from the chosen corner
    pad_x = int(w * pad_x_ratio)
    pad_y = int(h * pad_y_ratio)

    # x_rel/y_rel: 0 = left/top edge + padding, 1 = right/bottom edge - padding
    ax = int(w * anchor_info["x_rel"])
    ay = int(h * anchor_info["y_rel"])

    # Push inward from each border
    if anchor_info["x_rel"] == 0.0:
        ax += pad_x
    elif anchor_info["x_rel"] == 1.0:
        ax -= pad_x

    if anchor_info["y_rel"] == 0.0:
        ay += pad_y
    elif anchor_info["y_rel"] == 1.0:
        ay -= pad_y

    text_color   = (255, 255, 255, opacity)         # white fill
    stroke_color = (0,   0,   0,   opacity)         # black stroke

    draw.multiline_text(
        (ax, ay),
        wrapped,
        font=font,
        fill=text_color,
        stroke_width=stroke_width,
        stroke_fill=stroke_color,
        anchor=anchor_info["pil_anchor"],
        align="left",
    )
    return img


def apply_text_and_replace():
    cfg = load_text_config()

    # Path configuration
    in_dir  = cfg.get('GENERAL', 'input_dir',  fallback='Input')
    out_dir = cfg.get('GENERAL', 'output_dir', fallback='Output')

    # Text feature gate
    enabled = cfg.getboolean('TEXT', 'enable_text', fallback=False)
    if not enabled:
        print("[i] Text Obfuscator feature is disabled in config.ini")
        return

    word_count = int(cfg.get('TEXT', 'word_count', fallback='5'))

    # Load word dictionary
    words = load_dictionary(cfg.get('TEXT', 'dictionary_path', fallback='dictionary.txt'))

    input_path  = Path(in_dir)
    output_path = Path(out_dir)
    output_path.mkdir(exist_ok=True)

    valid_extensions = ('.jpg', '.jpeg', '.png', '.webp')
    processed_files  = []

    # STEP 1: Process images and apply text watermark
    print(f"[*] Starting text application...")
    for img_file in input_path.iterdir():
        if img_file.suffix.lower() in valid_extensions:
            try:
                with Image.open(img_file) as img:
                    # Convert to RGB to ensure JPEG compatibility
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")

                    # Generate random phrase from dictionary
                    phrase = generate_phrase(words, word_count)

                    # Apply text watermark
                    result = draw_text_on_image(img.copy(), phrase, cfg)

                    # Save to temporary output folder
                    save_path = output_path / f"{img_file.stem}.jpg"
                    result.save(save_path, "JPEG", quality=95)
                    processed_files.append(img_file)
                    print(f"[*] Text applied successfully: {img_file.name} | Phrase: \"{phrase}\"")
            except Exception as e:
                print(f"[-] Error processing {img_file.name}: {e}")

    if not processed_files:
        print("[-] No valid images found for processing.")
        return

    # STEP 2: Delete original source files
    print("\n[*] Deleting original files from Input directory...")
    for file in processed_files:
        try:
            file.unlink()
        except Exception as e:
            print(f"[-] Failed to delete {file.name}: {e}")

    # STEP 3: Move processed files back to Input
    print("[*] Moving processed files back to Input directory...")
    for out_file in output_path.iterdir():
        if out_file.suffix.lower() == '.jpg':
            try:
                # Move and overwrite if necessary
                shutil.move(str(out_file), str(input_path / out_file.name))
            except Exception as e:
                print(f"[-] Error moving {out_file.name}: {e}")

    print("\n[*] Operation completed. Original files replaced with text-watermarked versions.")


if __name__ == "__main__":
    apply_text_and_replace()
