"""Validate a data-only plan before synthesis or rendering."""

from __future__ import annotations

import importlib.util
import json
import sys
from functools import lru_cache
from pathlib import Path

RIG_PATH = Path(__file__).resolve().parent.parent / "stickman_assets" / "stickman.py"
spec = importlib.util.spec_from_file_location("factory_stickman_rig", RIG_PATH)
RIG = importlib.util.module_from_spec(spec)
spec.loader.exec_module(RIG)
ASSET_ROOT = RIG_PATH.parent
SEQUENCE_DIR = ASSET_ROOT / "sequences"
if str(ASSET_ROOT) not in sys.path:
    sys.path.insert(0, str(ASSET_ROOT))
from story_animation import StoryAnimation
import vfx as VFX


@lru_cache(maxsize=24)
def load_sequence(name: str) -> StoryAnimation:
    if not isinstance(name, str) or not name or name != Path(name).name or not name.isascii():
        raise ValueError("acting_sequence: expected a sequence name")
    path = SEQUENCE_DIR / f"{name}.json"
    if not path.is_file():
        raise ValueError(f"acting_sequence: unknown sequence {name!r}")
    return StoryAnimation.from_file(path)

VISUAL_TYPES = {"text", "table", "chart", "equation", "compare", "steps",
                "phone", "valley", "image", "store", "end"}
EFFECTS = set(VFX.EFFECTS)
VOICE_STYLES = {"comic_male", "calm_male", "warm_female", "clear_female"}
COLORS = {"orange", "teal"}


def check(condition, message):
    if not condition:
        raise ValueError(message)


def short_text(value, name, limit=280):
    check(isinstance(value, str) and 0 < len(value.strip()) <= limit, f"{name}: expected text up to {limit} characters")
    return value.strip()


def number(value, name, low, high):
    check(isinstance(value, (int, float)) and not isinstance(value, bool)
          and low <= value <= high, f"{name}: expected number from {low} to {high}")
    return float(value)


def validate_visual(visual, path):
    check(isinstance(visual, dict), f"{path}: visual must be an object")
    kind = visual.get("type")
    check(kind in VISUAL_TYPES, f"{path}: visual type must be one of {sorted(VISUAL_TYPES)}")
    if kind in ("text", "store", "end"):
        short_text(visual.get("headline", ""), f"{path}.headline", 100 if kind == "end" else 60)
        if "subtext" in visual:
            short_text(visual["subtext"], f"{path}.subtext",
                       160 if kind == "end" else 16 if kind == "store" else 120)
    if kind == "table":
        headers = visual.get("headers")
        rows = visual.get("rows")
        check(isinstance(headers, list) and len(headers) == 2,
              f"{path}: table needs two headers")
        check(isinstance(rows, list) and 1 <= len(rows) <= 5,
              f"{path}: table needs one to five rows")
        for j, value in enumerate(headers):
            short_text(value, f"{path}.headers[{j}]", 24)
        for j, row in enumerate(rows):
            check(isinstance(row, list) and len(row) == 2, f"{path}.rows[{j}]: two cells required")
            for k, cell in enumerate(row):
                check(isinstance(cell, (str, int, float)) and not isinstance(cell, bool),
                      f"{path}.rows[{j}][{k}]: expected short text or number")
                short_text(str(cell), f"{path}.rows[{j}][{k}]", 24)
    if kind == "chart":
        points = visual.get("points")
        check(isinstance(points, list) and 2 <= len(points) <= 8,
              f"{path}: chart needs two to eight numeric points")
        for j, point in enumerate(points):
            check(isinstance(point, list) and len(point) == 2,
                  f"{path}.points[{j}]: expected [x,y]")
            number(point[0], f"{path}.points[{j}][0]", -1e6, 1e6)
            number(point[1], f"{path}.points[{j}][1]", -1e6, 1e6)
        if "line" in visual:
            line = visual["line"]
            check(isinstance(line, dict), f"{path}.line: expected object")
            if "fit" in line:
                check(line["fit"] == "least_squares",
                      f"{path}.line.fit: only least_squares is supported")
                check(len({float(point[0]) for point in points}) >= 2,
                      f"{path}.points: least_squares requires two distinct x values")
                check("formula" not in visual,
                      f"{path}.formula: omit it when the line is computed from points")
            else:
                number(line.get("slope"), f"{path}.line.slope", -1e6, 1e6)
                number(line.get("intercept"), f"{path}.line.intercept", -1e6, 1e6)
        if "formula" in visual:
            short_text(visual["formula"], f"{path}.formula", 35)
        for axis in ("x_label", "y_label"):
            if axis in visual:
                short_text(visual[axis], f"{path}.{axis}", 20)
    if kind == "equation":
        short_text(visual.get("formula", ""), f"{path}.formula", 45)
        if "subtext" in visual:
            short_text(visual["subtext"], f"{path}.subtext", 65)
    if kind == "compare":
        for side in ("left", "right"):
            entry = visual.get(side)
            check(isinstance(entry, dict), f"{path}.{side}: expected object")
            short_text(entry.get("title", ""), f"{path}.{side}.title", 22)
            short_text(entry.get("value", ""), f"{path}.{side}.value", 22)
    if kind == "steps":
        items = visual.get("items")
        check(isinstance(items, list) and 2 <= len(items) <= 3,
              f"{path}: steps needs two or three items")
        for j, item in enumerate(items):
            short_text(item, f"{path}.items[{j}]", 50)
    if kind == "phone":
        short_text(visual.get("value", ""), f"{path}.value", 18)
        if "label" in visual:
            short_text(visual["label"], f"{path}.label", 30)
        if "subtext" in visual:
            short_text(visual["subtext"], f"{path}.subtext", 25)
        if "alert" in visual:
            check(isinstance(visual["alert"], bool), f"{path}.alert: expected true or false")
    if kind == "valley":
        if "caption" in visual:
            short_text(visual["caption"], f"{path}.caption", 45)
        if "overshoot" in visual:
            check(isinstance(visual["overshoot"], bool), f"{path}.overshoot: expected true or false")
    if kind == "image":
        asset = short_text(visual.get("path", ""), f"{path}.path", 180)
        check(not Path(asset).is_absolute() and ".." not in Path(asset).parts,
              f"{path}.path: use a relative asset path inside the plan folder")
        check(Path(asset).suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"),
              f"{path}.path: use PNG, JPG or WebP")
    if "title" in visual:
        short_text(visual["title"], f"{path}.title", 50)
    if "animation_seconds" in visual:
        number(visual["animation_seconds"], f"{path}.animation_seconds", .2, 12)
    if "notes" in visual:
        notes = visual["notes"]
        limit = {"text": 3, "equation": 2, "compare": 1}.get(kind, 1)
        check(isinstance(notes, list) and len(notes) <= limit,
              f"{path}.notes: at most {limit} item(s) for {kind}")
        for j, item in enumerate(notes):
            short_text(item, f"{path}.notes[{j}]", 65)


def load_plan(path: str | Path) -> dict:
    path = Path(path).resolve()
    data = json.loads(path.read_text(encoding="utf-8"))
    check(isinstance(data, dict), "Root: expected JSON object")
    short_text(data.get("title", ""), "title", 120)
    cast = data.get("cast")
    check(isinstance(cast, list) and 1 <= len(cast) <= 2,
          "cast: this two-character layout supports one or two people")
    ids = set()
    for i, actor in enumerate(cast):
        check(isinstance(actor, dict), f"cast[{i}]: expected object")
        actor_id = short_text(actor.get("id", ""), f"cast[{i}].id", 30)
        check(actor_id not in ids, f"cast[{i}].id: duplicate")
        ids.add(actor_id)
        short_text(actor.get("name", ""), f"cast[{i}].name", 20)
        check(actor.get("voice_style") in VOICE_STYLES,
              f"cast[{i}].voice_style: choose {sorted(VOICE_STYLES)}")
        check(actor.get("color") in COLORS, f"cast[{i}].color: choose orange or teal")
    scenes = data.get("scenes")
    check(isinstance(scenes, list) and 1 <= len(scenes) <= 30,
          "scenes: expected one to thirty scenes")
    total_lines = 0
    for si, scene in enumerate(scenes):
        check(isinstance(scene, dict), f"scenes[{si}]: expected object")
        short_text(scene.get("title", ""), f"scenes[{si}].title", 70)
        if "target_seconds" in scene:
            number(scene["target_seconds"], f"scenes[{si}].target_seconds", 2, 600)
        lines = scene.get("lines")
        check(isinstance(lines, list) and 1 <= len(lines) <= 60,
              f"scenes[{si}].lines: expected one to sixty lines")
        current_visual = None
        for li, line in enumerate(lines):
            prefix = f"scenes[{si}].lines[{li}]"
            check(isinstance(line, dict), f"{prefix}: expected object")
            check(line.get("speaker") in ids, f"{prefix}.speaker: unknown cast id")
            short_text(line.get("text", ""), f"{prefix}.text", 220)
            if "spoken" in line:
                short_text(line["spoken"], f"{prefix}.spoken", 340)
            if "pose" in line:
                check(line["pose"] in RIG.POSES, f"{prefix}.pose: unknown stickman pose")
            if "acting_sequence" in line:
                check("pose" not in line and "expression" not in line,
                      f"{prefix}.acting_sequence: use this instead of pose/expression")
                try:
                    load_sequence(line["acting_sequence"])
                except ValueError as exc:
                    raise ValueError(f"{prefix}.{exc}") from exc
            if "expression" in line:
                check(line["expression"] in RIG.FACES,
                      f"{prefix}.expression: unknown facial expression")
            if "listener_pose" in line:
                check(line["listener_pose"] in RIG.POSES,
                      f"{prefix}.listener_pose: unknown pose")
            if "effect" in line:
                check(line["effect"] in EFFECTS, f"{prefix}.effect: unknown effect")
            if "move_x" in line:
                number(line["move_x"], f"{prefix}.move_x", -85, 85)
            if "pause_after" in line:
                number(line["pause_after"], f"{prefix}.pause_after", 0, 4)
            if "visual" in line:
                validate_visual(line["visual"], f"{prefix}.visual")
                current_visual = line["visual"]
                if current_visual["type"] == "image":
                    asset = (path.parent / current_visual["path"]).resolve()
                    check(asset.is_relative_to(path.parent) and asset.is_file(),
                          f"{prefix}.visual.path: asset missing or outside plan folder")
            check(current_visual is not None, f"{prefix}: first line of each scene needs a visual")
            total_lines += 1
    check(total_lines <= 400, "Plan has too many lines")
    return data
