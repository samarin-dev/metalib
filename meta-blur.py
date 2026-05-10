#-----------------
# {meta}lib
# make your content unique
#-----------------
# Image Blur Proccesor script
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
from pathlib import Path
from PIL import Image, ImageFilter

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
        print("Blur feature is disabled in config.ini")
        return

    input_path = Path(in_dir)
    output_path = Path(out_dir)
    output_path.mkdir(exist_ok=True)

    valid_extensions = ('.jpg', '.jpeg', '.png', '.webp')
    processed_files = []

    # STEP 1: Process images and save to output
    print(f"Starting image blurring (Radius: {radius})...")
    for img_file in input_path.iterdir():
        if img_file.suffix.lower() in valid_extensions:
            try:
                with Image.open(img_file) as img:
                    # Convert to RGB to ensure JPEG compatibility
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    
                    # Apply Gaussian Blur filter
                    blurred_img = img.filter(ImageFilter.GaussianBlur(radius=radius))
                    
                    # Save to temporary output folder
                    save_path = output_path / f"{img_file.stem}.jpg"
                    blurred_img.save(save_path, "JPEG", quality=95)
                    processed_files.append(img_file)
                    print(f"Blurred successfully: {img_file.name}")
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
    print("Moving processed files back to Input directory...")
    for blurred_file in output_path.iterdir():
        if blurred_file.suffix.lower() == '.jpg':
            try:
                # Move and overwrite if necessary
                shutil.move(str(blurred_file), str(input_path / blurred_file.name))
            except Exception as e:
                print(f"Error moving {blurred_file.name}: {e}")

    print("\nOperation completed. Original files replaced with blurred versions.")

if __name__ == "__main__":
    apply_blur_and_replace()