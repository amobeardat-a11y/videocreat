#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hệ thống tự động hóa hoàn toàn Google Veo qua Gemini API (Mode A: Veo Video Pipeline)
- Gửi prompts theo từng cảnh lên Veo API (veo-2.0-generate-001)
- Polling tiến trình render và tự động tải video clips về thư mục clips/
- Dùng FFmpeg ghép video Veo + audio lồng tiếng VietTTS + công thức LaTeX
"""

import os
import sys
import time
import json
import shutil
import subprocess
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent
PROJ_DIR = WORKSPACE / "project_1_equals_2"
CLIPS_DIR = PROJ_DIR / "clips"
CLIPS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR = PROJ_DIR / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 6 Cảnh tương ứng với timeline giọng nói lồng tiếng VietTTS (Tổng: 109s)
SCENES = [
    {
        "id": 1,
        "name": "Cảnh 1: Thiên tài toán học",
        "duration": 17.6,
        "prompt": (
            "Cinematic 2D animated stickman video shot in modern anime-stickman style. "
            "Setting: A modern classroom. A confident teenage stickman student (wearing bright red beanie, yellow t-shirt) "
            "dashes into the classroom, excitedly slamming a paper on the desk. The wise stickman teacher and a skeptical classmate look on. "
            "Camera movement: Dynamic push-in tracking shot, energetic comedy framing. "
            "Visual style: Vibrant cel-shaded 2D animation, high contrast clean lines, crisp classroom environment. Aspect ratio: 16:9. "
            "Negative prompt: NO 3D CGI, NO PHOTOREALISTIC HUMAN FACE, NO BLURRY FRAMES, NO TEXT WATERMARKS."
        )
    },
    {
        "id": 2,
        "name": "Cảnh 2: Một chứng minh hoàn hảo",
        "duration": 26.3,
        "prompt": (
            "Cinematic 2D animated stickman video shot in modern anime-stickman style. "
            "Setting: The student stickman stands proudly at the large classroom blackboard, writing chalk equations: "
            "'a = b', 'a² = ab', '(a-b)(a+b) = b(a-b)', leading to '2 = 1!'. He raises both hands in triumphant victory. "
            "Camera movement: Medium pan following the blackboard writing, then quick cut to triumphant celebration. "
            "Visual style: Vibrant cel-shaded 2D animation, high contrast clean lines, crisp classroom environment. Aspect ratio: 16:9. "
            "Negative prompt: NO 3D CGI, NO PHOTOREALISTIC HUMAN FACE, NO BLURRY FRAMES, NO TEXT WATERMARKS."
        )
    },
    {
        "id": 3,
        "name": "Cảnh 3: Một câu hỏi nhỏ",
        "duration": 18.6,
        "prompt": (
            "Cinematic 2D animated stickman video shot in modern anime-stickman style. "
            "Setting: The stickman teacher calmly points to the blackboard, asking a probing question. "
            "The student freezes, eyes widening in sudden realization. The classmate facepalms in the background. "
            "Camera movement: Slow cinematic zoom-in on the student's dramatic pause of realization. "
            "Visual style: Vibrant cel-shaded 2D animation, high contrast clean lines, crisp classroom environment. Aspect ratio: 16:9. "
            "Negative prompt: NO 3D CGI, NO PHOTOREALISTIC HUMAN FACE, NO BLURRY FRAMES, NO TEXT WATERMARKS."
        )
    },
    {
        "id": 4,
        "name": "Cảnh 4: Điều đáng sợ hơn một đáp án sai",
        "duration": 21.1,
        "prompt": (
            "Cinematic 2D animated stickman video shot in modern anime-stickman style. "
            "Setting: The teacher gently erases the '2 = 1' line on the board, offering a profound teaching moment with deep cinematic warm classroom lighting. "
            "The student listens quietly with respectful posture. "
            "Camera movement: Warm atmospheric two-shot, soft depth of field. "
            "Visual style: Vibrant cel-shaded 2D animation, high contrast clean lines, crisp classroom environment. Aspect ratio: 16:9. "
            "Negative prompt: NO 3D CGI, NO PHOTOREALISTIC HUMAN FACE, NO BLURRY FRAMES, NO TEXT WATERMARKS."
        )
    },
    {
        "id": 5,
        "name": "Cảnh 5: Cú lật cuối",
        "duration": 20.5,
        "prompt": (
            "Cinematic 2D animated stickman video shot in modern anime-stickman style. "
            "Setting: Classmate asks for the money back. The student smirks, points to the paper, then comically bolts out the door! "
            "The classmate chases him through the hallway in classic stickman comedy motion. "
            "Camera movement: Wide slapstick chase tracking shot down the school hallway. "
            "Visual style: Vibrant cel-shaded 2D animation, high contrast clean lines, crisp classroom environment. Aspect ratio: 16:9. "
            "Negative prompt: NO 3D CGI, NO PHOTOREALISTIC HUMAN FACE, NO BLURRY FRAMES, NO TEXT WATERMARKS."
        )
    },
    {
        "id": 6,
        "name": "Cảnh 6: Dòng chữ kết",
        "duration": 4.9,
        "prompt": (
            "Cinematic 2D animated stickman video shot in modern anime-stickman style. "
            "Setting: Clean minimalist classroom desk with golden afternoon sunlight, open mathematics notebook, thoughtful philosophical aesthetic. "
            "Camera movement: Static elegant macro shot. "
            "Visual style: Vibrant cel-shaded 2D animation, high contrast clean lines, crisp classroom environment. Aspect ratio: 16:9. "
            "Negative prompt: NO 3D CGI, NO PHOTOREALISTIC HUMAN FACE, NO BLURRY FRAMES, NO TEXT WATERMARKS."
        )
    }
]

def check_gemini_api_key():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("=" * 70)
        print("❌ LỖI: Chưa tìm thấy biến môi trường GEMINI_API_KEY!")
        print("👉 Hướng dẫn lấy và thiết lập API Key:")
        print("   1. Truy cập https://aistudio.google.com/app/apikey để tạo khóa API miễn phí.")
        print("   2. Mở PowerShell và gõ lệnh sau:")
        print("      $env:GEMINI_API_KEY = \"AIzaSy...\"")
        print("   3. Sau đó chạy lại: py -3.11 generate_veo_pipeline.py")
        print("=" * 70)
        sys.exit(1)
    return api_key

def generate_scene_clip(client, scene, model="veo-2.0-generate-001"):
    scene_id = scene["id"]
    out_file = CLIPS_DIR / f"scene_{scene_id}.mp4"

    if out_file.exists() and out_file.stat().st_size > 100000:
        print(f"⏩ [Cảnh {scene_id}] Đã có sẵn clip: {out_file.name} ({out_file.stat().st_size / 1024:.1f} KB), bỏ qua tạo lại.")
        return out_file

    print(f"\n🚀 [Cảnh {scene_id}/6] Đang gửi prompt lên Google Veo ({model})...")
    print(f"   Tên cảnh: {scene['name']}")
    print(f"   Thời lượng mục tiêu: {scene['duration']}s")

    from google.genai import types
    config = types.GenerateVideosConfig(
        aspect_ratio="16:9",
        duration_seconds=5,
        fps=24,
        person_generation="ALLOW_ALL"
    )

    operation = client.models.generate_videos(
        model=model,
        prompt=scene["prompt"],
        config=config
    )
    print(f"   ⏳ Đang render trên cụm GPU của Google (Operation ID: {operation.name})...")

    t0 = time.time()
    while not operation.done:
        elapsed = int(time.time() - t0)
        print(f"   ... đang xử lý: {elapsed}s trôi qua (kiểm tra lại sau 10s)", end="\r")
        time.sleep(10)
        operation = client.operations.get(operation)

    print(f"\n   ✔ Render xong trong {time.time()-t0:.1f}s!")

    if operation.error:
        print(f"   ❌ Veo API trả về lỗi: {operation.error}")
        return None

    # Tải video bytes về file
    generated = operation.response.generated_videos[0]
    if hasattr(generated.video, "video_bytes") and generated.video.video_bytes:
        out_file.write_bytes(generated.video.video_bytes)
    elif hasattr(generated.video, "uri") and generated.video.uri:
        client.files.download(file=generated.video, output_path=str(out_file))

    print(f"   💾 Đã lưu clip: {out_file} ({out_file.stat().st_size / 1024:.1f} KB)")
    return out_file

def assemble_final_video():
    print("\n" + "=" * 70)
    print("🎬 ĐANG RÁP BẢN PHIM HOÀN CHỈNH BẰNG FFMPEG...")
    print("=" * 70)

    voice_wav = PROJ_DIR / "voice.wav"
    output_film = OUTPUT_DIR / "veo_film.mp4"

    # Tạo file danh sách clip để FFmpeg concat
    concat_list = PROJ_DIR / "concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for s in SCENES:
            clip_path = CLIPS_DIR / f"scene_{s['id']}.mp4"
            if clip_path.exists():
                f.write(f"file '{clip_path.resolve().as_posix()}'\n")

    # Lệnh ghép video clips + audio voice.wav
    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-i", str(voice_wav),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(output_film)
    ]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode == 0:
        print(f"\n🎉 HOÀN THÀNH PHIM VEO THÀNH PHẨM!")
        print(f"📹 Đường dẫn file: {output_film}")
    else:
        print(f"❌ FFmpeg báo lỗi: {res.stderr.decode('utf-8', errors='ignore')[:300]}")

def main():
    api_key = check_gemini_api_key()
    from google import genai
    client = genai.Client(api_key=api_key)

    print("=" * 70)
    print("🌟 BẮT ĐẦU QUY TRÌNH TẠO PHIM GOOGLE VEO TỰ ĐỘNG (100% API)")
    print("=" * 70)

    for scene in SCENES:
        clip = generate_scene_clip(client, scene)
        if not clip:
            print(f"⚠ Cảnh {scene['id']} chưa tải được clip, dừng tiến trình.")
            return

    assemble_final_video()

if __name__ == "__main__":
    main()
