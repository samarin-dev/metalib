#-----------------
# {meta}lib
# make your content unique
#-----------------
# Image Main Processor script
#-----------------
# Copyright (C) 2026 by Mykhailo Samarin
# All rights reserved worldwide
#-----------------
# Under General Public License
#-----------------
# Visit http://github.com/samarin-dev for more information
#-----------------

import os
import random
import configparser
from datetime import datetime, timedelta
from pathlib import Path
import piexif
from PIL import Image, ImageDraw

def load_configs():
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    
    presets = configparser.ConfigParser()
    presets.read('presets.ini', encoding='utf-8')
    
    return config, presets

def to_deg(value, loc):
    abs_val = abs(value)
    d = int(abs_val)
    m = int((abs_val - d) * 60)
    s = round((abs_val - d - m/60) * 3600 * 100)
    return (d, m, s), loc[1] if value >= 0 else loc[0]

def add_artifacts(img, pixel_count, stripe_count):
    draw = ImageDraw.Draw(img)
    w, h = img.size
    
    # dead pixels
    for _ in range(pixel_count):
        x, y = random.randint(0, w-1), random.randint(0, h-1)
        color = random.choice([(255,0,0), (0,255,0), (0,0,255), (255,255,255)])
        draw.point((x, y), fill=color)
    
    # sensor noise
    for _ in range(stripe_count):
        x = random.randint(0, w-1)
        length = random.randint(10, 100)
        y_start = random.randint(0, h - length)
        draw.line((x, y_start, x, y_start + length), fill=(random.randint(50,150), 50, 50), width=1)
    
    return img

def run_processor():
    cfg, pre = load_configs()
    
    in_dir = cfg['GENERAL']['input_dir']
    out_dir = cfg['GENERAL']['output_dir']
    target_preset_name = cfg['PRESETS']['current_preset']
    
    Path(out_dir).mkdir(exist_ok=True)

    # getting list of all presets
    available_presets = pre.sections()

    for img_path in Path(in_dir).iterdir():
        if img_path.suffix.lower() not in ('.jpg', '.jpeg', '.png', '.webp'): continue
        
        try:
            # --- Logic of preset selection ---
            if target_preset_name.lower() == 'random':
                active_preset_name = random.choice(available_presets)
            else:
                active_preset_name = target_preset_name
            
            p = pre[active_preset_name]
            # ----------------------------

            img = Image.open(img_path).convert("RGB")
            
            # Setting resolution
            if cfg.getboolean('RESOLUTION', 'enable_resizing'):
                mode = cfg['RESOLUTION']['mode']
                tw = cfg.getint('RESOLUTION', 'width')
                th = cfg.getint('RESOLUTION', 'height')
                target_res = (tw, th) if mode == 'landscape' else (th, tw)
                
                target_ratio = target_res[0] / target_res[1]
                img_ratio = img.width / img.height
                if img_ratio > target_ratio:
                    new_w = int(target_ratio * img.height)
                    offset = (img.width - new_w) // 2
                    img = img.crop((offset, 0, offset + new_w, img.height))
                else:
                    new_h = int(img.width / target_ratio)
                    offset = (img.height - new_h) // 2
                    img = img.crop((0, offset, img.width, offset + new_h))
                img = img.resize(target_res, Image.Resampling.LANCZOS)

            # Adding artifacts
            if cfg.getboolean('EFFECTS', 'enable_artifacts'):
                img = add_artifacts(
                    img, 
                    cfg.getint('EFFECTS', 'dead_pixels_count'),
                    cfg.getint('EFFECTS', 'sensor_stripes_count')
                )

            # EXIF
            m_back = random.randint(12, 19)
            time_str = (datetime.now() - timedelta(minutes=m_back)).strftime("%Y:%m:%d %H:%M:%S")
            
            # EXIF Calc
            f_num = int(float(p['f_number']) * 10), 10
            focal = int(float(p['focal_length']) * 100), 100
            
            exif_dict = {
                "0th": {
                    piexif.ImageIFD.Make: p['make'],
                    piexif.ImageIFD.Model: p['model'],
                    piexif.ImageIFD.Software: p['software'],
                    piexif.ImageIFD.DateTime: time_str,
                    piexif.ImageIFD.Orientation: 1,
                },
                "Exif": {
                    piexif.ExifIFD.DateTimeOriginal: time_str,
                    piexif.ExifIFD.DateTimeDigitized: time_str,
                    piexif.ExifIFD.LensModel: p['lens'],
                    piexif.ExifIFD.FNumber: f_num,
                    piexif.ExifIFD.FocalLength: focal,
                    piexif.ExifIFD.ISOSpeedRatings: random.choice([32, 50, 100]),
                }
            }
            
            exif_bytes = piexif.dump(exif_dict)
            save_path = Path(out_dir) / f"{img_path.stem}.jpg"
            img.save(save_path, "jpeg", exif=exif_bytes, quality=95, subsampling=0)
            
            print(f"OK: {img_path.name} | EXIF: {active_preset_name} | Time: -{m_back} мин")

        except Exception as e:
            print(f"Err in {img_path.name}: {e}")

if __name__ == "__main__":
    run_processor()