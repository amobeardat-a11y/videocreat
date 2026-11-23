#!/usr/bin/env python3
"""Create a short MP4 preview of the expanded story animation library."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
FONT = ROOT.parent / "phan_tram_stickman_video" / "NotoSans.ttf"
ITEMS = [
    ("search_and_discover", "Tìm kiếm và phát hiện", "Nhìn quanh · Đi qua lại · Nảy ý"),
    ("explain_with_numbers", "Giải thích bằng số", "Đếm ngón tay · Chỉ · Thuyết phục"),
    ("sudden_scary_news", "Tin xấu bất ngờ", "Sững người · Giật mình · Bình tĩnh lại"),
    ("impatient_waiting", "Chờ đợi sốt ruột", "Xem giờ · Gõ chân · Đi qua lại"),
    ("debate_and_agree", "Tranh luận rồi đồng ý", "Lắng nghe · Phản đối · Đồng ý"),
    ("small_victory", "Niềm vui nhỏ", "Suy nghĩ · Nảy ý · Ăn mừng nhẹ"),
    ("spot_and_measure", "Tìm và đo đạc", "Nhìn xa · Quan sát · Đo khoảng rộng"),
    ("calm_after_conflict", "Hòa giải", "Từ chối · Lắng nghe · Trấn an"),
]


def main() -> None:
    fps, width, height = 12, 960, 540
    output = ROOT / "library_expansion_preview.mp4"
    font_big = ImageFont.truetype(str(FONT), 28)
    font_mid = ImageFont.truetype(str(FONT), 19)
    font_small = ImageFont.truetype(str(FONT), 15)
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
               "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size",
               f"{width}x{height}", "-framerate", str(fps), "-i", "-",
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
               "-pix_fmt", "yuv420p", str(output)]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        for number, (name, title, description) in enumerate(ITEMS, 1):
            data = json.loads((ROOT / "sequences" / f"{name}.json").read_text(encoding="utf-8"))
            duration = sum(beat["duration"] for beat in data["beats"])
            webp = Image.open(ROOT / "sequences" / f"{name}.webp")
            for index in range(round(duration * fps)):
                time = index / fps
                webp.seek(min(round(time * 18), webp.n_frames - 1))
                frame = Image.new("RGB", (width, height), "#f3f7fb")
                draw = ImageDraw.Draw(frame)
                draw.rectangle((0, 0, width, 60), fill="#17324d")
                draw.text((28, 16), "THƯ VIỆN NGƯỜI QUE  ·  BẢN 6", font=font_mid, fill="white")
                draw.line((28, 462, 574, 462), fill="#cad6e1", width=2)
                actor = webp.convert("RGBA")
                frame.paste(actor, (0, 0), actor)
                draw = ImageDraw.Draw(frame)
                draw.rounded_rectangle((592, 102, 936, 425), radius=22, fill="white", outline="#dae5ed", width=2)
                draw.text((620, 130), f"{number:02d} / {len(ITEMS):02d}", font=font_mid, fill="#e56b35")
                draw.text((620, 179), title, font=font_big, fill="#17324d")
                draw.multiline_text((620, 238), description.replace(" · ", "\n"),
                                    font=font_mid, fill="#425a6b", spacing=9)
                elapsed = 0.0
                current_pose = data["beats"][-1]["pose"]
                for beat in data["beats"]:
                    elapsed += beat["duration"]
                    if time < elapsed:
                        current_pose = beat["pose"]
                        break
                draw.text((620, 378), f"pose: {current_pose}", font=font_small, fill="#64798a")
                draw.text((28, 496), "88 ĐỘNG TÁC   ·   12 CHUỖI   ·   10 VFX   ·   6 HÌNH MINH HỌA",
                          font=font_small, fill="#496478")
                process.stdin.write(frame.tobytes())
            webp.close()
    finally:
        process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError("FFmpeg preview render failed")
    print(output)


if __name__ == "__main__":
    main()
