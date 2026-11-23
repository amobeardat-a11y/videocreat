#!/usr/bin/env python3
"""Fit narration to the six authored time ranges and write synchronized captions."""

from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent


def caption_chunks(text: str, max_chars: int = 52) -> list[str]:
    words = text.split()
    chunks, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) > max_chars and current:
            chunks.append(current)
            current = word
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def srt_clock(time: float) -> str:
    milliseconds = round(time * 1000)
    hours, milliseconds = divmod(milliseconds, 3600000)
    minutes, milliseconds = divmod(milliseconds, 60000)
    seconds, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def main() -> None:
    manifest = json.loads((ROOT / "narration_manifest.json").read_text(encoding="utf-8"))
    sections = manifest["sections"]
    sample_rate = manifest["sample_rate"]
    final_sections = []
    captions = []
    for section in sections:
        target = section["end"] - section["start"]
        lines = section["lines"]
        speech = sum(line["raw_duration"] for line in lines)
        desired_gap = .30
        rate = speech / (target - desired_gap * (len(lines) + 1))
        if rate < .88:
            rate = .88
        if rate > 1.25:
            rate = 1.25
        output_gap = (target - speech / rate) / (len(lines) + 1)
        if output_gap < .05:
            rate = speech / (target - .12 * (len(lines) + 1))
            output_gap = .12
        raw_gap = output_gap * rate
        pieces = [np.zeros(round(raw_gap * sample_rate), dtype=np.float32)]
        cursor = raw_gap
        timed_lines = []
        for line in lines:
            path = ROOT / "audio_lines" / f"line_{line['index']:03d}.wav"
            audio, sr = sf.read(path, dtype="float32")
            if sr != sample_rate:
                raise ValueError(f"Sample rate drift: {path}")
            if audio.ndim > 1:
                audio = audio.mean(axis=1)
            start = section["start"] + cursor / rate
            end = section["start"] + (cursor + len(audio) / sample_rate) / rate
            timed_line = {**line, "section": section["index"],
                          "start": round(start, 4), "end": round(end, 4)}
            timed_lines.append(timed_line)
            chunks = caption_chunks(line["display"])
            weights = [max(1, len(chunk)) for chunk in chunks]
            total = sum(weights)
            used = 0
            for chunk, weight in zip(chunks, weights):
                cstart = start + (end - start) * used / total
                used += weight
                cend = start + (end - start) * used / total
                captions.append({"start": round(cstart, 3), "end": round(cend, 3),
                                 "text": chunk, "line_index": line["index"]})
            pieces.append(audio)
            pieces.append(np.zeros(round(raw_gap * sample_rate), dtype=np.float32))
            cursor += len(audio) / sample_rate + raw_gap
        raw = np.concatenate(pieces)
        with tempfile.TemporaryDirectory() as temp:
            raw_path = Path(temp) / "raw.wav"
            fitted_path = Path(temp) / "fitted.wav"
            sf.write(raw_path, raw, sample_rate)
            subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                            "-i", str(raw_path), "-af",
                            f"atempo={rate:.6f},apad,atrim=0:{target}",
                            "-ar", str(sample_rate), "-ac", "1", str(fitted_path)], check=True)
            fitted, sr = sf.read(fitted_path, dtype="float32")
        needed = round(target * sample_rate)
        fitted = np.pad(fitted[:needed], (0, max(0, needed - len(fitted))))
        final_sections.append(fitted)
        section["lines"] = timed_lines
        section["voice_rate"] = round(rate, 4)
        section["pause_seconds"] = round(output_gap, 4)
        print(f"Section {section['index'] + 1}: voice rate {rate:.3f}, pause {output_gap:.2f}s")
    full = np.concatenate(final_sections)
    sf.write(ROOT / "narration.wav", full, sample_rate)
    (ROOT / "timed_script.json").write_text(json.dumps({"duration": 300,
        "sample_rate": sample_rate, "sections": sections, "captions": captions},
        ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "subtitles.srt").write_text("\n\n".join(
        f"{i}\n{srt_clock(c['start'])} --> {srt_clock(c['end'])}\n{c['text']}"
        for i, c in enumerate(captions, 1)) + "\n", encoding="utf-8")
    print(f"Built narration.wav: {len(full)/sample_rate:.2f}s, {len(captions)} captions")


if __name__ == "__main__":
    main()
