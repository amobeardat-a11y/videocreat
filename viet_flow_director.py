#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Flow (Veo) + Viet TTS Director
Quy trình sản xuất video Model Engine (Mode A):
1. Phân cảnh & Tạo Prompt chuẩn Google Flow (Veo 3) theo các phong cách A1 - A7.
2. Tạo giọng đọc Tiếng Việt (VieNeu-TTS) và tính mốc thời gian phụ đề chuẩn xác.
3. Hậu kỳ tự động: Ghép các clip từ Google Flow, lồng tiếng, add phụ đề tiếng Việt và xuất video MP4.
"""

import os
import sys
import json
import time
import shutil
import argparse
import subprocess
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parent
REPO_DIR = WORKSPACE / "stickman-video-director"
SKILL_DIR = REPO_DIR / "skills" / "directing-stickman-videos"
FONTS_DIR = SKILL_DIR / "assets" / "fonts"

# Cấu hình phong cách Model Engine (A1 - A7) chuẩn cho Google Flow / Veo
STYLE_ANCHORS = {
    "A1": {
        "name": "Classic Minimalist (Trắng Đen Tối Giản)",
        "character": "A minimalist 2D animated stick figure with a clean hollow circle head, simple uniform black stick limbs, and fluid expressive motions. High contrast minimalist aesthetic.",
        "environment": "Digitally pure white canvas background, flat 2D studio space, no textures, no gradients.",
        "accents": "Vibrant saturated neon accents (cyan, bright red, energetic yellow) appearing dynamically on conceptual props and graphical arrows.",
        "negative": "NO 3D DEPTH, NO REALISTIC FACIAL FEATURES, NO EYES OR MOUTH, NO COMPLEX TEXTURES, NO GRADIENTS."
    },
    "A2": {
        "name": "Modern Pop Beanie Zeke (Chàng Trai Mũ Len & Công Nghệ)",
        "character": "A minimalist 2D animated stick figure wearing a bright red beanie (smooth rounded knit, no pom-pom) and a yellow t-shirt, simple black stick limbs and dark shorts. Expressive body gestures, confident posture.",
        "environment": "Bright modern white studio space with subtle light-gray perspective grid lines on the floor plane. Clean negative space.",
        "accents": "Floating glowing cyan and electric blue holographic glass UI cards, interactive data graphs, luminous light particles.",
        "negative": "NO DETAILED EYES, NO PHOTOREALISTIC FACE, NO POM-POM ON BEANIE, NO CIRCUIT BOARD TEXTURES, NO SCI-FI WALL PANELS."
    },
    "A4": {
        "name": "Cozy Storytelling (Hoạt Hình Đời Thường Ấm Áp)",
        "character": "A minimalist expressive white-filled character with clean dark stick limbs, rounded friendly head, natural relatable gestures.",
        "environment": "Warm, charming 2D cartoon environment: cozy cafe, bookshop street corner, sunny apartment interior with warm ambient sunlight and soft pastel tones.",
        "accents": "Gentle steaming coffee cup, warm paper notes, soft golden lamplight.",
        "negative": "NO PHOTOREALISTIC 3D RENDERING, NO CREEPY UNCANNY DETAILS, NO HARSH NEON LIGHTING."
    },
    "A6": {
        "name": "Amber Noir (Điện Ảnh Ánh Vàng & Bóng Đổ)",
        "character": "A stylized stickman wearing a vibrant orange hoodie with the hood up, clean silhouette, cinematic presence, expressive movement.",
        "environment": "Moody nocturnal city street, rain-slicked pavement reflecting warm amber street lamps, deep dramatic shadows, high contrast cinematic film lighting.",
        "accents": "Glowing orange reflections, warm lantern light, mist and cinematic volumetric haze.",
        "negative": "NO FLAT 2D CARTOON LOOK, NO DAYLIGHT, NO BRIGHT PLASTIC COLORS, NO REALISTIC HUMAN FACE."
    },
    "A7": {
        "name": "Rubber Hose Animation (Hoạt Hình Cổ Điển Thập Niên 1930)",
        "character": "Classic 1930s rubber hose cartoon stickman, pie eyes, white gloves with three black darts on back, curved flexible limbs with no elbows or knees, bouncing rhythmically.",
        "environment": "Vintage 1930s ink-and-paint cartoon scenery, hand-drawn paper grain, subtle film flicker, retro vignette.",
        "accents": "Vintage musical notes, classic cartoon smoke puffs, jaunty rhythmic walk cycle.",
        "negative": "NO MODERN 3D CGI, NO RIGID GEOMETRY, NO REALISTIC ANATOMY, NO DIGITAL GLOW."
    }
}

def generate_voice_and_captions(sentences, voice="Trúc Ly", output_wav="voice.wav", pause=0.4):
    """Tổng hợp giọng đọc tiếng Việt và sinh mốc phụ đề chuẩn."""
    import numpy as np
    import soundfile as sf
    from vieneu import Vieneu

    print(f"[*] Đang tải giọng đọc VieNeu: '{voice}'...")
    tts = Vieneu()
    sr = tts.sample_rate
    silence = np.zeros(int(sr * pause), dtype=np.float32)

    all_audio = []
    cues = []
    curr = 0.2

    for idx, txt in enumerate(sentences, 1):
        clean = txt.strip()
        if not clean:
            continue
        audio = tts.infer(text=clean, voice=voice)
        dur = len(audio) / sr
        end = curr + dur
        cues.append({
            "index": idx,
            "text": clean,
            "start": round(curr, 3),
            "end": round(end, 3),
            "duration": round(dur, 3)
        })
        all_audio.append(audio)
        all_audio.append(silence)
        print(f"   [{idx}/{len(sentences)}] ({dur:.2f}s): {clean}")
        curr = end + pause

    full_audio = np.concatenate(all_audio) if all_audio else np.zeros(sr, dtype=np.float32)
    sf.write(output_wav, full_audio, sr)
    total_len = len(full_audio) / sr
    return cues, total_len

def create_flow_project(project_dir, script_sentences, style="A2", voice="Anh Khôi", ratio="16:9"):
    """Tạo kịch bản, prompt Google Flow và voice tiếng Việt."""
    proj = Path(project_dir).resolve()
    proj.mkdir(parents=True, exist_ok=True)
    clips_dir = proj / "clips"
    clips_dir.mkdir(exist_ok=True)

    style_cfg = STYLE_ANCHORS.get(style, STYLE_ANCHORS["A2"])
    voice_wav = proj / "voice.wav"

    print("=" * 60)
    print(f"🎬 KHỞI TẠO DỰ ÁN GOOGLE FLOW (VEO 3) + VIET TTS")
    print(f"• Phong cách: {style} - {style_cfg['name']}")
    print(f"• Tỉ lệ: {ratio} | Giọng đọc: {voice}")
    print("=" * 60)

    # 1. Sinh Voiceover Tiếng Việt
    cues, total_dur = generate_voice_and_captions(script_sentences, voice=voice, output_wav=str(voice_wav))

    # 2. Xây dựng Prompts chi tiết cho Google Flow
    scenes = []
    for c in cues:
        idx = c["index"]
        txt = c["text"]
        target_seconds = round(c["duration"] + 0.5, 1)  # Kéo dài thêm 0.5s để dễ chuyển cảnh
        
        # Tạo mô tả hành động điện ảnh ăn khớp với lời thoại
        prompt_en = (
            f"Cinematic continuous video shot. {style_cfg['character']} "
            f"The scene takes place in: {style_cfg['environment']}. "
            f"Action beat: Character dynamically engages with the concept of '{txt}', "
            f"interacting with {style_cfg['accents']}. "
            f"Dynamic camera: Subtle push-in camera tracking movement, fluid natural pacing. "
            f"Aspect ratio: {ratio}. Negative prompt: {style_cfg['negative']} NO TEXT ON SCREEN, NO WATERMARKS."
        )

        scene = {
            "scene_number": idx,
            "narration_vi": txt,
            "start_time": c["start"],
            "end_time": c["end"],
            "target_duration_seconds": target_seconds,
            "expected_clip_filename": f"scene_{idx}.mp4",
            "prompt_for_google_flow": prompt_en
        }
        scenes.append(scene)

    # 3. Tạo file SRT phụ đề tiếng Việt
    srt_file = proj / "subtitles.srt"
    with open(srt_file, "w", encoding="utf-8") as f:
        for c in cues:
            s_min, s_sec = divmod(c["start"], 60)
            s_hr, s_min = divmod(s_min, 60)
            s_ms = int((c["start"] - int(c["start"])) * 1000)

            e_min, e_sec = divmod(c["end"], 60)
            e_hr, e_min = divmod(e_min, 60)
            e_ms = int((c["end"] - int(c["end"])) * 1000)

            f.write(f"{c['index']}\n")
            f.write(f"{int(s_hr):02d}:{int(s_min):02d}:{int(s_sec):02d},{s_ms:03d} --> {int(e_hr):02d}:{int(e_min):02d}:{int(e_sec):02d},{e_ms:03d}\n")
            f.write(f"{c['text']}\n\n")

    # 4. Ghi cấu hình project_flow.json
    manifest = {
        "project_name": proj.name,
        "style": style,
        "style_info": style_cfg,
        "ratio": ratio,
        "voice": voice,
        "total_duration": total_dur,
        "voice_audio": "voice.wav",
        "subtitles": "subtitles.srt",
        "scenes": scenes
    }

    manifest_path = proj / "project_flow.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    # 5. Tạo file hướng dẫn và copy prompt nhanh FLOW_PROMPTS.md
    md_path = proj / "FLOW_PROMPTS.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# 🎬 BỘ PROMPTS GOOGLE FLOW (VEO 3) - DỰ ÁN: {proj.name}\n\n")
        f.write(f"- **Phong cách:** {style} ({style_cfg['name']})\n")
        f.write(f"- **Tỉ lệ khung hình:** `{ratio}`\n")
        f.write(f"- **Tổng thời lượng kịch bản:** ~{total_dur:.1f} giây\n")
        f.write(f"- **Giọng đọc tiếng Việt:** `{voice}`\n\n")
        f.write("## Hướng dẫn các bước thực hiện:\n")
        f.write("1. Truy cập [Google Flow](https://flow.google.com/) và đăng nhập tài khoản Google.\n")
        f.write("2. Lần lượt copy từng **Prompt** bên dưới vào Google Flow để sinh video cho từng cảnh.\n")
        f.write(f"3. Tải các video đã sinh về và đặt tên tương ứng vào thư mục: `{clips_dir}`:\n")
        for s in scenes:
            f.write(f"   - Cảnh {s['scene_number']} đặt tên là: `{s['expected_clip_filename']}`\n")
        f.write(f"4. Chạy lệnh hậu kỳ tự động:\n")
        f.write(f"   ```powershell\n   py -3.11 viet_flow_director.py assemble --project-dir \"{proj}\"\n   ```\n\n")
        f.write("---\n\n")

        for s in scenes:
            f.write(f"### 📍 CẢNH {s['scene_number']} (~{s['target_duration_seconds']}s)\n")
            f.write(f"**Lời thoại tiếng Việt:** *\"{s['narration_vi']}\"*\n\n")
            f.write(f"**Tên file video cần lưu:** `{s['expected_clip_filename']}`\n\n")
            f.write("**Prompt copy vào Google Flow:**\n")
            f.write("```text\n")
            f.write(f"{s['prompt_for_google_flow']}\n")
            f.write("```\n\n")

    print(f"\n[✔] ĐÃ TẠO XONG BỘ PROMPTS VÀ CẤU HÌNH DỰ ÁN!")
    print(f"👉 File danh sách Prompt: {md_path}")
    print(f"👉 File âm thanh lời bình: {voice_wav}")
    print(f"👉 File phụ đề tiếng Việt: {srt_file}")
    print(f"👉 Thư mục chứa clip Veo: {clips_dir}")
    return proj

def assemble_flow_video(project_dir, font_path=None):
    """
    Ráp các video clips tạo từ Google Flow cùng lời bình VietTTS và phụ đề.
    """
    proj = Path(project_dir).resolve()
    manifest_path = proj / "project_flow.json"
    if not manifest_path.exists():
        print(f"❌ Không tìm thấy file {manifest_path}")
        return None

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    clips_dir = proj / "clips"
    scenes = manifest["scenes"]
    missing = []
    available_clips = []

    for s in scenes:
        clip_file = clips_dir / s["expected_clip_filename"]
        if not clip_file.exists():
            missing.append(s["expected_clip_filename"])
        else:
            available_clips.append(str(clip_file))

    if missing:
        print(f"⚠️ Chưa đủ clips để dựng video hoàn chỉnh. Đang thiếu:")
        for m in missing:
            print(f"   - {m}")
        print(f"Vui lòng thả các file trên vào thư mục: {clips_dir}")
        return None

    # Tạo file danh sách nối clips cho FFmpeg
    concat_txt = proj / "concat_list.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for c in available_clips:
            clean_p = c.replace("\\", "/")
            f.write(f"file '{clean_p}'\n")

    temp_video = proj / "temp_stitched.mp4"
    final_output = proj / "final_flow_video.mp4"
    voice_wav = proj / manifest["voice_audio"]
    srt_file = proj / manifest["subtitles"]

    # 1. Nối các video clips
    print("[*] Đang ghép nối các video clips từ Veo/Flow...")
    concat_cmd = [
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", "concat_list.txt",
        "-c", "copy",
        "temp_stitched.mp4"
    ]
    subprocess.run(concat_cmd, check=True, cwd=str(proj))

    # 2. Lồng tiếng Việt & Đốt phụ đề tiếng Việt bằng FFmpeg
    print("[*] Đang lồng tiếng Việt và gắn phụ đề...")
    sub_filter = "subtitles=subtitles.srt:force_style='FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=3,Outline=2,Shadow=1,Alignment=2,MarginV=30'"

    merge_cmd = [
        "ffmpeg", "-y",
        "-i", "temp_stitched.mp4",
        "-i", manifest["voice_audio"],
        "-vf", sub_filter,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v:0", "-map", "1:a:0",
        "-shortest",
        "final_flow_video.mp4"
    ]
    subprocess.run(merge_cmd, check=True, cwd=str(proj))

    temp_video = proj / "temp_stitched.mp4"
    if temp_video.exists():
        temp_video.unlink()

    print("=" * 60)
    print(f"🎉 XUẤT VIDEO HOÀN CHỈNH THÀNH CÔNG!")
    print(f"📹 Đường dẫn: {final_output}")
    print("=" * 60)
    return final_output

def main():
    parser = argparse.ArgumentParser(description="Google Flow (Veo) & Viet TTS Director")
    subparsers = parser.add_subparsers(dest="command")

    # Command: plan
    plan_parser = subparsers.add_parser("plan", help="Lên kịch bản, xuất Prompts chuẩn Veo và sinh voice tiếng Việt")
    plan_parser.add_argument("--project-dir", type=str, default="veo_project", help="Thư mục dự án")
    plan_parser.add_argument("--script", type=str, help="Văn bản hoặc file kịch bản tiếng Việt")
    plan_parser.add_argument("--style", type=str, default="A2", choices=["A1", "A2", "A4", "A6", "A7"], help="Phong cách Model Engine (A1..A7)")
    plan_parser.add_argument("--voice", type=str, default="Anh Khôi", help="Giọng đọc tiếng Việt (Anh Khôi, Trúc Ly, Adam bựa...)")
    plan_parser.add_argument("--ratio", type=str, default="16:9", choices=["16:9", "9:16"], help="Tỉ lệ video (16:9 hoặc 9:16)")

    # Command: assemble
    assemble_parser = subparsers.add_parser("assemble", help="Ghép clips từ Google Flow với voice và phụ đề thành video hoàn chỉnh")
    assemble_parser.add_argument("--project-dir", type=str, required=True, help="Thư mục dự án đã chứa các clips")

    args = parser.parse_args()

    if args.command == "plan":
        if args.script and os.path.isfile(args.script):
            with open(args.script, "r", encoding="utf-8") as f:
                content = f.read()
            sentences = [s.strip() for s in content.replace("\n", ".").split(".") if s.strip()]
        elif args.script:
            sentences = [s.strip() for s in args.script.split(".") if s.strip()]
        else:
            sentences = [
                "Chào các bạn, đây là video tạo bằng Google Veo kết hợp giọng đọc tiếng Việt.",
                "Mô hình AI Veo mang lại chuyển động mượt mà và ánh sáng điện ảnh chuyên nghiệp.",
                "Kịch bản và chuyển động được đồng bộ chuẩn xác với phụ đề tiếng Việt.",
                "Bây giờ bạn có thể sản xuất video chất lượng cao mà không tốn công biên tập!"
            ]
        create_flow_project(args.project_dir, sentences, style=args.style, voice=args.voice, ratio=args.ratio)

    elif args.command == "assemble":
        assemble_flow_video(args.project_dir)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
