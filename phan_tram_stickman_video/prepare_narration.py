#!/usr/bin/env python3
"""Parse the supplied Vietnamese script and synthesize a resumable voice track.

Run with Python 3.11: py -3.11 prepare_narration.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import soundfile as sf

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "source_script.txt"
AUDIO = ROOT / "audio_lines"


def seconds(clock: str) -> int:
    minutes, secs = clock.split(":")
    return int(minutes) * 60 + int(secs)


def display_text(raw: str) -> str:
    raw = raw.strip().replace("**", "")
    raw = raw.replace("\\(", "").replace("\\)", "")
    raw = raw.replace("\\%", "%").replace("^2", "²")
    raw = raw.replace("≈", "xấp xỉ")
    return raw


def spoken_text(raw: str) -> str:
    raw = display_text(raw)
    replacements = {
        "100(1-x/100)(1+x/100)": "một trăm nhân một trừ x chia một trăm, rồi nhân một cộng x chia một trăm",
        "100(1-x²/10000)": "một trăm nhân một trừ x bình phương chia mười nghìn",
        "100(1-x/100)": "một trăm nhân một trừ x chia một trăm",
        "x²/100": "x bình phương chia một trăm",
        "20²/100=4%": "hai mươi bình phương chia một trăm, bằng bốn phần trăm",
        "50²/100=25%": "năm mươi bình phương chia một trăm, bằng hai mươi lăm phần trăm",
        "x%": "x phần trăm",
        "1 ÷ 6 × 100% xấp xỉ 16,67%": "một chia sáu, nhân một trăm phần trăm, xấp xỉ mười sáu phẩy sáu bảy phần trăm",
    }
    for old, new in replacements.items():
        raw = raw.replace(old, new)
    return raw


def parse_script() -> list[dict]:
    text = SOURCE.read_text(encoding="utf-8")
    chunks = re.split(r"(?=^## )", text, flags=re.MULTILINE)
    sections = []
    line_index = 0
    for chunk in chunks:
        if not chunk.strip():
            continue
        lines = chunk.splitlines()
        match = re.match(r"## (\d+:\d+)[–-](\d+:\d+) — (.+)", lines[0])
        if not match:
            raise ValueError(f"Unrecognized section heading: {lines[0]}")
        start, end, title = match.groups()
        section = {"index": len(sections), "start": seconds(start), "end": seconds(end),
                   "title": title, "lines": []}
        for raw in lines[1:]:
            raw = raw.strip()
            if not raw or raw.startswith("**[") or raw.startswith("["):
                continue
            section["lines"].append({"index": line_index,
                                     "display": display_text(raw),
                                     "speech": spoken_text(raw)})
            line_index += 1
        sections.append(section)
    if len(sections) != 6 or sections[-1]["end"] != 300:
        raise ValueError("Expected six sections ending at 5:00")
    return sections


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sections = parse_script()
    AUDIO.mkdir(parents=True, exist_ok=True)
    from vieneu import Vieneu

    tts = Vieneu()
    # The third bundled preset is the same male narrator used in the prior project.
    narrator = list(tts._preset_voices)[2]
    for section in sections:
        for line in section["lines"]:
            path = AUDIO / f"line_{line['index']:03d}.wav"
            if path.exists() and path.stat().st_size > 1000:
                info = sf.info(path)
                line["raw_duration"] = round(info.duration, 4)
                continue
            try:
                audio = tts.infer(text=line["speech"], voice=narrator)
            except Exception as exc:
                print(f"Retrying line {line['index']}: {exc}", flush=True)
                audio = tts.infer(text=line["speech"].replace("%", " phần trăm "), voice=narrator)
            sf.write(path, audio, tts.sample_rate)
            line["raw_duration"] = round(len(audio) / tts.sample_rate, 4)
            print(f"{line['index'] + 1:03d}: {line['raw_duration']:.2f}s", flush=True)
        print(f"Section {section['index'] + 1}: {sum(x['raw_duration'] for x in section['lines']):.1f}s voice / {section['end']-section['start']}s slot", flush=True)
        (ROOT / "narration_manifest.json").write_text(
            json.dumps({"voice": "Anh Khôi", "sample_rate": tts.sample_rate,
                        "sections": sections}, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Narration complete", flush=True)


if __name__ == "__main__":
    main()
