#!/usr/bin/env python3
"""One-command plan validation, voice generation, rendering and QA."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from plan import load_plan, load_sequence
from source_check import check_source

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path, help="JSON plan made from your script")
    parser.add_argument("--out", type=Path, help="Folder for the video and source timing")
    parser.add_argument("--source", type=Path, help="Original Markdown script for dialogue coverage check")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--preview-seconds", type=float, default=0)
    args = parser.parse_args()
    if args.preview_seconds < 0:
        parser.error("--preview-seconds must be positive")
    plan_path = args.plan.resolve()
    try:
        plan = load_plan(plan_path)
    except (ValueError, FileNotFoundError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Plan error: {exc}\n")
    line_count = sum(len(scene["lines"]) for scene in plan["scenes"])
    print(f"Valid plan: {len(plan['scenes'])} scenes, {line_count} lines, {len(plan['cast'])} actors", flush=True)
    if args.source:
        try:
            count = check_source(args.source.resolve(), plan)
        except (ValueError, FileNotFoundError) as exc:
            parser.exit(2, f"Source check error: {exc}\n")
        print(f"Source dialogue matches: {count} turns", flush=True)
    if args.validate_only:
        return
    out = (args.out or plan_path.parent / f"{plan_path.stem}_output").resolve()
    out.mkdir(parents=True, exist_ok=True)
    launcher = shutil.which("py")
    if launcher:
        voice_command = [launcher, "-3.11", "-X", "utf8", str(ROOT / "speech.py")]
    else:
        voice_command = ["python3.11", str(ROOT / "speech.py")]
    subprocess.run([*voice_command, str(plan_path), str(out)], check=True)
    render_command = [sys.executable, "-X", "utf8", str(ROOT / "render.py"),
                      str(plan_path), str(out)]
    if args.preview_seconds:
        render_command += ["--preview-seconds", str(args.preview_seconds)]
    subprocess.run(render_command, check=True)
    video_path = out / ("preview.mp4" if args.preview_seconds else "video.mp4")
    probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                            "format=duration,size", "-show_entries",
                            "stream=codec_type,width,height", "-of", "json", str(video_path)],
                           capture_output=True, text=True, check=True)
    media = json.loads(probe.stdout)
    stream_types = {stream["codec_type"] for stream in media.get("streams", [])}
    if not {"video", "audio"}.issubset(stream_types):
        raise RuntimeError("Output MP4 is missing video or audio")
    timed = json.loads((out / "timed_plan.json").read_text(encoding="utf-8"))
    expected = min(timed["duration"], args.preview_seconds) if args.preview_seconds else timed["duration"]
    actual = float(media["format"]["duration"])
    if abs(expected - actual) > .12:
        raise RuntimeError(f"Output duration differs from timeline: {actual} vs {expected}")
    vfx_used = set()
    for line in timed["lines"]:
        if "effect" in line:
            if line["effect"] != "none":
                vfx_used.add(line["effect"])
        elif "acting_sequence" in line:
            vfx_used.update(beat["effect"] for beat in load_sequence(line["acting_sequence"]).beats
                            if beat["effect"] != "none")
    report = {"status": "media_valid", "checks": ["video_stream", "audio_stream", "duration"],
              "video": video_path.name,
              "duration_seconds": round(actual, 3), "scene_count": len(plan["scenes"]),
              "line_count": line_count, "voice_rate_max": max(s["voice_rate"] for s in timed["scenes"]),
               "acting_sequences": sorted({line["acting_sequence"] for line in timed["lines"]
                                           if "acting_sequence" in line}),
               "vfx_used": sorted(vfx_used),
              "visual_types": sorted({line["visual"]["type"] for line in timed["lines"]})}
    report_file = "qa_report_preview.json" if args.preview_seconds else "qa_report.json"
    (out / report_file).write_text(json.dumps(report, ensure_ascii=False, indent=2),
                                   encoding="utf-8")
    print(f"Verified {video_path} ({actual:.2f}s)", flush=True)


if __name__ == "__main__":
    main()
