#!/usr/bin/env python3
"""Create a small handoff ZIP with the builder, runtime rig, font and example."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent


def main():
    relatives = [
        "stickman_video_factory/README.md",
        "stickman_video_factory/MODEL_PROMPT.md",
        "stickman_video_factory/AGENT_TASK.md",
        "stickman_video_factory/build.py",
        "stickman_video_factory/plan.py",
        "stickman_video_factory/speech.py",
        "stickman_video_factory/render.py",
        "stickman_video_factory/source_check.py",
        "stickman_video_factory/package_factory.py",
        "stickman_video_factory/examples/discount_story.json",
        "stickman_video_factory/examples/discount_script.md",
        "stickman_video_factory/examples/discount_output/video.mp4",
        "stickman_video_factory/examples/discount_output/subtitles.srt",
        "stickman_video_factory/examples/discount_output/contact_sheet.png",
        "stickman_video_factory/examples/discount_output/qa_report.json",
        "stickman_video_factory/examples/acting_sequence_story.json",
        "stickman_video_factory/examples/acting_sequence_script.md",
        "stickman_video_factory/examples/acting_sequence_output/video.mp4",
        "stickman_video_factory/examples/acting_sequence_output/subtitles.srt",
        "stickman_video_factory/examples/acting_sequence_output/contact_sheet.png",
        "stickman_video_factory/examples/acting_sequence_output/qa_report.json",
        "stickman_assets/stickman.py",
        "stickman_assets/manifest.json",
        "stickman_assets/README.md",
        "stickman_assets/CATALOG.md",
        "stickman_assets/requirements.txt",
        "stickman_assets/story_animation.py",
        "stickman_assets/vfx.py",
        "phan_tram_stickman_video/NotoSans.ttf",
        "phan_tram_stickman_video/OFL-NotoSans.txt",
    ]
    for path in sorted((WORKSPACE / "stickman_assets" / "sequences").glob("*.json")):
        relatives.extend([
            f"stickman_assets/sequences/{path.stem}.json",
            f"stickman_assets/sequences/{path.stem}.webp",
        ])
    files = [(WORKSPACE / relative).resolve() for relative in relatives]
    if not all(path.is_relative_to(WORKSPACE) and path.is_file() for path in files):
        raise FileNotFoundError("A handoff file is missing or outside the workspace")
    output = WORKSPACE / "stickman_video_factory.zip"
    temporary = output.with_suffix(".zip.tmp")
    with ZipFile(temporary, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            archive.write(path, path.relative_to(WORKSPACE).as_posix())
    with ZipFile(temporary) as archive:
        if archive.testzip() is not None or len(archive.namelist()) != len(files):
            raise RuntimeError("ZIP verification failed")
    temporary.replace(output)
    print(f"Packed {len(files)} files: {output} ({output.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
