#!/usr/bin/env python3
"""Render the 5-minute stickman explainer with scene-specific vector illustrations."""

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
RIG_PATH = ROOT.parent / "stickman_assets" / "stickman.py"
FONT_PATH = ROOT / "NotoSans.ttf"
MATH_FONT_PATH = ROOT / "Nunito.ttf"
W, H, FPS = 1280, 720, 18
NAVY = "#17283b"
BLUE = "#2d69bd"
TEAL = "#1d9f9a"
ORANGE = "#f29d38"
RED = "#da5b57"
CREAM = "#f7f8fa"
PALE = "#eaf2f8"

SHORT_TITLES = [
    "CÁI BẪY 50% + 50%",
    "50% CỦA GIÁ NÀO?",
    "ĐIỂM SỐ VÀ MỐC SO SÁNH",
    "GIẢM RỒI TĂNG",
    "QUY LUẬT ẨN SAU",
    "CÂU HỎI CUỐI CÙNG",
]


def load_rig():
    spec = importlib.util.spec_from_file_location("stickman_rig", RIG_PATH)
    rig = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rig)
    return rig


RIG = load_rig()


@lru_cache(maxsize=80)
def font(size: int, heading: bool = False):
    loaded = ImageFont.truetype(str(FONT_PATH), size)
    if heading:
        loaded.set_variation_by_axes([800, 100])
    return loaded


def text(draw, xy, value, size=32, fill=NAVY, heading=False, anchor=None):
    draw.text(xy, value, font=font(size, heading), fill=fill, anchor=anchor)


def center(draw, xy, value, size=32, fill=NAVY, heading=False):
    text(draw, xy, value, size, fill, heading, anchor="mm")


def math_center(draw, xy, value, size=32, fill=NAVY):
    draw.text(xy, value, font=ImageFont.truetype(str(MATH_FONT_PATH), size),
              fill=fill, anchor="mm")


def panel(draw, box=(58, 126, 819, 560)):
    x0, y0, x1, y1 = box
    draw.rounded_rectangle((x0 + 7, y0 + 9, x1 + 7, y1 + 9), radius=25, fill="#d9e4ec")
    draw.rounded_rectangle(box, radius=25, fill="white", outline="#d9e4ec", width=2)


def pill(draw, box, label, fill=BLUE, fg="white", size=25):
    draw.rounded_rectangle(box, radius=15, fill=fill)
    center(draw, ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), label, size, fg)


def arrow(draw, x0, y0, x1, y1, color=BLUE, width=8, progress=1.0):
    x1 = x0 + (x1 - x0) * max(0, min(1, progress))
    y1 = y0 + (y1 - y0) * max(0, min(1, progress))
    draw.line((x0, y0, x1, y1), fill=color, width=width)
    angle = math.atan2(y1 - y0, x1 - x0)
    d = 16
    p1 = (x1 - d * math.cos(angle - .55), y1 - d * math.sin(angle - .55))
    p2 = (x1 - d * math.cos(angle + .55), y1 - d * math.sin(angle + .55))
    draw.polygon(((x1, y1), p1, p2), fill=color)


def shirt(draw, cx, cy, scale=1.0, color="#5384c9"):
    points = [(-65, -65), (-95, -25), (-56, -4), (-45, -25), (-45, 85),
              (45, 85), (45, -25), (56, -4), (95, -25), (65, -65),
              (35, -73), (20, -50), (-20, -50), (-35, -73)]
    points = [(cx + x * scale, cy + y * scale) for x, y in points]
    draw.polygon(points, fill=color, outline=NAVY, width=max(2, round(3 * scale)))
    draw.arc((cx - 20 * scale, cy - 70 * scale, cx + 20 * scale, cy - 28 * scale),
             0, 180, fill=NAVY, width=max(2, round(3 * scale)))
    draw.line((cx - 35 * scale, cy - 30 * scale, cx - 35 * scale, cy + 70 * scale),
              fill="#8fb2dc", width=max(2, round(3 * scale)))


def phone(draw, cx, cy, scale=1.0):
    box = (cx - 90 * scale, cy - 155 * scale, cx + 90 * scale, cy + 155 * scale)
    draw.rounded_rectangle(box, radius=24 * scale, fill=NAVY)
    draw.rounded_rectangle((cx - 77 * scale, cy - 136 * scale,
                            cx + 77 * scale, cy + 128 * scale), radius=12 * scale, fill="#d8ecf7")
    draw.ellipse((cx - 5 * scale, cy - 145 * scale, cx + 5 * scale,
                  cy - 135 * scale), fill="#7b94ad")
    draw.ellipse((cx - 28 * scale, cy - 30 * scale, cx + 28 * scale,
                  cy + 26 * scale), fill=BLUE)
    draw.ellipse((cx - 13 * scale, cy - 15 * scale, cx + 13 * scale,
                  cy + 11 * scale), fill="#d8ecf7")


def exam_paper(draw, x, y, score, accent=RED):
    draw.rounded_rectangle((x + 6, y + 7, x + 265, y + 270), radius=12, fill="#dbe4ea")
    draw.rounded_rectangle((x, y, x + 259, y + 263), radius=12, fill="white", outline="#aabcc8", width=3)
    text(draw, (x + 25, y + 18), "BÀI KIỂM TRA", 24, NAVY)
    for i in range(4):
        draw.line((x + 28, y + 77 + i * 32, x + 218, y + 77 + i * 32), fill="#b8cbd8", width=3)
    draw.ellipse((x + 81, y + 150, x + 205, y + 245), outline=accent, width=6)
    center(draw, (x + 143, y + 195), score, 46, accent, heading=True)


def wallet(draw, x, y, scale=1):
    box = lambda a, b, c, d: (x + a * scale, y + b * scale,
                              x + c * scale, y + d * scale)
    draw.rounded_rectangle(box(0, 24, 226, 160), radius=20 * scale,
                           fill="#a76b48", outline=NAVY, width=4)
    draw.rounded_rectangle(box(95, 62, 243, 130), radius=14 * scale,
                           fill="#cc8960", outline=NAVY, width=4)
    draw.ellipse(box(195, 87, 210, 102), fill="#f9d466")
    draw.line((x + 30 * scale, y + 13 * scale, x + 140 * scale, y + 13 * scale),
              fill="#e9bf7e", width=max(2, round(9 * scale)))
    draw.ellipse(box(18, -16, 45, 11), fill="#f8c94d", outline=NAVY, width=2)


def draw_store(draw, progress):
    panel(draw)
    x, y = 120, 205
    draw.rounded_rectangle((x, y + 78, x + 610, y + 300), radius=13,
                           fill="#e2edf4", outline=NAVY, width=4)
    draw.rectangle((x + 35, y + 142, x + 575, y + 278), fill="#c7e2eb")
    for k in range(10):
        color = RED if k % 2 else "#fff5df"
        draw.polygon(((x + k * 61, y + 78), (x + (k + 1) * 61, y + 78),
                      (x + (k + 1) * 61 - 9, y + 112), (x + k * 61 + 9, y + 112)), fill=color)
    pill(draw, (x + 120, y - 18, x + 492, y + 61), "SIÊU SALE", RED, "white", 45)
    draw.rounded_rectangle((x + 70, y + 148, x + 355, y + 257), radius=15, fill="white")
    center(draw, (x + 212, y + 181), "50% + 50%", 38, RED, heading=True)
    center(draw, (x + 212, y + 224), "GIẢM THÊM!", 27, NAVY)
    shirt(draw, x + 465, y + 202, .72)
    if progress > .35:
        for cx, cy in ((717, 176), (679, 198), (751, 213)):
            draw.line((cx - 8, cy, cx + 8, cy), fill=ORANGE, width=4)
            draw.line((cx, cy - 8, cx, cy + 8), fill=ORANGE, width=4)


def draw_sale_equation(draw, progress):
    panel(draw)
    center(draw, (438, 202), "50% + 50%", 69, RED, heading=True)
    arrow(draw, 442, 251, 442, 290, color=ORANGE, progress=progress)
    center(draw, (438, 358), "= 100%?", 70, NAVY, heading=True)
    if progress > .42:
        draw.line((254, 393, 626, 294), fill=RED, width=12)
    pill(draw, (183, 443, 689, 517), "VẬY LÀ MIỄN PHÍ?", ORANGE, NAVY, 35)


def draw_checkout(draw, progress):
    panel(draw)
    shirt(draw, 260, 320, 1.15)
    pill(draw, (107, 464, 409, 526), "1.000.000đ", BLUE, "white", 31)
    draw.rectangle((485, 407, 755, 430), fill=NAVY)
    draw.rectangle((513, 428, 735, 518), fill="#c89865")
    draw.ellipse((590, 252, 672, 334), fill="#fff9ee", outline=NAVY, width=5)
    draw.line((631, 334, 631, 405), fill=NAVY, width=6)
    draw.line((631, 362, 584, 395), fill=NAVY, width=6)
    draw.line((631, 362, 676, 397), fill=NAVY, width=6)
    if progress > .35:
        draw.rounded_rectangle((477, 157, 763, 231), radius=13, fill="#ffe9c7", outline=ORANGE, width=3)
        center(draw, (620, 194), "CẦN TRẢ: 250.000đ", 27, NAVY)


def draw_mystery(draw, progress):
    panel(draw)
    pill(draw, (113, 187, 763, 253), "CHUYỆN GÌ VỪA XẢY RA?", NAVY, "white", 33)
    draw.rounded_rectangle((107, 304, 405, 478), radius=22, fill="#e7f0fa", outline=BLUE, width=3)
    draw.rounded_rectangle((466, 304, 764, 478), radius=22, fill="#fff0e8", outline=RED, width=3)
    center(draw, (256, 359), "CỬA HÀNG", 29, BLUE)
    center(draw, (256, 410), "LỪA BẠN?", 34, BLUE, heading=True)
    center(draw, (615, 359), "BỘ NÃO", 29, RED)
    center(draw, (615, 410), "TỰ LỪA?", 34, RED, heading=True)


def draw_shirt_price(draw, progress):
    panel(draw)
    shirt(draw, 340, 320, 1.35)
    pill(draw, (490, 250, 765, 334), "1.000.000đ", BLUE, "white", 36)
    text(draw, (505, 363), "GIÁ BAN ĐẦU", 27, NAVY)


def draw_discount(draw, progress, second=False):
    panel(draw)
    a, b = ("500.000đ", "250.000đ") if second else ("1.000.000đ", "500.000đ")
    center(draw, (435, 186), "LẦN GIẢM THỨ HAI" if second else "LẦN GIẢM ĐẦU TIÊN", 34, NAVY, heading=True)
    pill(draw, (99, 273, 357, 352), a, BLUE, "white", 30)
    pill(draw, (432, 273, 713, 352), b if progress > .30 else "?", TEAL, "white", 33)
    arrow(draw, 357, 314, 428, 314, RED, 8, progress)
    pill(draw, (320, 392, 550, 456), "− 50%", RED, "white", 38)
    draw.rounded_rectangle((127, 493, 714, 523), radius=12, fill="#e0e8ef")
    draw.rounded_rectangle((127, 493, 127 + 587 * (.5 if not second else .25) * min(1, progress * 1.8), 523),
                           radius=12, fill=ORANGE)


def draw_percent_rule(draw, progress):
    panel(draw)
    center(draw, (436, 217), "50% CỦA CÁI GÌ?", 53, NAVY, heading=True)
    centers = (190, 435, 680)
    labels = ("1.000.000đ", "500.000đ", "250.000đ")
    for i, (cx, label) in enumerate(zip(centers, labels)):
        pill(draw, (cx - 95, 314, cx + 95, 382), label, (BLUE, ORANGE, TEAL)[i], "white", 22)
    arrow(draw, 290, 348, 335, 348, RED)
    arrow(draw, 535, 348, 580, 348, RED)
    center(draw, (436, 467), "MỖI LẦN CÓ MỘT MỐC MỚI", 32, RED)


def draw_exam_up(draw, progress):
    panel(draw)
    exam_paper(draw, 102, 213, "5/10")
    arrow(draw, 395, 338, 530, 338, TEAL, 9, progress)
    pill(draw, (407, 238, 552, 294), "+20%", TEAL, "white", 28)
    exam_paper(draw, 558, 213, "6/10", TEAL)


def draw_exam_down(draw, progress):
    panel(draw)
    center(draw, (435, 195), "CÙNG THAY ĐỔI 1 ĐIỂM", 39, NAVY, heading=True)
    for x, score, color in ((185, "5", BLUE), (435, "6", TEAL), (685, "5", RED)):
        draw.ellipse((x - 70, 285, x + 70, 425), fill=color)
        center(draw, (x, 355), score, 72, "white", heading=True)
    arrow(draw, 260, 355, 350, 355, TEAL)
    arrow(draw, 510, 355, 600, 355, RED)
    center(draw, (310, 471), "+20%", 31, TEAL)
    center(draw, (558, 471), "−16,67%", 31, RED)


def draw_exam_formula(draw, progress):
    panel(draw)
    center(draw, (435, 205), "MỐC SO SÁNH ĐÃ ĐỔI", 38, NAVY, heading=True)
    draw.rounded_rectangle((105, 268, 765, 376), radius=19, fill="#eaf4f8", outline=TEAL, width=3)
    math_center(draw, (435, 322), "1 ÷ 6 × 100% ≈ 16,67%", 45, TEAL)
    center(draw, (435, 454), "Giảm 1 điểm từ mốc 6 điểm", 30, NAVY)


def draw_phone(draw, progress, rising=False):
    panel(draw)
    phone(draw, 250, 342, .92)
    a, b = ("8.000.000đ", "9.600.000đ") if rising else ("10.000.000đ", "8.000.000đ")
    pill(draw, (431, 238, 746, 307), a, BLUE, "white", 28)
    arrow(draw, 590, 313, 590, 364, TEAL if rising else RED, 8, progress)
    pill(draw, (431, 377, 746, 449), b if progress > .3 else "?", TEAL if rising else ORANGE, "white", 29)
    center(draw, (590, 493), "+20% CỦA 8 TRIỆU" if rising else "GIẢM 20%", 26, NAVY)


def draw_loss_chart(draw, progress):
    panel(draw)
    center(draw, (438, 179), "GIẢM x% RỒI TĂNG x%", 37, NAVY, heading=True)
    values = [("10%", 1), ("20%", 4), ("30%", 9), ("50%", 25)]
    bottom = 468
    for i, (label, loss) in enumerate(values):
        x = 135 + i * 155
        height = (36 + loss * 8) * min(1, progress * 1.6)
        draw.rounded_rectangle((x, bottom - height, x + 92, bottom), radius=10,
                               fill=(BLUE, TEAL, ORANGE, RED)[i])
        center(draw, (x + 46, bottom + 32), label, 25, NAVY)
        center(draw, (x + 46, bottom - height - 24), f"−{loss}%", 24, RED)


def whiteboard(draw):
    panel(draw)
    draw.rounded_rectangle((91, 157, 785, 525), radius=16, fill="#f5fbff", outline=BLUE, width=5)
    draw.line((145, 505, 732, 505), fill="#b5d4e7", width=5)


def draw_algebra(draw, progress, stage):
    whiteboard(draw)
    if stage == 0:
        center(draw, (440, 224), "BẮT ĐẦU: 100", 42, NAVY, heading=True)
        center(draw, (440, 326), "GIẢM x%", 45, RED, heading=True)
        if progress > .3:
            center(draw, (440, 430), "100(1 − x/100)", 51, BLUE)
    elif stage == 1:
        center(draw, (440, 208), "GIẢM x% · TĂNG x%", 36, NAVY, heading=True)
        center(draw, (440, 324), "100(1 − x/100)", 43, BLUE)
        center(draw, (440, 420), "× (1 + x/100)", 43, TEAL)
    else:
        center(draw, (440, 212), "HIỆU HAI BÌNH PHƯƠNG", 34, NAVY, heading=True)
        center(draw, (440, 319), "100(1 − x²/10.000)", 43, BLUE)
        pill(draw, (177, 390, 705, 471), "MẤT x²/100 %", RED, "white", 39)


def draw_challenge(draw, progress, answer=False):
    panel(draw)
    center(draw, (440, 184), "ÁO GIÁ 100.000đ", 39, NAVY, heading=True)
    draw.rounded_rectangle((100, 253, 410, 479), radius=21, fill="#eaf2fc", outline=BLUE, width=4)
    draw.rounded_rectangle((464, 253, 774, 479), radius=21, fill="#eaf9f4", outline=TEAL, width=4)
    center(draw, (255, 301), "CỬA HÀNG A", 29, BLUE, heading=True)
    center(draw, (619, 301), "CỬA HÀNG B", 29, TEAL, heading=True)
    center(draw, (255, 367), "GIẢM 40%", 31, NAVY)
    center(draw, (619, 367), "GIẢM 20%, RỒI 20%", 26, NAVY)
    if answer:
        pill(draw, (143, 404, 367, 462), "60.000đ", BLUE, "white", 29)
        pill(draw, (507, 404, 731, 462), "64.000đ", TEAL, "white", 29)
        center(draw, (438, 521), "A RẺ HƠN 4.000đ", 31, RED, heading=True)
    else:
        center(draw, (255, 437), "?", 50, BLUE, heading=True)
        center(draw, (619, 437), "?", 50, TEAL, heading=True)


def draw_content(draw, mode, progress):
    if mode == "store": draw_store(draw, progress)
    elif mode == "sale_equation": draw_sale_equation(draw, progress)
    elif mode == "checkout": draw_checkout(draw, progress)
    elif mode == "mystery": draw_mystery(draw, progress)
    elif mode == "shirt_price": draw_shirt_price(draw, progress)
    elif mode == "discount1": draw_discount(draw, progress)
    elif mode == "discount2": draw_discount(draw, progress, second=True)
    elif mode == "percent_rule": draw_percent_rule(draw, progress)
    elif mode == "exam_up": draw_exam_up(draw, progress)
    elif mode == "exam_down": draw_exam_down(draw, progress)
    elif mode == "exam_formula": draw_exam_formula(draw, progress)
    elif mode == "phone_down": draw_phone(draw, progress)
    elif mode == "phone_up": draw_phone(draw, progress, rising=True)
    elif mode == "loss_chart": draw_loss_chart(draw, progress)
    elif mode == "algebra_intro": draw_algebra(draw, progress, 0)
    elif mode == "algebra_product": draw_algebra(draw, progress, 1)
    elif mode == "algebra_identity": draw_algebra(draw, progress, 2)
    elif mode == "challenge": draw_challenge(draw, progress)
    elif mode == "challenge_answer": draw_challenge(draw, progress, answer=True)
    else: raise ValueError(mode)


def visual_plan(section, local_line):
    if section == 0:
        mode = "store" if local_line < 4 else "sale_equation" if local_line < 7 else "checkout" if local_line < 11 else "mystery"
    elif section == 1:
        mode = "shirt_price" if local_line < 4 else "discount1" if local_line < 7 else "discount2" if local_line < 12 else "percent_rule"
    elif section == 2:
        mode = "exam_up" if local_line < 7 else "exam_down" if local_line < 12 else "exam_formula"
    elif section == 3:
        mode = "phone_down" if local_line < 6 else "phone_up" if local_line < 11 else "loss_chart"
    elif section == 4:
        mode = "algebra_intro" if local_line < 6 else "algebra_product" if local_line < 11 else "algebra_identity"
    else:
        mode = "store" if local_line < 6 else "challenge" if local_line < 13 else "challenge_answer" if local_line < 14 else "outro"
    poses = {
        "store": ("spot_sale", "wave"), "sale_equation": ("calculate_discount", "surprised"),
        "checkout": ("pay_cashier", "facepalm"), "mystery": ("shrug", "think"),
        "shirt_price": ("explain_open", "think"), "discount1": ("write_formula", "explain_open"),
        "discount2": ("calculate_discount", "point_side"), "percent_rule": ("explain_open", "point_up"),
        "exam_up": ("celebrate", "write_formula"), "exam_down": ("compare_prices", "confused"),
        "exam_formula": ("write_formula", "point_side"), "phone_down": ("spot_sale", "pay_cashier"),
        "phone_up": ("surprised", "calculate_discount"), "loss_chart": ("empty_wallet", "cry_body"),
        "algebra_intro": ("write_formula", "explain_up"), "algebra_product": ("write_formula", "point_side"),
        "algebra_identity": ("idea", "explain_open"), "challenge": ("compare_prices", "think"),
        "challenge_answer": ("idea", "point_side"), "outro": ("idle",),
    }
    choices = poses[mode]
    return mode, choices[(local_line // 2) % len(choices)]


@lru_cache(maxsize=360)
def actor_frame(pose, frame_index):
    return RIG.raster(RIG.frame_svg(pose, frame_index / 36), 400)


def draw_actor(image, pose, time):
    frame = actor_frame(pose, round(time * FPS) % 36)
    x, y = 856, 126
    shadow = ImageDraw.Draw(image)
    shadow.ellipse((1002, 550, 1159, 571), fill="#d6e3e9")
    image.paste(frame, (x, y), frame)


def actor_on_left(image):
    """Swap the body band; text keeps its reading direction and captions stay put."""
    body = image.crop((0, 110, W, 605))
    image.paste(body.crop((830, 0, W, 495)), (0, 110))
    image.paste(body.crop((0, 0, 830, 495)), (450, 110))


def draw_header(draw, section, time):
    draw.rectangle((0, 0, W, 102), fill=NAVY)
    pill(draw, (47, 27, 151, 77), f"{section + 1}/6", ORANGE, NAVY, 23)
    text(draw, (177, 31), SHORT_TITLES[section], 33, "white")
    draw.rectangle((0, 102, W, 109), fill="#d4e4ef")
    draw.rectangle((0, 102, W * min(1, time / 300), 109), fill=ORANGE)


def draw_caption(draw, value):
    if not value:
        return
    draw.rounded_rectangle((72, 608, 1208, 695), radius=20, fill=NAVY)
    size = 35 if len(value) < 48 else 32
    center(draw, (640, 652), value, size, "white")


def find_line(lines, time):
    starts = [line["start"] for line in lines]
    return max(0, bisect.bisect_right(starts, time) - 1)


def build_mode_spans(sections):
    spans = {}
    for section in sections:
        lines = section["lines"]
        modes = [visual_plan(section["index"], i)[0] for i in range(len(lines))]
        for i, mode in enumerate(modes):
            if i == 0 or mode != modes[i - 1]:
                start = section["start"] if i == 0 else lines[i]["start"]
            if i == len(lines) - 1 or mode != modes[i + 1]:
                end = section["end"] if i == len(lines) - 1 else lines[i + 1]["start"]
                spans[(section["index"], mode)] = (start, end)
    return spans


def frame_at(time, timeline, spans, captions_starts, no_actor=False, no_caption=False):
    sections = timeline["sections"]
    section = min(5, max(0, bisect.bisect_right([s["start"] for s in sections], time) - 1))
    lines = sections[section]["lines"]
    local_line = find_line(lines, time)
    mode, pose = visual_plan(section, local_line)
    if mode == "outro":
        image = Image.new("RGB", (W, H), NAVY)
        draw = ImageDraw.Draw(image)
        center(draw, (640, 305), "ĐỪNG ĐỂ DẤU %", 58, "white", heading=True)
        center(draw, (640, 385), "THAO TÚNG BẠN.", 58, ORANGE, heading=True)
    else:
        image = Image.new("RGB", (W, H), CREAM)
        draw = ImageDraw.Draw(image)
        draw.ellipse((915, 150, 1250, 485), fill="#e4f0f7")
        draw.line((837, 562, 1250, 562), fill="#c0d3df", width=4)
        start, end = spans[(section, mode)]
        progress = min(1, max(0, (time - start) / max(.001, end - start)))
        draw_content(draw, mode, progress)
        draw_header(draw, section, time)
        if not no_actor:
            draw_actor(image, pose, time)
            if mode == "loss_chart":
                wallet(ImageDraw.Draw(image), 1015, 402, .48)
        actor_on_left(image)
    if not no_caption:
        captions = timeline["captions"]
        ci = bisect.bisect_right(captions_starts, time) - 1
        if ci >= 0 and time < captions[ci]["end"]:
            draw_caption(ImageDraw.Draw(image), captions[ci]["text"])
    return image


def save_illustrations(timeline, spans, captions_starts):
    out = ROOT / "illustrations"
    out.mkdir(exist_ok=True)
    examples = {
        "01_cua_hang_sale": 7, "02_giam_gia_ao": 74, "03_diem_kiem_tra": 117,
        "04_gia_dien_thoai": 174, "05_bieu_do_phan_tram": 202,
        "06_cong_thuc": 243, "07_thu_thach_cuoi": 286,
    }
    for name, time in examples.items():
        image = frame_at(time, timeline, spans, captions_starts,
                         no_actor=False, no_caption=True)
        image.save(out / f"{name}.png")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preview-seconds", type=float, default=0,
                        help="Render only the first N seconds for layout review")
    parser.add_argument("--output", type=Path, default=ROOT / "final_video.mp4")
    args = parser.parse_args()
    timeline = json.loads((ROOT / "timed_script.json").read_text(encoding="utf-8"))
    spans = build_mode_spans(timeline["sections"])
    captions_starts = [caption["start"] for caption in timeline["captions"]]
    save_illustrations(timeline, spans, captions_starts)
    duration = min(300, args.preview_seconds) if args.preview_seconds else 300
    total = round(duration * FPS)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
               "-pixel_format", "rgb24", "-video_size", f"{W}x{H}", "-framerate", str(FPS),
               "-i", "-", "-i", str(ROOT / "narration.wav"),
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
               "-t", str(duration), "-movflags", "+faststart", str(args.output)]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        for index in range(total):
            image = frame_at(index / FPS, timeline, spans, captions_starts)
            process.stdin.write(image.tobytes())
            if index % (FPS * 20) == 0:
                print(f"Rendered {index/FPS:.0f}/{duration:.0f}s", flush=True)
    finally:
        process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError("FFmpeg render failed")
    print(f"Saved {args.output}", flush=True)


if __name__ == "__main__":
    main()
