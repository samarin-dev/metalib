#-----------------
# {meta}lib
# make your content unique
#-----------------
# Video Blur Processor script
#-----------------
# Copyright (C) 2026 by Mykhailo Samarin
# All rights reserved worldwide
#-----------------
# Under General Public License
#-----------------
# Visit http://github.com/samarin-dev for more information
#-----------------

import configparser
import os
import shutil
import subprocess
from pathlib import Path

from meta_utils import get_ffmpeg_exe, get_best_encoder, get_encoder_flags_for_filter


def load_blur_config():
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    return config


def apply_blur_and_replace():
    cfg = load_blur_config()

    # Path configuration
    in_dir = cfg.get('GENERAL', 'input_dir', fallback='Input')
    out_dir = cfg.get('GENERAL', 'output_dir', fallback='Output')

    # Blur configuration
    enabled = cfg.getboolean('BLUR', 'enable_blur', fallback=False)
    radius = cfg.getfloat('BLUR', 'blur_radius', fallback=1.0)

    if not enabled:
        print("[i] Blur feature is disabled in config.ini")
        return

    input_path = Path(in_dir)
    output_path = Path(out_dir)
    output_path.mkdir(exist_ok=True)

    valid_extensions = ('.mp4', '.mov', '.avi', '.mkv', '.webm')
    processed_files = []

    # Detect best available encoder once before processing loop
    encoder = get_best_encoder()
    print(f"[i] Using encoder: {encoder}")

    # STEP 1: Process videos and save to output
    print(f"Starting video blurring (Radius: {radius})...")
    for video_file in input_path.iterdir():
        if video_file.suffix.lower() in valid_extensions:
            try:
                # Apply Gaussian Blur filter
                # ffmpeg gblur sigma maps directly to PIL GaussianBlur radius
                blur_filter = f"gblur=sigma={radius}"

                # Select encoder; gblur is hw-compatible, guard added for safety
                enc_flags = get_encoder_flags_for_filter(blur_filter, encoder)

                # Save to temporary output folder
                save_path = output_path / f"{video_file.stem}.mp4"

                subprocess.run(
                    [
                        get_ffmpeg_exe(), "-y",
                        "-i", str(video_file),
                        "-vf", blur_filter,
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
                print(f"[*] Blurred successfully: {video_file.name}")
            except Exception as e:
                print(f"[*] Error processing {video_file.name}: {e}")

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
    for blurred_file in output_path.iterdir():
        if blurred_file.suffix.lower() == '.mp4':
            try:
                # Move and overwrite if necessary
                shutil.move(str(blurred_file), str(input_path / blurred_file.name))
            except Exception as e:
                print(f"[-] Error moving {blurred_file.name}: {e}")

    print("\n[*] Operation completed. Original files replaced with blurred versions.")


if __name__ == "__main__":
    apply_blur_and_replace()