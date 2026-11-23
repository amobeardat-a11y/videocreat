#!/usr/bin/env python3
"""Align every spoken line to the six scenes and assemble the dialogue track."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent


def srt_time(seconds: float) -> str:
    millis = round(seconds * 1000)
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def chunks(value: str, width=54) -> list[str]:
    result, current = [], ""
    for word in value.split():
        next_value = f"{current} {word}".strip()
        if len(next_value) > width and current:
            result.append(current)
            current = word
        else:
            current = next_value
    if current:
        result.append(current)
    return result


def main() -> None:
    source = json.loads((ROOT / "dialogue.json").read_text(encoding="utf-8"))
    scenes_out, lines_out, audio_scenes = [], [], []
    sample_rate = None
    global_index = 0
    cursor = 0.0
    for scene_index, scene in enumerate(source["scenes"]):
        clips = []
        for _ in scene["lines"]:
            path = ROOT / "audio_lines" / f"line_{global_index:03d}.wav"
            if not path.exists():
                raise FileNotFoundError(f"Voice line missing: {path.name}")
            clip, sr = sf.read(path, dtype="float32")
            if clip.ndim == 2:
                clip = clip.mean(axis=1)
            sample_rate = sample_rate or sr
            if sr != sample_rate:
                raise ValueError(f"Sample rate mismatch: {path}")
            clips.append(clip)
            global_index += 1
        n = len(clips)
        nominal = scene["end"] - scene["start"]
        raw_speech = sum(len(x) / sample_rate for x in clips)
        gaps = [0.28] + [0.17] * (n - 1) + [0.34]
        if scene_index == 2:
            gaps[-2] += 2.0  # Silence after Minh's philosophy line.
        if scene_index == 4:
            gaps[10] += 0.65  # Nam has no answer to the missing data.
        if scene_index == 5:
            gaps[-2] += 1.4  # Minh's silent reaction before the last line.
        target = max(nominal, raw_speech / 1.18 + sum(gaps))
        if raw_speech + sum(gaps) < target:
            extra = (target - raw_speech - sum(gaps)) / len(gaps)
            gaps = [x + extra for x in gaps]
            rate = 1.0
        else:
            rate = raw_speech / (target - sum(gaps))
        assert 1 <= rate <= 1.180001
        raw_pieces = []
        local = 0.0
        start = cursor
        for index, (line, clip) in enumerate(zip(scene["lines"], clips)):
            gap = gaps[index]
            raw_pieces.append(np.zeros(round(gap * rate * sample_rate), dtype=np.float32))
            local += gap
            speaker, text, visual = line
            line_start = start + local
            local += len(clip) / sample_rate / rate
            lines_out.append({"index": len(lines_out), "scene": scene_index,
                              "speaker": speaker, "text": text, "visual": visual,
                              "start": round(line_start, 3), "end": round(start + local, 3)})
            raw_pieces.append(clip)
        raw_pieces.append(np.zeros(round(gaps[-1] * rate * sample_rate), dtype=np.float32))
        scene_raw = np.concatenate(raw_pieces)
        if abs(rate - 1) > 0.0001:
            with tempfile.TemporaryDirectory() as temp:
                raw_path = Path(temp) / "raw.wav"
                out_path = Path(temp) / "fitted.wav"
                sf.write(raw_path, scene_raw, sample_rate)
                subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                                "-i", str(raw_path), "-af", f"atempo={rate:.6f}",
                                "-ar", str(sample_rate), "-ac", "1", str(out_path)], check=True)
                fitted, _ = sf.read(out_path, dtype="float32")
        else:
            fitted = scene_raw
        needed = round(target * sample_rate)
        fitted = np.pad(fitted[:needed], (0, max(0, needed - len(fitted))))
        audio_scenes.append(fitted)
        scenes_out.append({"index": scene_index, "title": scene["title"],
                           "start": round(start, 3), "end": round(start + target, 3),
                           "nominal_duration": nominal, "voice_rate": round(rate, 3)})
        cursor += target
        print(f"Scene {scene_index+1}: {target:.1f}s, voice rate {rate:.3f}")
    full = np.concatenate(audio_scenes)
    sf.write(ROOT / "dialogue.wav", full, sample_rate)
    timeline = {"title": source["title"], "duration": round(len(full) / sample_rate, 3),
                "fps": 18, "scenes": scenes_out, "lines": lines_out}
    (ROOT / "timed_dialogue.json").write_text(
        json.dumps(timeline, ensure_ascii=False, indent=2), encoding="utf-8")
    captions = []
    for line in lines_out:
        parts = chunks(line["text"])
        weights = [len(x) for x in parts]
        total = sum(weights)
        used = 0
        for part, weight in zip(parts, weights):
            begin = line["start"] + (line["end"] - line["start"]) * used / total
            used += weight
            end = line["start"] + (line["end"] - line["start"]) * used / total
            captions.append((begin, end, f"{line['speaker']}: {part}"))
    (ROOT / "subtitles.srt").write_text("\n\n".join(
        f"{i}\n{srt_time(a)} --> {srt_time(b)}\n{value}"
        for i, (a, b, value) in enumerate(captions, 1)) + "\n", encoding="utf-8")
    print(f"Total {timeline['duration']:.1f}s, {len(lines_out)} lines, {len(captions)} captions")


if __name__ == "__main__":
    main()
