#-----------------
# {meta}lib
# make your content unique
#-----------------
# Video Grain Processor script
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
import random
import subprocess
from pathlib import Path

from meta_utils import get_ffmpeg_exe, get_best_encoder, get_encoder_flags_for_filter


def load_grain_config():
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    return config


def apply_grain_and_replace():
    cfg = load_grain_config()

    # Path configuration
    in_dir = cfg.get('GENERAL', 'input_dir', fallback='Input')
    out_dir = cfg.get('GENERAL', 'output_dir', fallback='Output')

    # Grain configuration
    enabled = cfg.getboolean('GRAIN', 'enable_grain', fallback=False)
    intensity = cfg.getfloat('GRAIN', 'grain_intensity', fallback=0.2)

    if not enabled:
        print("[i] Grain feature is disabled in config.ini")
        return

    input_path = Path(in_dir)
    output_path = Path(out_dir)
    output_path.mkdir(exist_ok=True)

    valid_extensions = ('.mp4', '.mov', '.avi', '.mkv', '.webm')
    processed_files = []

    # Detect best available encoder once before processing loop
    encoder = get_best_encoder()
    print(f"[i] Using encoder: {encoder}")

    # STEP 1: Process videos and apply grain
    print(f"[*] Starting grain application (Intensity: {intensity})...")
    for video_file in input_path.iterdir():
        if video_file.suffix.lower() in valid_extensions:
            try:
                # Map intensity (0.0–1.0) to geq noise strength (0–100)
                noise_strength = intensity * 100

                # Create noise layer and blend using Soft Light-like blending via geq filter
                # geq applies per-pixel expression: mixes original luma with random noise
                grain_filter = (
                    f"geq="
                    f"lum='clip(lum(X,Y) + {noise_strength}*(random(1)-0.5), 0, 255)':"
                    f"cb='cb(X,Y)':"
                    f"cr='cr(X,Y)'"
                )

                # geq is a CPU-only filter; select encoder accordingly
                enc_flags = get_encoder_flags_for_filter(grain_filter, encoder)

                # Save to temporary output folder
                save_path = output_path / f"{video_file.stem}.mp4"

                # Apply grain effect
                subprocess.run(
                    [
                        get_ffmpeg_exe(), "-y",
                        "-i", str(video_file),
                        "-vf", grain_filter,
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
                print(f"[*] Grain applied successfully: {video_file.name}")
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
    print("[*] Moving grained files back to Input directory...")
    for grain_file in output_path.iterdir():
        if grain_file.suffix.lower() == '.mp4':
            try:
                shutil.move(str(grain_file), str(input_path / grain_file.name))
            except Exception as e:
                print(f"[-] Error moving {grain_file.name}: {e}")

    print("\n[*] Operation completed. Original files replaced with grained versions.")


if __name__ == "__main__":
    apply_grain_and_replace()