"""Small animated SVG effects that can be layered over any stickman pose."""

from __future__ import annotations

import math


EFFECTS = {
    "none": "Không hiệu ứng",
    "surprise": "Tia bất ngờ",
    "thought": "Bong bóng suy nghĩ",
    "idea": "Bật ý tưởng",
    "speed": "Vệt tốc độ",
    "sparkle": "Lấp lánh vui mừng",
    "sweat": "Giọt mồ hôi lo lắng",
    "question": "Dấu hỏi bối rối",
    "impact": "Cú sốc mạnh",
    "anger": "Tia giận dữ",
    "rain": "Mưa quanh nhân vật",
}


def _line(x1, y1, x2, y2, color, width=4, opacity=1):
    return (f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke="{color}" stroke-width="{width}" stroke-linecap="round" '
            f'opacity="{opacity:.3f}"/>')


def _star(x, y, radius, color, opacity=1):
    points = [(x, y - radius), (x + radius * .23, y - radius * .23),
              (x + radius, y), (x + radius * .23, y + radius * .23),
              (x, y + radius), (x - radius * .23, y + radius * .23),
              (x - radius, y), (x - radius * .23, y - radius * .23)]
    coords = " ".join(f"{px:.2f},{py:.2f}" for px, py in points)
    return f'<polygon points="{coords}" fill="{color}" opacity="{opacity:.3f}"/>'


def effect_svg(name: str, x: float, y: float, elapsed: float,
               scale: float = 1.0, facing: int = 1) -> str:
    """Return a self-contained SVG fragment centered near the actor's head."""
    if name not in EFFECTS:
        raise ValueError(f"Unknown VFX: {name}")
    if name == "none":
        return ""
    t = max(0.0, float(elapsed))
    pulse = .72 + .28 * math.sin(t * 9) ** 2
    parts = [f'<g transform="translate({x:.2f},{y:.2f}) '
             f'scale({scale * facing:.4f},{scale:.4f})">']
    if name == "surprise":
        for angle in (-2.4, -1.7, -.95, -.2):
            parts.append(_line(math.cos(angle) * 53, math.sin(angle) * 53,
                               math.cos(angle) * (70 + 11 * pulse),
                               math.sin(angle) * (70 + 11 * pulse), "#e99a33", 5))
    elif name == "thought":
        for i in range(3):
            drift = (t * 10 + i * 3) % 12
            parts.append(f'<circle cx="{47+i*17:.2f}" cy="{-32-i*14-drift:.2f}" '
                         f'r="{(4+i*2)*pulse:.2f}" fill="#7893ad" opacity=".88"/>')
    elif name == "idea":
        parts.append(f'<circle cx="53" cy="-78" r="{14*pulse:.2f}" '
                     'fill="#fbd36a" stroke="#dc9836" stroke-width="3"/>')
        for angle in (-2.8, -1.6, -.4, .6):
            parts.append(_line(53 + math.cos(angle) * 22, -78 + math.sin(angle) * 22,
                               53 + math.cos(angle) * 32, -78 + math.sin(angle) * 32,
                               "#dc9836", 3))
    elif name == "speed":
        for i in range(3):
            shift = (t * 45) % 30
            parts.append(_line(-105 - i * 10 + shift, 55 + i * 31,
                               -52 - i * 6 + shift, 55 + i * 31,
                               "#84abc8", 4, .8))
    elif name == "sparkle":
        for i, (sx, sy, size) in enumerate(((-64, -45, 13), (65, -63, 18),
                                             (78, 39, 12), (-58, 38, 10))):
            twinkle = .35 + .65 * math.sin(t * 7 + i * 1.5) ** 2
            parts.append(_star(sx, sy, size * (.7 + .3 * twinkle),
                               "#e9aa39" if i % 2 else "#f5ca59", twinkle))
    elif name == "sweat":
        for i in range(2):
            drop = (t * 28 + i * 19) % 42
            dx = 43 + i * 21
            dy = -29 + drop
            parts.append(f'<path d="M{dx:.2f} {dy-15:.2f} '
                         f'C{dx+9:.2f} {dy-1:.2f} {dx+9:.2f} {dy+7:.2f} '
                         f'{dx:.2f} {dy+8:.2f} C{dx-9:.2f} {dy+7:.2f} '
                         f'{dx-8:.2f} {dy-1:.2f} {dx:.2f} {dy-15:.2f}Z" '
                         f'fill="#64acd2" opacity="{.85-i*.22:.2f}"/>')
    elif name == "question":
        bob = 3 * math.sin(t * 5)
        parts.append(f'<g transform="translate(0,{bob:.2f})">'
                     '<circle cx="68" cy="-65" r="35" fill="white" '
                     'stroke="#7f9bb2" stroke-width="3"/>'
                     '<path d="M53 -75 C54 -96 81 -97 84 -76 C87 -59 66 -56 67 -43" '
                     'fill="none" stroke="#426d91" stroke-width="6" '
                     'stroke-linecap="round"/>'
                     '<circle cx="67" cy="-31" r="4" fill="#426d91"/></g>')
    elif name == "impact":
        for i in range(8):
            angle = i * math.tau / 8 - .2
            inner = 54 + 2 * math.sin(t * 10 + i)
            outer = 78 + 13 * pulse
            parts.append(_line(math.cos(angle) * inner, math.sin(angle) * inner,
                               math.cos(angle) * outer, math.sin(angle) * outer,
                               "#e56b35" if i % 2 else "#f2b54e", 5))
        parts.append(_star(-73, -65, 13 * pulse, "#e56b35"))
    elif name == "anger":
        for i in range(2):
            sx = -57 + i * 92
            sy = -77 + 3 * math.sin(t * 10 + i)
            coords = " ".join(f"{px:.2f},{py:.2f}" for px, py in
                              ((sx, sy), (sx + 13, sy - 11), (sx + 7, sy + 4),
                               (sx + 23, sy - 5), (sx + 16, sy + 13)))
            parts.append(f'<polyline points="{coords}" fill="none" '
                         'stroke="#dc5964" stroke-width="5" '
                         'stroke-linecap="round" stroke-linejoin="round"/>')
    elif name == "rain":
        for i, sx in enumerate((-95, -66, -34, 3, 39, 72, 100)):
            sy = ((t * 95 + i * 43) % 270) - 110
            parts.append(_line(sx, sy, sx - 9, sy + 23, "#71a7ca", 3, .7))
    parts.append("</g>")
    return "".join(parts)
