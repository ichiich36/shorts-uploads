"""How Cars Work - Part 4: The Differential.  python3 render.py stills t... | range a b out.mp4"""
import math
import os
import subprocess
import sys
import cv2
import numpy as np
from PIL import Image
import script as S
from common import *

_tl = S.load_timeline('timeline.json')
TL = S.Timeline(_tl['words'], _tl['duration'])
DUR = TL.duration
N_FRAMES = int(math.ceil(DUR * FPS))


def ws(seg, key, nth=1):
    return TL.word(seg, key, nth)[0]


T = {s: TL.seg_start(s) for s, _ in S.SEGMENTS}
GREEN = (74, 222, 128)
BLUE = (96, 165, 250)
ORANGE = (251, 146, 60)
RED = (248, 72, 72)
GREY = (120, 128, 140)
ICE = (186, 230, 253)
TIRE = (30, 34, 44)
DARK = (14, 22, 40)

# --- word times (every visual event is keyed to the spoken word)
DIFFR_S = ws('A', 'different')
ENGINE_S = ws('A', 'engine')
BOTH_S = ws('A', 'both')
PART_S = ws('A', 'part')
OUTSIDE_B = ws('B', 'outside')
FARTHER_S = ws('B', 'farther')
ON_S = ws('B', 'on')
SOLID_S = ws('B', 'solid')
SAME_S = ws('B', 'same')
SKID_S = ws('B', 'skid')
DIFF_S = ws('C', 'differential')
DSHAFT_S = ws('C', 'driveshaft')
PINION_S = ws('C', 'pinion')
RING_S = ws('C', 'ring')
BOLTED_S = ws('D', 'bolted')
CAGE_S = ws('D', 'cage')
SPIDER_S = ws('D', 'spider')
SIDE_S = ws('D', 'side')
PERW_S = ws('D', 'wheel')
DONT_S = ws('E', "don't")
WHOLE_S = ws('E', 'whole')
BOTHW_S = ws('E', 'both')
CORNER_F = ws('F', 'corner')
SLOWS_S = ws('F', 'slows')
START_S = ws('F', 'start')
SPEEDS_S = ws('F', 'speeds')
EXACTLY_S = ws('F', 'exactly')
RING_G = ws('G', 'ring')
NINETY_S = ws('G', 'ninety')
ONETEN_S = ws('G', 'one', 2)
AVERAGE_S = ws('G', 'average')
CATCH_S = ws('H', 'catch')
EQUAL_S = ws('H', 'equal')
ICE_S = ws('H', 'ice')
SPINS_H = ws('H', 'spins')
OTHER_S = ws('H', 'other')
NOTHING_S = ws('H', 'nothing')
SPORTS_S = ws('I', 'sports')
OFFR_S = ws('I', 'off-roaders')
LSD_S = ws('I', 'limited-slip')
LOCK_S = ws('I', 'locking')
BRAKES_S = ws('K', 'brakes')
FOOT_S = ws('K', 'foot')
STOP_S = ws('K', 'stop')
TON_S = ws('K', 'two-ton')
FOLLOW_S = ws('K', 'follow')


def ramp(t, t0, d=0.3):
    return min(1.0, max(0.0, (t - t0) / d))


def eramp(t, t0, d=0.3):
    return ease_io(ramp(t, t0, d))


exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_parts.py')).read())

SPR_SERIES = text_sprite([('HOW CARS WORK', CYAN)], font(F_XBOLD, 34), tracking=7, shadow=0.4)
SPR_TITLE = fit(text_sprite([('PART 4: ', WHITE), ('THE DIFFERENTIAL', YEL)], font(F_BLACK, 76)))


def badge(text, col=WHITE):
    return fit(text_sprite([(text, col)], font(F_XBOLD, 40), tracking=3))


BADGES = [(0.0, PART_S, badge('ONE ENGINE · TWO WHEEL SPEEDS?', YEL)),
          (PART_S, T['B'], badge('THE GEARS BETWEEN YOUR WHEELS')),
          (T['B'], ON_S, badge('THE OUTSIDE WHEEL GOES FARTHER', ORANGE)),
          (ON_S, T['C'], badge('PROBLEM: A SOLID AXLE', RED)),
          (T['C'], DSHAFT_S, badge('THE FIX: A DIFFERENTIAL', GREEN)),
          (DSHAFT_S, T['D'], badge('STEP 1: PINION + RING GEAR', YEL)),
          (T['D'], T['E'], badge('STEP 2: SPIDER + SIDE GEARS', YEL)),
          (T['E'], T['F'], badge('GOING STRAIGHT', GREEN)),
          (T['F'], T['G'], badge('IN A CORNER', ORANGE)),
          (T['G'], T['H'], badge('THE AVERAGE NEVER CHANGES', CYAN)),
          (T['H'], T['I'], badge('THE CATCH: ONE WHEEL ON ICE', RED)),
          (T['I'], T['K'], badge('THE FIX: LIMITED-SLIP OR LOCKER', GREEN))]
TXT = {k: text_sprite([(k, c)], font(F_BLACK, 46), shadow=0.6) for k, c in
       [('INSIDE', BLUE), ('OUTSIDE', ORANGE), ('SLOWER', BLUE), ('FASTER', ORANGE), ('ENGINE', WHITE),
        ('SAME SPEED', WHITE), ('SOLID AXLE', M_HI), ('FARTHER', ORANGE), ('NOT TURNING', RED), ('TURNING', YEL),
        ('ONE BLOCK', CYAN), ('ICE', ICE), ('EQUAL TORQUE', GREEN), ('ALMOST NOTHING', RED), ('STUCK', RED),
        ('SPORTS CARS', WHITE), ('OFF-ROADERS', WHITE), ('LIMITED-SLIP', ORANGE), ('LOCKER', YEL),
        ('1 FOOT', WHITE), ('2 TONS', WHITE), ('LEFT TURN', WHITE), ('-10', BLUE), ('+10', ORANGE), ('=', WHITE),
        ('DIFFERENTIAL', YEL), ('STRAIGHT', WHITE)]}
BIG = {k: fit(text_sprite([(k, c)], font(F_BLACK, 130), stroke=6, shadow=0.8), 980) for k, c in
       [('HOW?', YEL)]}
SPR_SKID = text_sprite([('SKID!', RED)], font(F_BLACK, 96), stroke=6, shadow=0.8)
SPR_HEAD1 = fit(text_sprite([('THE', WHITE)], font(F_BLACK, 110), shadow=0.8))
SPR_HEAD2 = fit(text_sprite([('DIFFERENTIAL', YEL)], font(F_BLACK, 112), shadow=0.8))
SPR_PART5 = fit(text_sprite([('PART 5: ', WHITE), ('THE BRAKES', YEL)], font(F_BLACK, 74)))
SPR_FOLLOW = fit(text_sprite([('FOLLOW FOR PART 5', (10, 14, 24))], font(F_BLACK, 54), shadow=0))
SPR_RPMU = text_sprite([('RPM', M_LIGHT)], font(F_XBOLD, 24), tracking=3, shadow=0.3)
SPR_RINGLBL = text_sprite([('RING GEAR', YEL)], font(F_XBOLD, 26), tracking=3, shadow=0.3)
SPR_EQ = fit(text_sprite([('(', WHITE), ('90', BLUE), (' + ', WHITE), ('110', ORANGE), (') ÷ 2 = ', WHITE), ('100', YEL)],
                         font(F_BLACK, 78), stroke=5, shadow=0.7), 980)
_num = {}


def num_sprite(v, col, size=64):
    key = (v, col, size)
    if key not in _num:
        _num[key] = text_sprite([(str(v), col)], font(F_BLACK, size), shadow=0.5)
    return _num[key]


# ------------------------------------------------------------------ drawing helpers
def red_x(img, cx, cy, r, k):
    L = r * k
    line(img, cx - L, cy - L, cx + L, cy + L, C3(RED), 14)
    line(img, cx - L, cy + L, cx + L, cy - L, C3(RED), 14)


def lock_icon(img, cx, cy, s=1.0, col=RED):
    rrect(img, cx - 26 * s, cy - 6 * s, cx + 26 * s, cy + 34 * s, 6 * s, C3(col))
    circle(img, cx, cy - 6 * s, 18 * s, C3(col), th=7 * s)
    circle(img, cx, cy + 12 * s, 5 * s, C3(DARK))


def arrow(img, x0, y0, x1, y1, col, th=10, head=26):
    L = math.hypot(x1 - x0, y1 - y0)
    if L < 2:
        return
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    head = min(head, L * 0.6)
    bx, by = x1 - ux * head, y1 - uy * head
    line(img, x0, y0, bx, by, col, th)
    poly(img, [(x1, y1), (bx - uy * head * 0.62, by + ux * head * 0.62), (bx + uy * head * 0.62, by - ux * head * 0.62)], col)


def arc_arrow(img, cx, cy, r, a0, a1, col, th=10, head=26):
    n = 28
    pts = [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]
    polyline(img, pts[:-3], col, th)
    arrow(img, pts[-4][0], pts[-4][1], pts[-1][0], pts[-1][1], col, th, head)


def tire_top(img, x, y, hw, hh, phase, rim_col, k=1.0):
    """Tyre seen from above; tread lines run with the rotation (forward = up)."""
    rrect(img, x - hw, y - hh, x + hw, y + hh, 22, C3(TIRE, k))
    for j in range(16):
        a = phase + 2 * math.pi * j / 16
        c = math.cos(a)
        if c <= 0.08:
            continue
        yy = y - (hh - 12) * math.sin(a)
        line(img, x - hw + 9, yy, x + hw - 9, yy, C3(mixc(TIRE, (120, 128, 144), 0.25 + 0.75 * c), k), 7)
    rrect_outline(img, x - hw, y - hh, x + hw, y + hh, 22, C3(rim_col, k), 5)


def wheel_icon(img, x, y, R, ang, col):
    circle(img, x, y, R, C3(TIRE))
    for j in range(12):
        a = ang + j * 2 * math.pi / 12
        line(img, x + R * 0.8 * math.cos(a), y + R * 0.8 * math.sin(a), x + R * 0.97 * math.cos(a),
             y + R * 0.97 * math.sin(a), C3((78, 86, 102)), 6)
    circle(img, x, y, R * 0.62, C3(mixc(col, DARK, 0.6)))
    circle(img, x, y, R * 0.62, C3(col), th=6)
    for j in range(5):
        a = ang + j * 2 * math.pi / 5
        line(img, x + R * 0.14 * math.cos(a), y + R * 0.14 * math.sin(a), x + R * 0.56 * math.cos(a),
             y + R * 0.56 * math.sin(a), C3(col), 9)
    circle(img, x, y, R * 0.16, C3(col))


def bevel(img, glow, bx, by, dx, dy, base_hw, tip_hw, length, phase, col, n=12, glow_k=0.0, k=1.0):
    """Bevel gear seen from the side: trapezoid from the wide base (bx,by) towards its apex direction (dx,dy).
    Tooth lines run base->tip and slide across the face as the gear turns (phase)."""
    px, py = -dy, dx
    tx, ty = bx + dx * length, by + dy * length
    pts = [(bx + px * base_hw, by + py * base_hw), (tx + px * tip_hw, ty + py * tip_hw),
           (tx - px * tip_hw, ty - py * tip_hw), (bx - px * base_hw, by - py * base_hw)]
    body = mixc(col, DARK, 0.5)
    poly(img, pts, C3(body, k))
    for j in range(n):
        a = phase + 2 * math.pi * j / n
        c = math.cos(a)
        if c <= 0.06:
            continue
        s = math.sin(a) * 0.96
        line(img, bx + px * base_hw * s, by + py * base_hw * s, tx + px * tip_hw * s, ty + py * tip_hw * s,
             C3(mixc(body, col, 0.3 + 0.7 * c), k), 5)
    polyline(img, pts, C3(col, k), 4, closed=True)
    line(img, pts[0][0], pts[0][1], pts[3][0], pts[3][1], C3(col, k), 9)
    if glow_k > 0:
        circle(glow, bx + dx * length * 0.5, by + dy * length * 0.5, length * 0.75, C3(col, glow_k), s=0.5)


def ring_slab(img, glow, x0, y0, x1, y1, phase, col, n=44, glow_k=0.0, k=1.0):
    """Ring gear seen edge-on from above, teeth on its left face."""
    body = mixc(col, DARK, 0.4)
    rrect(img, x0, y0, x1, y1, 8, C3(body, k))
    cyc, R = (y0 + y1) / 2, (y1 - y0) / 2 - 8
    for j in range(n):
        a = phase + 2 * math.pi * j / n
        c = math.cos(a)
        if c <= 0.05:
            continue
        yy = cyc - R * math.sin(a)
        poly(img, [(x0 + 1, yy - 7 * c - 1), (x0 - 15, yy), (x0 + 1, yy + 7 * c + 1)], C3(col, k))
        line(img, x0 + 5, yy, x1 - 5, yy, C3(mixc(body, col, 0.2 + 0.6 * c), k), 3)
    rrect_outline(img, x0, y0, x1, y1, 8, C3(col, k), 4)
    if glow_k > 0:
        rrect_outline(glow, x0 / 2 - 6, y0 / 2 - 6, x1 / 2 + 6, y1 / 2 + 6, 8, C3(col, glow_k), 10)


def counter(img, x, y, v, col, k=1.0, pop=0.0):
    if k <= 0.01:
        return
    rrect(img, x - 80, y - 54, x + 80, y + 54, 18, C3(DARK, k))
    rrect_outline(img, x - 80, y - 54, x + 80, y + 54, 18, C3(col, k), 4)
    blit(img, num_sprite(int(round(v)), col), x, y - 10, opacity=k, scale=1 + 0.3 * pop)
    blit(img, SPR_RPMU, x, y + 33, opacity=k)


def pop_k(t, t0, d=0.35):
    """1 -> 0 pulse right after t0 (for scale pops)."""
    if t < t0:
        return 0.0
    return max(0.0, 1 - (t - t0) / d)


def smoke(img, glow, x, y, t, t0, k=1.0, seed=1):
    if t < t0:
        return
    rng = np.random.default_rng(seed)
    for j in range(16):
        b = t0 + rng.random() * 0.9
        age = t - b
        if age < 0 or age > 1.2:
            continue
        f = age / 1.2
        px = x + (rng.random() - 0.5) * 90 + (rng.random() - 0.5) * 120 * f
        py = y + rng.random() * 60 + 150 * f
        r = 16 + 46 * f
        circle(img, px, py, r, C3(mixc((150, 156, 168), (24, 32, 48), f), k * (1 - 0.6 * f)))


def sparks(img, glow, x, y, t, t0, dur=0.8, seed=3, dirx=1.0):
    if not (t0 <= t < t0 + dur + 0.4):
        return
    rng = np.random.default_rng(seed)
    for j in range(26):
        b = t0 + rng.random() * dur
        age = t - b
        if age < 0 or age > 0.35:
            continue
        a = math.radians(rng.uniform(40, 140))
        v = rng.uniform(500, 1100)
        x0 = x + math.cos(a) * v * age * dirx
        y0 = y + math.sin(a) * v * age + 400 * age * age
        x1 = x0 - math.cos(a) * 30 * dirx
        y1 = y0 - math.sin(a) * 30
        col = YEL if rng.random() < 0.6 else ORANGE
        line(img, x0, y0, x1, y1, C3(col), 4)
        circle(glow, x0, y0, 10, C3(col, 0.7), s=0.5)


def car_top(img, hx, hy, tx, ty, nx, ny, L=110, Wd=70):
    def P2(u, v):
        return (hx + tx * u + nx * v, hy + ty * u + ny * v)
    for u in (-70, 70):
        for v, col in ((-Wd - 6, BLUE), (Wd + 6, ORANGE)):
            poly(img, [P2(u - 26, v - 11), P2(u + 26, v - 11), P2(u + 26, v + 11), P2(u - 26, v + 11)], C3(col))
    poly(img, [P2(-L, -Wd), P2(L - 18, -Wd), P2(L, -Wd + 18), P2(L, Wd - 18), P2(L - 18, Wd), P2(-L, Wd)], C3(CYAN))
    poly(img, [P2(12, -Wd + 12), P2(62, -Wd + 12), P2(62, Wd - 12), P2(12, Wd - 12)], C3(DARK))
    poly(img, [P2(-82, -Wd + 14), P2(-58, -Wd + 14), P2(-58, Wd - 14), P2(-82, Wd - 14)], C3(DARK))


def engine_icon(img, glow, x, y, k=1.0):
    rrect(img, x - 72, y - 30, x + 72, y + 52, 12, C3(M_MID, k))
    for i in range(3):
        rrect(img, x - 62 + i * 44, y - 64, x - 26 + i * 44, y - 26, 6, C3(M_LIGHT, k))
    circle(img, x - 80, y + 12, 24, C3(M_HI, k))
    circle(img, x - 80, y + 12, 8, C3(DARK, k))
    rrect_outline(img, x - 72, y - 30, x + 72, y + 52, 12, C3(M_HI, k), 3)


def blend_mask(img, mask, x0, y0, color, alpha):
    h, w = mask.shape
    reg = img[y0:y0 + h, x0:x0 + w].astype(np.float32)
    a = (mask * alpha)[..., None]
    img[y0:y0 + h, x0:x0 + w] = (reg * (1 - a) + np.array(color, np.float32) * a).astype(np.uint8)


# ------------------------------------------------------------------ intro: car in a left-hand corner
RCX, RCY, RC = 540, 1300, 400
A_T0, A_T1 = math.radians(-28), math.radians(-150)   # car drives right -> left (left turn)
TRACK_IN, TRACK_OUT = RC - 76, RC + 76


def car_angle(t):
    return A_T0 + (A_T1 - A_T0) * (t / PART_S)


def arc_pts(r, a0, a1, n=48):
    return [(RCX + r * math.cos(a0 + (a1 - a0) * j / n), RCY + r * math.sin(a0 + (a1 - a0) * j / n)) for j in range(n + 1)]


def road(img, k=1.0):
    cv2.ellipse(img, P(RCX, RCY), (int(RC * SC), int(RC * SC)), 0, -172, -8, C3(M_DARK, k), int(232), cv2.LINE_AA, SH)
    for j in range(30):
        a = math.radians(-170 + j * 162 / 29)
        circle(img, RCX + RC * math.cos(a), RCY + RC * math.sin(a), 5, C3(M_MID, k))


def scene_intro(img, glow, t):
    road(img)
    a = car_angle(t)
    a_start = math.radians(-6)
    if a < a_start:
        polyline(img, arc_pts(TRACK_IN, a_start, a), C3(BLUE), 10)
        polyline(img, arc_pts(TRACK_OUT, a_start, a), C3(ORANGE), 10)
    hx, hy = RCX + RC * math.cos(a), RCY + RC * math.sin(a)
    car_top(img, hx, hy, math.sin(a), -math.cos(a), math.cos(a), math.sin(a))
    # the two wheels as gauges: same engine, different spin
    wa_in, wa_out = -2.2 * t, -3.2 * t
    for x, ang, col, k1, k2 in ((250, wa_in, BLUE, 'INSIDE', 'SLOWER'), (830, wa_out, ORANGE, 'OUTSIDE', 'FASTER')):
        wheel_icon(img, x, 610, 70, ang, col)
        circle(glow, x, 610, 80, C3(col, 0.25), th=14, s=0.5)
        blit(img, TXT[k1], x, 505)
        if t >= DIFFR_S - 0.05:
            kk = ease_out3((t - DIFFR_S + 0.05) / 0.25)
            blit(img, TXT[k2], x, 722, opacity=kk, scale=1.3 - 0.3 * kk)
    if t >= ENGINE_S - 0.1:
        k = ramp(t, ENGINE_S - 0.1, 0.25)
        engine_icon(img, glow, 540, 615, k)
        blit(img, TXT['ENGINE'], 540, 722, opacity=k)
        for x1, col in ((345, BLUE), (735, ORANGE)):
            x0 = 540 - 105 if x1 < 540 else 540 + 105
            arrow(img, x0, 610, x1, 610, C3(col, k), 8, 22)
            p = ((t - ENGINE_S) * 1.4) % 1.0
            circle(img, x0 + (x1 - x0) * p, 610, 9, C3(YEL, k))
            circle(glow, x0 + (x1 - x0) * p, 610, 18, C3(YEL, 0.6 * k), s=0.5)
    if t >= BOTH_S:
        k = ease_out3((t - BOTH_S) / 0.3)
        blit(img, BIG['HOW?'], 540, 1165, opacity=k, scale=1.5 - 0.5 * k)


def scene_title(img, glow, t):
    k = ease_out3((t - PART_S + 0.1) / 0.3)
    blit(img, SPR_HEAD1, 540, 690, opacity=k, scale=2.0 - k)
    k2 = ease_out3((t - PART_S - 0.15) / 0.3)
    blit(img, SPR_HEAD2, 540, 850, opacity=k2, scale=2.0 - k2)
    cx, cy = 540, 1110
    circle(img, cx, cy, 92, C3(M_DARK))
    circle(img, cx, cy, 92, C3(CYAN), th=8)
    f = min(1.0, (t - PART_S) / 2.0)
    for j in range(int(60 * f)):
        a = -math.pi / 2 + j * 2 * math.pi / 60
        line(img, cx + 70 * math.cos(a), cy + 70 * math.sin(a), cx + 82 * math.cos(a), cy + 82 * math.sin(a), C3(CYAN), 4)
    ph = t * 2.5
    bevel(img, glow, cx, cy - 56, 0, 1, 26, 11, 34, ph, GREEN, n=8)
    bevel(img, glow, cx, cy + 56, 0, -1, 26, 11, 34, -ph, GREEN, n=8)
    bevel(img, glow, cx - 56, cy, 1, 0, 28, 12, 34, -ph, BLUE, n=8)
    bevel(img, glow, cx + 56, cy, -1, 0, 28, 12, 34, ph, ORANGE, n=8)


# ------------------------------------------------------------------ the outside wheel goes farther
AR0, AR1 = math.radians(-6), math.radians(-174)
BAR_K = 0.62
LEN_IN, LEN_OUT = TRACK_IN * abs(AR1 - AR0) * BAR_K, TRACK_OUT * abs(AR1 - AR0) * BAR_K
BAR_X0 = 540 - LEN_OUT / 2
BAR_Y_OUT, BAR_Y_IN = 960, 1080


def scene_paths(img, glow, t):
    f = eramp(t, FARTHER_S, 0.75)
    for r, L, yb, col, glow_on in ((TRACK_IN, LEN_IN, BAR_Y_IN, BLUE, False), (TRACK_OUT, LEN_OUT, BAR_Y_OUT, ORANGE, True)):
        pts = []
        for j in range(61):
            s = j / 60
            a = AR0 + (AR1 - AR0) * s
            px, py = RCX + r * math.cos(a), RCY + r * math.sin(a)
            qx, qy = BAR_X0 + L * (1 - s), yb          # unrolled: arc start (right) -> bar end
            pts.append((px + (qx - px) * f, py + (qy - py) * f))
        th = 14
        if glow_on and t >= OUTSIDE_B:
            th = 14 + 6 * pop_k(t, OUTSIDE_B, 0.5)
            polyline(glow, [(x / 2, y / 2) for x, y in pts], C3(col, 0.6), 10)
        polyline(img, pts, C3(col), th)
        circle(img, pts[0][0], pts[0][1], 12, C3(col))
        circle(img, pts[-1][0], pts[-1][1], 12, C3(col))
    ka = 1 - f
    if ka > 0.01:
        blit(img, TXT['OUTSIDE'], 540, RCY - TRACK_OUT - 52, opacity=ka)
        blit(img, TXT['INSIDE'], 540, RCY - TRACK_IN + 56, opacity=ka)
    if f > 0.6:
        kb = ramp(t, FARTHER_S + 0.45, 0.3)
        blit(img, TXT['OUTSIDE'], BAR_X0 + 120, BAR_Y_OUT - 56, opacity=kb)
        blit(img, TXT['INSIDE'], BAR_X0 + 95, BAR_Y_IN + 56, opacity=kb)
        x_a, x_b = BAR_X0 + LEN_IN, BAR_X0 + LEN_OUT
        if t >= FARTHER_S + 0.7:
            kc = ramp(t, FARTHER_S + 0.7, 0.25)
            line(img, x_a, BAR_Y_OUT - 40, x_a, BAR_Y_IN + 10, C3(WHITE, 0.6 * kc), 3)
            rrect(img, x_a, BAR_Y_OUT - 13, x_b, BAR_Y_OUT + 13, 6, C3(YEL, kc))
            circle(glow, (x_a + x_b) / 2, BAR_Y_OUT, 140, C3(YEL, 0.35 * kc), s=0.5)
            blit(img, TXT['FARTHER'], (x_a + x_b) / 2, BAR_Y_OUT + 62, opacity=kc, scale=1.2 - 0.2 * kc)


# ------------------------------------------------------------------ solid axle: same speed -> skid
AX_Y = 990
AX_L, AX_R = 250, 830
TURN_CX = -350


def scene_axle(img, glow, t):
    ph = 3.0 * (t - ON_S)
    kk = ramp(t, SOLID_S - 0.1, 0.3)
    # wanted paths (left turn): inner wheel short, outer wheel long
    if kk > 0:
        for xw, col in ((AX_L, BLUE), (AX_R, ORANGE)):
            r = xw - TURN_CX
            a0 = -math.asin(130 / r)
            arc_arrow(img, TURN_CX, AX_Y, r, a0, a0 - 0.25 * kk, C3(col, kk), 9, 26)
    # skid marks behind the inner tyre
    if t >= SKID_S:
        ks = ramp(t, SKID_S, 0.6)
        for dx in (-30, 30):
            line(img, AX_L + dx, AX_Y + 128, AX_L + dx + 8 * ks, AX_Y + 128 + 220 * ks, C3((8, 10, 14)), 14)
    shake = 6 * math.sin(t * 70) * pop_k(t, SKID_S, 0.5)
    # solid axle bar
    rrect(img, AX_L + 40, AX_Y - 22, AX_R - 40, AX_Y + 22, 8, C3(M_MID))
    stripes(img, AX_L + 40, AX_Y - 22, AX_R - 40, AX_Y + 22, ph * 30, M_HI)
    tire_top(img, AX_L + shake, AX_Y, 52, 128, ph, BLUE)
    tire_top(img, AX_R, AX_Y, 52, 128, ph, ORANGE)
    if kk > 0:
        rrect(img, 540 - 46, AX_Y - 46, 540 + 46, AX_Y + 46, 14, C3(DARK, kk))
        lock_icon(img, 540, AX_Y - 12, 1.0, RED)
        blit(img, TXT['SOLID AXLE'], 540, AX_Y + 96, opacity=kk)
    if t >= SAME_S - 0.1:
        k = ramp(t, SAME_S - 0.1, 0.25)
        p = pop_k(t, SAME_S)
        counter(img, 395, AX_Y - 170, 100, WHITE, k, p)
        counter(img, 685, AX_Y - 170, 100, WHITE, k, p)
        blit(img, TXT['='], 540, AX_Y - 172, opacity=k, scale=1.4)
        blit(img, TXT['SAME SPEED'], 540, AX_Y - 262, opacity=k)
    if t >= SKID_S - 0.1:
        smoke(img, glow, AX_L, AX_Y + 60, t, SKID_S - 0.1, seed=7)
        k = ease_out3((t - SKID_S + 0.1) / 0.25)
        blit(img, SPR_SKID, AX_L + 40, AX_Y + 300, opacity=k, scale=1.5 - 0.5 * k)
        circle(glow, AX_L, AX_Y, 170, C3(RED, 0.45 * pop_k(t, SKID_S, 0.6)), s=0.5)


# ------------------------------------------------------------------ the differential (top view, car points up)
CX, CY = 470, 940
XR = CX + 150                 # ring gear face
XP = XR - 30                  # pinion / driveshaft axis
WL, WR = 140, 940             # wheel centres
K_VIS = 0.03                  # rad/s per rpm (for drawing)
DT = 1 / 240.0
TGRID = np.arange(0, DUR + 1, DT)


def speeds_diff(t):
    """(carrier, left, right) in rpm for the explanation scene."""
    if t < DSHAFT_S - 0.1:
        return 0.0, 0.0, 0.0
    base = 100 * eramp(t, DSHAFT_S - 0.1, 0.8)
    d = 10 * eramp(t, SLOWS_S - 0.05, 1.0)
    return base, base - d, base + d


def speeds_ice(t):
    c = 100.0
    up = eramp(t, SPINS_H - 0.25, 0.8)
    back = eramp(t, LSD_S + 0.15, 0.9)
    left = 100 + 100 * up - 100 * back
    right = 100 - 100 * up + 100 * back
    return c, left, right


def phase_table(fn):
    sp = np.array([fn(u) for u in TGRID])
    ph = np.cumsum(sp, axis=0) * DT * K_VIS
    return sp, ph


SP_D, PH_D = phase_table(speeds_diff)
SP_I, PH_I = phase_table(speeds_ice)


def lookup(tab, t):
    i = min(len(TGRID) - 1, max(0, int(t / DT)))
    return tab[i]


# housing silhouette (closed axle) as a soft mask
HX0, HY0, HX1, HY1 = 180, 580, 900, 1200
_tmp = np.zeros((HY1 - HY0, HX1 - HX0), np.uint8)
cv2.circle(_tmp, P(CX + 40 - HX0, CY - HY0), int(240 * SC), 255, -1, cv2.LINE_AA, SH)
cv2.fillPoly(_tmp, [np.array([P(XP - 58 - HX0, CY - 345 - HY0), P(XP + 58 - HX0, CY - 345 - HY0),
                               P(XP + 70 - HX0, CY - 150 - HY0), P(XP - 70 - HX0, CY - 150 - HY0)], np.int32)], 255, cv2.LINE_AA, SH)
cv2.rectangle(_tmp, (200 - HX0, CY - 38 - HY0), (885 - HX0, CY + 38 - HY0), 255, -1)
HOUSING_MASK = _tmp.astype(np.float32) / 255.0
_edge = cv2.morphologyEx(_tmp, cv2.MORPH_GRADIENT, np.ones((5, 5), np.uint8)).astype(np.float32) / 255.0
HOUSING_EDGE = _edge


def draw_diff(img, glow, t, sp, ph, mode):
    """mode: 'explain' (build-up + straight + corner) or 'ice'."""
    c_rpm, l_rpm, r_rpm = lookup(sp, t)
    pc, pl, pr = lookup(ph, t)
    p_pin = pc * 3.4
    spider = (pr - pl) * 0.8
    explain = mode == 'explain'
    vis = (lambda t0: 1.0 if not explain else ramp(t, t0 - 0.1, 0.3))
    k_hous = 1.0 - eramp(t, DSHAFT_S + 0.2, 0.6) if explain else 0.0
    corner = explain and t >= SLOWS_S - 0.05
    col_l = BLUE if corner or not explain else M_HI
    col_r = ORANGE if corner or not explain else M_HI
    if not explain:
        col_l, col_r = M_HI, M_HI
    # wheels + axle shafts
    tire_top(img, WL, CY, 48, 124, pl, col_l)
    tire_top(img, WR, CY, 48, 124, pr, col_r)
    for x0, x1, p in ((WL + 46, CX - 120, pl), (XR + 30, WR - 46, pr)):
        rrect(img, x0, CY - 17, x1, CY + 17, 6, C3(M_MID))
        stripes(img, x0, CY - 17, x1, CY + 17, p * 30, M_HI)
    # closed housing (fades away = cut-away view)
    if k_hous > 0.01:
        blend_mask(img, HOUSING_MASK, HX0, HY0, (46, 58, 80), 0.97 * k_hous)
        blend_mask(img, HOUSING_EDGE, HX0, HY0, M_LIGHT, k_hous)
    else:
        blend_mask(img, HOUSING_EDGE, HX0, HY0, M_DARK, 0.8)
    if explain and DIFF_S - 0.1 <= t < DSHAFT_S + 0.8:
        kd = ramp(t, DIFF_S - 0.1, 0.25) * (1 - ramp(t, DSHAFT_S + 0.4, 0.4))
        circle(glow, CX + 40, CY, 250, C3(YEL, 0.45 * kd), th=24, s=0.5)
        blit(img, TXT['DIFFERENTIAL'], CX + 40, CY + 300, opacity=kd, scale=1.25 - 0.25 * ramp(t, DIFF_S - 0.1, 0.25))
    # driveshaft from the engine
    ks = vis(DSHAFT_S)
    if ks > 0:
        rrect(img, XP - 20, 470, XP + 20, CY - 282, 6, C3(M_MID, ks))
        stripes(img, XP - 20, 470, XP + 20, CY - 282, p_pin * 20, M_HI, horiz=False)
    # carrier (cage)
    kc = vis(CAGE_S)
    glow_block = explain and WHOLE_S - 0.1 <= t < SLOWS_S - 0.1
    if kc > 0:
        cage_col = CYAN
        rrect(img, CX - 150, CY - 152, XR, CY + 152, 26, C3(mixc(DARK, cage_col, 0.12), kc))
        rrect_outline(img, CX - 150, CY - 152, XR, CY + 152, 26, C3(cage_col, kc), 7)
        if glow_block:
            gk = 0.35 + 0.15 * math.sin(t * 8)
            rrect_outline(glow, (CX - 150) / 2 - 6, (CY - 152) / 2 - 6, XR / 2 + 6, (CY + 152) / 2 + 6, 14, C3(CYAN, gk), 12)
    # ring gear (bolted to the cage)
    kr = vis(RING_S)
    if kr > 0:
        ring_slab(img, glow, XR, CY - 215, XR + 34, CY + 215, pc, YEL, glow_k=0.35 * pop_k(t, RING_S, 0.8) if explain else 0, k=kr)
        if explain and t >= BOLTED_S - 0.1:
            kb = ramp(t, BOLTED_S - 0.1, 0.3)
            for j in range(10):
                a = pc + 2 * math.pi * j / 10
                cc = math.cos(a)
                if cc <= 0.1:
                    continue
                yy = CY - 150 * math.sin(a)
                circle(img, XR + 17, yy, 7, C3(WHITE, kb * (0.4 + 0.6 * cc)))
                if t < BOLTED_S + 0.8:
                    circle(glow, XR + 17, yy, 14, C3(WHITE, 0.5 * pop_k(t, BOLTED_S, 0.8)), s=0.5)
    # pinion on the driveshaft
    kp = vis(PINION_S)
    if kp > 0:
        bevel(img, glow, XP, CY - 282, 0, 1, 46, 22, 78, p_pin, ORANGE, n=10, k=kp,
              glow_k=0.4 * pop_k(t, PINION_S, 0.8) if explain else 0)
    # cross pin + spider gears
    kd = vis(SPIDER_S)
    spin_glow = 0.0
    if (explain and t >= START_S - 0.1) or (not explain and abs(l_rpm - r_rpm) > 5):
        spin_glow = 0.35 + 0.15 * math.sin(t * 10)
    if kd > 0:
        rrect(img, CX - 9, CY - 140, CX + 9, CY + 140, 4, C3(M_LIGHT, kd))
        sp_col = GREEN
        bevel(img, glow, CX, CY - 128, 0, 1, 54, 22, 76, spider, sp_col, n=10, k=kd, glow_k=spin_glow)
        bevel(img, glow, CX, CY + 128, 0, -1, 54, 22, 76, -spider, sp_col, n=10, k=kd, glow_k=spin_glow)
    # side gears (one per wheel)
    kg = vis(SIDE_S)
    if kg > 0:
        bevel(img, glow, CX - 128, CY, 1, 0, 60, 25, 76, -pl, col_l if col_l != M_HI else BLUE, n=12, k=kg)
        bevel(img, glow, CX + 128, CY, -1, 0, 60, 25, 76, pr, col_r if col_r != M_HI else ORANGE, n=12, k=kg)
    return c_rpm, l_rpm, r_rpm


LABELS = [('DRIVESHAFT', WHITE, 330, 520, lambda t: (XP - 22, 540), DSHAFT_S, T['D'] - 0.4),
          ('PINION', ORANGE, 330, 640, lambda t: (XP - 30, CY - 240), PINION_S, T['E'] - 0.4),
          ('RING GEAR', YEL, 845, 600, lambda t: (XR + 30, CY - 150), RING_S, T['E'] - 0.4),
          ('CAGE', CYAN, 190, 1215, lambda t: (CX - 120, CY + 150), CAGE_S, T['E'] - 0.4),
          ('SIDE GEARS', BLUE, 230, 1310, lambda t: (CX - 95, CY + 20), SIDE_S, T['E'] - 0.4),
          ('SPIDER GEARS', GREEN, 650, 1300, lambda t: (CX + 10, CY + 75), SPIDER_S, T['E'] - 0.4)]


def scene_diff(img, glow, t):
    c, l, r = draw_diff(img, glow, t, SP_D, PH_D, 'explain')
    # "one per wheel": power pulses run out to both wheels
    if PERW_S - 0.3 <= t < T['E'] + 0.3:
        k = ramp(t, PERW_S - 0.3, 0.2) * (1 - ramp(t, T['E'], 0.3))
        for x0, x1 in ((CX - 128, WL + 50), (CX + 128, WR - 50)):
            p = ((t - PERW_S + 0.3) * 1.5) % 1.0
            circle(img, x0 + (x1 - x0) * p, CY, 12, C3(YEL, k))
            circle(glow, x0 + (x1 - x0) * p, CY, 22, C3(YEL, 0.7 * k), s=0.5)
    # straight: spider gears do not turn, everything one block, equal speeds
    if T['E'] - 0.1 <= t < CORNER_F:
        if t >= DONT_S - 0.1:
            k = ramp(t, DONT_S - 0.1, 0.25) * (1 - ramp(t, WHOLE_S - 0.2, 0.25))
            blit(img, TXT['NOT TURNING'], CX, 1215, opacity=k)
            if k > 0.05:
                for yy in (CY - 92, CY + 92):
                    red_x(img, CX + 82, yy, 16, k)
        if t >= WHOLE_S - 0.1:
            k = ramp(t, WHOLE_S - 0.1, 0.25)
            blit(img, TXT['ONE BLOCK'], CX, 1215, opacity=k, scale=1.2 - 0.2 * k)
    # wheel speed counters
    if t >= BOTHW_S - 0.1:
        k = ramp(t, BOTHW_S - 0.1, 0.25)
        corner = t >= SLOWS_S - 0.05
        cl = BLUE if corner else WHITE
        cr = ORANGE if corner else WHITE
        pl = max(pop_k(t, BOTHW_S), pop_k(t, SLOWS_S, 0.5), pop_k(t, NINETY_S, 0.5), pop_k(t, EXACTLY_S, 0.5))
        pr = max(pop_k(t, BOTHW_S), pop_k(t, SPEEDS_S, 0.5), pop_k(t, ONETEN_S, 0.5), pop_k(t, EXACTLY_S, 0.5))
        counter(img, WL + 10, 1150, l, cl, k, pl)
        counter(img, WR - 10, 1150, r, cr, k, pr)
        if t < SLOWS_S:
            blit(img, TXT['='], 540, 1150, opacity=k, scale=1.4)
    # corner: turn sign, spider gears start to turn, -10 / +10
    if T['E'] - 0.1 <= t < CORNER_F:
        k = ramp(t, T['E'] - 0.1, 0.25)
        arrow(img, 340, 735, 340, 535, C3(WHITE, k), 14, 36)
        blit(img, TXT['STRAIGHT'], 170, 690, opacity=k)
    if t >= CORNER_F - 0.1:
        k = ramp(t, CORNER_F - 0.1, 0.25)
        polyline(img, [(340, 735), (340, 640)], C3(WHITE, k), 14)
        arc_arrow(img, 260, 640, 80, 0.0, -math.pi / 2 * k - 0.001, C3(WHITE, k), 14, 0.1)
        arrow(img, 270, 560, 215, 560, C3(WHITE, k), 14, 36)
        blit(img, TXT['LEFT TURN'], 175, 690, opacity=k)
        if t >= SLOWS_S:
            k1 = ramp(t, SLOWS_S, 0.25)
            blit(img, TXT['-10'], WL + 150, 1150, opacity=k1, scale=1 + 0.3 * pop_k(t, SLOWS_S))
        if t >= SPEEDS_S:
            k2 = ramp(t, SPEEDS_S, 0.25)
            blit(img, TXT['+10'], WR - 150, 1150, opacity=k2, scale=1 + 0.3 * pop_k(t, SPEEDS_S))
        if START_S - 0.1 <= t < T['G']:
            k3 = ramp(t, START_S - 0.1, 0.25)
            blit(img, TXT['TURNING'], CX, 1215, opacity=k3, scale=1.2 - 0.2 * k3)
            for yy, s in ((CY - 92, 1), (CY + 92, -1)):
                a0 = (t * 4 * s) % (2 * math.pi)
                arc_arrow(img, CX, yy, 64, a0, a0 + 1.6 * s, C3(YEL, k3), 6, 18)
    # the numbers: ring 100, inside 90, outside 110, average 100
    if t >= RING_G - 0.1:
        k = ramp(t, RING_G - 0.1, 0.25)
        blit(img, SPR_RINGLBL, 845, 548, opacity=k)
        counter(img, 845, 625, c, YEL, k, pop_k(t, RING_G, 0.5))
        line(img, 845 - 82, 660, XR + 40, CY - 200, C3(YEL, 0.5 * k), 3)
    if t >= AVERAGE_S - 0.1:
        k = ease_out3((t - AVERAGE_S + 0.1) / 0.3)
        blit(img, SPR_EQ, 540, 1310, opacity=k, scale=1.25 - 0.25 * k)
        circle(glow, 540, 1310, 150, C3(YEL, 0.18 * k * (0.6 + 0.4 * pop_k(t, AVERAGE_S, 0.8))), s=0.5)


ICE_X0, ICE_X1 = 40, 245


def scene_ice(img, glow, t):
    # ice patch under the left wheel (slides away once the car drives off)
    if t >= ICE_S - 0.15:
        k = ramp(t, ICE_S - 0.15, 0.3)
        drive = eramp(t, LOCK_S + 0.2, 1.0)
        off = 260 * drive
        k *= 1 - drive
        y0, y1 = CY - 210 + off, min(CY + 210 + off, 1225)
        if k > 0.01 and y1 - y0 > 40:
            blend_rect(img, ICE_X0, y0, ICE_X1, y1, ICE, 0.32 * k)
            rrect_outline(img, ICE_X0, y0, ICE_X1, y1, 18, C3(ICE, k), 3)
            rng = np.random.default_rng(11)
            for j in range(9):
                sx = ICE_X0 + 20 + rng.random() * (ICE_X1 - ICE_X0 - 40)
                sy = y0 + 20 + rng.random() * (y1 - y0 - 40)
                tw = 0.5 + 0.5 * math.sin(t * 5 + j * 1.7)
                L = 6 + 10 * tw
                line(img, sx - L, sy, sx + L, sy, C3(WHITE, k * tw), 3)
                line(img, sx, sy - L, sx, sy + L, C3(WHITE, k * tw), 3)
            if off < 50:
                blit(img, TXT['ICE'], (ICE_X0 + ICE_X1) / 2, CY - 250, opacity=k)
    c, l, r = draw_diff(img, glow, t, SP_I, PH_I, 'ice')
    # ice spray from the spinning wheel
    if SPINS_H - 0.2 <= t < LSD_S + 0.6:
        rng = np.random.default_rng(5)
        k = ramp(t, SPINS_H - 0.2, 0.3) * (1 - ramp(t, LSD_S + 0.2, 0.4))
        for j in range(22):
            ph0 = rng.random()
            f = ((t * 2.2) + ph0) % 1.0
            x = WL + (rng.random() - 0.5) * 80 + (rng.random() - 0.5) * 140 * f
            y = CY + 125 + 260 * f
            circle(img, x, y, 7 * (1 - f) + 2, C3(mixc(WHITE, ICE, f), k * (1 - f)))
    # torque arrows: equal on both sides; tiny once one wheel spins; big on the grip side after the fix
    if t >= EQUAL_S - 0.1:
        k = ramp(t, EQUAL_S - 0.1, 0.3)
        small = eramp(t, SPINS_H - 0.1, 0.6)
        fix = eramp(t, LSD_S + 0.15, 0.8)
        L_left = 115 * (1 - 0.8 * small)
        L_right = 115 * (1 - 0.8 * small) + 80 * fix
        col_t = RED if (small > 0.5 and fix < 0.5) else GREEN
        arrow(img, CX - 165, CY - 95, CX - 165 - L_left, CY - 95, C3(col_t, k), 16, 30)
        arrow(img, XR + 60, CY - 95, XR + 60 + L_right, CY - 95, C3(col_t, k), 16, 30)
        kk = k * (1 - ramp(t, ICE_S - 0.2, 0.25))
        blit(img, TXT['EQUAL TORQUE'], CX, 1215, opacity=kk)
    # counters
    k = ramp(t, T['H'] - 0.1, 0.3)
    cl = ICE if l > 130 else (GREEN if t > LSD_S + 0.5 else WHITE)
    cr = RED if r < 30 else (GREEN if t > LSD_S + 0.5 else WHITE)
    counter(img, WL + 10, 1150, l, cl, k, pop_k(t, SPINS_H + 0.4, 0.5))
    counter(img, WR - 10, 1150, r, cr, k, max(pop_k(t, OTHER_S + 0.2, 0.5), pop_k(t, LSD_S + 0.9, 0.5)))
    if OTHER_S - 0.1 <= t < LSD_S:
        k2 = ramp(t, NOTHING_S - 0.15, 0.25)
        blit(img, TXT['ALMOST NOTHING'], 730, 1255, opacity=k2, scale=1.2 - 0.2 * k2)
        k3 = ramp(t, OTHER_S - 0.1, 0.25)
        blit(img, TXT['STUCK'], WR - 10, 760, opacity=k3)
    # the fix
    if t >= SPORTS_S - 0.1:
        k = ramp(t, SPORTS_S - 0.1, 0.25)
        blit(img, TXT['SPORTS CARS'], 845, 545, opacity=k)
    if t >= OFFR_S - 0.1:
        k = ramp(t, OFFR_S - 0.1, 0.25)
        blit(img, TXT['OFF-ROADERS'], 845, 620, opacity=k)
    if t >= LSD_S - 0.1:
        k = ramp(t, LSD_S - 0.1, 0.25)
        sq = eramp(t, LSD_S + 0.1, 0.5)
        gap = 9 * (1 - sq)
        for x_in, sgn in ((CX - 156, -1), (XR + 40, 1)):
            x = x_in
            for j in range(5):
                col = ORANGE if j % 2 == 0 else M_HI
                w = 8
                xa = x if sgn > 0 else x - w
                rrect(img, xa, CY - 62 + (0 if j % 2 else 10), xa + w, CY + 62 - (0 if j % 2 else 10), 3, C3(col, k))
                x += sgn * (w + gap)
        if sq > 0.9:
            circle(glow, CX - 175, CY, 70, C3(ORANGE, 0.5), s=0.5)
            circle(glow, XR + 70, CY, 70, C3(ORANGE, 0.5), s=0.5)
        blit(img, TXT['LIMITED-SLIP'], 300, 1300, opacity=k, scale=1.2 - 0.2 * k)
    if t >= LOCK_S - 0.1:
        k = ramp(t, LOCK_S - 0.1, 0.25)
        rrect(img, CX - 42, CY - 46, CX + 42, CY + 46, 14, C3(DARK, k))
        lock_icon(img, CX, CY - 12, 1.1, YEL)
        circle(glow, CX, CY, 90, C3(YEL, 0.5 * k), s=0.5)
        blit(img, TXT['LOCKER'], 720, 1300, opacity=k, scale=1.2 - 0.2 * k)


# ------------------------------------------------------------------ teaser: brakes
DSX, DSY, DSR = 600, 830, 185


def disc_angle(t):
    t0 = T['K'] - 0.3
    t_stop = STOP_S + 0.7
    w0 = 5.0
    if t <= STOP_S:
        return w0 * (t - t0)
    u = min(t, t_stop) - STOP_S
    d = t_stop - STOP_S
    return w0 * (STOP_S - t0) + w0 * (u - u * u / (2 * d))


def scene_teaser(img, glow, t):
    a = disc_angle(t)
    heat = eramp(t, STOP_S, 0.5) * (1 - 0.5 * ramp(t, STOP_S + 1.5, 1.5))
    disc_col = mixc(M_LIGHT, ORANGE, 0.75 * heat)
    circle(img, DSX, DSY, DSR, C3(disc_col))
    circle(img, DSX, DSY, DSR, C3(M_HI), th=5)
    if heat > 0.05:
        circle(glow, DSX, DSY, DSR + 10, C3(ORANGE, 0.45 * heat), th=40, s=0.5)
    for j in range(18):
        aa = a + j * 2 * math.pi / 18
        for rr in (DSR * 0.62, DSR * 0.8):
            circle(img, DSX + rr * math.cos(aa + (0.17 if rr > 120 else 0)), DSY + rr * math.sin(aa + (0.17 if rr > 120 else 0)), 7, C3(DARK))
    circle(img, DSX, DSY, DSR * 0.42, C3(M_MID))
    circle(img, DSX, DSY, DSR * 0.42, C3(M_HI), th=4)
    for j in range(5):
        aa = a + j * 2 * math.pi / 5
        circle(img, DSX + 46 * math.cos(aa), DSY + 46 * math.sin(aa), 11, C3(M_HI))
    circle(img, DSX, DSY, 20, C3(DARK))
    # caliper clamps on the word "stop"
    kc = ramp(t, BRAKES_S - 0.1, 0.25)
    if kc > 0:
        sq = 10 * eramp(t, STOP_S - 0.05, 0.15)
        x0 = DSX + DSR - 70 - sq
        rrect(img, x0, DSY - 105, DSX + DSR + 45, DSY + 105, 26, C3(RED, kc))
        rrect(img, x0 + 16, DSY - 70, x0 + 40, DSY + 70, 8, C3((150, 40, 40), kc))
        sparks(img, glow, DSX + DSR - 40, DSY + 90, t, STOP_S, dur=0.7, seed=9)
    # foot on the pedal
    if t >= FOOT_S - 0.15:
        k = ramp(t, FOOT_S - 0.15, 0.25)
        press = eramp(t, FOOT_S, 0.3)
        px, py = 190, 900
        ang = math.radians(-62 + 18 * press)
        ex, ey = px + 150 * math.cos(ang), py + 150 * math.sin(ang)
        line(img, px, py + 70, ex, ey, C3(M_LIGHT, k), 14)
        rrect(img, ex - 55, ey - 18, ex + 55, ey + 18, 9, C3(M_HI, k))
        arrow(img, ex + 10, ey - 120 + 30 * press, ex + 10, ey - 30, C3(YEL, k), 10, 24)
        blit(img, TXT['1 FOOT'], 140, 640, opacity=k)
        # hydraulic line to the caliper
        pts = [(px + 30, py + 70), (px + 30, 1030), (DSX + DSR + 10, 1030), (DSX + DSR + 10, DSY + 105)]
        polyline(img, pts, C3(BLUE, 0.8 * k), 6)
        if t >= FOOT_S:
            f = min(1.0, (t - FOOT_S) / 0.55)
            q = path_point(pts, f)
            circle(img, q[0], q[1], 11, C3(YEL))
            circle(glow, q[0], q[1], 22, C3(YEL, 0.7), s=0.5)
    if t >= TON_S - 0.1:
        k = ramp(t, TON_S - 0.1, 0.25)
        x, y = 880, 560
        poly(img, [(x - 70, y + 50), (x + 70, y + 50), (x + 50, y - 40), (x - 50, y - 40)], C3(M_MID, k))
        circle(img, x, y - 52, 18, C3(M_MID, k), th=7)
        blit(img, TXT['2 TONS'], x, y + 8, opacity=k, scale=0.9 + 0.1 * ease_out3((t - TON_S) / 0.25))
    blit(img, SPR_PART5, W / 2, 1180)


SCENES = [(0.0, scene_intro), (PART_S - 0.15, scene_title), (T['B'] - 0.15, scene_paths),
          (ON_S - 0.15, scene_axle), (T['C'] - 0.15, scene_diff), (T['H'] - 0.15, scene_ice),
          (T['K'] - 0.15, scene_teaser)]
FADE = 0.25


def render_frame(t):
    frame = BG.copy()
    glow = np.zeros((H // 2, W // 2, 3), np.uint8)
    for i, (t0, fn) in enumerate(SCENES):
        t1 = SCENES[i + 1][0] if i + 1 < len(SCENES) else 1e9
        if t < t0 or t >= t1 + FADE:
            continue
        a = min(1.0, (t - t0) / FADE) if i > 0 else 1.0
        if t >= t1:
            a *= max(0.0, 1 - (t - t1) / FADE)
        if a <= 0.01:
            continue
        if a < 0.999:
            tmp = BG.copy()
            fn(tmp, glow, t)
            frame = cv2.addWeighted(frame, 1 - a, tmp, a, 0)
        else:
            fn(frame, glow, t)
    if t >= FOLLOW_S - 0.1:
        fa = min(1, (t - FOLLOW_S + 0.1) / 0.25)
        pulse = 1 + 0.05 * math.sin((t - FOLLOW_S) * 8)
        bw, bh = 300 * pulse, 52 * pulse
        rrect(frame, W / 2 - bw, 1300 - bh, W / 2 + bw, 1300 + bh, 52, C3(YEL, fa))
        circle(glow, W / 2, 1300, 200, C3(YEL, 0.35 * fa), th=40, s=0.5)
        blit(frame, SPR_FOLLOW, W / 2, 1302, opacity=fa, scale=pulse)
    g = cv2.GaussianBlur(glow, (0, 0), 8)
    frame = cv2.add(frame, cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR))
    if T['C'] - 0.15 <= t < T['E']:
        draw_labels(frame, t)
    blit(frame, SPR_SERIES, W / 2, 168)
    blit(frame, SPR_TITLE, W / 2, 238)
    prog = min(1.0, t / max(DUR - 0.5, 1))
    rrect(frame, 140, 300, 940, 310, 5, C3(M_DARK))
    rrect(frame, 140, 300, 140 + max(12, 800 * prog), 310, 5, C3(CYAN))
    for b0, b1, spr in BADGES:
        if b0 <= t < b1:
            first = b0 <= 0.0
            blit(frame, spr, W / 2, 395, opacity=1.0 if first else min(1.0, (t - b0 + 0.05) / 0.25),
                 scale=1.0 if first else 0.9 + 0.1 * ease_out3((t - b0) / 0.25))
    draw_caption(frame, t)
    return frame


def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'stills':
        for ts in sys.argv[2:]:
            Image.fromarray(render_frame(float(ts))).save(f'still_{float(ts):05.2f}.png')
        print('stills done; DUR', round(DUR, 2), 'frames', N_FRAMES)
        return
    a, b, out = int(sys.argv[2]), min(int(sys.argv[3]), N_FRAMES), sys.argv[4]
    cmd = ['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p',
           '-threads', '2', out + '.tmp.mp4']
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(a, b):
        proc.stdin.write(render_frame(i / FPS).tobytes())
    proc.stdin.close()
    if proc.wait() == 0:
        os.replace(out + '.tmp.mp4', out)
        print('done', a, b, out)
    else:
        sys.exit('ffmpeg failed')


if __name__ == '__main__':
    main()
