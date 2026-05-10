#-----------------
# {meta}lib
# make your content unique
#-----------------
# Image Sharpen Processor script
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
from PIL import Image, ImageEnhance

def load_sharpen_config():
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    return config

def apply_sharpen_and_replace():
    cfg = load_sharpen_config()
    
    # Path configuration
    in_dir = cfg.get('GENERAL', 'input_dir', fallback='Input')
    out_dir = cfg.get('GENERAL', 'output_dir', fallback='Output')
    
    # Sharpen configuration
    enabled = cfg.getboolean('SHARPEN', 'enable_sharpen', fallback=False)
    factor = cfg.getfloat('SHARPEN', 'sharpen_factor', fallback=1.0)
    
    if not enabled:
        print("Sharpen feature is disabled in config.ini")
        return

    input_path = Path(in_dir)
    output_path = Path(out_dir)
    output_path.mkdir(exist_ok=True)

    valid_extensions = ('.jpg', '.jpeg', '.png', '.webp')
    processed_files = []

    # STEP 1: Process images and enhance sharpness
    print(f"Starting image sharpening (Factor: {factor})...")
    for img_file in input_path.iterdir():
        if img_file.suffix.lower() in valid_extensions:
            try:
                with Image.open(img_file) as img:
                    # Convert to RGB to ensure JPEG compatibility
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    
                    # Apply Sharpness Enhancement
                    enhancer = ImageEnhance.Sharpness(img)
                    sharpened_img = enhancer.enhance(factor)
                    
                    # Save to temporary output folder
                    save_path = output_path / f"{img_file.stem}.jpg"
                    sharpened_img.save(save_path, "JPEG", quality=95)
                    processed_files.append(img_file)
                    print(f"Sharpened successfully: {img_file.name}")
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
    print("Moving sharpened files back to Input directory...")
    for sharp_file in output_path.iterdir():
        if sharp_file.suffix.lower() == '.jpg':
            try:
                # Move and overwrite
                shutil.move(str(sharp_file), str(input_path / sharp_file.name))
            except Exception as e:
                print(f"Error moving {sharp_file.name}: {e}")

    print("\nOperation completed. Original files replaced with sharpened versions.")

if __name__ == "__main__":
    apply_sharpen_and_replace()