#!/usr/bin/env python3
"""Small, prop-free SVG stickman rig with loop and transition export.

Angles: 0 points down, +90 points right, 180 points up. The SVG canvas is
transparent. `python stickman.py package` rebuilds the distributable assets.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import subprocess
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

INK = "#1f2933"
W, H, GROUND = 500, 600, 510
TORSO, UPPER_ARM, FOREARM, THIGH, SHIN, HEAD_R = 110, 70, 65, 90, 90, 32
ROOT = Path(__file__).resolve().parent


def dots(radius=3.2, y=-5):
    return "".join(
        f'<circle cx="{x}" cy="{y}" r="{radius}" fill="{INK}" stroke="none"/>'
        for x in (-11, 11)
    )


def filled_mouth(path):
    return f'<path d="{path}" fill="{INK}"/>'


# Facial art stays independent from the body pose, so either can be chosen at render time.
FACES = {
    "neutral": (dots() + '<path d="M-8 14H8"/>', "Bình thường"),
    "happy": (dots() + '<path d="M-12 8Q0 24 12 8"/>', "Vui"),
    "talk": (dots() + f'<ellipse cx="0" cy="14" rx="7" ry="5" fill="{INK}"/>', "Đang nói"),
    "surprised": ('<circle cx="-11" cy="-5" r="5"/><circle cx="11" cy="-5" r="5"/>'
                  '<path d="M-17-17Q-11-23-5-17M5-17Q11-23 17-17"/>'
                  '<ellipse cx="0" cy="15" rx="5" ry="7"/>', "Ngạc nhiên"),
    "sad": (dots(3.2, -3) + '<path d="M-17-10L-6-16M6-16L17-10"/>'
            '<path d="M-9 20Q0 10 9 20"/>', "Buồn"),
    "angry": (dots(3.2, -3) + '<path d="M-18-16L-6-9M6-9L18-16"/>'
              '<path d="M-9 18Q0 12 9 18"/>', "Giận"),
    "thinking": (dots(3, -8) + '<path d="M5-18Q11-22 17-17"/>'
                 '<path d="M-6 16L8 12"/>', "Suy nghĩ"),
    "confused": (dots() + '<path d="M-17-14L-6-17M6-13L17-18"/>'
                 '<path d="M-10 15Q-5 9 0 15T10 15"/>', "Bối rối"),
    "laugh": ('<path d="M-17-3Q-11-11-5-3M5-3Q11-11 17-3"/>'
              + filled_mouth("M-12 8H12Q10 26 0 26Q-10 26-12 8Z"), "Cười lớn"),
    "wink": (f'<circle cx="-11" cy="-5" r="3.2" fill="{INK}" stroke="none"/>'
             '<path d="M5-3Q11-11 17-3"/><path d="M-12 8Q0 24 12 8"/>', "Nháy mắt"),
    "bored": ('<path d="M-17-5H-6M6-5H17"/><path d="M-8 15H8"/>', "Chán"),
    "excited": (dots(4.5) + filled_mouth("M-13 7H13Q10 26 0 26Q-10 26-13 7Z"), "Hào hứng"),
    "blink": ('<path d="M-17-5H-5M5-5H17"/><path d="M-9 13Q0 20 9 13"/>', "Chớp mắt"),
    "determined": (dots() + '<path d="M-17-14L-5-9M5-9L17-14M-9 16H9"/>', "Quyết tâm"),
    "worried": (dots() + '<path d="M-18-12Q-11-19-5-14M5-14Q11-19 18-12"/>'
                '<path d="M-8 21Q0 9 8 21"/>', "Lo lắng"),
    "embarrassed": (dots() + '<path d="M-8 13Q0 20 8 13"/>'
                   '<path d="M-25 8l7-2M18 6l7 2" stroke="#e07a80"/>', "Ngượng ngùng"),
    "sleepy": ('<path d="M-17-3Q-11 1-5-3M5-3Q11 1 17-3"/>'
               '<ellipse cx="0" cy="17" rx="4" ry="6"/>', "Buồn ngủ"),
    "curious": (dots(3.5, -6) + '<path d="M4-18Q11-23 18-16"/>'
                '<path d="M-5 14Q1 10 7 15"/>', "Tò mò"),
    "proud": (dots() + '<path d="M-14 7Q0 23 14 7"/>'
              '<path d="M-18-15L-6-12M6-12L18-15"/>', "Tự hào"),
    "crying": (dots() + '<path d="M-10 21Q0 8 10 21"/>'
               '<path d="M-12 0v11M12 0v11" stroke="#2b8ed1"/>', "Khóc"),
    "skeptical": (f'<circle cx="-11" cy="-5" r="3.2" fill="{INK}" stroke="none"/>'
                  '<path d="M5-5H17M5-16L18-21M-8 16L9 13"/>', "Hoài nghi"),
}

# Extra faces for quieter acting and sharper emotional changes.
FACES.update({
    "focused": ('<path d="M-18-7L-5-5M5-5L18-7"/><path d="M-17-16L-5-12M5-12L17-16"/>'
                '<path d="M-6 17H6"/>', "Tập trung"),
    "panic": ('<circle cx="-11" cy="-5" r="5.5"/><circle cx="11" cy="-5" r="5.5"/>'
              '<path d="M-19-18Q-11-24-4-18M4-18Q11-24 19-18"/>'
              '<path d="M-9 14Q-5 9-1 15T9 14V23H-9Z"/>', "Hoảng hốt"),
    "smirk": (dots() + '<path d="M-18-16L-5-18M5-17L18-11"/>'
              '<path d="M-11 11Q2 21 13 9"/>', "Cười nhếch mép"),
    "amazed": ('<circle cx="-11" cy="-5" r="5"/><circle cx="11" cy="-5" r="5"/>'
               '<path d="M-17-18Q-11-23-5-18M5-18Q11-23 17-18"/>'
               '<path d="M-12 9Q0 28 12 9Z"/>', "Kinh ngạc thích thú"),
    "grateful": ('<path d="M-17-4Q-11-10-5-4M5-4Q11-10 17-4"/>'
                 '<path d="M-12 9Q0 22 12 9"/>'
                 '<path d="M-24 7l5-2M19 5l5 2" stroke="#e7a0a2"/>', "Biết ơn"),
    "frustrated": ('<path d="M-18-8H-5M5-8H18M-19-17L-5-11M5-11L19-17"/>'
                   '<path d="M-10 15H10M-7 15v5M0 15v5M7 15v5"/>', "Bực bội"),
})

DEFAULT = dict(t=0, h=0, la=(-14, -8), ra=(14, 8), ll=(-7, -3),
               rl=(7, 3), e="neutral", dx=0, lift=0, feet="out")
POSES = {
    "idle": ("Đứng nghỉ", dict(e="happy")),
    "talk": ("Nói và minh họa", dict(ra=(45, 125), h=3, e="talk")),
    "explain_open": ("Giải thích hai tay", dict(la=(-50, -125), ra=(50, 125), e="talk")),
    "point_side": ("Chỉ sang bên", dict(ra=(80, 88), t=3, h=5, e="talk")),
    "point_up": ("Chỉ lên trên", dict(ra=(115, 140), e="talk")),
    "explain_up": ("Nêu ý kiến", dict(ra=(60, 170), e="talk")),
    "raise_hand": ("Giơ tay", dict(ra=(165, 178), e="happy")),
    "think": ("Chống cằm suy nghĩ", dict(ra=(90, 253), h=8, e="thinking")),
    "idea": ("Nảy ra ý tưởng", dict(ra=(150, 172), e="excited")),
    "confused": ("Gãi đầu bối rối", dict(ra=(110, 232), h=-6, e="confused")),
    "wave": ("Vẫy tay", dict(ra=(105, 165), h=4, e="happy")),
    "shrug": ("Nhún vai", dict(la=(-35, -100), ra=(35, 100), h=6, e="confused")),
    "arms_crossed": ("Khoanh tay", dict(la=(-20, 95), ra=(20, -95), e="skeptical")),
    "hands_on_hips": ("Chống nạnh", dict(la=(-50, 34), ra=(50, -34), e="proud")),
    "walk": ("Đi tại chỗ", dict(t=5, la=(-25, -15), ra=(25, 15), ll=(-2, 0), rl=(2, 0), feet="right", e="happy")),
    "run": ("Chạy tại chỗ", dict(t=18, la=(-50, -20), ra=(40, 120), ll=(-3, 0), rl=(3, 0), feet="right", e="determined")),
    "celebrate": ("Ăn mừng", dict(la=(-135, -155), ra=(135, 155), ll=(-18, -10), rl=(18, 10), lift=35, e="laugh")),
    "bow": ("Cúi chào", dict(t=55, h=10, la=(-4, 0), ra=(4, 0), e="happy")),
    "facepalm": ("Ôm mặt", dict(t=3, h=-6, ra=(130, 262), e="sad")),
    "surprised": ("Giật mình", dict(t=-4, la=(-110, -170), ra=(110, 170), e="surprised")),
    "clap": ("Vỗ tay", dict(la=(-45, 120), ra=(45, -120), e="happy")),
    "listen": ("Chú ý lắng nghe", dict(t=7, h=-8, ra=(55, 210), e="curious")),
    "nod": ("Gật đầu đồng ý", dict(h=10, e="happy")),
    "shake_head": ("Lắc đầu phản đối", dict(h=-8, e="skeptical")),
    "reach": ("Vươn tay lấy", dict(t=12, ra=(82, 100), e="determined")),
    "jump": ("Nhảy lên", dict(la=(-125, -155), ra=(125, 155), ll=(-32, -70), rl=(32, 70), lift=55, e="excited")),
    "dance": ("Nhảy múa", dict(t=-8, la=(-110, -150), ra=(70, 145), ll=(-20, -35), rl=(30, 15), lift=12, e="happy")),
    "stretch": ("Vươn vai", dict(la=(-165, -175), ra=(165, 175), e="sleepy")),
    "sneak": ("Rón rén", dict(t=28, la=(-30, -95), ra=(70, 15), ll=(0, 20), rl=(0, -20), e="worried")),
    "step_back": ("Lùi lại", dict(t=-17, la=(-60, -110), ra=(90, 120), ll=(-20, 20), rl=(35, 15), e="worried")),
}

# Extra prop-free performances for dialogue, reactions, movement and action.
POSES.update({
    "salute": ("Chào kiểu quân lệnh", dict(ra=(80, 214), e="proud")),
    "beckon": ("Ra hiệu lại gần", dict(ra=(80, 160), t=5, e="happy")),
    "whisper": ("Nói thầm", dict(ra=(100, 240), t=8, h=7, e="talk")),
    "present_left": ("Giới thiệu bên trái", dict(la=(-60, -100), t=-4, e="talk")),
    "present_right": ("Giới thiệu bên phải", dict(ra=(60, 100), t=4, e="talk")),
    "apologize": ("Xin lỗi", dict(t=35, h=10, la=(-20, -10), ra=(20, 10), e="embarrassed")),
    "plead": ("Năn nỉ", dict(la=(-50, -130), ra=(50, 130), h=-4, e="worried")),
    "laugh_body": ("Cười nghiêng người", dict(t=12, la=(-55, -25), ra=(55, 25), e="laugh")),
    "cry_body": ("Khóc và lau nước mắt", dict(t=18, h=-8, la=(-25, -15), ra=(100, 240), e="crying")),
    "tremble": ("Run rẩy", dict(t=3, la=(-20, -100), ra=(20, 100), ll=(-10, -10), rl=(10, 10), e="worried")),
    "sigh": ("Thở dài", dict(t=15, h=15, la=(-5, -5), ra=(5, 5), e="sad")),
    "angry_stomp": ("Giậm chân tức giận", dict(t=12, la=(-40, -80), ra=(40, 80), rl=(35, 15), e="angry")),
    "shy": ("Ngại ngùng", dict(t=-5, h=12, la=(-20, 20), ra=(20, -20), e="embarrassed")),
    "sleepy_nod": ("Gật gù buồn ngủ", dict(t=5, h=10, e="sleepy")),
    "relieved": ("Thở phào", dict(t=-6, h=-5, la=(-30, -60), ra=(30, 60), e="happy")),
    "march": ("Bước đều tại chỗ", dict(t=3, la=(-35, -20), ra=(35, 20), ll=(-30, -5), rl=(30, 5), e="determined")),
    "tiptoe": ("Nhón chân", dict(t=5, la=(-25, -15), ra=(25, 15), ll=(-15, -10), rl=(15, 10), lift=15, e="curious")),
    "side_step": ("Bước ngang tại chỗ", dict(t=7, la=(-20, -25), ra=(40, 30), ll=(-30, -20), rl=(25, 15), e="happy")),
    "stumble": ("Loạng choạng", dict(t=30, h=-6, la=(-90, -120), ra=(100, 120), ll=(-30, -80), rl=(40, 50), e="surprised")),
    "squat": ("Ngồi xổm", dict(ll=(-55, 35), rl=(55, -35), la=(-35, -45), ra=(35, 45), e="determined")),
    "kneel": ("Quỳ một gối", dict(ll=(0, 90), rl=(60, -70), la=(-20, -20), ra=(20, 20), e="neutral")),
    "sit": ("Ngồi, ghép ghế riêng", dict(ll=(85, -5), rl=(95, 5), feet="right", e="neutral")),
    "hop": ("Nhảy một chân", dict(ll=(-20, -45), rl=(20, 45), lift=35, la=(-100, -140), ra=(100, 140), e="excited")),
    "kick": ("Đá chân", dict(t=-8, ll=(-10, -5), rl=(75, 90), la=(-45, -30), ra=(65, 40), e="determined")),
    "push": ("Đẩy vật", dict(t=35, la=(-75, -85), ra=(75, 85), ll=(-25, -10), rl=(20, 15), e="determined")),
    "pull": ("Kéo vật", dict(t=-25, la=(-55, -105), ra=(55, 105), ll=(-25, -25), rl=(25, 25), e="determined")),
    "stretch_side": ("Nghiêng người giãn cơ", dict(t=30, h=-10, la=(-160, -175), ra=(50, 70), e="sleepy")),
    "shadow_box": ("Đấm gió", dict(t=15, la=(-85, 60), ra=(85, 95), ll=(-20, -10), rl=(25, 15), e="determined")),
    "reach_high": ("Vươn lấy trên cao", dict(t=10, ra=(150, 175), la=(-30, -20), lift=5, e="determined")),
    "duck": ("Cúi tránh", dict(t=25, la=(-35, -20), ra=(65, 240), ll=(-55, 35), rl=(55, -35), e="worried")),
    "spot_sale": ("Nhìn thấy biển giảm giá", dict(t=-8, h=-10, ra=(70, 125), e="excited")),
    "calculate_discount": ("Nhẩm tính tiền giảm", dict(t=4, h=7, la=(-45, 95), ra=(90, 253), e="thinking")),
    "pay_cashier": ("Đưa tiền ra quầy", dict(t=8, ra=(80, 88), e="surprised")),
    "compare_prices": ("Cân nhắc hai mức giá", dict(la=(-55, -110), ra=(55, 110), e="curious")),
    "write_formula": ("Viết công thức lên bảng", dict(t=3, h=-3, ra=(120, 130), e="talk")),
    "empty_wallet": ("Đau ví vì mất tiền", dict(t=20, h=10, la=(-60, -100), ra=(60, 100), e="crying")),
})

# Short, prop-free acting gestures that can be combined in a story timeline.
POSES.update({
    "look_around": ("Nhìn quanh tìm kiếm", dict(t=5, h=-18, ra=(100, 225), e="curious")),
    "lean_in": ("Nghiêng người lắng nghe", dict(t=19, h=-7, ra=(65, 210), e="curious")),
    "lean_away": ("Ngả người tránh ra", dict(t=-18, la=(-75, -120), ra=(75, 120), e="worried")),
    "count_fingers": ("Đếm bằng ngón tay", dict(t=8, h=9, la=(-45, 100), ra=(55, 120), e="focused")),
    "point_down": ("Chỉ xuống dưới", dict(t=7, h=5, ra=(45, 35), e="talk")),
    "show_two": ("Đưa ra hai phương án", dict(la=(-70, -110), ra=(70, 110), e="talk")),
    "offer_hand": ("Đưa tay mời hoặc trao", dict(t=12, ra=(85, 90), e="happy")),
    "block": ("Giơ tay ngăn lại", dict(t=-8, la=(-80, -110), ra=(80, 110), e="determined")),
    "check_time": ("Nhìn đồng hồ trên tay", dict(t=7, h=12, la=(-35, 95), ra=(75, 255), e="worried")),
    "double_take": ("Giật mình nhìn lại", dict(t=-5, h=20, e="surprised")),
    "flinch": ("Co người vì hoảng", dict(t=-17, la=(-100, -140), ra=(95, 135), e="panic")),
    "wait": ("Đứng đợi sốt ruột", dict(t=4, la=(-20, 95), ra=(20, -95), e="bored")),
    "quiet_joy": ("Vui mừng nhẹ", dict(ra=(110, 165), lift=7, e="grateful")),
    "pace": ("Đi qua lại suy nghĩ", dict(t=8, h=7, la=(-25, -20), ra=(25, 20), ll=(-2, 0), rl=(2, 0), e="thinking")),
})

POSES.update({
    "shield_eyes": ("Che mắt nhìn xa", dict(t=4, h=-13, ra=(110, 245), e="curious")),
    "inspect_ground": ("Cúi xuống quan sát", dict(t=55, h=8, ra=(40, 85), ll=(-35, 30), rl=(35, -30), e="focused")),
    "measure_span": ("Đo khoảng rộng", dict(la=(-78, -90), ra=(78, 90), e="focused")),
    "reassure": ("Trấn an người khác", dict(t=5, la=(-45, -110), ra=(55, 95), e="grateful")),
    "refuse": ("Từ chối dứt khoát", dict(t=-9, la=(-20, 100), ra=(75, 85), e="determined")),
    "ponder_walk": ("Đi chậm suy nghĩ", dict(t=11, h=8, ra=(85, 250), ll=(-2, 0), rl=(2, 0), e="thinking")),
    "call_out": ("Gọi lớn", dict(t=8, h=-8, ra=(110, 245), la=(-30, -25), e="talk")),
    "fist_pump": ("Nắm tay mừng nhẹ", dict(t=-5, ra=(125, 170), e="proud")),
})


def key(time, delta=None, face=None):
    return (time, delta or {}, face)


# Each loop has its own authored beats. Deltas are relative to its named pose.
# The first and last beats match to make a seamless loop.
MOTIONS = {
    "idle": [key(0), key(.25, {"t": 2, "h": -2}), key(.48, {"t": 1}, "blink"), key(.56, {"t": 1}), key(.75, {"t": -2, "h": 2}), key(1)],
    "talk": [key(0, {"ra": (-12, -18)}, "happy"), key(.25, {"ra": (10, 17), "h": -4}, "talk"), key(.5, {"ra": (-4, -8)}, "happy"), key(.75, {"ra": (7, 12), "t": 3}, "talk"), key(1, {"ra": (-12, -18)}, "happy")],
    "explain_open": [key(0, {"la": (18, 20), "ra": (-18, -20)}, "neutral"), key(.28, {"la": (-6, -10), "ra": (6, 10)}, "talk"), key(.55, {"h": -4, "t": 3}, "talk"), key(.8, {"la": (8, 6), "ra": (-8, -6)}, "happy"), key(1, {"la": (18, 20), "ra": (-18, -20)}, "neutral")],
    "point_side": [key(0, {"ra": (-20, -25)}), key(.35, {"ra": (6, 7), "t": 4}, "talk"), key(.65, {"ra": (2, -6), "h": -3}, "talk"), key(1, {"ra": (-20, -25)})],
    "point_up": [key(0, {"ra": (-32, -30)}), key(.32, {"ra": (9, 5), "h": -5}), key(.65, {"ra": (3, -4)}, "talk"), key(1, {"ra": (-32, -30)})],
    "explain_up": [key(0, {"ra": (-28, -28)}, "neutral"), key(.3, {"ra": (8, 5)}, "talk"), key(.65, {"ra": (-3, -7), "h": -5}, "talk"), key(1, {"ra": (-28, -28)}, "neutral")],
    "raise_hand": [key(0, {"ra": (-40, -45)}), key(.3, {"ra": (6, 2), "lift": 4}), key(.65, {"ra": (-4, -8), "h": -4}), key(1, {"ra": (-40, -45)})],
    "think": [key(0, {"ra": (-14, -12)}, "curious"), key(.3, {"ra": (5, 8), "h": 5}, "thinking"), key(.65, {"h": -5, "t": 3}, "skeptical"), key(1, {"ra": (-14, -12)}, "curious")],
    "idea": [key(0, {"ra": (-70, -70), "lift": -8}, "thinking"), key(.35, {"ra": (9, 9), "lift": 12}, "excited"), key(.6, {"lift": 22, "h": -8}, "excited"), key(1, {"ra": (-70, -70), "lift": -8}, "thinking")],
    "confused": [key(0, {"ra": (-16, -15)}, "confused"), key(.3, {"ra": (7, 12), "h": 6}, "confused"), key(.65, {"ra": (-5, -10), "h": -7}, "worried"), key(1, {"ra": (-16, -15)}, "confused")],
    "wave": [key(0, {"ra": (-10, -28)}), key(.25, {"ra": (10, 27)}, "happy"), key(.5, {"ra": (-10, -28)}), key(.75, {"ra": (10, 27)}, "wink"), key(1, {"ra": (-10, -28)})],
    "shrug": [key(0, {"la": (18, 18), "ra": (-18, -18), "h": -4}, "neutral"), key(.35, {"la": (-7, -8), "ra": (7, 8), "h": 7}, "confused"), key(.65, {"lift": 5}, "confused"), key(1, {"la": (18, 18), "ra": (-18, -18), "h": -4}, "neutral")],
    "arms_crossed": [key(0, {"t": -3}, "skeptical"), key(.35, {"h": 8, "t": 4}, "bored"), key(.7, {"h": -8}, "skeptical"), key(1, {"t": -3}, "skeptical")],
    "hands_on_hips": [key(0, {"t": -4}, "happy"), key(.35, {"t": 8, "h": -5}, "proud"), key(.7, {"t": 2, "h": 5}, "proud"), key(1, {"t": -4}, "happy")],
    "walk": [key(0, {"la": (20, 15), "ra": (-20, -15), "ll": (-22, -20), "rl": (22, 20)}), key(.25, {"lift": 5}), key(.5, {"la": (-20, -15), "ra": (20, 15), "ll": (22, 20), "rl": (-22, -20)}), key(.75, {"lift": 5}), key(1, {"la": (20, 15), "ra": (-20, -15), "ll": (-22, -20), "rl": (22, 20)})],
    "run": [key(0, {"la": (20, 30), "ra": (-20, -30), "ll": (-32, -12), "rl": (32, 45), "lift": 4}), key(.25, {"lift": 8}), key(.5, {"la": (-20, -30), "ra": (20, 30), "ll": (32, 45), "rl": (-32, -12), "lift": 4}), key(.75, {"lift": 8}), key(1, {"la": (20, 30), "ra": (-20, -30), "ll": (-32, -12), "rl": (32, 45), "lift": 4})],
    "celebrate": [key(0, {"lift": -25, "la": (20, 20), "ra": (-20, -20)}, "happy"), key(.3, {"lift": 28, "la": (-8, -8), "ra": (8, 8)}, "laugh"), key(.6, {"lift": 45, "h": -6}, "excited"), key(1, {"lift": -25, "la": (20, 20), "ra": (-20, -20)}, "happy")],
    "bow": [key(0, {"t": -50, "h": -8}), key(.38, {"t": 8, "h": 5}), key(.68, {"t": 8, "h": 5}), key(1, {"t": -50, "h": -8})],
    "facepalm": [key(0, {"ra": (-50, -65)}, "worried"), key(.4, {"ra": (2, 8), "t": 6}, "sad"), key(.7, {"h": 8}, "crying"), key(1, {"ra": (-50, -65)}, "worried")],
    "surprised": [key(0, {"la": (55, 60), "ra": (-55, -60), "lift": -6}, "neutral"), key(.3, {"la": (-8, -8), "ra": (8, 8), "lift": 12}, "surprised"), key(.65, {"h": -7, "lift": 8}, "worried"), key(1, {"la": (55, 60), "ra": (-55, -60), "lift": -6}, "neutral")],
    "clap": [key(0, {"la": (-22, -25), "ra": (22, 25)}), key(.25, {"la": (10, 10), "ra": (-10, -10)}, "excited"), key(.5, {"la": (-22, -25), "ra": (22, 25)}), key(.75, {"la": (10, 10), "ra": (-10, -10)}, "excited"), key(1, {"la": (-22, -25), "ra": (22, 25)})],
    "listen": [key(0, {"ra": (-20, -20)}, "curious"), key(.35, {"ra": (5, 9), "t": 7, "h": -6}, "curious"), key(.7, {"h": 6}, "happy"), key(1, {"ra": (-20, -20)}, "curious")],
    "nod": [key(0, {"h": -12}, "neutral"), key(.3, {"h": 11}, "happy"), key(.55, {"h": -9}, "neutral"), key(.8, {"h": 10}, "happy"), key(1, {"h": -12}, "neutral")],
    "shake_head": [key(0, {"h": -11}, "skeptical"), key(.25, {"h": 18}, "skeptical"), key(.5, {"h": -16}, "neutral"), key(.75, {"h": 18}, "skeptical"), key(1, {"h": -11}, "skeptical")],
    "reach": [key(0, {"ra": (-48, -45), "t": -12}), key(.4, {"ra": (8, 8), "t": 12}), key(.7, {"ra": (3, 5), "t": 8}, "curious"), key(1, {"ra": (-48, -45), "t": -12})],
    "jump": [key(0, {"lift": -55, "ll": (25, 35), "rl": (-25, -35)}, "determined"), key(.35, {"lift": 30}, "excited"), key(.6, {"lift": 60, "h": -5}, "laugh"), key(1, {"lift": -55, "ll": (25, 35), "rl": (-25, -35)}, "determined")],
    "dance": [key(0, {"t": -15, "la": (25, 25), "ra": (-25, -25), "ll": (25, 25), "rl": (-25, -25), "lift": 0}), key(.25, {"t": 8, "lift": 14, "h": 8}, "excited"), key(.5, {"t": 18, "la": (-25, -25), "ra": (25, 25), "ll": (-25, -25), "rl": (25, 25), "lift": 0}), key(.75, {"t": -5, "lift": 14, "h": -8}, "wink"), key(1, {"t": -15, "la": (25, 25), "ra": (-25, -25), "ll": (25, 25), "rl": (-25, -25), "lift": 0})],
    "stretch": [key(0, {"la": (35, 40), "ra": (-35, -40), "t": 8}, "sleepy"), key(.4, {"la": (-8, -8), "ra": (8, 8), "t": -8, "lift": 6}, "sleepy"), key(.7, {"t": -12, "h": -5}, "happy"), key(1, {"la": (35, 40), "ra": (-35, -40), "t": 8}, "sleepy")],
    "sneak": [key(0, {"ll": (-15, 10), "rl": (15, -10), "t": -5}), key(.25, {"lift": 3}), key(.5, {"ll": (15, -10), "rl": (-15, 10), "t": 5}), key(.75, {"lift": 3}, "blink"), key(1, {"ll": (-15, 10), "rl": (15, -10), "t": -5})],
    "step_back": [key(0, {"t": 15, "ra": (-30, -25)}, "neutral"), key(.35, {"t": -10, "ra": (8, 8), "lift": 6}, "worried"), key(.7, {"t": -16, "h": -8}, "surprised"), key(1, {"t": 15, "ra": (-30, -25)}, "neutral")],
}

MOTIONS.update({
    "salute": [key(0, {"ra": (-55, -55)}, "neutral"), key(.28, {"ra": (3, 5)}, "proud"), key(.65, {"h": -5}, "proud"), key(1, {"ra": (-55, -55)}, "neutral")],
    "beckon": [key(0, {"ra": (0, -22)}), key(.25, {"ra": (0, 20)}, "happy"), key(.5, {"ra": (0, -22)}), key(.75, {"ra": (0, 20)}, "happy"), key(1, {"ra": (0, -22)})],
    "whisper": [key(0, {"ra": (-25, -35), "t": -5}, "neutral"), key(.3, {"ra": (2, 4), "t": 5, "h": 5}, "talk"), key(.55, {"ra": (4, -3), "h": -3}, "talk"), key(.8, {"ra": (-3, 2)}, "wink"), key(1, {"ra": (-25, -35), "t": -5}, "neutral")],
    "present_left": [key(0, {"la": (42, 40)}, "neutral"), key(.35, {"la": (-5, -7), "t": -6}, "talk"), key(.7, {"la": (4, 7), "h": 4}, "happy"), key(1, {"la": (42, 40)}, "neutral")],
    "present_right": [key(0, {"ra": (-42, -40)}, "neutral"), key(.35, {"ra": (5, 7), "t": 6}, "talk"), key(.7, {"ra": (-4, -7), "h": -4}, "happy"), key(1, {"ra": (-42, -40)}, "neutral")],
    "apologize": [key(0, {"t": -30, "h": -10}, "worried"), key(.35, {"t": 10, "h": 5}, "embarrassed"), key(.7, {"t": 10, "h": 5}, "sad"), key(1, {"t": -30, "h": -10}, "worried")],
    "plead": [key(0, {"la": (25, 30), "ra": (-25, -30)}, "worried"), key(.3, {"la": (-5, -5), "ra": (5, 5), "h": 6}, "worried"), key(.6, {"la": (6, 9), "ra": (-6, -9), "t": 6}, "sad"), key(1, {"la": (25, 30), "ra": (-25, -30)}, "worried")],
    "laugh_body": [key(0, {"t": -10, "h": 7}, "happy"), key(.3, {"t": 14, "h": -6, "lift": 8}, "laugh"), key(.55, {"t": -7, "h": 5}, "laugh"), key(.8, {"t": 12, "h": -7, "lift": 6}, "laugh"), key(1, {"t": -10, "h": 7}, "happy")],
    "cry_body": [key(0, {"ra": (-22, -25), "h": -5}, "sad"), key(.35, {"ra": (4, 6), "h": 8}, "crying"), key(.65, {"ra": (-5, -7), "t": 7}, "crying"), key(1, {"ra": (-22, -25), "h": -5}, "sad")],
    "tremble": [key(0, {"dx": -4, "t": -3}), key(.125, {"dx": 4, "t": 3}), key(.25, {"dx": -4, "t": -3}), key(.375, {"dx": 4, "t": 3}, "blink"), key(.5, {"dx": -4, "t": -3}), key(.625, {"dx": 4, "t": 3}), key(.75, {"dx": -4, "t": -3}), key(.875, {"dx": 4, "t": 3}), key(1, {"dx": -4, "t": -3})],
    "sigh": [key(0, {"t": -10, "h": -10, "lift": 6}, "neutral"), key(.4, {"t": 9, "h": 8, "lift": -5}, "sad"), key(.7, {"t": 12, "h": 12, "lift": -6}, "sad"), key(1, {"t": -10, "h": -10, "lift": 6}, "neutral")],
    "angry_stomp": [key(0, {"rl": (-25, -20), "lift": 0}, "angry"), key(.3, {"rl": (15, 25), "lift": 16, "t": 5}, "angry"), key(.5, {"rl": (-8, -5), "lift": -5}, "angry"), key(.75, {"t": -7, "h": 6}, "determined"), key(1, {"rl": (-25, -20), "lift": 0}, "angry")],
    "shy": [key(0, {"h": -8, "t": -5}, "neutral"), key(.35, {"h": 11, "t": 5, "la": (6, 8), "ra": (-6, -8)}, "embarrassed"), key(.7, {"h": 5, "t": -4}, "wink"), key(1, {"h": -8, "t": -5}, "neutral")],
    "sleepy_nod": [key(0, {"h": -10}, "sleepy"), key(.4, {"h": 14, "t": 5}, "blink"), key(.65, {"h": 8, "t": 2}, "sleepy"), key(1, {"h": -10}, "sleepy")],
    "relieved": [key(0, {"t": 11, "h": 8, "la": (12, 12), "ra": (-12, -12)}, "worried"), key(.35, {"t": -8, "h": -7, "lift": 5}, "happy"), key(.7, {"t": -5, "h": -4}, "proud"), key(1, {"t": 11, "h": 8, "la": (12, 12), "ra": (-12, -12)}, "worried")],
    "march": [key(0, {"la": (30, 25), "ra": (-30, -25), "ll": (40, 30), "rl": (-40, -30)}), key(.25, {"lift": 8}), key(.5, {"la": (-30, -25), "ra": (30, 25), "ll": (-40, -30), "rl": (40, 30)}), key(.75, {"lift": 8}), key(1, {"la": (30, 25), "ra": (-30, -25), "ll": (40, 30), "rl": (-40, -30)})],
    "tiptoe": [key(0, {"lift": -8, "ll": (15, 15), "rl": (-15, -15)}), key(.25, {"lift": 10, "ll": (-5, -5), "rl": (5, 5)}), key(.5, {"lift": -8, "ll": (-15, -15), "rl": (15, 15)}), key(.75, {"lift": 10, "ll": (5, 5), "rl": (-5, -5)}, "blink"), key(1, {"lift": -8, "ll": (15, 15), "rl": (-15, -15)})],
    "side_step": [key(0, {"dx": -16, "ll": (20, 20), "rl": (-20, -20)}), key(.3, {"dx": 0, "lift": 8}), key(.5, {"dx": 16, "ll": (-20, -20), "rl": (20, 20)}), key(.8, {"dx": 0, "lift": 8}), key(1, {"dx": -16, "ll": (20, 20), "rl": (-20, -20)})],
    "stumble": [key(0, {"t": -20, "la": (25, 20), "ra": (-25, -20)}, "neutral"), key(.25, {"t": 14, "dx": 15, "lift": 8}, "surprised"), key(.55, {"t": -10, "dx": -12, "h": 8}, "worried"), key(.8, {"t": 8, "dx": 7, "lift": 4}, "surprised"), key(1, {"t": -20, "la": (25, 20), "ra": (-25, -20)}, "neutral")],
    "squat": [key(0, {"ll": (10, 10), "rl": (-10, -10), "t": 5}), key(.4, {"ll": (-8, -8), "rl": (8, 8), "t": -5}, "determined"), key(.7, {"ll": (4, 4), "rl": (-4, -4), "h": 6}), key(1, {"ll": (10, 10), "rl": (-10, -10), "t": 5})],
    "kneel": [key(0, {"t": -7, "h": -5}), key(.4, {"t": 8, "h": 6, "la": (-8, -8), "ra": (8, 8)}, "curious"), key(.7, {"t": 2, "h": -3}), key(1, {"t": -7, "h": -5})],
    "sit": [key(0, {"t": -6, "h": -4}, "neutral"), key(.3, {"t": 5, "h": 5}, "curious"), key(.55, {"ra": (35, 95), "h": -5}, "talk"), key(.8, {"ra": (5, 15)}, "happy"), key(1, {"t": -6, "h": -4}, "neutral")],
    "hop": [key(0, {"lift": -25, "ll": (25, 25), "rl": (-25, -25)}, "happy"), key(.35, {"lift": 35, "h": -5}, "excited"), key(.6, {"lift": 55, "la": (-8, -8), "ra": (8, 8)}, "laugh"), key(1, {"lift": -25, "ll": (25, 25), "rl": (-25, -25)}, "happy")],
    "kick": [key(0, {"rl": (-55, -75), "t": 10}, "neutral"), key(.3, {"rl": (10, 20), "t": -5}, "determined"), key(.55, {"rl": (25, 5), "lift": 8}, "determined"), key(.8, {"rl": (-15, -25), "t": 6}, "happy"), key(1, {"rl": (-55, -75), "t": 10}, "neutral")],
    "push": [key(0, {"la": (30, 25), "ra": (-30, -25), "t": -10}), key(.4, {"la": (-10, -10), "ra": (10, 10), "t": 11}, "determined"), key(.7, {"t": 15, "lift": 3}, "determined"), key(1, {"la": (30, 25), "ra": (-30, -25), "t": -10})],
    "pull": [key(0, {"la": (-15, -20), "ra": (15, 20), "t": 15}), key(.35, {"la": (20, 25), "ra": (-20, -25), "t": -10}, "determined"), key(.65, {"t": -15, "h": 5}, "determined"), key(1, {"la": (-15, -20), "ra": (15, 20), "t": 15})],
    "stretch_side": [key(0, {"t": -35, "h": 10, "la": (25, 20)}, "sleepy"), key(.4, {"t": 12, "h": -5, "la": (-8, -8)}, "happy"), key(.7, {"t": 18, "h": -8, "lift": 4}, "happy"), key(1, {"t": -35, "h": 10, "la": (25, 20)}, "sleepy")],
    "shadow_box": [key(0, {"ra": (0, 0), "la": (0, 0)}, "determined"), key(.25, {"ra": (0, 145), "la": (0, -155), "t": 8}, "angry"), key(.5, {"ra": (0, 135), "la": (0, -150)}, "determined"), key(.75, {"ra": (0, 55), "la": (0, -65), "t": -8}, "angry"), key(1, {"ra": (0, 0), "la": (0, 0)}, "determined")],
    "reach_high": [key(0, {"ra": (-45, -40), "lift": -5}, "curious"), key(.35, {"ra": (7, 6), "lift": 10, "t": 8}, "determined"), key(.65, {"ra": (10, 8), "lift": 17, "h": -6}, "determined"), key(1, {"ra": (-45, -40), "lift": -5}, "curious")],
    "duck": [key(0, {"ll": (15, 15), "rl": (-15, -15), "t": -15}, "neutral"), key(.3, {"ll": (-5, -5), "rl": (5, 5), "t": 10, "h": 12}, "worried"), key(.65, {"ll": (-5, -5), "rl": (5, 5), "t": 13}, "blink"), key(1, {"ll": (15, 15), "rl": (-15, -15), "t": -15}, "neutral")],
    "spot_sale": [key(0, {"ra": (-45, -50), "lift": -4}, "neutral"), key(.28, {"ra": (8, 8), "lift": 12, "h": -8}, "surprised"), key(.55, {"ra": (6, -4), "lift": 18}, "excited"), key(.8, {"ra": (-8, -10), "lift": 4}, "happy"), key(1, {"ra": (-45, -50), "lift": -4}, "neutral")],
    "calculate_discount": [key(0, {"ra": (-25, -30)}, "curious"), key(.3, {"ra": (6, 7), "h": 8}, "thinking"), key(.6, {"la": (-8, -10), "h": -7}, "skeptical"), key(.8, {"ra": (-5, -8), "t": 5}, "thinking"), key(1, {"ra": (-25, -30)}, "curious")],
    "pay_cashier": [key(0, {"ra": (-50, -50), "t": -8}, "happy"), key(.35, {"ra": (8, 5), "t": 9}, "surprised"), key(.6, {"ra": (10, 8), "h": 8}, "worried"), key(1, {"ra": (-50, -50), "t": -8}, "happy")],
    "compare_prices": [key(0, {"la": (15, 20), "ra": (-15, -20), "t": -8}, "curious"), key(.3, {"la": (-10, -12), "ra": (7, 9), "h": -9}, "thinking"), key(.65, {"la": (8, 10), "ra": (-10, -12), "t": 8, "h": 9}, "thinking"), key(1, {"la": (15, 20), "ra": (-15, -20), "t": -8}, "curious")],
    "write_formula": [key(0, {"ra": (-30, -35)}, "neutral"), key(.3, {"ra": (10, 12), "t": 5}, "talk"), key(.55, {"ra": (-7, -10), "h": -7}, "talk"), key(.8, {"ra": (7, 9), "h": 5}, "happy"), key(1, {"ra": (-30, -35)}, "neutral")],
    "empty_wallet": [key(0, {"t": -10, "la": (20, 20), "ra": (-20, -20)}, "worried"), key(.35, {"t": 12, "h": 8, "la": (-7, -8), "ra": (7, 8)}, "crying"), key(.7, {"t": 7, "h": -7, "lift": -5}, "sad"), key(1, {"t": -10, "la": (20, 20), "ra": (-20, -20)}, "worried")],
})

MOTIONS.update({
    "shield_eyes": [key(0, {"h": 12}, "neutral"), key(.3, {"h": -12, "ra": (3, 5)}, "curious"),
                    key(.65, {"t": 5, "h": 10}, "focused"), key(1, {"h": 12}, "neutral")],
    "inspect_ground": [key(0, {"t": -32, "h": -8}, "curious"),
                       key(.36, {"t": 8, "h": 8, "ra": (12, -8)}, "focused"),
                       key(.7, {"t": 10, "h": -5}, "curious"),
                       key(1, {"t": -32, "h": -8}, "curious")],
    "measure_span": [key(0, {"la": (35, 30), "ra": (-35, -30)}, "neutral"),
                     key(.35, {"la": (-9, -5), "ra": (9, 5)}, "focused"),
                     key(.7, {"h": -6, "t": 4}, "talk"),
                     key(1, {"la": (35, 30), "ra": (-35, -30)}, "neutral")],
    "reassure": [key(0, {"ra": (-35, -30), "la": (18, 12)}, "worried"),
                 key(.3, {"ra": (8, 8), "la": (-5, -5)}, "grateful"),
                 key(.65, {"h": 6, "t": 3}, "happy"),
                 key(1, {"ra": (-35, -30), "la": (18, 12)}, "worried")],
    "refuse": [key(0, {"la": (45, 45), "ra": (-45, -45)}, "neutral"),
               key(.25, {"la": (-9, -8), "ra": (9, 8), "t": -5}, "determined"),
               key(.6, {"h": 10, "t": -8}, "angry"),
               key(1, {"la": (45, 45), "ra": (-45, -45)}, "neutral")],
    "ponder_walk": [key(0, {"ll": (-22, -20), "rl": (22, 20), "h": -4}, "thinking"),
                    key(.25, {"lift": 4, "t": 3}, "focused"),
                    key(.5, {"ll": (22, 20), "rl": (-22, -20), "h": 4}, "thinking"),
                    key(.75, {"lift": 4, "t": -3}, "focused"),
                    key(1, {"ll": (-22, -20), "rl": (22, 20), "h": -4}, "thinking")],
    "call_out": [key(0, {"ra": (-35, -35), "h": 10}, "neutral"),
                 key(.27, {"ra": (5, 4), "t": 6}, "talk"),
                 key(.58, {"h": -8, "t": 4}, "amazed"),
                 key(1, {"ra": (-35, -35), "h": 10}, "neutral")],
    "fist_pump": [key(0, {"ra": (-60, -55), "lift": -7}, "neutral"),
                  key(.32, {"ra": (8, 8), "lift": 10}, "proud"),
                  key(.63, {"ra": (-6, -4), "lift": 6}, "happy"),
                  key(1, {"ra": (-60, -55), "lift": -7}, "neutral")],
})

MOTIONS.update({
    "look_around": [key(0, {"h": -10, "ra": (-15, -12)}, "curious"),
                    key(.28, {"h": 18, "t": -3}, "focused"),
                    key(.57, {"h": 34, "ra": (3, 8)}, "skeptical"),
                    key(.82, {"h": -2, "t": 3}, "curious"),
                    key(1, {"h": -10, "ra": (-15, -12)}, "curious")],
    "lean_in": [key(0, {"t": -14, "ra": (-25, -25)}, "neutral"),
                key(.36, {"t": 8, "h": 9, "ra": (4, 8)}, "curious"),
                key(.68, {"t": 11, "h": -5}, "focused"),
                key(1, {"t": -14, "ra": (-25, -25)}, "neutral")],
    "lean_away": [key(0, {"t": 16, "la": (45, 45), "ra": (-45, -45)}, "neutral"),
                  key(.32, {"t": -8, "la": (-6, -8), "ra": (6, 8), "lift": 5}, "worried"),
                  key(.62, {"t": -13, "h": -8, "lift": 3}, "panic"),
                  key(1, {"t": 16, "la": (45, 45), "ra": (-45, -45)}, "neutral")],
    "count_fingers": [key(0, {"la": (18, 22), "ra": (-18, -22), "h": -6}, "thinking"),
                      key(.25, {"ra": (9, 12), "h": 6}, "focused"),
                      key(.5, {"la": (-9, -12), "ra": (-4, -8)}, "talk"),
                      key(.75, {"la": (8, 10), "ra": (6, 8), "h": 4}, "focused"),
                      key(1, {"la": (18, 22), "ra": (-18, -22), "h": -6}, "thinking")],
    "point_down": [key(0, {"ra": (55, 48)}, "neutral"),
                   key(.3, {"ra": (-8, -5), "t": 5}, "talk"),
                   key(.63, {"ra": (4, 6), "h": 6}, "focused"),
                   key(1, {"ra": (55, 48)}, "neutral")],
    "show_two": [key(0, {"la": (35, 35), "ra": (-35, -35)}, "neutral"),
                 key(.3, {"la": (-5, -8), "ra": (5, 8)}, "talk"),
                 key(.62, {"la": (-12, -10), "ra": (12, 10), "h": -4}, "talk"),
                 key(1, {"la": (35, 35), "ra": (-35, -35)}, "neutral")],
    "offer_hand": [key(0, {"ra": (-55, -65), "t": -10}, "neutral"),
                   key(.36, {"ra": (6, 6), "t": 5}, "happy"),
                   key(.68, {"ra": (10, 10), "h": -4}, "grateful"),
                   key(1, {"ra": (-55, -65), "t": -10}, "neutral")],
    "block": [key(0, {"la": (40, 40), "ra": (-40, -40), "t": 10}, "neutral"),
              key(.32, {"la": (-8, -10), "ra": (8, 10), "t": -7}, "determined"),
              key(.63, {"la": (-12, -14), "ra": (12, 14), "h": -5}, "frustrated"),
              key(1, {"la": (40, 40), "ra": (-40, -40), "t": 10}, "neutral")],
    "check_time": [key(0, {"ra": (-45, -50), "h": -10}, "neutral"),
                   key(.34, {"ra": (10, 8), "h": 7, "t": 5}, "focused"),
                   key(.66, {"ra": (4, -6), "h": 10}, "worried"),
                   key(1, {"ra": (-45, -50), "h": -10}, "neutral")],
    "double_take": [key(0, {"h": -35, "t": 5}, "neutral"),
                    key(.23, {"h": 5, "t": -5, "lift": 5}, "surprised"),
                    key(.43, {"h": 22, "t": -8, "lift": 9}, "amazed"),
                    key(.7, {"h": 14, "t": -2}, "surprised"),
                    key(1, {"h": -35, "t": 5}, "neutral")],
    "flinch": [key(0, {"t": 15, "la": (40, 40), "ra": (-40, -40)}, "neutral"),
               key(.22, {"t": -7, "la": (-8, -8), "ra": (8, 8), "lift": 10}, "panic"),
               key(.5, {"t": -12, "h": -8, "lift": 7}, "panic"),
               key(.77, {"t": 2, "lift": 2}, "worried"),
               key(1, {"t": 15, "la": (40, 40), "ra": (-40, -40)}, "neutral")],
    "wait": [key(0, {"rl": (0, 0), "h": -5}, "bored"),
             key(.22, {"rl": (-18, -23), "h": 8}, "bored"),
             key(.42, {"rl": (0, 0), "t": 5}, "frustrated"),
             key(.62, {"rl": (-18, -23), "h": -7}, "bored"),
             key(.82, {"rl": (0, 0), "t": -3}, "skeptical"),
             key(1, {"rl": (0, 0), "h": -5}, "bored")],
    "quiet_joy": [key(0, {"ra": (-70, -70), "lift": -5}, "neutral"),
                  key(.35, {"ra": (6, 8), "lift": 8}, "grateful"),
                  key(.62, {"ra": (12, 12), "lift": 14, "h": -5}, "proud"),
                  key(1, {"ra": (-70, -70), "lift": -5}, "neutral")],
    "pace": [key(0, {"ll": (-22, -20), "rl": (22, 20), "la": (15, 10), "ra": (-15, -10)}, "thinking"),
             key(.25, {"lift": 4, "h": 5}, "focused"),
             key(.5, {"ll": (22, 20), "rl": (-22, -20), "la": (-15, -10), "ra": (15, 10)}, "thinking"),
             key(.75, {"lift": 4, "h": -5}, "focused"),
             key(1, {"ll": (-22, -20), "rl": (22, 20), "la": (15, 10), "ra": (-15, -10)}, "thinking")],
})

# Fast actions repeat their authored beats within the two-second asset loop.
MOTION_CYCLES = {"talk": 2, "walk": 2, "run": 3, "clap": 2, "march": 2, "pace": 2,
                 "ponder_walk": 2,
                 "tiptoe": 2, "side_step": 2, "tremble": 2, "shadow_box": 2}

POSE_CATEGORY = {}
for category, names in {
    "hội thoại": ("talk explain_open point_side point_up explain_up raise_hand think idea confused "
                 "wave shrug listen nod shake_head reach bow salute beckon whisper present_left "
                  "present_right apologize plead spot_sale calculate_discount compare_prices write_formula "
                   "look_around lean_in count_fingers point_down show_two offer_hand check_time "
                   "shield_eyes measure_span reassure refuse call_out").split(),
    "cảm xúc": ("idle arms_crossed hands_on_hips celebrate facepalm surprised clap laugh_body "
                  "cry_body tremble sigh angry_stomp shy sleepy_nod relieved empty_wallet "
                   "lean_away block double_take flinch wait quiet_joy fist_pump").split(),
    "di chuyển": ("walk run jump dance stretch sneak step_back march tiptoe side_step stumble "
                     "squat kneel sit hop kick pace ponder_walk").split(),
    "hành động": ("push pull stretch_side shadow_box reach_high duck pay_cashier inspect_ground").split(),
}.items():
    for name in names:
        if name in POSE_CATEGORY:
            raise ValueError(f"Duplicate pose category: {name}")
        POSE_CATEGORY[name] = category
if set(POSE_CATEGORY) != set(POSES) or set(MOTIONS) != set(POSES):
    raise ValueError("Every pose needs one category and one motion timeline")


def pose_state(name):
    if name not in POSES:
        raise ValueError(f"Unknown pose: {name}")
    return {**DEFAULT, **POSES[name][1]}


def blend(a, b, amount):
    """Interpolate rig values; discrete face and foot direction switch midway."""
    out = {}
    for field in DEFAULT:
        av, bv = a[field], b[field]
        if isinstance(av, (tuple, list)):
            out[field] = tuple(x + (y - x) * amount for x, y in zip(av, bv))
        elif isinstance(av, (int, float)):
            out[field] = av + (bv - av) * amount
        else:
            out[field] = av if amount < .5 else bv
    return out


def motion_state(name, phase, expression=None):
    base, beats = pose_state(name), MOTIONS[name]
    phase = (phase * MOTION_CYCLES.get(name, 1)) % 1.0
    for left, right in zip(beats, beats[1:]):
        if left[0] <= phase < right[0]:
            portion = (phase - left[0]) / (right[0] - left[0])
            portion = portion * portion * (3 - 2 * portion)
            delta = {}
            for field in ("t", "h", "dx", "lift", "la", "ra", "ll", "rl"):
                start = left[1].get(field, (0, 0) if field in ("la", "ra", "ll", "rl") else 0)
                end = right[1].get(field, (0, 0) if field in ("la", "ra", "ll", "rl") else 0)
                if isinstance(start, tuple):
                    delta[field] = tuple(x + (y - x) * portion for x, y in zip(start, end))
                else:
                    delta[field] = start + (end - start) * portion
            state = dict(base)
            for field, value in delta.items():
                if isinstance(value, tuple):
                    state[field] = tuple(x + y for x, y in zip(base[field], value))
                else:
                    state[field] = base[field] + value
            state["e"] = expression or (left[2] if left[2] and portion < .5 else right[2] or left[2] or base["e"])
            return state
    raise AssertionError("Motion timeline has a gap")


def point(origin, angle, length, upward=False):
    radians = math.radians(angle)
    sign = -1 if upward else 1
    return (origin[0] + length * math.sin(radians), origin[1] + sign * length * math.cos(radians))


def polyline(points, width=6):
    coords = " ".join(f"{x:.2f},{y:.2f}" for x, y in points)
    return (f'<polyline points="{coords}" fill="none" stroke="{INK}" '
            f'stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round"/>')


def face_svg(expression, x, y, tilt=0):
    if expression not in FACES:
        raise ValueError(f"Unknown expression: {expression}")
    return (f'<g transform="translate({x:.2f},{y:.2f}) rotate({tilt:.2f})" '
            f'fill="none" stroke="{INK}" stroke-width="3" stroke-linecap="round" '
            f'stroke-linejoin="round">{FACES[expression][0]}</g>')


def draw(state):
    def solve(hip_y):
        hip = (250 + state["dx"], hip_y)
        neck = point(hip, state["t"], TORSO, upward=True)
        shoulder = point(hip, state["t"], .88 * TORSO, upward=True)
        head = point(neck, state["t"] + state["h"], 38, upward=True)
        arms = {}
        for side in ("la", "ra"):
            elbow = point(shoulder, state[side][0], UPPER_ARM)
            arms[side] = (shoulder, elbow, point(elbow, state[side][1], FOREARM))
        legs = {}
        for side, sign in (("ll", -1), ("rl", 1)):
            knee = point(hip, state[side][0], THIGH)
            ankle = point(knee, state[side][1], SHIN)
            foot_dx = 16 if state["feet"] == "right" else 16 * sign
            legs[side] = (hip, knee, ankle, (ankle[0] + foot_dx, ankle[1]))
        return hip, neck, head, arms, legs

    neutral = solve(330)
    lowest_foot = max(foot[2][1] for foot in neutral[4].values())
    hip, neck, head, arms, legs = solve(330 + GROUND - lowest_foot - state["lift"])
    return (polyline(legs["ll"]) + polyline(legs["rl"]) + polyline((hip, neck))
            + f'<circle cx="{head[0]:.2f}" cy="{head[1]:.2f}" r="{HEAD_R}" '
              f'fill="white" stroke="{INK}" stroke-width="6"/>'
            + face_svg(state["e"], *head, state["t"] + state["h"])
            + polyline(arms["la"]) + polyline(arms["ra"]))


def wrap(inner, viewbox=None, width=W, height=H):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="{viewbox or f"0 0 {W} {H}"}" width="{width}" height="{height}">'
            f'{inner}</svg>')


def build(name, expression=None):
    state = pose_state(name)
    if expression:
        state["e"] = expression
    return wrap(draw(state))


def frame_svg(name, phase, expression=None):
    return wrap(draw(motion_state(name, phase, expression)))


def transition_svg(from_pose, to_pose, progress, expression=None):
    progress = max(0.0, min(1.0, progress))
    eased = progress * progress * (3 - 2 * progress)
    state = blend(pose_state(from_pose), pose_state(to_pose), eased)
    if expression:
        state["e"] = expression
    return wrap(draw(state))


def raster(svg, width):
    try:
        import resvg_py
        from PIL import Image
    except ImportError as exc:
        raise SystemExit("Install requirements first: python -m pip install -r requirements.txt") from exc
    raw = resvg_py.svg_to_bytes(svg_string=svg, width=width)
    return Image.open(io.BytesIO(raw)).convert("RGBA")


def export_frames(svg_at_phase, output, fmt="webp", fps=18, duration=2,
                  width=400, include_endpoint=False):
    from PIL import Image

    if fps <= 0 or duration <= 0 or width <= 0:
        raise ValueError("fps, duration and width must be positive")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    count = max(2, round(fps * duration))
    denominator = count - 1 if include_endpoint else count
    frames = [raster(svg_at_phase(i / denominator), width) for i in range(count)]
    if fmt == "webp":
        frames[0].save(output, format="WEBP", save_all=True, append_images=frames[1:],
                       duration=round(1000 / fps), loop=1 if include_endpoint else 0,
                       lossless=True, method=4)
    elif fmt in ("png", "mp4"):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp) if fmt == "mp4" else output
            folder.mkdir(parents=True, exist_ok=True)
            for index, frame in enumerate(frames):
                if fmt == "mp4":
                    white = Image.new("RGB", frame.size, "white")
                    white.paste(frame, mask=frame.getchannel("A"))
                    frame = white
                frame.save(folder / f"frame_{index:04d}.png")
            if fmt == "mp4":
                subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                                "-framerate", str(fps), "-i", str(folder / "frame_%04d.png"),
                                "-c:v", "libx264", "-pix_fmt", "yuv420p", str(output)], check=True)
    else:
        raise ValueError(f"Unknown format: {fmt}")
    return count


def clean_legacy():
    """Remove only the known generated duplicates from the original archive."""
    old_poses = set(POSES) | {"board", "write_board", "hold_book"}
    old_files = [ROOT / name for name in (
        "poses.json", "poses_sheet.png", "poses_sheet.svg",
        "expressions_sheet.png", "expressions_sheet.svg",
    )]
    old_files += [ROOT / "png" / "poses" / f"{name}.png" for name in old_poses]
    old_files += [ROOT / "svg" / "poses" / f"{name}.svg"
                  for name in ("board", "write_board", "hold_book")]
    for path in old_files:
        if not path.resolve().is_relative_to(ROOT):
            raise ValueError(f"Cleanup path escaped package: {path}")
        path.unlink(missing_ok=True)
    for folder in (ROOT / "png" / "poses", ROOT / "png"):
        if folder.exists() and not any(folder.iterdir()):
            folder.rmdir()


def package(fps=18, duration=2, width=400):
    import vfx
    import illustrations

    clean_legacy()
    (ROOT / "svg" / "poses").mkdir(parents=True, exist_ok=True)
    (ROOT / "svg" / "expressions").mkdir(parents=True, exist_ok=True)
    (ROOT / "animations").mkdir(parents=True, exist_ok=True)
    (ROOT / "illustrations" / "svg").mkdir(parents=True, exist_ok=True)
    (ROOT / "illustrations" / "png").mkdir(parents=True, exist_ok=True)
    for name in POSES:
        (ROOT / "svg" / "poses" / f"{name}.svg").write_text(build(name), encoding="utf-8")
        export_frames(lambda phase, n=name: frame_svg(n, phase),
                      ROOT / "animations" / f"{name}.webp", fps=fps, duration=duration, width=width)
    for expression in FACES:
        inner = (f'<circle r="{HEAD_R}" fill="white" stroke="{INK}" stroke-width="6"/>'
                 + face_svg(expression, 0, 0))
        (ROOT / "svg" / "expressions" / f"{expression}.svg").write_text(
            wrap(inner, "-40 -40 80 80", 320, 320), encoding="utf-8")
    for name in illustrations.ILLUSTRATIONS:
        art = illustrations.svg(name)
        (ROOT / "illustrations" / "svg" / f"{name}.svg").write_text(art, encoding="utf-8")
        raster(art, 520).save(ROOT / "illustrations" / "png" / f"{name}.png")
    manifest = {
        "version": 6,
        "canvas": [W, H],
        "background": "transparent",
        "loop": {"fps": fps, "duration_seconds": duration, "width": width,
                 "sampled_frames": round(fps * duration), "format": "animated WebP lossless",
                 "note": "Identical frames may be merged by the WebP encoder."},
        "angles": "degrees: 0 down, +90 right, 180 up",
        "poses": {name: {"vi": label, "category": POSE_CATEGORY[name],
                         "default_expression": pose_state(name)["e"],
                         "cycles_per_loop": MOTION_CYCLES.get(name, 1),
                         "motion_beats": [beat[0] for beat in MOTIONS[name]]}
                  for name, (label, _) in POSES.items()},
        "expressions": {name: label for name, (_, label) in FACES.items()},
        "effects": vfx.EFFECTS,
        "illustrations": illustrations.ILLUSTRATIONS,
        "story_sequences": {
            path.stem: {
                "duration_seconds": sum(beat["duration"] for beat in data["beats"]),
                "beats": len(data["beats"]),
            }
            for path in sorted((ROOT / "sequences").glob("*.json"))
            for data in [json.loads(path.read_text(encoding="utf-8"))]
        },
    }
    (ROOT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    catalog = ["# Danh mục animation", "",
               "Mỗi tên có SVG tĩnh trong `svg/poses/` và WebP động trong `animations/`.", ""]
    for category in dict.fromkeys(POSE_CATEGORY.values()):
        catalog += [f"## {category.capitalize()}", ""]
        catalog += [f"- `{name}` — {POSES[name][0]}"
                    for name in POSES if POSE_CATEGORY[name] == category]
        catalog.append("")
    catalog += ["## VFX", ""]
    catalog += [f"- `{name}` — {label}" for name, label in vfx.EFFECTS.items()
                if name != "none"]
    catalog.append("")
    catalog += ["## Hình minh họa", ""]
    catalog += [f"- `{name}` — {label}" for name, label in illustrations.ILLUSTRATIONS.items()]
    catalog.append("")
    (ROOT / "CATALOG.md").write_text("\n".join(catalog), encoding="utf-8")


def make_archive(output):
    """Zip only the current deliverables, even if the source folder has other files."""
    output = Path(output).resolve()
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    files = [ROOT / name for name in ("README.md", "CATALOG.md", "requirements.txt",
                                       "stickman.py", "story_animation.py", "vfx.py", "illustrations.py",
                                       "story_demo.json", "manifest.json")]
    files += [ROOT / "animations" / f"{name}.webp" for name in manifest["poses"]]
    files += [ROOT / "svg" / "poses" / f"{name}.svg" for name in manifest["poses"]]
    files += [ROOT / "svg" / "expressions" / f"{name}.svg" for name in manifest["expressions"]]
    for name in manifest["illustrations"]:
        files += [ROOT / "illustrations" / folder / f"{name}.{ext}"
                  for folder, ext in (("svg", "svg"), ("png", "png"))]
    for name in manifest["story_sequences"]:
        files += [ROOT / "sequences" / f"{name}.{ext}" for ext in ("json", "webp")]
    if not all(path.is_file() and path.is_relative_to(ROOT) for path in files):
        raise ValueError("Some generated asset files are missing")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    with ZipFile(temporary, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            archive.write(path, path.relative_to(ROOT.parent).as_posix())
    with ZipFile(temporary) as archive:
        if archive.testzip() is not None or len(archive.namelist()) != len(files):
            raise ValueError("Archive verification failed")
    temporary.replace(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("package", help="Rebuild all static SVGs and transparent animated WebPs")
    p.add_argument("--fps", type=int, default=18)
    p.add_argument("--duration", type=float, default=2)
    p.add_argument("--width", type=int, default=400)
    p.add_argument("--zip", type=Path, help="Write a clean ZIP to this path")
    p = sub.add_parser("frame", help="Print one SVG animation frame")
    p.add_argument("pose", choices=POSES)
    p.add_argument("--phase", type=float, default=0)
    p.add_argument("--expression", choices=FACES)
    for command in ("loop", "transition"):
        p = sub.add_parser(command, help=f"Render a {command} as WebP, MP4 or transparent PNG frames")
        if command == "loop":
            p.add_argument("pose", choices=POSES)
        else:
            p.add_argument("from_pose", choices=POSES)
            p.add_argument("to_pose", choices=POSES)
        p.add_argument("output", type=Path)
        p.add_argument("--format", choices=("webp", "mp4", "png"), default="webp")
        p.add_argument("--fps", type=int, default=18)
        p.add_argument("--duration", type=float, default=2)
        p.add_argument("--width", type=int, default=400)
        p.add_argument("--expression", choices=FACES)
    args = parser.parse_args()
    if args.command == "package":
        package(args.fps, args.duration, args.width)
        if args.zip:
            make_archive(args.zip)
    elif args.command == "frame":
        print(frame_svg(args.pose, args.phase, args.expression))
    elif args.command == "loop":
        export_frames(lambda phase: frame_svg(args.pose, phase, args.expression),
                      args.output, args.format, args.fps, args.duration, args.width)
    else:
        export_frames(lambda phase: transition_svg(args.from_pose, args.to_pose, phase, args.expression),
                      args.output, args.format, args.fps, args.duration, args.width,
                      include_endpoint=True)


if __name__ == "__main__":
    main()
