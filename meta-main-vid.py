#-----------------
# {meta}lib
# make your content unique
#-----------------
# Video Main Processor script
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
import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path

from meta_utils import get_ffmpeg_exe, get_ffprobe_exe, probe_video, get_best_encoder, get_encoder_flags_for_filter


def load_configs():
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')

    presets = configparser.ConfigParser()
    presets.read('presets.ini', encoding='utf-8')

    return config, presets


def build_artifact_filter(pixel_count, stripe_count, width, height):
    # Build an ffmpeg drawgraph filter string to simulate dead pixels and sensor stripes
    filters = []

    # dead pixels
    for _ in range(pixel_count):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        color = random.choice(['red', 'lime', 'blue', 'white'])
        filters.append(f"drawbox=x={x}:y={y}:w=1:h=1:color={color}:t=fill")

    # sensor noise
    for _ in range(stripe_count):
        x = random.randint(0, width - 1)
        length = random.randint(10, 100)
        y_start = random.randint(0, max(0, height - length - 1))
        r = random.randint(50, 150)
        filters.append(f"drawbox=x={x}:y={y_start}:w=1:h={length}:color=#{r:02x}3232:t=fill")

    return ",".join(filters) if filters else None


def run_processor():
    cfg, pre = load_configs()

    in_dir = cfg['GENERAL']['input_dir']
    out_dir = cfg['GENERAL']['output_dir']
    target_preset_name = cfg['PRESETS']['current_preset']

    Path(out_dir).mkdir(exist_ok=True)

    # getting list of all presets
    available_presets = pre.sections()

    # Detect best available encoder once before processing loop
    encoder = get_best_encoder()
    print(f"[i] Using encoder: {encoder}")

    for video_path in Path(in_dir).iterdir():
        if video_path.suffix.lower() not in ('.mp4', '.mov', '.avi', '.mkv', '.webm'):
            continue

        try:
            # --- Logic of preset selection ---
            if target_preset_name.lower() == 'random':
                active_preset_name = random.choice(available_presets)
            else:
                active_preset_name = target_preset_name

            p = pre[active_preset_name]
            # ----------------------------

            orig_w, orig_h = probe_video(video_path)
            vf_chain = []

            # Setting resolution
            if cfg.getboolean('RESOLUTION', 'enable_resizing'):
                mode = cfg['RESOLUTION']['mode']
                tw = cfg.getint('RESOLUTION', 'width')
                th = cfg.getint('RESOLUTION', 'height')
                target_res = (tw, th) if mode == 'landscape' else (th, tw)

                target_ratio = target_res[0] / target_res[1]
                img_ratio = orig_w / orig_h

                if img_ratio > target_ratio:
                    new_w = int(target_ratio * orig_h)
                    offset = (orig_w - new_w) // 2
                    vf_chain.append(f"crop={new_w}:{orig_h}:{offset}:0")
                else:
                    new_h = int(orig_w / target_ratio)
                    offset = (orig_h - new_h) // 2
                    vf_chain.append(f"crop={orig_w}:{new_h}:0:{offset}")

                vf_chain.append(f"scale={target_res[0]}:{target_res[1]}:flags=lanczos")
                out_w, out_h = target_res
            else:
                out_w, out_h = orig_w, orig_h

            # Adding artifacts
            if cfg.getboolean('EFFECTS', 'enable_artifacts'):
                artifact_filter = build_artifact_filter(
                    cfg.getint('EFFECTS', 'dead_pixels_count'),
                    cfg.getint('EFFECTS', 'sensor_stripes_count'),
                    out_w, out_h
                )
                if artifact_filter:
                    vf_chain.append(artifact_filter)

            # EXIF
            m_back = random.randint(12, 19)
            time_str = (datetime.now() - timedelta(minutes=m_back)).strftime("%Y-%m-%dT%H:%M:%S")

            # EXIF Calc
            f_number = float(p['f_number'])
            focal_length = float(p['focal_length'])
            iso = random.choice([32, 50, 100])

            # Build metadata flags for ffmpeg (written into QuickTime/MP4 atoms)
            metadata_args = [
                "-metadata", f"make={p['make']}",
                "-metadata", f"model={p['model']}",
                "-metadata", f"software={p['software']}",
                "-metadata", f"lens={p['lens']}",
                "-metadata", f"creation_time={time_str}",
                "-metadata", f"date={time_str}",
                "-metadata", f"f_number={f_number}",
                "-metadata", f"focal_length={focal_length}mm",
                "-metadata", f"iso={iso}",
            ]

            save_path = Path(out_dir) / f"{video_path.stem}.mp4"

            # Select encoder based on the final vf chain (some filters are CPU-only)
            vf_string = ",".join(vf_chain)
            enc_flags = get_encoder_flags_for_filter(vf_string, encoder)

            ffmpeg_cmd = [get_ffmpeg_exe(), "-y", "-i", str(video_path)]

            if vf_chain:
                ffmpeg_cmd += ["-vf", vf_string]

            # Re-encode with detected encoder; copy audio stream unchanged
            ffmpeg_cmd += [*enc_flags, "-c:a", "copy"]
            ffmpeg_cmd += metadata_args
            ffmpeg_cmd.append(str(save_path))

            subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            print(f"[*] OK: {video_path.name} | EXIF: {active_preset_name} | Time: -{m_back} мин")

        except Exception as e:
            print(f"[-] Err in {video_path.name}: {e}")


if __name__ == "__main__":
    run_processor()