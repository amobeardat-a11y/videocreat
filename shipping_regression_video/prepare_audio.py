#!/usr/bin/env python3
"""Generate resumable Vietnamese dialogue with the locally installed VieNeu model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import soundfile as sf

ROOT = Path(__file__).resolve().parent
AUDIO = ROOT / "audio_lines"


def speech_text(value: str) -> str:
    return (value.replace("1 km", "một ki lô mét")
                 .replace("2 km", "hai ki lô mét")
                 .replace("5 km", "năm ki lô mét")
                 .replace("MSE", "em ét i")
                 .replace("AI", "ây ai"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0, help="Only synthesize this many lines")
    args = parser.parse_args()
    data = json.loads((ROOT / "dialogue.json").read_text(encoding="utf-8"))
    AUDIO.mkdir(exist_ok=True)
    from vieneu import Vieneu

    tts = Vieneu()
    voices = list(tts._preset_voices)
    names = {"Nam": voices[0], "Minh": voices[2]}
    print("Voices:", names, flush=True)
    index = 0
    for scene in data["scenes"]:
        for speaker, line, _ in scene["lines"]:
            if args.limit and index >= args.limit:
                return
            path = AUDIO / f"line_{index:03d}.wav"
            if path.exists() and path.stat().st_size > 1024:
                duration = sf.info(path).duration
            else:
                audio = tts.infer(text=speech_text(line), voice=names[speaker],
                                  show_progress=False)
                sf.write(path, audio, tts.sample_rate)
                duration = len(audio) / tts.sample_rate
            print(f"{index:03d} {speaker:4s} {duration:5.2f}s {line[:55]}", flush=True)
            index += 1


if __name__ == "__main__":
    main()
