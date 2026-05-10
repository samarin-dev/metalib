#-----------------
# {meta}lib
# make your content unique
#-----------------
# Image Grain Processor script
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
from pathlib import Path
from PIL import Image, ImageChops

def load_grain_config():
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    return config

def add_grain(image, intensity):
    """Adds a film grain effect by overlaying random noise."""
    # Create noise layer
    noise = Image.effect_noise(image.size, intensity * 50)
    noise = noise.convert("RGB")
    
    # Blend noise with the original image
    # We use Soft Light-like blending via ImageChops
    return ImageChops.soft_light(image, noise)

def apply_grain_and_replace():
    cfg = load_grain_config()
    
    # Path configuration
    in_dir = cfg.get('GENERAL', 'input_dir', fallback='Input')
    out_dir = cfg.get('GENERAL', 'output_dir', fallback='Output')
    
    # Grain configuration
    enabled = cfg.getboolean('GRAIN', 'enable_grain', fallback=False)
    intensity = cfg.getfloat('GRAIN', 'grain_intensity', fallback=0.2)
    
    if not enabled:
        print("Grain feature is disabled in config.ini")
        return

    input_path = Path(in_dir)
    output_path = Path(out_dir)
    output_path.mkdir(exist_ok=True)

    valid_extensions = ('.jpg', '.jpeg', '.png', '.webp')
    processed_files = []

    # STEP 1: Process images and apply grain
    print(f"Starting grain application (Intensity: {intensity})...")
    for img_file in input_path.iterdir():
        if img_file.suffix.lower() in valid_extensions:
            try:
                with Image.open(img_file) as img:
                    # Convert to RGB
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    
                    # Apply grain effect
                    grained_img = add_grain(img, intensity)
                    
                    # Save to temporary output folder
                    save_path = output_path / f"{img_file.stem}.jpg"
                    grained_img.save(save_path, "JPEG", quality=95)
                    processed_files.append(img_file)
                    print(f"Grain applied successfully: {img_file.name}")
            except Exception as e:
                print(f"Error processing {img_file.name}: {e}")

    if not processed_files:
        print("No valid images found for processing.")
        return

    # STEP 2: Delete original source files
    print("\nDeleting original files from Input directory...")
    for file in processed_files:
        try:
            file.unlink()
        except Exception as e:
            print(f"Failed to delete {file.name}: {e}")

    # STEP 3: Move processed files back to Input
    print("Moving grained files back to Input directory...")
    for grain_file in output_path.iterdir():
        if grain_file.suffix.lower() == '.jpg':
            try:
                shutil.move(str(grain_file), str(input_path / grain_file.name))
            except Exception as e:
                print(f"Error moving {grain_file.name}: {e}")

    print("\nOperation completed. Original files replaced with grained versions.")

if __name__ == "__main__":
    apply_grain_and_replace()