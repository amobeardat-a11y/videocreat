#!/usr/bin/env python3
"""Render a short visual preview of the new stickman VFX."""

from __future__ import annotations

import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import stickman as rig
from story_animation import StoryAnimation


ROOT = Path(__file__).resolve().parent
FONT = ROOT.parent / "phan_tram_stickman_video" / "NotoSans.ttf"
ITEMS = [
    ("sparkle", "Lấp lánh", "Vui mừng, chiến thắng", "quiet_joy", "grateful"),
    ("sweat", "Mồ hôi", "Lo lắng, áp lực", "check_time", "worried"),
    ("question", "Dấu hỏi", "Bối rối, tìm lời giải", "confused", "confused"),
    ("impact", "Cú sốc", "Tin bất ngờ, va chạm", "flinch", "panic"),
    ("anger", "Giận dữ", "Cãi nhau, mất kiên nhẫn", "angry_stomp", "angry"),
    ("rain", "Mưa", "Bối cảnh trời mưa", "walk", "worried"),
]


def main() -> None:
    fps, duration = 12, 2.4
    output = ROOT / "vfx_preview.mp4"
    title_font = ImageFont.truetype(str(FONT), 29)
    body_font = ImageFont.truetype(str(FONT), 19)
    small_font = ImageFont.truetype(str(FONT), 16)
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
               "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", "960x540",
               "-framerate", str(fps), "-i", "-", "-c:v", "libx264",
               "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
               str(output)]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        for number, (effect, title, description, pose, expression) in enumerate(ITEMS, 1):
            sequence = StoryAnimation({
                "canvas": [960, 540], "initial_x": 295, "ground_y": 460,
                "scale": .85, "background": "#f3f7fb",
                "beats": [{"pose": pose, "expression": expression,
                           "duration": duration, "transition": 0,
                           "to_x": 295, "effect": effect}],
            })
            for index in range(round(duration * fps)):
                frame = rig.raster(sequence.svg(index / fps), 960).convert("RGB")
                draw = ImageDraw.Draw(frame)
                draw.rectangle((0, 0, 960, 60), fill="#17324d")
                draw.text((28, 16), "VFX NGƯỜI QUE  ·  6 HIỆU ỨNG MỚI",
                          font=body_font, fill="white")
                draw.rounded_rectangle((590, 110, 934, 415), radius=22,
                                       fill="white", outline="#d7e3ec", width=2)
                draw.text((619, 138), f"{number:02d} / 06", font=body_font, fill="#e56b35")
                draw.text((619, 186), title, font=title_font, fill="#17324d")
                draw.text((619, 249), description, font=body_font, fill="#425a6b")
                draw.text((619, 364), f"effect: {effect}", font=small_font, fill="#64798a")
                draw.text((28, 496), "DÙNG TRÊN MỌI POSE  ·  CÓ THỂ TẮT TỪ JSON",
                          font=small_font, fill="#496478")
                process.stdin.write(frame.tobytes())
    finally:
        process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError("VFX preview render failed")
    print(output)


if __name__ == "__main__":
    main()
