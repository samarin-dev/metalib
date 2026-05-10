#-----------------
# {meta}lib
# make your content unique
#-----------------
# Video Text Obfuscation Processor script
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
import subprocess
import re
import textwrap
from pathlib import Path

from meta_utils import (
    get_ffmpeg_exe, get_ffprobe_exe, probe_video,
    get_best_encoder, get_encoder_flags_for_filter,
    load_dictionary, generate_phrase, ANCHOR_MAP,
)


def load_text_config():
    # inline_comment_prefixes allows ; and # comments on the same line as values
    config = configparser.ConfigParser(inline_comment_prefixes=(';', '#'))
    config.read('config.ini', encoding='utf-8')
    return config


def find_system_font():
    # Return path to a usable system font for ffmpeg drawtext
    candidates = [
        # Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        # macOS
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
        # Windows
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/segoeui.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            return p
    raise FileNotFoundError("[-] No suitable system font found. Set font_path in config.ini [TEXT].")


def build_drawtext_filter(phrase, img_w, img_h, cfg):
    # Read TEXT config values
    pad_x_ratio  = float(cfg.get('TEXT', 'padding_x_ratio',  fallback='0.05'))
    pad_y_ratio  = float(cfg.get('TEXT', 'padding_y_ratio',  fallback='0.05'))
    wrap_ratio   = float(cfg.get('TEXT', 'wrap_width_ratio', fallback='0.7'))
    opacity      = float(cfg.get('TEXT', 'opacity',          fallback='0.85'))
    stroke_width = int(cfg.get('TEXT', 'stroke_width',       fallback='2'))
    font_size    = int(cfg.get('TEXT', 'font_size',          fallback='32'))
    anchor_key   = cfg.get('TEXT', 'anchor',                 fallback='BL').upper()

    # Allow override of font path via config; otherwise auto-detect
    font_path = cfg.get('TEXT', 'font_path', fallback='').strip()
    if not font_path:
        font_path = find_system_font()

    # ffmpeg drawtext on Windows requires the drive letter colon to be escaped
    # e.g. "C:/Windows/Fonts/arial.ttf" -> "C\:/Windows/Fonts/arial.ttf"
    font_path = re.sub(r"^([A-Za-z]):", r"\1\\:", font_path)
    font_path = font_path.replace("\\\\", "\\")

    # Wrap phrase to fit wrap_ratio * image width
    avg_char_px = font_size * 0.55
    max_chars   = max(1, int((img_w * wrap_ratio) / avg_char_px))
    wrapped     = textwrap.fill(phrase, width=max_chars)

    # ffmpeg drawtext requires literal newlines escaped as \n
    escaped_text = wrapped.replace("'", "\\'").replace(":", "\\:").replace("\n", "\\n")

    # Convert opacity (0.0–1.0) to ffmpeg alpha hex (00–ff)
    alpha_hex = format(int(opacity * 255), '02x')

    # Colors: white fill, black stroke
    font_color   = f"white@{opacity:.2f}"
    border_color = f"black@{opacity:.2f}"

    anchor_info = ANCHOR_MAP.get(anchor_key, ANCHOR_MAP["BL"])

    # Compute pixel padding from ratios
    pad_x = int(img_w * pad_x_ratio)
    pad_y = int(img_h * pad_y_ratio)

    # Build x/y expressions, substituting pre-computed pad values
    x_expr = anchor_info["dt_x"].replace("pad_x", str(pad_x))
    y_expr = anchor_info["dt_y"].replace("pad_y", str(pad_y))

    # Adjust for text box size based on anchor alignment
    x_rel = anchor_info["x_rel"]
    y_rel = anchor_info["y_rel"]

    if x_rel == 0.0:
        pass                                    # left-aligned: x = left edge + pad
    elif x_rel == 0.5:
        x_expr = f"({x_expr}-tw/2)"            # center: shift left by half text width
    else:
        x_expr = f"({x_expr}-tw)"              # right: shift left by full text width

    if y_rel == 0.0:
        pass                                    # top: y = top edge + pad
    elif y_rel == 0.5:
        y_expr = f"({y_expr}-th/2)"            # middle: shift up by half text height
    else:
        y_expr = f"({y_expr}-th)"              # bottom: shift up by full text height

    filter_str = (
        f"drawtext="
        f"fontfile='{font_path}':"
        f"text='{escaped_text}':"
        f"fontsize={font_size}:"
        f"fontcolor={font_color}:"
        f"borderw={stroke_width}:"
        f"bordercolor={border_color}:"
        f"x={x_expr}:"
        f"y={y_expr}"
    )
    return filter_str


def apply_text_and_replace():
    cfg = load_text_config()

    # Path configuration
    in_dir  = cfg.get('GENERAL', 'input_dir',  fallback='Input')
    out_dir = cfg.get('GENERAL', 'output_dir', fallback='Output')

    # Text feature gate
    enabled = cfg.getboolean('TEXT', 'enable_text', fallback=False)
    if not enabled:
        print("[*] Text obfuscation feature is disabled in config.ini")
        return

    word_count = int(cfg.get('TEXT', 'word_count', fallback='5'))

    # Load word dictionary
    words = load_dictionary(cfg.get('TEXT', 'dictionary_path', fallback='dictionary.txt'))

    input_path  = Path(in_dir)
    output_path = Path(out_dir)
    output_path.mkdir(exist_ok=True)

    valid_extensions = ('.mp4', '.mov', '.avi', '.mkv', '.webm')
    processed_files  = []

    # Detect best available encoder once before processing loop
    encoder = get_best_encoder()
    print(f"[i] Using encoder: {encoder}")

    # STEP 1: Process videos and apply text watermark
    print("[*] Starting text application...")
    for video_file in input_path.iterdir():
        if video_file.suffix.lower() in valid_extensions:
            try:
                # Retrieve video dimensions for layout calculations
                vid_w, vid_h = probe_video(video_file)

                # Generate random phrase from dictionary
                phrase = generate_phrase(words, word_count)

                # Build drawtext filter with layout from config
                drawtext = build_drawtext_filter(phrase, vid_w, vid_h, cfg)

                # Select encoder; drawtext is hw-compatible, guard added for safety
                enc_flags = get_encoder_flags_for_filter(drawtext, encoder)

                # Save to temporary output folder
                save_path = output_path / f"{video_file.stem}.mp4"

                # Apply text watermark via ffmpeg drawtext filter
                subprocess.run(
                    [
                        get_ffmpeg_exe(), "-y",
                        "-i", str(video_file),
                        "-vf", drawtext,
                        # Re-encode with detected encoder; copy audio stream unchanged
                        *enc_flags,
                        "-c:a", "copy",
                        str(save_path)
                    ],
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )

                processed_files.append(video_file)
                print(f"[*] Text applied successfully: {video_file.name} | Phrase: \"{phrase}\"")
            except Exception as e:
                print(f"[-] Error processing {video_file.name}: {e}")

    if not processed_files:
        print("[-] No valid videos found for processing.")
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
        if out_file.suffix.lower() == '.mp4':
            try:
                # Move and overwrite if necessary
                shutil.move(str(out_file), str(input_path / out_file.name))
            except Exception as e:
                print(f"[-] Error moving {out_file.name}: {e}")

    print("\n[*] Operation completed. Original files replaced with text-watermarked versions.")


if __name__ == "__main__":
    apply_text_and_replace()
