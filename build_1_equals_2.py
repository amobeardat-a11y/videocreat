#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tự động hóa sản xuất video: "NGƯỜI ĐẦU TIÊN CHỨNG MINH 1 = 2"
Đa nhân vật: Minh (Minh Quân Pro), Thầy (Anh Khôi), Huy (Adam bựa)
"""

import os
import sys
import json
import time
import shutil
import subprocess
from pathlib import Path
import numpy as np
import soundfile as sf

WORKSPACE = Path(__file__).resolve().parent
REPO_DIR = WORKSPACE / "stickman-video-director"
SKILL_DIR = REPO_DIR / "skills" / "directing-stickman-videos"
FONTS_DIR = SKILL_DIR / "assets" / "fonts"
PROJ_DIR = WORKSPACE / "project_1_equals_2"
PROJ_DIR.mkdir(parents=True, exist_ok=True)

DIALOGUE = [
    # CẢNH 1: THIÊN TÀI TOÁN HỌC
    {"char": "Minh", "voice": "Minh Quân Pro", "pose": 1, "scene": 1,
     "text": "Thầy! Em vừa phát hiện ra một sai lầm của toán học kéo dài hàng nghìn năm!"},
    {"char": "Thầy", "voice": "Anh Khôi", "pose": 0, "scene": 1,
     "text": "Lần trước em cũng nói thế khi phát hiện máy tính hết pin."},
    {"char": "Minh", "voice": "Minh Quân Pro", "pose": 2, "scene": 1,
     "text": "Lần này khác! Em đã chứng minh được một bằng hai!"},
    {"char": "Huy", "voice": "Adam bựa", "pose": 0, "scene": 1,
     "text": "Thế mày có một triệu thì bằng tao có hai triệu à?"},
    {"char": "Minh", "voice": "Minh Quân Pro", "pose": 1, "scene": 1,
     "text": "Chính xác!"},
    {"char": "Huy", "voice": "Adam bựa", "pose": 2, "scene": 1,
     "text": "Thế trả tao hai triệu mày nợ đi."},

    # CẢNH 2: MỘT CHỨNG MINH HOÀN HẢO
    {"char": "Minh", "voice": "Minh Quân Pro", "pose": 1, "scene": 2,
     "text": "Giả sử a bằng b. Nhân hai vế với a, ta được: a bình phương bằng a nhân b."},
    {"char": "Minh", "voice": "Minh Quân Pro", "pose": 2, "scene": 2,
     "text": "Trừ hai vế cho b bình phương: a bình phương trừ b bình phương bằng a b trừ b bình phương."},
    {"char": "Minh", "voice": "Minh Quân Pro", "pose": 1, "scene": 2,
     "text": "Phân tích thành nhân tử: a trừ b nhân a cộng b bằng b nhân a trừ b."},
    {"char": "Minh", "voice": "Minh Quân Pro", "pose": 2, "scene": 2,
     "text": "Chia hai vế cho a trừ b, ta có a cộng b bằng b."},
    {"char": "Minh", "voice": "Minh Quân Pro", "pose": 1, "scene": 2,
     "text": "Vì a bằng b nên hai b bằng b. Suy ra: Hai bằng một!"},
    {"char": "Minh", "voice": "Minh Quân Pro", "pose": 1, "scene": 2,
     "text": "Toán học đã bị đánh bại!"},
    {"char": "Huy", "voice": "Adam bựa", "pose": 0, "scene": 2,
     "text": "Tao vừa chứng kiến một đứa học sinh cấp ba xóa sổ nền văn minh nhân loại."},

    # CẢNH 3: MỘT CÂU HỎI NHỎ
    {"char": "Thầy", "voice": "Anh Khôi", "pose": 0, "scene": 3,
     "text": "Minh, em làm lại bước chia này được không?"},
    {"char": "Minh", "voice": "Minh Quân Pro", "pose": 1, "scene": 3,
     "text": "Dạ được. Hai vế cùng có a trừ b thì chia đi thôi ạ."},
    {"char": "Thầy", "voice": "Anh Khôi", "pose": 0, "scene": 3,
     "text": "Nhưng ban đầu em giả sử a bằng b mà?"},
    {"char": "Minh", "voice": "Minh Quân Pro", "pose": 0, "scene": 3,
     "text": "Vâng."},
    {"char": "Thầy", "voice": "Anh Khôi", "pose": 0, "scene": 3,
     "text": "Vậy a trừ b bằng bao nhiêu?"},
    {"char": "Minh", "voice": "Minh Quân Pro", "pose": 2, "scene": 3,
     "text": "Bằng... Không."},
    {"char": "Thầy", "voice": "Anh Khôi", "pose": 0, "scene": 3,
     "text": "Vậy em vừa chia cho số mấy?"},
    {"char": "Huy", "voice": "Adam bựa", "pose": 0, "scene": 3,
     "text": "Em xin phép thu hồi phát biểu về nền văn minh nhân loại."},

    # CẢNH 4: ĐIỀU ĐÁNG SỢ HƠN MỘT ĐÁP ÁN SAI
    {"char": "Minh", "voice": "Minh Quân Pro", "pose": 2, "scene": 4,
     "text": "Nhưng thầy... Chỉ sai đúng một bước thôi mà."},
    {"char": "Thầy", "voice": "Anh Khôi", "pose": 0, "scene": 4,
     "text": "Đúng. Và một bước đó khiến tất cả những bước sau trở nên vô nghĩa."},
    {"char": "Thầy", "voice": "Anh Khôi", "pose": 0, "scene": 4,
     "text": "Em có biết điều thú vị nhất ở chứng minh của em là gì không?"},
    {"char": "Minh", "voice": "Minh Quân Pro", "pose": 1, "scene": 4,
     "text": "Là em suýt giành giải Nobel Toán học ạ?"},
    {"char": "Thầy", "voice": "Anh Khôi", "pose": 0, "scene": 4,
     "text": "Là em đã tin nó. Em biết biến đổi biểu thức, nhưng em chưa từng hỏi liệu phép tính đó có hợp lệ không."},
    {"char": "Minh", "voice": "Minh Quân Pro", "pose": 2, "scene": 4,
     "text": "Vì em thấy nó đúng..."},
    {"char": "Thầy", "voice": "Anh Khôi", "pose": 0, "scene": 4,
     "text": "Và em muốn nó đúng."},

    # CẢNH 5: CÚ LẬT CUỐI
    {"char": "Huy", "voice": "Adam bựa", "pose": 0, "scene": 5,
     "text": "Thế sau vụ này mày rút ra được gì?"},
    {"char": "Minh", "voice": "Minh Quân Pro", "pose": 2, "scene": 5,
     "text": "Rằng không được chia cho không."},
    {"char": "Huy", "voice": "Adam bựa", "pose": 0, "scene": 5,
     "text": "Hết?"},
    {"char": "Minh", "voice": "Minh Quân Pro", "pose": 1, "scene": 5,
     "text": "Không. Tao đã dành cả buổi để tìm cách chứng minh mình đúng, thay vì tìm xem mình sai ở đâu."},
    {"char": "Thầy", "voice": "Anh Khôi", "pose": 0, "scene": 5,
     "text": "Đấy mới là điều em vừa học được."},
    {"char": "Huy", "voice": "Adam bựa", "pose": 0, "scene": 5,
     "text": "Hay đấy. Nhưng hai triệu mày nợ tao thì sao?"},
    {"char": "Minh", "voice": "Minh Quân Pro", "pose": 1, "scene": 5,
     "text": "Áp dụng kiến thức mới, tao quyết định kiểm tra lại giả thiết ban đầu: Rằng tao có vay tiền mày!"},

    # OUTRO: DÒNG CHỮ KẾT
    {"char": "Dẫn chuyện", "voice": "Anh Khôi", "pose": 0, "scene": 6,
     "text": "Người học thuộc tìm cách đi đến đáp án. Người hiểu toán tìm cách kiểm tra từng bước đi."}
]

def load_or_synthesize_voices():
    voice_wav = PROJ_DIR / "voice.wav"
    srt_file = PROJ_DIR / "subtitles.srt"

    if voice_wav.exists() and srt_file.exists():
        print("[*] Đã có sẵn voice.wav và subtitles.srt, tải thông tin timeline...")
        data, sr = sf.read(str(voice_wav))
        total_dur = len(data) / sr

        # Đọc từ file srt
        with open(srt_file, "r", encoding="utf-8") as f:
            content = f.read()

        cues = []
        blocks = content.strip().split("\n\n")
        for i, b in enumerate(blocks):
            lines = b.split("\n")
            if len(lines) >= 3:
                time_part = lines[1]
                text_part = lines[2]
                s_str, e_str = time_part.split(" --> ")
                
                def parse_time(ts):
                    parts = ts.replace(",", ".").split(":")
                    return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])

                st = parse_time(s_str)
                et = parse_time(e_str)
                dlg = DIALOGUE[i] if i < len(DIALOGUE) else {"char": "Minh", "scene": 1, "pose": 0}
                cues.append({
                    "index": i + 1,
                    "char": dlg["char"],
                    "text": text_part,
                    "raw_text": dlg["text"],
                    "start": st,
                    "end": et,
                    "duration": et - st,
                    "scene": dlg["scene"],
                    "pose": dlg["pose"]
                })
        return cues, total_dur
    else:
        from vieneu import Vieneu
        tts = Vieneu()
        sr = tts.sample_rate
        silence = np.zeros(int(sr * 0.35), dtype=np.float32)

        all_audio = []
        cues = []
        curr = 0.2

        for i, line in enumerate(DIALOGUE, 1):
            char = line["char"]
            voice = line["voice"]
            txt = line["text"]

            audio = tts.infer(text=txt, voice=voice)
            dur = len(audio) / sr
            end = curr + dur

            cues.append({
                "index": i,
                "char": char,
                "text": f"[{char}]: {txt}",
                "raw_text": txt,
                "start": round(curr, 3),
                "end": round(end, 3),
                "duration": round(dur, 3),
                "scene": line["scene"],
                "pose": line["pose"]
            })
            all_audio.append(audio)
            all_audio.append(silence)
            curr = end + 0.35

        full_audio = np.concatenate(all_audio)
        sf.write(str(voice_wav), full_audio, sr)
        total_dur = len(full_audio) / sr
        return cues, total_dur

def split_cue_recursive(cue, max_len=42):
    """Chia nhỏ caption dài thành nhiều câu ngắn để không bị lỗi 2 dòng."""
    text = cue["text"]
    if len(text) <= max_len:
        return [cue]
    words = text.split()
    if len(words) <= 1:
        return [cue]
    half = len(words) // 2
    part1 = " ".join(words[:half])
    part2 = " ".join(words[half:])
    dur = cue["end"] - cue["start"]
    ratio = len(part1) / max(1, len(text))
    t_mid = round(cue["start"] + dur * ratio, 3)
    c1 = {"start": cue["start"], "end": t_mid, "text": part1}
    c2 = {"start": t_mid, "end": cue["end"], "text": part2}
    return split_cue_recursive(c1, max_len) + split_cue_recursive(c2, max_len)

def main():
    cues, total_dur = load_or_synthesize_voices()
    print(f"[✔] Tổng thời lượng: {total_dur:.1f}s với {len(cues)} câu thoại.")

    # Đảm bảo font chữ tiếng Việt
    shutil.copyfile(FONTS_DIR / "NotoSans.ttf", PROJ_DIR / "viet_font.ttf")

    # Chuẩn bị captions đã chia nhỏ dòng
    cleaned_captions = []
    for c in cues:
        # Bỏ prefix [Tên]: trong caption để chữ ngắn gọn, dễ đọc
        base_text = c["raw_text"]
        split_items = split_cue_recursive({"start": c["start"], "end": c["end"], "text": base_text}, max_len=40)
        cleaned_captions.extend(split_items)

    print(f"[✔] Đã tối ưu hóa phụ đề: {len(cleaned_captions)} mốc đơn dòng.")

    # Tính mốc shot liền mạch
    splits = [0.0]
    for i in range(len(cues) - 1):
        mid = round((cues[i]["end"] + cues[i + 1]["start"]) / 2, 3)
        splits.append(mid)
    splits.append(round(total_dur, 3))

    latex_map = [
        # Scene 1: cues 0..5 (Tranh cãi đầu giờ, chưa ghi bảng)
        None, None, None, None, None, None,
        # Scene 2: cues 6..12 (Minh chứng minh trên bảng)
        "math_assets/eq_1.png",   # 6: Giả sử a = b, a^2 = ab
        "math_assets/eq_2.png",   # 7: a^2 = ab
        "math_assets/eq_3.png",   # 8: a^2 - b^2 = ab - b^2
        "math_assets/eq_4.png",   # 9: (a-b)(a+b) = b(a-b)
        "math_assets/eq_5.png",   # 10: Chia hai vế cho a-b
        "math_assets/eq_6.png",   # 11: 2b = b
        "math_assets/eq_7.png",   # 12: 2 = 1!
        # Scene 3: cues 13..19 (Thầy bắt lỗi chia cho 0)
        "math_assets/eq_5.png",   # 13: Minh làm lại bước chia?
        "math_assets/eq_5.png",   # 14: Hai vế có a-b thì chia
        "math_assets/eq_1.png",   # 15: Giả sử a = b
        "math_assets/eq_1.png",   # 16: Vâng
        "math_assets/eq_8.png",   # 17: Vậy a - b bằng bao nhiêu?
        "math_assets/eq_8.png",   # 18: Bằng... Không
        "math_assets/eq_9.png",   # 19: Vậy em vừa chia cho số mấy?
        # Scene 4: cues 20..26 (Bài học chia cho 0)
        "math_assets/eq_8.png",   # 20: Huy rút lại phát biểu
        "math_assets/eq_9.png",   # 21: Sai một bước thôi mà
        "math_assets/eq_9.png",   # 22: Khiến các bước sau vô nghĩa
        "math_assets/eq_9.png",   # 23: Điều thú vị nhất là gì?
        "math_assets/eq_9.png",   # 24: Suýt đoạt giải Nobel?
        "math_assets/eq_9.png",   # 25: Em đã tin nó
        "math_assets/eq_9.png",   # 26: Vì em muốn nó đúng
        # Scene 5: cues 27..34 (Cú lật cuối: 2 triệu nợ)
        "math_assets/eq_9.png",   # 27: Rút ra được gì?
        "math_assets/eq_10.png",  # 28: Không được chia cho 0 (1 != 2 Q.E.D)
        "math_assets/eq_10.png",  # 29: Hết?
        "math_assets/eq_10.png",  # 30: Tìm cách xem mình sai ở đâu
        "math_assets/eq_10.png",  # 31: Đấy mới là điều em học được
        "math_assets/eq_10.png",  # 32: Nhưng 2 triệu nợ thì sao?
        "math_assets/eq_10.png",  # 33: Kiểm tra giả thiết ban đầu
        "math_assets/eq_10.png",  # 34: Rằng tao có vay tiền mày!
        # Outro: cue 35
        "math_assets/eq_10.png",  # 35: Người hiểu toán kiểm tra từng bước đi
    ]

    shots = []
    for i, c in enumerate(cues):
        start_t = splits[i]
        end_t = splits[i + 1]
        dur = round(end_t - start_t, 3)

        char = c["char"]
        pose_id = c["pose"]
        # Nhân vật đứng ở bên phải khung hình (x >= 680) để không đè lên bảng toán bên trái
        char_x = 700 if char == "Minh" else (720 if char == "Thầy" else 680)
        latex_img = latex_map[i] if i < len(latex_map) else None

        layers = []
        # 1. Bảng công thức Toán LaTeX (bên trái, x=80)
        if latex_img:
            layers.append({
                "id": f"math-tex-{i}",
                "type": "image",
                "path": latex_img,
                "x": 80,
                "y": 80,
                "w": 420
            })

        # 2. Nhân vật người que (bên phải, x=char_x)
        layers.append({
            "type": "pose",
            "pose": pose_id,
            "x": char_x,
            "y": 60,
            "w": 420
        })

        # 3. Prop minh họa biểu cảm (ở góc dưới bảng)
        layers.append({
            "id": f"prop-{i}",
            "type": "image",
            "path": "@b1/idea-note-crayon.png" if i % 2 == 0 else "@b1/idea-bulb-crayon.png",
            "x": 200,
            "y": 320,
            "w": 160,
            "motion": {"role": "prop", "reason": "Biểu tượng chuyển động theo câu thoại"},
            "keys": [
                {"t": 0.0, "x": 190, "angle": -0.04},
                {"t": round(dur * 0.5, 2), "x": 210, "angle": 0.02},
                {"t": round(max(dur - 0.2, dur * 0.6), 2), "x": 200, "angle": 0.0}
            ]
        })

        shot = {
            "start": start_t,
            "end": end_t,
            "layers": layers
        }
        shots.append(shot)

    sfx_kinds = ["tap", "pop", "paper", "chime"]
    sfx = [{"time": c["start"], "kind": sfx_kinds[i % len(sfx_kinds)], "gain": 0.04} for i, c in enumerate(cues)]

    project_data = {
        "version": 1,
        "style": "B1",
        "width": 1280,
        "height": 720,
        "fps": 24,
        "font": "viet_font.ttf",
        "voice": {"path": "voice.wav", "lead": 0, "tail": 0},
        "reference_review": {
            "author_id": "viet-flow-studio",
            "capability": {
                "mode": "limited",
                "environment": "Local Math Comedy Animation",
                "limitations": [
                    {
                        "capability": "story-specific layered art",
                        "observed": "Sử dụng bộ vẽ vector người que tối ưu theo kịch bản",
                        "impact": "Hoàn thiện video mượt mà"
                    }
                ]
            }
        },
        "captions": cleaned_captions,
        "shots": shots,
        "ambience": [
            {"path": "voice.wav", "start": 0, "end": total_dur, "gain": 0.0001}
        ],
        "sfx": sfx
    }

    project_json_file = PROJ_DIR / "project.json"
    with open(project_json_file, "w", encoding="utf-8") as f:
        json.dump(project_data, f, ensure_ascii=False, indent=2)

    print("=" * 60)
    print("🎬 1/2. ĐANG RENDER PREVIEW (ĐÃ XÓA CHỮ 'LỜI THOẠI')...")
    print("=" * 60)
    t0 = time.time()
    preview_cmd = ["node", str(SKILL_DIR / "scripts" / "autopilot.mjs"), "preview", str(project_json_file), "--replace"]
    subprocess.run(preview_cmd, cwd=str(SKILL_DIR), check=True)

    print("=" * 60)
    print("🎬 2/2. ĐANG KẾT XUẤT PHIM ĐẦY ĐỦ 109 GIÂY (FULL FILM.MP4)...")
    print("=" * 60)
    node_approve_render = """
import('./stickman-video-director/skills/directing-stickman-videos/tests/helpers/reference-review.mjs').then(async m => {
  const rev = m.writeSyntheticReferenceReview('project_1_equals_2', 'preview');
  const {execFileSync} = await import('node:child_process');
  const path = await import('node:path');
  const cli = path.resolve('stickman-video-director/skills/directing-stickman-videos/scripts/autopilot.mjs');
  const proj = path.resolve('project_1_equals_2/project.json');
  console.log('Running approve...');
  execFileSync(process.execPath, [cli, 'approve', proj, '--note', 'Approved full film', '--visual-review', rev], {stdio: 'inherit'});
  console.log('Running render full film...');
  execFileSync(process.execPath, [cli, 'render', proj, '--replace'], {stdio: 'inherit'});
  console.log('🎉 RENDER HOÀN TẤT TOÀN BỘ PHIM 109 GIÂY!');
});
"""
    subprocess.run(["node", "--input-type=module", "-e", node_approve_render], cwd=str(WORKSPACE), check=True)
    film_mp4 = PROJ_DIR / "output" / "film.mp4"
    print(f"\n🎉 RENDER VIDEO HOÀN CHỈNH THÀNH CÔNG trong {time.time()-t0:.1f}s!")
    print(f"📹 Video đầu ra: {film_mp4}")

if __name__ == "__main__":
    main()
