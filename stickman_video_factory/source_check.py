"""Compare a model's plan against dialogue in the original Markdown script."""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = re.sub(r"\*{1,2}", "", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip().casefold()


def group_turns(turns):
    result = []
    for speaker, value in turns:
        if result and result[-1][0] == speaker:
            result[-1] = (speaker, result[-1][1] + " " + value)
        else:
            result.append((speaker, value))
    return [(speaker, normalize(value)) for speaker, value in result]


def original_turns(path: Path, names: set[str]):
    turns = []
    lines = path.read_text(encoding="utf-8").splitlines()
    pending = None
    for raw in lines:
        plain = raw.strip().replace("**", "").replace("__", "")
        match = re.match(r"^([^:]{1,65}):\s*(.*)$", plain)
        if match:
            speaker = re.sub(r"\s*\([^)]*\)\s*", "", match.group(1)).strip()
            name = next((name for name in names if normalize(name) == normalize(speaker)), None)
            if name is not None:
                value = match.group(2).strip()
                if value:
                    turns.append((normalize(name), value))
                    pending = None
                else:
                    pending = normalize(name)
                continue
        if pending and plain and not plain.startswith(("*", "[", "#", "|", "-")):
            turns.append((pending, plain))
            pending = None
    return group_turns(turns)


def planned_turns(plan):
    names = {actor["id"]: actor["name"] for actor in plan["cast"]}
    turns = []
    for scene in plan["scenes"]:
        for line in scene["lines"]:
            turns.append((normalize(names[line["speaker"]]), line["text"]))
    return group_turns(turns)


def check_source(source_path: Path, plan: dict):
    names = {actor["name"] for actor in plan["cast"]}
    original = original_turns(source_path, names)
    if not original:
        raise ValueError("Source check found no labeled dialogue for the cast names")
    planned = planned_turns(plan)
    for index, (a, b) in enumerate(zip(original, planned), 1):
        if a != b:
            raise ValueError(
                f"Dialogue mismatch at turn {index}. Source: {a[0]}: {a[1][:100]!r}; "
                f"plan: {b[0]}: {b[1][:100]!r}")
    if len(original) != len(planned):
        raise ValueError(f"Dialogue turn count differs: source {len(original)}, plan {len(planned)}")
    return len(original)
