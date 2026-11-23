#!/usr/bin/env python3
"""Join stickman actions into a continuous, movable performance.

Usage: python story_animation.py story_demo.json story_motion_demo.mp4
       python story_animation.py story_demo.json frames --format png --transparent
"""

from __future__ import annotations

import argparse
import bisect
import json
import math
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape

import stickman as rig
import vfx


def ease(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3 - 2 * value)


class StoryAnimation:
    """An ordered acting timeline with continuous position and pose transitions."""

    def __init__(self, data: dict):
        canvas = data.get("canvas", [1280, 720])
        if not (isinstance(canvas, list) and len(canvas) == 2 and
                all(isinstance(x, int) and 240 <= x <= 4096 for x in canvas)):
            raise ValueError("canvas must be two integer pixel dimensions")
        self.width, self.height = canvas
        self.ground_y = float(data.get("ground_y", self.height - 95))
        self.scale = float(data.get("scale", 1.0))
        if not (0.2 <= self.scale <= 2.5 and 50 <= self.ground_y <= self.height):
            raise ValueError("Invalid scale or ground_y")
        self.background = str(data.get("background", "#f7f8fa"))
        self.initial_x = float(data.get("initial_x", self.width * .2))
        if not (0 <= self.initial_x <= self.width):
            raise ValueError("initial_x outside canvas")
        self.beats = []
        self.starts = []
        elapsed, x = 0.0, self.initial_x
        for raw in data.get("beats", []):
            pose = raw.get("pose")
            if pose not in rig.POSES:
                raise ValueError(f"Unknown pose: {pose}")
            duration = float(raw.get("duration", 0))
            transition = float(raw.get("transition", .2))
            to_x = float(raw.get("to_x", x))
            facing = int(raw.get("facing", 1))
            expression = raw.get("expression")
            if duration <= 0 or not (0 <= transition <= duration * .5):
                raise ValueError(f"Invalid duration/transition for {pose}")
            if not (0 <= to_x <= self.width) or facing not in (-1, 1):
                raise ValueError(f"Invalid actor placement for {pose}")
            if expression is not None and expression not in rig.FACES:
                raise ValueError(f"Unknown expression: {expression}")
            effect = raw.get("effect", "none")
            if effect not in vfx.EFFECTS:
                raise ValueError(f"Unknown effect: {effect}")
            self.starts.append(elapsed)
            self.beats.append({"pose": pose, "start": elapsed, "end": elapsed + duration,
                               "duration": duration, "transition": transition,
                               "from_x": x, "to_x": to_x, "facing": facing,
                               "expression": expression, "effect": effect})
            elapsed += duration
            x = to_x
        if not self.beats:
            raise ValueError("A story animation needs at least one beat")
        self.duration = elapsed

    @classmethod
    def from_file(cls, path: str | Path):
        return cls(json.loads(Path(path).read_text(encoding="utf-8")))

    def sample(self, time: float):
        """Return rig state and actor position at a time in seconds."""
        time = max(0.0, min(float(time), self.duration))
        index = min(len(self.beats) - 1, bisect.bisect_right(self.starts, time) - 1)
        beat = self.beats[index]
        local = max(0.0, min(beat["duration"], time - beat["start"]))
        phase = local / 2.0  # The rig's authored loops are two seconds long.
        state = rig.motion_state(beat["pose"], phase, beat["expression"])
        if index and beat["transition"] and local < beat["transition"]:
            previous = self.beats[index - 1]
            previous_state = rig.motion_state(
                previous["pose"], previous["duration"] / 2.0,
                previous["expression"])
            state = rig.blend(previous_state, state, ease(local / beat["transition"]))
        travel = local / beat["duration"]
        # Even spacing keeps walking feet tied to travel; acting shifts settle gently.
        if beat["pose"] not in ("walk", "run", "march", "tiptoe", "side_step", "sneak", "pace", "ponder_walk"):
            travel = ease(travel)
        x = beat["from_x"] + (beat["to_x"] - beat["from_x"]) * travel
        return state, x, beat["facing"], beat["effect"], local

    def svg(self, time: float, transparent: bool = False) -> str:
        state, x, facing, effect, local = self.sample(time)
        top = self.ground_y - self.scale * rig.GROUND
        left = x - self.scale * 250 if facing == 1 else x + self.scale * 250
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" '
                 f'width="{self.width}" height="{self.height}" '
                 f'viewBox="0 0 {self.width} {self.height}">']
        if not transparent:
            parts.append(f'<rect width="100%" height="100%" fill="{escape(self.background)}"/>')
            parts.append(f'<line x1="30" y1="{self.ground_y:.2f}" '
                         f'x2="{self.width-30}" y2="{self.ground_y:.2f}" '
                         'stroke="#d7e1e9" stroke-width="3"/>')
            parts.append(f'<ellipse cx="{x:.2f}" cy="{self.ground_y+3:.2f}" '
                         f'rx="{70*self.scale:.2f}" ry="{8*self.scale:.2f}" fill="#dce6ec"/>')
        parts.append(f'<g transform="translate({left:.3f},{top:.3f}) '
                     f'scale({self.scale*facing:.4f},{self.scale:.4f})">')
        parts.append(rig.draw(state))
        parts.append("</g>")
        parts.append(self._effect_svg(effect, x, facing, local))
        parts.append("</svg>")
        return "".join(parts)

    def _effect_svg(self, effect, x, facing, local):
        y = self.ground_y - 320 * self.scale
        return vfx.effect_svg(effect, x, y, local, self.scale, facing)


def render(sequence: StoryAnimation, output: Path, fmt: str, fps: int,
           width: int, transparent: bool = False):
    if fps <= 0 or width <= 0:
        raise ValueError("fps and width must be positive")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    count = max(2, math.ceil(sequence.duration * fps))
    height = round(width * sequence.height / sequence.width)
    if fmt == "mp4":
        if transparent:
            raise ValueError("Transparent output requires PNG or WebP")
        if width % 2 or height % 2:
            raise ValueError("MP4 dimensions must be even")
        command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                   "-f", "rawvideo", "-pixel_format", "rgb24",
                   "-video_size", f"{width}x{height}", "-framerate", str(fps),
                   "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                   "-pix_fmt", "yuv420p", str(output)]
        process = subprocess.Popen(command, stdin=subprocess.PIPE)
    elif fmt == "png":
        output.mkdir(exist_ok=True)
    elif fmt != "webp":
        raise ValueError(f"Unknown format: {fmt}")
    frames = []
    for index in range(count):
        svg = sequence.svg(index / fps, transparent=transparent)
        frame = rig.raster(svg, width)
        if fmt == "mp4":
            process.stdin.write(frame.convert("RGB").tobytes())
        elif fmt == "png":
            frame.save(output / f"frame_{index:04d}.png")
        else:
            frames.append(frame)
    if fmt == "mp4":
        process.stdin.close()
        if process.wait() != 0:
            raise RuntimeError("FFmpeg render failed")
    elif fmt == "webp":
        frames[0].save(output, format="WEBP", save_all=True,
                       append_images=frames[1:], duration=round(1000 / fps),
                       loop=1, lossless=True, method=4)
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sequence", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--format", choices=("mp4", "webp", "png"), default="mp4")
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--transparent", action="store_true",
                        help="Use a transparent canvas for WebP or PNG")
    args = parser.parse_args()
    sequence = StoryAnimation.from_file(args.sequence)
    frames = render(sequence, args.output, args.format, args.fps,
                    args.width, args.transparent)
    print(f"Rendered {frames} frames / {sequence.duration:.2f}s to {args.output}")


if __name__ == "__main__":
    main()
