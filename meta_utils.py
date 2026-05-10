#-----------------
# {meta}lib
# make your content unique
#-----------------
# Shared utilities: ffprobe helper and hardware encoder detection
#-----------------
# Copyright (C) 2026 by Mykhailo Samarin
# All rights reserved worldwide
#-----------------
# Under General Public License
#-----------------
# Visit http://github.com/samarin-dev for more information
#-----------------

import json
import random
import subprocess
import textwrap
from pathlib import Path

import imageio_ffmpeg


def get_ffmpeg_exe():
    # Return bundled ffmpeg binary path via imageio_ffmpeg
    return imageio_ffmpeg.get_ffmpeg_exe()


def get_ffprobe_exe():
    # imageio_ffmpeg does not bundle ffprobe; this function is kept for API
    # compatibility but probe_video() uses ffmpeg directly instead
    return None


def probe_video(path):
    # Retrieve video stream dimensions using ffmpeg itself (no ffprobe needed)
    # ffmpeg -i prints stream info to stderr; we parse width/height from it
    result = subprocess.run(
        [get_ffmpeg_exe(), "-i", str(path)],
        capture_output=True, text=True
    )
    # ffmpeg always exits with error when no output is given — that is expected
    # Parse "Stream #0:0: Video: ..., WxH" pattern from stderr
    import re
    for line in result.stderr.splitlines():
        if "Video:" in line:
            match = re.search(r"(\d{2,5})x(\d{2,5})", line)
            if match:
                return int(match.group(1)), int(match.group(2))
    raise ValueError(
        f"Could not detect video dimensions in: {path}\n"
        f"ffmpeg output: {result.stderr[-500:]}"
    )


def _test_encoder(encoder):
    # Verify encoder actually works by encoding a 1-frame black video in memory
    # -f lavfi generates a synthetic source; no input file needed
    result = subprocess.run(
        [
            get_ffmpeg_exe(),
            "-f", "lavfi", "-i", "color=black:s=128x128:r=1",
            "-frames:v", "1",
            "-c:v", encoder,
            "-f", "null", "-"
        ],
        capture_output=True
    )
    return result.returncode == 0


def get_best_encoder():
    # First pass: filter encoders present in ffmpeg -encoders output
    hw_encoders = ["h264_nvenc", "h264_amf", "h264_qsv", "h264_videotoolbox"]
    list_result = subprocess.run(
        [get_ffmpeg_exe(), "-encoders"],
        capture_output=True, text=True
    )
    candidates = [enc for enc in hw_encoders if enc in list_result.stdout]

    # Second pass: actually test each candidate with a real encode attempt
    # This filters out encoders that are compiled in but have no hardware support
    for enc in candidates:
        if _test_encoder(enc):
            return enc

    return "libx264"


def get_encoder_flags(encoder):
    # Return encode flags appropriate for the detected encoder
    if encoder == "libx264":
        return ["-c:v", "libx264", "-crf", "18", "-preset", "slow"]
    elif encoder == "h264_nvenc":
        return ["-c:v", "h264_nvenc", "-b:v", "8M", "-preset", "p4"]
    elif encoder == "h264_amf":
        return ["-c:v", "h264_amf", "-b:v", "8M", "-quality", "quality"]
    elif encoder == "h264_qsv":
        return ["-c:v", "h264_qsv", "-b:v", "8M", "-preset", "slow"]
    elif encoder == "h264_videotoolbox":
        return ["-c:v", "h264_videotoolbox", "-b:v", "8M"]
    # Unknown encoder: safe fallback
    return ["-c:v", "libx264", "-crf", "18", "-preset", "slow"]


# ---------------------------------------------------------------------------
# Shared text / watermark utilities
# ---------------------------------------------------------------------------

# Anchor positions: map config keys to (x_rel, y_rel, PIL anchor, drawtext x/y expr)
# x_rel / y_rel are fractions of image size used to compute the offset point.
# pil_anchor: two-char PIL ImageDraw anchor string.
# dt_x / dt_y: ffmpeg drawtext x/y expressions (use W/H for frame size, tw/th for text box).
ANCHOR_MAP = {
    "TL": dict(x_rel=0.0, y_rel=0.0, pil_anchor="la", dt_x="(pad_x)",            dt_y="(pad_y)"),
    "TC": dict(x_rel=0.5, y_rel=0.0, pil_anchor="ma", dt_x="(W/2)",              dt_y="(pad_y)"),
    "TR": dict(x_rel=1.0, y_rel=0.0, pil_anchor="ra", dt_x="(W-pad_x)",          dt_y="(pad_y)"),
    "LC": dict(x_rel=0.0, y_rel=0.5, pil_anchor="lm", dt_x="(pad_x)",            dt_y="(H/2)"),
    "CC": dict(x_rel=0.5, y_rel=0.5, pil_anchor="mm", dt_x="(W/2)",              dt_y="(H/2)"),
    "RC": dict(x_rel=1.0, y_rel=0.5, pil_anchor="rm", dt_x="(W-pad_x)",          dt_y="(H/2)"),
    "BL": dict(x_rel=0.0, y_rel=1.0, pil_anchor="ld", dt_x="(pad_x)",            dt_y="(H-pad_y)"),
    "BC": dict(x_rel=0.5, y_rel=1.0, pil_anchor="md", dt_x="(W/2)",              dt_y="(H-pad_y)"),
    "BR": dict(x_rel=1.0, y_rel=1.0, pil_anchor="rd", dt_x="(W-pad_x)",          dt_y="(H-pad_y)"),
    # legacy aliases from the brief (LT=TL, RT=TR, RB=BR, LB=BL, TT=TC)
    "LT": dict(x_rel=0.0, y_rel=0.0, pil_anchor="la", dt_x="(pad_x)",            dt_y="(pad_y)"),
    "RT": dict(x_rel=1.0, y_rel=0.0, pil_anchor="ra", dt_x="(W-pad_x)",          dt_y="(pad_y)"),
    "RB": dict(x_rel=1.0, y_rel=1.0, pil_anchor="rd", dt_x="(W-pad_x)",          dt_y="(H-pad_y)"),
    "LB": dict(x_rel=0.0, y_rel=1.0, pil_anchor="ld", dt_x="(pad_x)",            dt_y="(H-pad_y)"),
    "TT": dict(x_rel=0.5, y_rel=0.0, pil_anchor="ma", dt_x="(W/2)",              dt_y="(pad_y)"),
}


def load_dictionary(dict_path="dictionary.txt"):
    # Load space-separated words from dictionary file
    text = Path(dict_path).read_text(encoding="utf-8")
    words = text.split()
    if not words:
        raise ValueError(f"Dictionary file is empty: {dict_path}")
    return words


def generate_phrase(words, word_count):
    # Pick a random sequence of word_count words (with repetition allowed)
    return " ".join(random.choices(words, k=word_count))


def wrap_phrase(phrase, img_width, wrap_ratio):
    # Wrap phrase so each line fits within wrap_ratio * img_width characters (approx)
    max_chars = max(1, int(len(phrase) * wrap_ratio))
    return textwrap.fill(phrase, width=max_chars)

# Filters that operate in CPU pixel space and are incompatible with hardware encoders.
# When any of these appear in the vf chain, encoding must fall back to libx264.
_CPU_ONLY_FILTERS = ("geq", "smartblur", "convolution", "kerndeint")


def get_encoder_flags_for_filter(vf_string, detected_encoder):
    # If the filter chain contains a CPU-only filter, force software encoding
    if any(f in vf_string for f in _CPU_ONLY_FILTERS):
        return get_encoder_flags("libx264")
    return get_encoder_flags(detected_encoder)
