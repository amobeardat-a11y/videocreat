#!/usr/bin/env python3
"""Preview the new stickman acting loops beside reusable illustrations."""

from __future__ import annotations

import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

import illustrations
import stickman as rig
from story_animation import StoryAnimation


ROOT = Path(__file__).resolve().parent
FONT = ROOT.parent / "phan_tram_stickman_video" / "NotoSans.ttf"
PAIRS = [
    ("shield_eyes", "parcel_route", "Tìm đường giao hàng"),
    ("inspect_ground", "rainy_street", "Quan sát khi trời mưa"),
    ("measure_span", "idea_lab", "Đo đạc và tìm ý tưởng"),
    ("ponder_walk", "calendar_clock", "Suy nghĩ về thời gian"),
    ("call_out", "team_talk", "Trao đổi với người khác"),
    ("fist_pump", "growth_steps", "Tiến bộ từng bước"),
    ("think", "data_network", "Kết nối dữ liệu"),
    ("show_two", "balance_scale", "Cân nhắc lựa chọn"),
    ("pay_cashier", "wallet_payment", "Thanh toán"),
    ("look_around", "search_document", "Tra cứu tài liệu"),
    ("block", "secure_lock", "Bảo vệ thông tin"),
    ("present_right", "storyboard", "Dựng câu chuyện"),
]


def main():
    fps, duration = 12, 2.4
    output = ROOT / "illustration_animation_preview.mp4"
    font_title = ImageFont.truetype(str(FONT), 24)
    font_small = ImageFont.truetype(str(FONT), 16)
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
               "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", "960x540",
               "-framerate", str(fps), "-i", "-", "-c:v", "libx264",
               "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", str(output)]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        for number, (pose, art_name, caption) in enumerate(PAIRS, 1):
            sequence = StoryAnimation({"canvas": [960, 540], "ground_y": 460,
                                       "scale": .82, "initial_x": 215,
                                       "background": "#f3f7fb",
                                       "beats": [{"pose": pose, "duration": duration,
                                                  "transition": 0, "to_x": 215}]})
            for frame_index in range(round(duration * fps)):
                t = frame_index / fps
                frame = rig.raster(sequence.svg(t), 960).convert("RGB")
                draw = ImageDraw.Draw(frame)
                draw.rectangle((0, 0, 960, 65), fill="#17324d")
                draw.text((28, 18), f"{number:02d} / {len(PAIRS):02d}  ·  {caption}",
                          font=font_title, fill="white")
                draw.rounded_rectangle((408, 107, 944, 430), radius=23,
                                       fill="white", outline="#d7e3ec", width=2)
                art = rig.raster(illustrations.svg(art_name, min(1, t / 1.4)), 500)
                frame.paste(art, (425, 122), art)
                draw = ImageDraw.Draw(frame)
                draw.text((425, 451), f"pose: {pose}   ·   illustration: {art_name}",
                          font=font_small, fill="#496478")
                process.stdin.write(frame.tobytes())
    finally:
        process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError("Preview render failed")
    print(output)


if __name__ == "__main__":
    main()
