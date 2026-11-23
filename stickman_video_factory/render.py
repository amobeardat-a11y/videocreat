#!/usr/bin/env python3
"""Render any validated two-person plan in the established stickman video style."""

from __future__ import annotations

import argparse
import bisect
import json
import math
import re
import subprocess
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from plan import RIG, VFX, ILLU, load_plan, load_sequence

ROOT = Path(__file__).resolve().parent
FONT_FILE = ROOT.parent / "phan_tram_stickman_video" / "NotoSans.ttf"
W, H, FPS = 1280, 720, 18
NAVY, BLUE, TEAL = "#20354b", "#426db8", "#168e8a"
ORANGE, RED, BG = "#e88942", "#d95760", "#f7f8fa"
PALE, LIGHT = "#edf4f8", "#dce6ed"
COLORS = {"orange": ORANGE, "teal": TEAL}


@lru_cache(maxsize=48)
def font(size: int):
    return ImageFont.truetype(str(FONT_FILE), size)


def clean(value) -> str:
    return str(value).replace("→", " > ").replace("≠", "khác")


def text(draw, xy, value, size=28, fill=NAVY, anchor=None):
    draw.text(xy, clean(value), font=font(size), fill=fill, anchor=anchor)


def center(draw, xy, value, size=28, fill=NAVY):
    text(draw, xy, value, size, fill, anchor="mm")


def fit_size(draw, value, max_width, start=34, minimum=18):
    for size in range(start, minimum - 1, -2):
        if draw.textbbox((0, 0), clean(value), font=font(size))[2] <= max_width:
            return size
    return minimum


def wrapped(draw, value, max_width, max_lines=3):
    for size in (32, 30, 28, 26, 24, 22):
        lines, current = [], ""
        for word in clean(value).split():
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
    return lines, 22


def card(draw, box=(605, 126, 1224, 550), fill="white"):
    x0, y0, x1, y1 = box
    draw.rounded_rectangle((x0 + 7, y0 + 8, x1 + 7, y1 + 8), radius=23, fill=LIGHT)
    draw.rounded_rectangle(box, radius=23, fill=fill, outline=LIGHT, width=2)


def pill(draw, box, value, color=BLUE, size=26, fg="white"):
    draw.rounded_rectangle(box, radius=14, fill=color)
    center(draw, ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), value, size, fg)


def arrow(draw, x0, y0, x1, y1, color=BLUE):
    draw.line((x0, y0, x1, y1), fill=color, width=5)
    angle = math.atan2(y1 - y0, x1 - x0)
    draw.polygon(((x1, y1),
                  (x1 - 16 * math.cos(angle - .55), y1 - 16 * math.sin(angle - .55)),
                  (x1 - 16 * math.cos(angle + .55), y1 - 16 * math.sin(angle + .55))),
                 fill=color)


def visual_title(draw, value):
    if value:
        center(draw, (914, 174), value, fit_size(draw, value, 525, 30, 21), NAVY)


def notes(draw, values, top=462):
    for i, value in enumerate(values[:3]):
        center(draw, (915, top + i * 34), value,
               fit_size(draw, value, 526, 24, 17), TEAL if i % 2 == 0 else NAVY)


def short_number(value):
    return f"{value:.2f}".rstrip("0").rstrip(".").replace(".", ",")


def fitted_line(points):
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    x_mean, y_mean = sum(xs) / len(xs), sum(ys) / len(ys)
    variance = sum((x - x_mean) ** 2 for x in xs)
    slope = sum((x - x_mean) * (y - y_mean) for x, y in points) / variance
    return slope, y_mean - slope * x_mean


def draw_visual(image, visual, progress, plan_dir):
    draw = ImageDraw.Draw(image)
    kind = visual["type"]
    if kind == "end":
        image.paste(NAVY, (0, 0, W, H))
        draw = ImageDraw.Draw(image)
        headline = visual["headline"]
        center(draw, (640, 292), headline, fit_size(draw, headline, 1100, 48, 27), "white")
        if visual.get("subtext"):
            center(draw, (640, 420), visual["subtext"],
                   fit_size(draw, visual["subtext"], 1100, 34, 22), "#ffbc70")
        return
    card(draw)
    title = visual.get("title", "")
    if kind == "text":
        headline = visual["headline"]
        center(draw, (914, 248), headline, fit_size(draw, headline, 530, 41, 23), BLUE)
        if visual.get("subtext"):
            lines, size = wrapped(draw, visual["subtext"], 520, 3)
            start = 344 - (len(lines) - 1) * (size + 9) / 2
            for i, line in enumerate(lines):
                center(draw, (914, start + i * (size + 9)), line, size, NAVY)
        notes(draw, visual.get("notes", []), 466)
    elif kind == "table":
        visual_title(draw, title or "DỮ LIỆU")
        rows = visual["rows"]
        y0, x0, x1, x2 = 218, 675, 920, 1164
        row_height = min(57, (244 - (36 if visual.get("notes") else 0)) / len(rows))
        draw.rounded_rectangle((x0, y0, x2, y0 + 53 + len(rows) * row_height),
                               radius=13, fill=PALE)
        draw.rounded_rectangle((x0, y0, x2, y0 + 52), radius=13, fill=BLUE)
        for j, heading in enumerate(visual["headers"]):
            cx = (x0 + x1) / 2 if j == 0 else (x1 + x2) / 2
            center(draw, (cx, y0 + 26), heading, fit_size(draw, heading, 220, 22, 17), "white")
        for i, row in enumerate(rows):
            y = y0 + 53 + (i + .5) * row_height
            if i % 2:
                draw.rectangle((x0, y - row_height / 2, x2, y + row_height / 2), fill="white")
            for j, value in enumerate(row):
                cx = (x0 + x1) / 2 if j == 0 else (x1 + x2) / 2
                center(draw, (cx, y), value, fit_size(draw, value, 220, 27, 18), NAVY)
        if visual.get("notes"):
            notes(draw, visual["notes"], y0 + 53 + len(rows) * row_height + 26)
    elif kind == "chart":
        points = [(float(x), float(y)) for x, y in visual["points"]]
        x_values = [p[0] for p in points]
        y_values = [p[1] for p in points]
        x_low, x_high = min(x_values), max(x_values)
        y_low, y_high = min(y_values), max(y_values)
        if x_low == x_high:
            x_low -= 1; x_high += 1
        if y_low == y_high:
            y_low -= 1; y_high += 1
        x_pad = (x_high - x_low) * .13
        y_pad = (y_high - y_low) * .22
        x_low -= x_pad; x_high += x_pad
        y_low -= y_pad; y_high += y_pad
        def xy(x, y):
            return (690 + (x - x_low) / (x_high - x_low) * 450,
                    472 - (y - y_low) / (y_high - y_low) * 231)
        visual_title(draw, title or "DỮ LIỆU TRÊN ĐỒ THỊ")
        draw.line((690, 472, 1150, 472), fill=NAVY, width=3)
        draw.line((690, 472, 690, 232), fill=NAVY, width=3)
        if visual.get("x_label"):
            text(draw, (1060, 501), visual["x_label"], 18, NAVY)
        if visual.get("y_label"):
            text(draw, (630, 208), visual["y_label"], 17, NAVY)
        for i, (x, y) in enumerate(points):
            px, py = xy(x, y)
            radius = 9 if i < max(1, math.ceil(len(points) * progress * 1.7)) else 5
            draw.ellipse((px - radius, py - radius, px + radius, py + radius),
                         fill=ORANGE, outline="white", width=2)
        formula = visual.get("formula")
        if visual.get("line"):
            if visual["line"].get("fit") == "least_squares":
                slope, intercept = fitted_line(points)
                sign = "+" if intercept >= 0 else "−"
                formula = f"ŷ = {short_number(slope)}x {sign} {short_number(abs(intercept))}"
            else:
                slope = float(visual["line"]["slope"])
                intercept = float(visual["line"]["intercept"])
            line_low, line_high = x_low, x_high
            if slope:
                crossings = sorted(((y_low - intercept) / slope, (y_high - intercept) / slope))
                line_low, line_high = max(x_low, crossings[0]), min(x_high, crossings[1])
            if line_low <= line_high and y_low <= slope * line_low + intercept <= y_high:
                left = xy(line_low, slope * line_low + intercept)
                right = xy(line_high, slope * line_high + intercept)
                fraction = min(1, progress * 1.7)
                draw.line((left[0], left[1], left[0] + (right[0] - left[0]) * fraction,
                           left[1] + (right[1] - left[1]) * fraction), fill=BLUE, width=6)
        if formula:
            pill(draw, (800, 198, 1128, 253), formula, TEAL,
                 fit_size(draw, formula, 300, 29, 18))
        notes(draw, visual.get("notes", []), 525)
    elif kind == "equation":
        visual_title(draw, title or "CÔNG THỨC")
        formula = visual["formula"]
        pill(draw, (680, 245, 1166, 345), formula, BLUE,
             fit_size(draw, formula, 451, 38, 20))
        if visual.get("subtext"):
            center(draw, (915, 405), visual["subtext"],
                   fit_size(draw, visual["subtext"], 520, 25, 18), NAVY)
        notes(draw, visual.get("notes", []), 473)
    elif kind == "compare":
        visual_title(draw, title or "SO SÁNH")
        for i, side in enumerate(("left", "right")):
            entry = visual[side]
            x0 = 670 + i * 256
            color = TEAL if i == 0 else RED
            draw.rounded_rectangle((x0, 260, x0 + 230, 428), radius=19,
                                   fill="#e8f5f3" if i == 0 else "#fff0ed",
                                   outline=color, width=3)
            center(draw, (x0 + 115, 302), entry["title"],
                   fit_size(draw, entry["title"], 205, 23, 17), NAVY)
            center(draw, (x0 + 115, 365), entry["value"],
                   fit_size(draw, entry["value"], 200, 37, 20), color)
        notes(draw, visual.get("notes", []), 487)
    elif kind == "steps":
        visual_title(draw, title or "TỪ DỮ LIỆU ĐẾN KẾT QUẢ")
        items = visual["items"]
        for i, item in enumerate(items):
            y = 220 + i * 99
            color = (BLUE, TEAL, ORANGE)[i]
            pill(draw, (673, y, 1158, y + 62), item, color,
                 fit_size(draw, item, 449, 25, 17))
            if i < len(items) - 1:
                arrow(draw, 914, y + 67, 914, y + 90, color)
        notes(draw, visual.get("notes", []), 525)
    elif kind == "phone":
        visual_title(draw, title or "ĐƠN HÀNG")
        draw.rounded_rectangle((786, 204, 1045, 487), radius=27, fill=NAVY)
        draw.rounded_rectangle((803, 223, 1028, 463), radius=17, fill="white")
        center(draw, (916, 278), visual.get("label", "PHÍ HIỂN THỊ"),
               fit_size(draw, visual.get("label", "PHÍ HIỂN THỊ"), 203, 23, 16), NAVY)
        value = visual["value"]
        center(draw, (916, 358), value,
               fit_size(draw, value, 204, 44, 24), RED if visual.get("alert") else TEAL)
        if visual.get("subtext"):
            center(draw, (916, 422), visual["subtext"],
                   fit_size(draw, visual["subtext"], 210, 17, 13), NAVY)
        notes(draw, visual.get("notes", []), 524)
    elif kind == "valley":
        visual_title(draw, title or "TÌM ĐIỂM THẤP NHẤT")
        curve = [(x, 440 - .0028 * (x - 918) ** 2) for x in range(665, 1172, 5)]
        draw.line(curve, fill=BLUE, width=7, joint="curve")
        if visual.get("overshoot"):
            stops = [(710, 318), (1060, 384), (802, 402), (1100, 347)]
            j = min(3, int(progress * 4))
            x, y = stops[j]
            draw.line(stops[:j + 1], fill=RED, width=3)
        else:
            x = 710 + 208 * min(1, progress * 1.25)
            y = 440 - .0028 * (x - 918) ** 2
        draw.ellipse((x - 16, y - 16, x + 16, y + 16), fill=ORANGE, outline=NAVY, width=3)
        center(draw, (917, 480), visual.get("caption", "SAI SỐ THẤP NHẤT"),
               fit_size(draw, visual.get("caption", "SAI SỐ THẤP NHẤT"), 510, 23, 17), TEAL)
        notes(draw, visual.get("notes", []), 527)
    elif kind == "store":
        visual_title(draw, title or visual["headline"])
        draw.rounded_rectangle((711, 286, 900, 429), radius=15, fill="#d8e9f1", outline=BLUE, width=4)
        draw.rectangle((694, 300, 918, 329), fill=ORANGE)
        draw.line((712, 374, 900, 374), fill=BLUE, width=4)
        draw.rectangle((971, 331, 1109, 438), fill="#dcae72", outline=NAVY, width=3)
        draw.line((971, 331, 1040, 361, 1109, 331), fill=NAVY, width=3)
        center(draw, (1039, 390), visual.get("subtext", "SHIP?"), 24, NAVY)
        notes(draw, visual.get("notes", []), 503)
    elif kind == "illustration":
        visual_title(draw, title or ILLU.ILLUSTRATIONS[visual["name"]].upper())
        art = illustration_sprite(visual["name"], round(progress * 18))
        image.paste(art, (664, 213), art)
        notes(draw, visual.get("notes", []), 527)
    elif kind == "image":
        path = (plan_dir / visual["path"]).resolve()
        source = Image.open(path).convert("RGBA")
        source.thumbnail((552, 312), Image.Resampling.LANCZOS)
        x = round(914 - source.width / 2)
        y = round(320 - source.height / 2)
        image.paste(source, (x, y), source)
        visual_title(draw, title)
        notes(draw, visual.get("notes", []), 509)


@lru_cache(maxsize=120)
def illustration_sprite(name, tick):
    return RIG.raster(ILLU.svg(name, tick / 18), 500)


@lru_cache(maxsize=420)
def actor_sprite(pose, expression, tick):
    state = RIG.motion_state(pose, tick / 36, expression)
    return raster_state(state)


def raster_state(state):
    svg = RIG.wrap(RIG.draw(state), viewbox="140 100 220 440", width=220, height=440)
    return RIG.raster(svg, 220)


@lru_cache(maxsize=180)
def vfx_sprite(effect, tick, facing):
    inner = VFX.effect_svg(effect, 140, 120, tick / 12, facing=facing)
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="280" height="400" '
           f'viewBox="0 0 280 400">{inner}</svg>')
    return RIG.raster(svg, 280)


def ease(value):
    value = min(1.0, max(0.0, value))
    return value * value * (3 - 2 * value)


class Video:
    def __init__(self, plan_path: Path, output_dir: Path):
        self.plan_path = plan_path.resolve()
        self.plan_dir = self.plan_path.parent
        self.plan = load_plan(self.plan_path)
        self.out = output_dir.resolve()
        self.timeline = json.loads((self.out / "timed_plan.json").read_text(encoding="utf-8"))
        self.lines = self.timeline["lines"]
        self.starts = [line["start"] for line in self.lines]
        self.scenes = self.timeline["scenes"]
        self.scene_starts = [scene["start"] for scene in self.scenes]
        self.cast = self.plan["cast"]
        offsets = {actor["id"]: 0.0 for actor in self.cast}
        self.offsets_before = []
        self.offsets_after = []
        for line in self.lines:
            self.offsets_before.append(offsets.copy())
            if "move_x" in line:
                offsets[line["speaker"]] = float(line["move_x"])
            if "acting_sequence" in line:
                sequence = load_sequence(line["acting_sequence"])
                _, x, _, _, _ = sequence.sample(sequence.duration)
                offsets[line["speaker"]] = max(-85, min(85, offsets[line["speaker"]]
                                                   + self.sequence_shift(sequence, x)))
            self.offsets_after.append(offsets.copy())

    def sequence_shift(self, sequence, x):
        distance = max(abs(beat["to_x"] - sequence.initial_x)
                       for beat in sequence.beats)
        travel = 100 if len(self.cast) == 1 else 35
        factor = min(.55, travel / distance) if distance else .55
        return (x - sequence.initial_x) * factor

    def actor_pose(self, actor_id, line):
        if line is None:
            return "idle", "neutral"
        if line["speaker"] == actor_id:
            return line.get("pose", "talk"), line.get("expression")
        return line.get("listener_pose", "listen"), "curious"

    def actor_state(self, actor_id, line, local):
        if line and line["speaker"] == actor_id and "acting_sequence" in line:
            sequence = load_sequence(line["acting_sequence"])
            duration = max(.001, line.get("acting_end", line["end"]) - line["start"])
            progress = max(0, min(1, local / duration))
            state, x, facing, effect, _ = sequence.sample(progress * sequence.duration)
            return state, self.sequence_shift(sequence, x), facing, effect
        pose, expression = self.actor_pose(actor_id, line)
        return RIG.motion_state(pose, (local * .5) % 1, expression), 0, 1, "none"

    def actor(self, image, draw, actor, actor_index, line, previous, time):
        actor_id = actor["id"]
        base_x = 90 if len(self.cast) == 2 and actor_index == 0 else 350 if len(self.cast) == 2 else 220
        color = COLORS[actor["color"]]
        if line is None:
            if previous and previous["speaker"] == actor_id and "acting_sequence" in previous:
                duration = previous.get("acting_end", previous["end"]) - previous["start"]
                state, _, facing, _ = self.actor_state(actor_id, previous, duration)
                sprite = raster_state(state)
                if facing == -1:
                    sprite = ImageOps.mirror(sprite)
            else:
                pose, expression = self.actor_pose(actor_id, previous)
                phase = ((previous["end"] - previous["start"]) * .5) % 1 if previous else (time * .5) % 1
                sprite = actor_sprite(pose, expression, round(phase * 36) % 36)
            offset = self.offsets_after[previous["index"]][actor_id] if previous else 0
            effect = "none"
        else:
            pose, expression = self.actor_pose(actor_id, line)
            local = max(0, time - line["start"])
            phase = (local * .5) % 1
            start_offset = self.offsets_before[line["index"]][actor_id]
            duration = max(.001, line.get("acting_end", line["end"]) - line["start"])
            target_offset = float(line["move_x"]) if line["speaker"] == actor_id and "move_x" in line else start_offset
            state, sequence_offset, facing, effect = self.actor_state(actor_id, line, local)
            offset = max(-85, min(85, start_offset + (target_offset - start_offset)
                                  * ease(local / duration) + sequence_offset))
            transition = min(.26, duration * .25)
            if local < transition:
                if previous and previous["scene"] == line["scene"]:
                    old_duration = previous.get("acting_end", previous["end"]) - previous["start"]
                    before, _, _, _ = self.actor_state(actor_id, previous, old_duration)
                else:
                    before = RIG.motion_state("idle", 0, "neutral")
                sprite = raster_state(RIG.blend(before, state, ease(local / transition)))
            elif line["speaker"] == actor_id and "acting_sequence" in line:
                sprite = raster_state(state)
            else:
                sprite = actor_sprite(pose, expression, round(phase * 36) % 36)
            if facing == -1:
                sprite = ImageOps.mirror(sprite)
        image.paste(sprite, (round(base_x + offset), 105), sprite)
        active = line is not None and line["speaker"] == actor_id
        actor_name = actor["name"].upper()
        pill(draw, (base_x + 44 + offset, 526, base_x + 176 + offset, 562),
             actor_name, color if active else "#a7bac5",
             fit_size(draw, actor_name, 117, 19, 13))
        effect = line.get("effect", effect) if line else effect
        if active and effect != "none":
            cx = base_x + 115 + offset
            sprite = vfx_sprite(effect, round(local * 12) % 48, facing)
            left = round(cx - 140)
            crop_left, crop_right = max(0, -left), min(280, 600 - left)
            if crop_right > crop_left:
                sprite = sprite.crop((crop_left, 0, crop_right, 400))
                image.paste(sprite, (left + crop_left, 68), sprite)

    def frame(self, time):
        time = max(0, min(float(time), self.timeline["duration"] - .001))
        si = max(0, bisect.bisect_right(self.scene_starts, time) - 1)
        scene = self.scenes[si]
        li = bisect.bisect_right(self.starts, time) - 1
        line = (self.lines[li] if li >= 0 and
                time < self.lines[li].get("acting_end", self.lines[li]["end"]) and
                self.lines[li]["scene"] == si else None)
        scene_lines = [item for item in self.lines if item["scene"] == si]
        current_visual_line = next((item for item in reversed(scene_lines) if item["start"] <= time), scene_lines[0])
        visual = current_visual_line["visual"]
        if visual["type"] == "end":
            image = Image.new("RGB", (W, H), NAVY)
            draw_visual(image, visual, 1, self.plan_dir)
            return image
        image = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(image)
        draw.ellipse((27, 169, 580, 722), fill="#e8f2f5")
        draw.line((51, 536, 566, 536), fill="#c8d9e0", width=4)
        draw.rounded_rectangle((39, 30, 1218, 91), radius=18, fill="white", outline=LIGHT, width=2)
        title = re.sub(r"^\s*CẢNH\s*\d+\s*[:.\-–—]?\s*", "", scene["title"], flags=re.IGNORECASE)
        text(draw, (65, 54), title, fit_size(draw, title, 1110, 25, 19), NAVY)
        draw.rectangle((39, 103, 1218, 108), fill=LIGHT)
        draw.rectangle((39, 103, 39 + 1179 * time / self.timeline["duration"], 108), fill=TEAL)
        visual_time = current_visual_line.get("visual_start", current_visual_line["start"])
        progress = max(0, min(1, (time - visual_time) / visual.get("animation_seconds", 1.4)))
        draw_visual(image, visual, progress, self.plan_dir)
        previous = (self.lines[li - 1] if line is not None and li > 0
                    else current_visual_line if current_visual_line["start"] <= time else None)
        for actor_index, actor in enumerate(self.cast):
            self.actor(image, draw, actor, actor_index, line, previous, time)
        if line is not None:
            actor = next(actor for actor in self.cast if actor["id"] == line["speaker"])
            color = COLORS[actor["color"]]
            draw.rounded_rectangle((42, 578, 1220, 707), radius=18,
                                   fill="white", outline=color, width=3)
            actor_name = actor["name"].upper()
            pill(draw, (61, 592, 185, 632), actor_name, color,
                 fit_size(draw, actor_name, 109, 19, 13))
            values, size = wrapped(draw, line["text"], 1003, 3)
            line_height = size + 6
            start_y = 642 - (len(values) - 1) * line_height / 2
            for j, value in enumerate(values):
                text(draw, (206, start_y + j * line_height), value, size, NAVY, anchor="lm")
        return image


def render(video: Video, output: Path, preview_seconds=0):
    duration = min(video.timeline["duration"], preview_seconds) if preview_seconds else video.timeline["duration"]
    count = math.ceil(duration * FPS)
    output.parent.mkdir(parents=True, exist_ok=True)
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
               "-f", "rawvideo", "-pixel_format", "rgb24", "-video_size", f"{W}x{H}",
               "-framerate", str(FPS), "-i", "-", "-i", str(video.out / "dialogue.wav"),
               "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
               "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k",
               "-t", str(duration), "-movflags", "+faststart", str(output)]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        for index in range(count):
            process.stdin.write(video.frame(index / FPS).tobytes())
            if index % (FPS * 20) == 0:
                print(f"Rendered {index/FPS:.0f}/{duration:.0f}s", flush=True)
    finally:
        process.stdin.close()
    if process.wait() != 0:
        raise RuntimeError("FFmpeg render failed")
    return output


def contact_sheet(video: Video, output: Path):
    scenes = video.scenes
    columns = min(3, len(scenes))
    rows = math.ceil(len(scenes) / columns)
    sheet = Image.new("RGB", (columns * 480, rows * 270), "white")
    for i, scene in enumerate(scenes):
        image = video.frame((scene["start"] + scene["end"]) / 2)
        image.thumbnail((480, 270))
        sheet.paste(image, ((i % columns) * 480, (i // columns) * 270))
    sheet.save(output)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--preview-seconds", type=float, default=0)
    parser.add_argument("--still", type=float, default=None)
    args = parser.parse_args()
    video = Video(args.plan, args.out)
    if args.still is not None:
        output = args.out / "still.png"
        video.frame(args.still).save(output)
        print(output)
        return
    output = args.out / ("preview.mp4" if args.preview_seconds else "video.mp4")
    render(video, output, args.preview_seconds)
    if not args.preview_seconds:
        contact_sheet(video, args.out / "contact_sheet.png")
    print(f"Saved {output}")


if __name__ == "__main__":
    main()
