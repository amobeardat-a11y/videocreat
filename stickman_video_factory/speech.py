#!/usr/bin/env python3
"""Synthesize, cache and align dialogue from a validated video plan."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

from plan import load_plan, load_sequence

VOICE_NAMES = {"comic_male": "Adam bựa", "calm_male": "Anh Khôi",
               "warm_female": "Mai Anh", "clear_female": "Thùy Dung"}


def caption_parts(value: str, width=55) -> list[str]:
    parts, current = [], ""
    for word in value.split():
        candidate = f"{current} {word}".strip()
        if len(candidate) > width and current:
            parts.append(current)
            current = word
        else:
            current = candidate
    if current:
        parts.append(current)
    return parts


def clock(seconds: float) -> str:
    ms = round(seconds * 1000)
    hours, ms = divmod(ms, 3_600_000)
    minutes, ms = divmod(ms, 60_000)
    secs, ms = divmod(ms, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def make_audio(plan_path: Path, out: Path) -> dict:
    plan = load_plan(plan_path)
    out.mkdir(parents=True, exist_ok=True)
    audio_dir = out / "audio_lines"
    audio_dir.mkdir(exist_ok=True)
    manifest_path = out / "audio_manifest.json"
    old = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    old_entries = old.get("entries", {})
    cast = {actor["id"]: actor for actor in plan["cast"]}
    entries = {}
    requests = []
    index = 0
    for scene in plan["scenes"]:
        for line in scene["lines"]:
            spoken = line.get("spoken", line["text"])
            voice = VOICE_NAMES[cast[line["speaker"]]["voice_style"]]
            digest = hashlib.sha256(f"{voice}\0{spoken}".encode("utf-8")).hexdigest()
            key = f"{index:03d}"
            path = audio_dir / f"line_{key}.wav"
            entries[key] = {"sha256": digest, "voice": voice, "spoken": spoken}
            if not (path.exists() and path.stat().st_size > 1024
                    and old_entries.get(key, {}).get("sha256") == digest):
                requests.append((index, path, spoken, voice))
            index += 1
    if requests:
        from vieneu import Vieneu
        tts = Vieneu()
        for index, path, spoken, voice in requests:
            if voice not in tts._preset_voices:
                raise ValueError(f"Local VieNeu voice unavailable: {voice}")
            audio = tts.infer(text=spoken, voice=voice, show_progress=False)
            sf.write(path, audio, tts.sample_rate)
            print(f"Voice {index+1}/{len(entries)}: {voice}", flush=True)
            # Persist after each line so an interrupted build can resume safely.
            old_entries[f"{index:03d}"] = entries[f"{index:03d}"]
            manifest_path.write_text(json.dumps({"entries": old_entries}, ensure_ascii=False, indent=2),
                                     encoding="utf-8")
    manifest_path.write_text(json.dumps({"entries": entries}, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    sample_rate = None
    scenes_out, lines_out, scene_audio = [], [], []
    cursor = 0.0
    global_index = 0
    for si, scene in enumerate(plan["scenes"]):
        clips = []
        for _ in scene["lines"]:
            clip, sr = sf.read(audio_dir / f"line_{global_index:03d}.wav", dtype="float32")
            if clip.ndim == 2:
                clip = clip.mean(axis=1)
            sample_rate = sample_rate or sr
            if sr != sample_rate:
                raise ValueError("Voice clips have different sample rates")
            clips.append(clip)
            global_index += 1
        n = len(clips)
        gaps = [0.26] + [0.18] * (n - 1) + [0.34]
        for li, line in enumerate(scene["lines"]):
            gaps[li + 1] += line.get("pause_after", 0)
            if "acting_sequence" in line:
                natural = load_sequence(line["acting_sequence"]).duration
                minimum = min(4.0, max(2.4, natural * .6))
                gaps[li + 1] = max(gaps[li + 1], minimum - len(clips[li]) / sample_rate / 1.18)
        speech = sum(len(clip) / sample_rate for clip in clips)
        nominal = scene.get("target_seconds", speech + sum(gaps) + .8)
        target = max(nominal, speech / 1.18 + sum(gaps))
        if speech + sum(gaps) < target:
            extra = (target - speech - sum(gaps)) / len(gaps)
            gaps = [gap + extra for gap in gaps]
            rate = 1.0
        else:
            rate = speech / (target - sum(gaps))
        raw_parts = []
        local = 0.0
        last_visual = None
        last_visual_start = cursor
        for li, (line, clip) in enumerate(zip(scene["lines"], clips)):
            gap = gaps[li]
            raw_parts.append(np.zeros(round(gap * rate * sample_rate), dtype=np.float32))
            local += gap
            start = cursor + local
            local += len(clip) / sample_rate / rate
            if "visual" in line:
                last_visual = line["visual"]
                last_visual_start = start
            timed_line = {**line, "index": len(lines_out), "scene": si,
                          "visual": last_visual, "visual_start": round(last_visual_start, 3),
                          "start": round(start, 3),
                          "end": round(cursor + local, 3)}
            if "acting_sequence" in line:
                timed_line["acting_end"] = round(cursor + local + gaps[li + 1], 3)
            lines_out.append(timed_line)
            raw_parts.append(clip)
        raw_parts.append(np.zeros(round(gaps[-1] * rate * sample_rate), dtype=np.float32))
        raw = np.concatenate(raw_parts)
        if abs(rate - 1) > .0001:
            with tempfile.TemporaryDirectory() as folder:
                raw_path = Path(folder) / "raw.wav"
                fitted_path = Path(folder) / "fitted.wav"
                sf.write(raw_path, raw, sample_rate)
                subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                                "-i", str(raw_path), "-af", f"atempo={rate:.6f}",
                                "-ar", str(sample_rate), "-ac", "1", str(fitted_path)], check=True)
                fitted, _ = sf.read(fitted_path, dtype="float32")
        else:
            fitted = raw
        needed = round(target * sample_rate)
        fitted = np.pad(fitted[:needed], (0, max(0, needed - len(fitted))))
        scene_audio.append(fitted)
        scenes_out.append({"index": si, "title": scene["title"],
                           "start": round(cursor, 3), "end": round(cursor + target, 3),
                           "voice_rate": round(rate, 3)})
        cursor += target
        print(f"Scene {si+1}: {target:.1f}s at {rate:.3f}x", flush=True)
    full = np.concatenate(scene_audio)
    sf.write(out / "dialogue.wav", full, sample_rate)
    timeline = {"title": plan["title"], "cast": plan["cast"],
                "duration": round(len(full) / sample_rate, 3),
                "scenes": scenes_out, "lines": lines_out}
    (out / "timed_plan.json").write_text(json.dumps(timeline, ensure_ascii=False, indent=2),
                                         encoding="utf-8")
    captions = []
    names = {actor["id"]: actor["name"] for actor in plan["cast"]}
    for line in lines_out:
        parts = caption_parts(line["text"])
        total = sum(len(part) for part in parts)
        used = 0
        for part in parts:
            begin = line["start"] + (line["end"] - line["start"]) * used / total
            used += len(part)
            end = line["start"] + (line["end"] - line["start"]) * used / total
            captions.append((begin, end, f"{names[line['speaker']]}: {part}"))
    (out / "subtitles.srt").write_text("\n\n".join(
        f"{i}\n{clock(start)} --> {clock(end)}\n{text}"
        for i, (start, end, text) in enumerate(captions, 1)) + "\n", encoding="utf-8")
    return timeline


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args()
    result = make_audio(args.plan, args.out)
    print(f"Dialogue: {result['duration']:.2f}s, {len(result['lines'])} lines", flush=True)


if __name__ == "__main__":
    main()
