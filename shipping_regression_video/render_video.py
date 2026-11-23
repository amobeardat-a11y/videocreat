#!/usr/bin/env python3
"""Render the six-scene Vietnamese stickman dialogue as an MP4."""

from __future__ import annotations

import argparse
import bisect
import importlib.util
import json
import math
import subprocess
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1280, 720, 18
NAVY, BLUE, TEAL = "#20354b", "#426db8", "#168e8a"
ORANGE, RED, BG = "#e88942", "#d95760", "#f7f8fa"
LIGHT, PALE = "#e0ebf3", "#edf4f8"
FONT = ROOT.parent / "phan_tram_stickman_video" / "NotoSans.ttf"
MATH_FONT = ROOT.parent / "phan_tram_stickman_video" / "Nunito.ttf"
spec = importlib.util.spec_from_file_location("stickman_rig", ROOT.parent / "stickman_assets" / "stickman.py")
RIG = importlib.util.module_from_spec(spec)
spec.loader.exec_module(RIG)


@lru_cache(maxsize=32)
def font(size: int, math_font: bool = False):
    return ImageFont.truetype(str(MATH_FONT if math_font else FONT), size)


def label(draw, xy, value, size=30, fill=NAVY, anchor=None, math_font=False):
    value = value.replace("→", " > ")
    draw.text(xy, value, fill=fill, font=font(size, math_font), anchor=anchor)


def centered(draw, xy, value, size=30, fill=NAVY, math_font=False):
    label(draw, xy, value, size, fill, anchor="mm", math_font=math_font)


def card(draw, box=(605, 126, 1224, 550), fill="white"):
    x0, y0, x1, y1 = box
    draw.rounded_rectangle((x0 + 7, y0 + 8, x1 + 7, y1 + 8), radius=23, fill="#dce6ed")
    draw.rounded_rectangle(box, radius=23, fill=fill, outline="#dce6ed", width=2)


def pill(draw, box, value, color=BLUE, size=26, fg="white"):
    draw.rounded_rectangle(box, radius=14, fill=color)
    centered(draw, ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), value, size, fg)


def arrow(draw, x0, y0, x1, y1, color=BLUE, width=6):
    draw.line((x0, y0, x1, y1), fill=color, width=width)
    angle = math.atan2(y1 - y0, x1 - x0)
    points = [(x1, y1)]
    for delta in (-.55, .55):
        points.append((x1 - 15 * math.cos(angle + delta), y1 - 15 * math.sin(angle + delta)))
    draw.polygon(points, fill=color)


def draw_table(draw, emphasized=False):
    centered(draw, (915, 172), "4 ĐƠN HÀNG ĐÃ BIẾT", 29, NAVY)
    x0, x1, x2 = 675, 930, 1160
    y0 = 213
    draw.rounded_rectangle((x0, y0, x2, 483), radius=14, fill=PALE)
    draw.rounded_rectangle((x0, y0, x2, y0 + 52), radius=14, fill=BLUE)
    centered(draw, ((x0 + x1) / 2, y0 + 25), "KHOẢNG CÁCH", 23, "white")
    centered(draw, ((x1 + x2) / 2, y0 + 25), "PHÍ SHIP", 23, "white")
    for i, (km, fee) in enumerate(((1, 15), (2, 19), (3, 21), (4, 25))):
        y = 287 + i * 49
        if i % 2:
            draw.rectangle((x0, y - 23, x2, y + 24), fill="white")
        centered(draw, ((x0 + x1) / 2, y), f"{km} km", 29, NAVY)
        centered(draw, ((x1 + x2) / 2, y), f"{fee}.000đ", 29, NAVY)
    if emphasized:
        pill(draw, (770, 488, 1065, 535), "5 km → ?", ORANGE, 29)


def xy_for_point(x, y):
    return 680 + (x - 1) * 104, 473 - (y - 12) * 15


def draw_graph(draw, progress, show_line=False, bad=False, residual=False, equation=False):
    card(draw)
    centered(draw, (916, 169), "KHOẢNG CÁCH  →  PHÍ SHIP", 27, NAVY)
    draw.line((680, 473, 1150, 473), fill=NAVY, width=3)
    draw.line((680, 473, 680, 215), fill=NAVY, width=3)
    for x in range(1, 6):
        px, _ = xy_for_point(x, 12)
        label(draw, (px, 481), str(x), 20, NAVY, anchor="mt")
    for y in (15, 20, 25):
        _, py = xy_for_point(1, y)
        label(draw, (669, py), str(y), 20, NAVY, anchor="rm")
        draw.line((683, py, 1150, py), fill="#e3edf2", width=1)
    label(draw, (1070, 509), "km", 20, NAVY)
    label(draw, (625, 212), "nghìn đ", 19, NAVY)
    if show_line:
        x0, y0 = xy_for_point(1, 15.2)
        x1, y1 = xy_for_point(5, 28)
        fraction = min(1, max(0, progress * 1.8))
        draw.line((x0, y0, x0 + (x1 - x0) * fraction, y0 + (y1 - y0) * fraction),
                  fill=BLUE, width=6)
    if residual:
        px, true_y = xy_for_point(2, 19)
        _, pred_y = xy_for_point(2, 17)
        draw.line((px, true_y, px, pred_y), fill=RED, width=6)
        draw.ellipse((px - 8, pred_y - 8, px + 8, pred_y + 8), fill=ORANGE)
        pill(draw, (890, 303, 1155, 354), "DỰ ĐOÁN: 17", ORANGE, 25)
        pill(draw, (890, 363, 1155, 414), "THỰC TẾ: 19", TEAL, 25)
        centered(draw, (1019, 441), "Sai lệch = 2 nghìn", 23, RED)
    for x, y in ((1, 15), (2, 19), (3, 21), (4, 25)):
        px, py = xy_for_point(x, y)
        r = 9 + 2 * math.sin(progress * 7) ** 2
        draw.ellipse((px - r, py - r, px + r, py + r), fill=ORANGE, outline="white", width=2)
    if equation:
        pill(draw, (825, 195, 1110, 251), "ŷ = wx + b", TEAL, 37)
    if bad:
        draw.rounded_rectangle((752, 267, 1150, 420), radius=18, fill="#fff0eb", outline=RED, width=3)
        centered(draw, (950, 311), "w = 100, b = 500", 29, NAVY, True)
        centered(draw, (950, 370), "1 km → 600.000đ", 38, RED, True)


def draw_valley(draw, progress, big=False):
    card(draw)
    centered(draw, (918, 169), "GRADIENT DESCENT", 33, NAVY)
    points = []
    for x in range(665, 1172, 5):
        y = 438 - .0028 * (x - 918) ** 2
        points.append((x, y))
    draw.line(points, fill=BLUE, width=7, joint="curve")
    centered(draw, (917, 475), "MSE THẤP NHẤT", 23, TEAL)
    if big:
        stops = [(722, 333), (1053, 386), (802, 400), (1100, 345)]
        x, y = stops[min(len(stops) - 1, int(progress * len(stops)))]
        draw.line(stops[:min(len(stops), int(progress * len(stops))) + 1], fill=RED, width=3)
    else:
        x = 710 + 208 * min(1, progress * 1.2)
        y = 438 - .0028 * (x - 918) ** 2
    draw.ellipse((x - 16, y - 16, x + 16, y + 16), fill=ORANGE, outline=NAVY, width=3)
    if big:
        pill(draw, (781, 498, 1054, 538), "BƯỚC QUÁ LỚN!", RED, 21)


def draw_visual(draw, scene, mode, progress):
    card(draw)
    if scene == 0:
        if mode == "desk":
            centered(draw, (910, 177), "CỬA HÀNG ONLINE CỦA NAM", 28, NAVY)
            draw.rounded_rectangle((710, 262, 880, 413), radius=18, fill="#d8e9f1", outline=BLUE, width=4)
            draw.rectangle((695, 287, 895, 313), fill=ORANGE)
            draw.line((710, 354, 880, 354), fill=BLUE, width=4)
            draw.rectangle((920, 316, 1062, 431), fill="#dcae72", outline=NAVY, width=3)
            draw.line((920, 316, 988, 348, 1062, 316), fill=NAVY, width=3)
            label(draw, (942, 360), "SHIP?", 30, NAVY)
        elif mode in ("table", "question"):
            draw_table(draw, mode == "question")
        elif mode in ("answer", "hack", "medicine"):
            pill(draw, (717, 243, 1119, 344), "5 km → 28.000đ", TEAL, 42)
            centered(draw, (919, 409), "DỰ ĐOÁN TỪ 4 ĐƠN HÀNG", 26, NAVY)
            if mode == "hack":
                centered(draw, (919, 470), "HACK HỆ THỐNG?!", 32, RED)
            if mode == "medicine":
                centered(draw, (919, 470), "LINEAR REGRESSION", 28, BLUE)
        else:
            pill(draw, (703, 228, 855, 294), "DỮ LIỆU", BLUE, 23)
            arrow(draw, 862, 261, 925, 261)
            pill(draw, (931, 228, 1169, 294), "QUY LUẬT", TEAL, 23)
            centered(draw, (918, 393), "Tìm mối quan hệ gần đúng", 28, NAVY)
            centered(draw, (918, 450), "→ dự đoán giá chưa biết", 26, ORANGE)
    elif scene == 1:
        if mode in ("badline", "helicopter"):
            draw_graph(draw, progress, bad=True)
            if mode == "helicopter":
                draw.line((905, 224, 1045, 224), fill=NAVY, width=5)
                draw.ellipse((950, 226, 1000, 256), outline=NAVY, width=4)
                draw.line((977, 256, 977, 273), fill=NAVY, width=3)
        else:
            draw_graph(draw, progress, show_line=mode != "scatter",
                       equation=mode in ("formula", "learn"))
            if mode == "formula":
                label(draw, (733, 515), "x: khoảng cách   w: độ dốc   b: hệ số chặn", 18, NAVY)
    elif scene == 2:
        if mode in ("scatter", "residual", "loss"):
            draw_graph(draw, progress, show_line=mode != "scatter", residual=mode == "residual")
            if mode == "loss":
                pill(draw, (790, 493, 1100, 536), "LOSS = ĐỘ SAI", RED, 22)
        elif mode in ("mse", "square", "many", "minimize"):
            centered(draw, (912, 196), "MEAN SQUARED ERROR", 30, NAVY)
            pill(draw, (688, 259, 1164, 350), "MSE = 1/n · Σ(yᵢ − ŷᵢ)²", BLUE, 31)
            centered(draw, (912, 416), "Bình phương sai số từng đơn", 26, NAVY)
            centered(draw, (912, 463), "→ lấy trung bình → tìm giá trị nhỏ nhất", 23, TEAL)
        elif mode == "compare":
            centered(draw, (913, 196), "LỖI LỚN BỊ PHẠT NẶNG HƠN", 27, NAVY)
            pill(draw, (685, 268, 899, 351), "2² = 4", TEAL, 37)
            pill(draw, (926, 268, 1161, 351), "10² = 100", RED, 37)
            draw.rounded_rectangle((695, 408, 893, 435), radius=9, fill=TEAL)
            draw.rounded_rectangle((926, 408, 1160, 470), radius=9, fill=RED)
        else:
            centered(draw, (916, 248), "Ít sai nhất", 46, TEAL)
            centered(draw, (916, 330), "khác với", 30, NAVY)
            centered(draw, (916, 413), "không bao giờ sai", 41, RED)
    elif scene == 3:
        if mode in ("valley", "bigstep", "stairs"):
            draw_valley(draw, progress, big=mode != "valley")
        elif mode in ("update", "alpha"):
            centered(draw, (912, 190), "CẬP NHẬT TỪNG BƯỚC", 30, NAVY)
            pill(draw, (666, 246, 1174, 316), "w mới = w − α · ∂MSE/∂w", BLUE, 26)
            pill(draw, (666, 333, 1174, 403), "b mới = b − α · ∂MSE/∂b", TEAL, 26)
            centered(draw, (913, 466), "α = learning rate = độ lớn bước học", 25, ORANGE)
        else:
            draw_graph(draw, progress, show_line=True)
            if mode in ("fit", "slope", "intercept", "predict"):
                pill(draw, (820, 198, 1117, 260), "ŷ = 3,2x + 12", TEAL, 31)
            if mode == "predict":
                pill(draw, (830, 495, 1105, 538), "5 km = 28.000đ", ORANGE, 23)
            elif mode == "slope":
                pill(draw, (813, 495, 1113, 538), "+1 km → +3.200đ", BLUE, 23)
            elif mode == "intercept":
                pill(draw, (750, 495, 1170, 538), "b = 12 chỉ là dự đoán tại 0 km", BLUE, 19)
    elif scene == 4:
        if mode in ("phone", "shock", "rain", "rush", "missing"):
            draw.rounded_rectangle((790, 176, 1040, 480), radius=26, fill=NAVY)
            draw.rounded_rectangle((806, 195, 1024, 456), radius=17, fill="white")
            centered(draw, (914, 244), "ĐƠN GIAO 5 KM", 25, NAVY)
            centered(draw, (914, 315), "55.000đ" if mode != "phone" else "28.000đ?",
                     44, RED if mode != "phone" else TEAL)
            centered(draw, (914, 395), "TRỜI MƯA · GIỜ CAO ĐIỂM" if mode in ("rain", "rush", "missing")
                     else "PHÍ SHIP HIỂN THỊ", 19, NAVY)
            if mode in ("rain", "rush", "missing"):
                for i in range(7):
                    x = 681 + i * 68
                    y = 182 + (i % 2) * 26
                    draw.line((x, y, x - 17, y + 38), fill=BLUE, width=4)
        elif mode in ("features", "multiple"):
            centered(draw, (914, 182), "THÊM ĐẶC TRƯNG PHÙ HỢP", 28, NAVY)
            for j, (name, color) in enumerate((("KHOẢNG CÁCH", BLUE), ("THỜI TIẾT", TEAL),
                                               ("GIỜ ĐẶT", ORANGE))):
                pill(draw, (676, 224 + j * 72, 1158, 281 + j * 72), name, color, 25)
            if mode == "multiple":
                centered(draw, (912, 488), "ŷ = b + w₁x₁ + w₂x₂ + w₃x₃", 26, NAVY)
        else:
            centered(draw, (914, 209), "KIỂM TRA TRÊN DỮ LIỆU MỚI", 29, NAVY)
            draw.rounded_rectangle((693, 282, 1150, 427), radius=18, fill=PALE)
            centered(draw, (918, 326), "Dữ liệu tốt giúp dự đoán tốt hơn", 25, TEAL)
            centered(draw, (918, 389), "nhưng không bảo đảm luôn đúng", 25, RED)
    else:
        if mode == "joke":
            pill(draw, (711, 262, 1117, 357), "28.000đ?", TEAL, 40)
            centered(draw, (914, 417), "Minh im lặng...", 30, NAVY)
        else:
            centered(draw, (911, 198), "MÔ HÌNH HỌC TỪ DỮ LIỆU", 27, NAVY)
            pill(draw, (689, 255, 1170, 327), "MSE thấp chưa chắc dự đoán đúng", BLUE, 23)
            centered(draw, (912, 394), "Thiếu biến  •  Dữ liệu mới khác", 25, RED)
            centered(draw, (912, 470), "→ cần kiểm tra ngoài tập huấn luyện", 23, TEAL)


@lru_cache(maxsize=450)
def actor_sprite(pose, expression, phase_tick):
    state = RIG.motion_state(pose, phase_tick / 36, expression)
    return raster_actor_state(state)


def raster_actor_state(state):
    svg = RIG.wrap(RIG.draw(state), viewbox="140 100 220 440", width=220, height=440)
    return RIG.raster(svg, 220)


def ease(value):
    value = min(1, max(0, value))
    return value * value * (3 - 2 * value)


def position_offset(name, line):
    if line is None:
        return 0
    cue = line["visual"]
    if name == "Nam":
        return {"hack": -12, "shock": -24, "stairs": -22,
                "phone": 12, "joke": 10}.get(cue, 0)
    return {"line": 9, "formula": 9, "fit": 9, "multiple": 9}.get(cue, 0)


def actor_pose(name, line):
    if line is None:
        return "idle", "neutral"
    active = line["speaker"] == name
    cue = line["visual"]
    if name == "Nam":
        special = {"desk": ("sit", "worried"),
                   "table": ("calculate_discount", "worried"),
                   "question": ("point_side", "curious"),
                   "hack": ("surprised", "surprised"),
                   "medicine": ("confused", "confused"),
                   "badline": ("hands_on_hips", "proud"),
                   "helicopter": ("surprised", "surprised"),
                   "life": ("sigh", "sad"), "awkward": ("shrug", "confused"),
                   "stairs": ("step_back", "worried"),
                   "phone": ("reach", "excited"),
                   "shock": ("surprised", "surprised"),
                   "missing": ("shy", "embarrassed"),
                   "joke": ("point_side", "wink")}
        if active and cue in special:
            return special[cue]
        if active:
            return "talk", "talk"
        return ("listen", "curious") if line["speaker"] == "Minh" else ("idle", "neutral")
    special = {"scatter": "point_side", "line": "present_right", "formula": "explain_open",
               "learn": "think", "loss": "point_up", "residual": "point_side",
               "mse": "write_formula", "compare": "point_side", "minimize": "explain_open",
               "valley": "point_side", "update": "write_formula", "alpha": "point_up",
               "fit": "present_right", "rain": "point_up", "rush": "point_up",
               "multiple": "explain_open", "test": "point_side"}
    if active:
        return special.get(cue, "explain_open"), "talk" if cue != "life" else "skeptical"
    return "listen", "curious"


def fit_lines(draw, value, max_width, max_lines=3):
    for size in (32, 30, 28, 26, 24):
        lines, current = [], ""
        for word in value.split():
            candidate = f"{current} {word}".strip()
            if draw.textbbox((0, 0), candidate, font=font(size))[2] > max_width and current:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        if len(lines) <= max_lines:
            return lines, size
    return lines, 24


def frame_at(time, timeline, starts, scene_starts):
    scene_index = max(0, bisect.bisect_right(scene_starts, time) - 1)
    scene = timeline["scenes"][scene_index]
    li = bisect.bisect_right(starts, time) - 1
    line = timeline["lines"][li] if li >= 0 and time < timeline["lines"][li]["end"] else None
    if line is None or line["scene"] != scene_index:
        scene_lines = [x for x in timeline["lines"] if x["scene"] == scene_index]
        visual_line = next((x for x in reversed(scene_lines) if x["start"] <= time), scene_lines[0])
    else:
        visual_line = line
    mode = visual_line["visual"]
    if scene_index == 5 and mode == "end":
        image = Image.new("RGB", (W, H), NAVY)
        draw = ImageDraw.Draw(image)
        centered(draw, (640, 254), "LINEAR REGRESSION", 48, "white")
        centered(draw, (640, 333), "tìm đường thẳng phù hợp nhất với dữ liệu", 32, "#d8e8f4")
        centered(draw, (640, 403), "theo một tiêu chí sai số.", 32, "#d8e8f4")
        centered(draw, (640, 535), "55.000đ tiền ship là sự thật tuyệt đối!", 33, "#ffbc70")
        return image
    image = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(image)
    draw.ellipse((27, 169, 580, 722), fill="#e8f2f5")
    draw.line((51, 536, 566, 536), fill="#c8d9e0", width=4)
    draw.rounded_rectangle((39, 30, 1218, 91), radius=18, fill="white", outline=LIGHT, width=2)
    label(draw, (65, 54), scene["title"], 25, NAVY)
    draw.rectangle((39, 103, 1218, 108), fill=LIGHT)
    fraction = min(1, max(0, time / timeline["duration"]))
    draw.rectangle((39, 103, 39 + 1179 * fraction, 108), fill=TEAL)
    local_progress = (time - visual_line["start"]) / max(.1, visual_line["end"] - visual_line["start"])
    draw_visual(draw, scene_index, mode, local_progress)
    for name, x, color in (("Nam", 90, ORANGE), ("Minh", 350, TEAL)):
        previous = (timeline["lines"][li - 1]
                    if line is not None and li > 0 and timeline["lines"][li - 1]["scene"] == scene_index
                    else None)
        if line is None and visual_line["start"] > time:
            pose, expression = "idle", "neutral"
            phase = (time * .5) % 1
            offset = 0
        elif line is None:
            pose, expression = actor_pose(name, visual_line)
            phase = ((visual_line["end"] - visual_line["start"]) * .5) % 1
            offset = position_offset(name, visual_line)
        else:
            pose, expression = actor_pose(name, line)
            phase = ((time - line["start"]) * .5) % 1
            offset = position_offset(name, line)
        if line is not None and time - line["start"] < .26:
            if previous is None:
                before = RIG.motion_state("idle", 0, "neutral")
                old_offset = 0
            else:
                old_pose, old_expression = actor_pose(name, previous)
                old_phase = ((previous["end"] - previous["start"]) * .5) % 1
                before = RIG.motion_state(old_pose, old_phase, old_expression)
                old_offset = position_offset(name, previous)
            after = RIG.motion_state(pose, phase, expression)
            amount = ease((time - line["start"]) / .26)
            sprite = raster_actor_state(RIG.blend(before, after, amount))
            offset = old_offset + (offset - old_offset) * amount
        else:
            sprite = actor_sprite(pose, expression, round(phase * 36) % 36)
        if name == "Nam" and scene_index == 0 and mode == "desk":
            draw.line((135, 388, 256, 388), fill="#b48661", width=10)
            draw.line((154, 390, 154, 533), fill="#b48661", width=7)
            draw.line((256, 390, 265, 533), fill="#b48661", width=7)
            draw.line((137, 315, 137, 392), fill="#b48661", width=8)
            draw.rounded_rectangle((265, 360, 320, 391), radius=5, fill="#e1ba90", outline=NAVY, width=2)
        image.paste(sprite, (round(x + offset), 105), sprite)
        active = line is not None and line["speaker"] == name
        pill(draw, (x + 44, 526, x + 176, 562), name.upper(), color if active else "#a7bac5", 19)
        if active and (mode in ("shock", "hack", "helicopter", "question", "idea", "joke")):
            cx = x + 115
            for j in (-1, 0, 1):
                draw.line((cx + j * 33, 177, cx + j * 42, 158), fill=color, width=4)
    if line:
        color = ORANGE if line["speaker"] == "Nam" else TEAL
        draw.rounded_rectangle((42, 578, 1220, 707), radius=18, fill="white", outline=color, width=3)
        pill(draw, (61, 592, 185, 632), line["speaker"].upper(), color, 19)
        lines, size = fit_lines(draw, line["text"], 1003, 3)
        line_height = size + 6
        start_y = 642 - (len(lines) - 1) * line_height / 2
        for j, value in enumerate(lines):
            label(draw, (206, start_y + j * line_height), value, size, NAVY, anchor="lm")
    return image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "linear_regression_stickman.mp4")
    parser.add_argument("--preview-seconds", type=float, default=0)
    parser.add_argument("--still", type=float, default=None, help="Save one PNG at this time")
    args = parser.parse_args()
    timeline = json.loads((ROOT / "timed_dialogue.json").read_text(encoding="utf-8"))
    starts = [x["start"] for x in timeline["lines"]]
    scene_starts = [x["start"] for x in timeline["scenes"]]
    if args.still is not None:
        frame_at(args.still, timeline, starts, scene_starts).save(args.output)
        print(f"Saved {args.output}")
        return
    duration = min(timeline["duration"], args.preview_seconds) if args.preview_seconds else timeline["duration"]
    frames = math.ceil(duration * FPS)
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
               "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{W}x{H}",
               "-framerate", str(FPS), "-i", "-", "-i", str(ROOT / "dialogue.wav"),
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
               "-t", str(duration), "-movflags", "+faststart", str(args.output)]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        for i in range(frames):
            image = frame_at(i / FPS, timeline, starts, scene_starts)
            process.stdin.write(image.tobytes())
            if i % (FPS * 20) == 0:
                print(f"Rendered {i/FPS:.0f}/{duration:.0f}s", flush=True)
    finally:
        process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError("FFmpeg render failed")
    print(f"Saved {args.output}")


if __name__ == "__main__":
    main()
