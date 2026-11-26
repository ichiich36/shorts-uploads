"""Shared drawing / text / caption helpers for the 'How Cars Work' shorts."""
import math
import os
import random
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
BG_TOP = np.array([12, 20, 38], np.float32)
BG_BOT = np.array([5, 9, 18], np.float32)
CYAN = (56, 189, 248)
INTAKE = (96, 165, 250)
COMP = (45, 212, 191)
POWER = (251, 146, 60)
FLAME = (253, 224, 71)
EXH = (156, 163, 175)
WHITE = (241, 245, 249)
YEL = (253, 224, 71)
M_DARK = (51, 61, 79)
M_MID = (100, 112, 132)
M_LIGHT = (160, 170, 186)
M_HI = (215, 221, 230)
HEADC = (64, 78, 100)
CAVITY = (16, 24, 42)

def _first_font(cands):
    for c in cands:
        if os.path.exists(c):
            return c
    raise FileNotFoundError(cands)


F_BLACK = _first_font(["/usr/share/fonts/opentype/inter/InterDisplay-Black.otf",
                       "/usr/share/fonts/truetype/noto/NotoSans-Black.ttf",
                       "/usr/share/fonts/truetype/noto/NotoSans-ExtraBold.ttf",
                       "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
                       "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"])
F_XBOLD = _first_font(["/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf",
                       "/usr/share/fonts/truetype/noto/NotoSans-ExtraBold.ttf",
                       "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
                       "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"])


def ease_io(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def ease_out3(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3



SH = 4
SC = 1 << SH


def P(x, y, s=1.0):
    return (int(round(x * s * SC)), int(round(y * s * SC)))


def C3(c, k=1.0):
    return (int(min(255, max(0, c[0] * k))), int(min(255, max(0, c[1] * k))), int(min(255, max(0, c[2] * k))))


def mixc(a, b, f):
    return tuple(a[i] * (1 - f) + b[i] * f for i in range(3))


def circle(img, x, y, r, c, th=-1, s=1.0):
    cv2.circle(img, P(x, y, s), max(1, int(round(r * s * SC))), c, th if th < 0 else max(1, int(round(th * s))), cv2.LINE_AA, SH)


def line(img, x0, y0, x1, y1, c, th, s=1.0):
    cv2.line(img, P(x0, y0, s), P(x1, y1, s), c, max(1, int(round(th * s))), cv2.LINE_AA, SH)


def poly(img, pts, c, s=1.0):
    arr = np.array([P(x, y, s) for x, y in pts], np.int32)
    cv2.fillPoly(img, [arr], c, cv2.LINE_AA, SH)


def polyline(img, pts, c, th, closed=False, s=1.0):
    arr = np.array([P(x, y, s) for x, y in pts], np.int32)
    cv2.polylines(img, [arr], closed, c, max(1, int(round(th * s))), cv2.LINE_AA, SH)


def rrect_pts(x0, y0, x1, y1, r, n=6):
    r = min(r, (x1 - x0) / 2, (y1 - y0) / 2)
    pts = []
    for cx, cy, a0 in ((x1 - r, y0 + r, -90), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)):
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def rrect(img, x0, y0, x1, y1, r, c, s=1.0):
    poly(img, rrect_pts(x0, y0, x1, y1, r), c, s)


def rrect_outline(img, x0, y0, x1, y1, r, c, th, s=1.0):
    polyline(img, rrect_pts(x0, y0, x1, y1, r), c, th, closed=True, s=s)


def blend_rect(img, x0, y0, x1, y1, color, alpha):
    x0, y0, x1, y1 = int(max(0, x0)), int(max(0, y0)), int(min(W, x1)), int(min(H, y1))
    if x1 <= x0 or y1 <= y0 or alpha <= 0:
        return
    reg = img[y0:y1, x0:x1].astype(np.float32)
    reg = reg * (1 - alpha) + np.array(color, np.float32) * alpha
    img[y0:y1, x0:x1] = reg.astype(np.uint8)


def path_point(path, s):
    """Point at fraction s along a polyline."""
    seg = [math.dist(path[i], path[i + 1]) for i in range(len(path) - 1)]
    tot = sum(seg)
    d = min(max(s, 0), 1) * tot
    for i, L in enumerate(seg):
        if d <= L or i == len(seg) - 1:
            f = d / L if L else 0
            return (path[i][0] + (path[i + 1][0] - path[i][0]) * f, path[i][1] + (path[i + 1][1] - path[i][1]) * f)
        d -= L
    return path[-1]



_fonts = {}


def font(path, size):
    if (path, size) not in _fonts:
        _fonts[(path, size)] = ImageFont.truetype(path, size)
    return _fonts[(path, size)]


def text_sprite(parts, fnt, stroke=0, shadow=0.6, tracking=0, glow=None):
    widths = [sum(fnt.getlength(ch) + tracking for ch in s) - (tracking if s else 0) for s, _ in parts]
    total = int(math.ceil(sum(widths))) + 2 * stroke
    asc, desc = fnt.getmetrics()
    pad = 30
    img = Image.new("RGBA", (total + 2 * pad, asc + desc + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x = pad + stroke
    for (s, c), w in zip(parts, widths):
        if tracking:
            for ch in s:
                d.text((x, pad), ch, font=fnt, fill=tuple(int(v) for v in c) + (255,), stroke_width=stroke, stroke_fill=(6, 8, 14, 255))
                x += fnt.getlength(ch) + tracking
            x -= tracking
        else:
            d.text((x, pad), s, font=fnt, fill=tuple(int(v) for v in c) + (255,), stroke_width=stroke, stroke_fill=(6, 8, 14, 255))
            x += w
    a = np.asarray(img).astype(np.float32) / 255.0
    rgb = a[..., :3] * a[..., 3:4]
    al = a[..., 3:4].copy()
    if glow is not None:
        ga = cv2.GaussianBlur(al[..., 0], (0, 0), 12)[..., None] * 0.8
        rgb = rgb + (1 - al) * ga * (np.array(glow, np.float32) / 255)
        al = al + (1 - al) * ga
    if shadow:
        sa = np.roll(cv2.GaussianBlur(al[..., 0], (0, 0), 6), 4, axis=0)[..., None] * shadow
        al = al + (1 - al) * sa
    return np.concatenate([rgb * 255, al], axis=2).astype(np.float32)


def fit(spr, maxw=1030):
    w = spr.shape[1] - 60
    if w > maxw:
        f = maxw / w
        spr = cv2.resize(spr, None, fx=f, fy=f, interpolation=cv2.INTER_LINEAR)
    return spr


def blit(frame, spr, cx, cy, opacity=1.0, scale=1.0):
    if opacity <= 0.003:
        return
    if abs(scale - 1) > 1e-3:
        spr = cv2.resize(spr, None, fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)
    h, w = spr.shape[:2]
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    sx0, sy0 = max(0, -x0), max(0, -y0)
    x0c, y0c, x1c, y1c = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if x1c <= x0c or y1c <= y0c:
        return
    s = spr[sy0:sy0 + (y1c - y0c), sx0:sx0 + (x1c - x0c)]
    reg = frame[y0c:y1c, x0c:x1c].astype(np.float32)
    a = s[..., 3:4] * opacity
    frame[y0c:y1c, x0c:x1c] = np.clip(reg * (1 - a) + s[..., :3] * opacity, 0, 255).astype(np.uint8)



def make_bg():
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    bg = BG_TOP[None, None] * (1 - y) + BG_BOT[None, None] * y
    bg = np.repeat(bg, W, axis=1)
    for gx in range(0, W, 60):
        bg[:, gx:gx + 1] += 7
    for gy in range(0, H, 60):
        bg[gy:gy + 1, :] += 7
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt((xx - 540) ** 2 + (yy - 880) ** 2)
    bg += (np.exp(-(d / 560) ** 2)[..., None] * np.array([14, 30, 52], np.float32))
    vig = np.clip(1 - 0.3 * (((xx - 540) / 540) ** 2 + ((yy - 960) / 1200) ** 2), 0.6, 1)[..., None]
    bg *= vig
    bg += np.random.default_rng(3).uniform(-1.5, 1.5, bg.shape).astype(np.float32)
    return np.clip(bg, 0, 255).astype(np.uint8)



BG = make_bg()


def gear_pts(cx, cy, R, teeth, ang, depth=16):
    pts = []
    n = teeth * 4
    for k in range(n):
        a = ang + 2 * math.pi * k / n
        rr = R + (depth if (k % 4) in (1, 2) else 0)
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts



_label_cache = {}


def label_sprite(text, col):
    key = (text, col)
    if key not in _label_cache:
        _label_cache[key] = text_sprite([(text, col)], font(F_XBOLD, 34), tracking=2, shadow=0.7)
    return _label_cache[key]


