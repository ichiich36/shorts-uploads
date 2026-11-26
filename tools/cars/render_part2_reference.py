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


def we(seg, key, nth=1):
    return TL.word(seg, key, nth)[1]


T = {s: TL.seg_start(s) for s in 'ACDEFGHIJK'}
GREEN = (74, 222, 128)
BLUE = (96, 165, 250)
ORANGE = (251, 146, 60)
RED = (248, 72, 72)
GREY = (120, 128, 140)

HERE_S = ws('A', "here's")
STALL_S = ws('C', 'stalls')
SCREAM_S = ws('D', 'screams')
KEEP_S = ws('E', 'gears')
BIG_S = ws('F', 'big', 2)
PRESS_S = ws('G', 'press')
DISC_S = ws('G', 'disconnects')
STICK_S = ws('H', 'stick')
FORK_S = ws('H', 'fork')
COLLAR_S = ws('H', 'collar')
LOCK_S = ws('H', 'locks')
SHAFT_S = ws('H', 'output')
SPIN_S = ws('I', 'spinning')
PICK_S = ws('I', 'picks')
WHEELS_S = ws('I', 'wheels')
SYN_S = ws('J', 'synchronizer')
NOCL_S = ws('J', 'without')
GRIND_S = ws('J', 'clash')
FOLLOW_S = ws('K', 'follow')


def ramp(t, t0, d=0.3):
    return min(1.0, max(0.0, (t - t0) / d))


SPR_SERIES = text_sprite([('HOW CARS WORK', CYAN)], font(F_XBOLD, 34), tracking=7, shadow=0.4)
SPR_TITLE = fit(text_sprite([('PART 2: ', WHITE), ('THE GEARBOX', YEL)], font(F_BLACK, 76)))


def badge(text, col=WHITE):
    return fit(text_sprite([(text, col)], font(F_XBOLD, 40), tracking=3))


BADGES = [(0.0, HERE_S, badge('WHY DOES A CAR NEED GEARS?', YEL)),
          (HERE_S, T['C'], badge('EXPLAINED IN 60 SECONDS')),
          (T['C'], T['D'], badge('5TH GEAR FROM A STOP', ORANGE)),
          (T['D'], T['E'], badge('1ST GEAR ON THE HIGHWAY', RED)),
          (T['E'], T['F'], badge('THE SWEET SPOT', GREEN)),
          (T['F'], BIG_S, badge('1ST GEAR  =  FORCE', GREEN)),
          (BIG_S, T['G'], badge('5TH GEAR  =  SPEED', BLUE)),
          (T['G'], DISC_S, badge('THE CLUTCH')),
          (DISC_S, T['H'], badge('ENGINE DISCONNECTED', ORANGE)),
          (T['H'], T['I'], badge('SHIFTING 1ST → 2ND', YEL)),
          (T['I'], T['J'], badge('ALWAYS SPINNING')),
          (T['J'], NOCL_S, badge('SYNCHRONIZER', GREEN)),
          (NOCL_S, T['K'], badge('NO CLUTCH = GRIND', RED))]
TXT = {k: text_sprite([(k, c)], font(F_BLACK, 46), shadow=0.6) for k, c in
       [('ENGINE', WHITE), ('WHEELS', WHITE), ('GEARBOX', WHITE), ('CLUTCH', ORANGE), ('1ST', GREEN), ('2ND', BLUE),
        ('FORCE', WHITE), ('SPEED', WHITE)]}
BIG = {k: fit(text_sprite([(k, c)], font(F_BLACK, 130), stroke=6, shadow=0.8), 980) for k, c in
       [('STALLED!', RED), ('REDLINE!', RED), ('GRIND!', RED), ('GEARS?', YEL)]}
SPR_HEAD1 = fit(text_sprite([('THE MANUAL', WHITE)], font(F_BLACK, 120), shadow=0.8))
SPR_HEAD2 = fit(text_sprite([('GEARBOX', YEL)], font(F_BLACK, 170), shadow=0.8))
SPR_60 = text_sprite([('60s', WHITE)], font(F_BLACK, 64), shadow=0.5)
SPR_PART3 = fit(text_sprite([('PART 3: ', WHITE), ('THE AUTOMATIC', YEL)], font(F_BLACK, 78)))
SPR_FOLLOW = fit(text_sprite([('FOLLOW FOR PART 3', (10, 14, 24))], font(F_BLACK, 54), shadow=0))
SPR_PEDAL = text_sprite([('PEDAL', M_HI)], font(F_XBOLD, 30), tracking=2, shadow=0.5)
SPR_SWEET = text_sprite([('SWEET SPOT', GREEN)], font(F_XBOLD, 34), tracking=2, shadow=0.5)
SPR_RPM = text_sprite([('RPM x1000', M_LIGHT)], font(F_XBOLD, 26), tracking=2, shadow=0.3)
SPR_GEARLBL = text_sprite([('GEAR', M_LIGHT)], font(F_XBOLD, 26), tracking=3, shadow=0.3)
DIGITS = {str(k): text_sprite([(str(k), YEL)], font(F_BLACK, 96), shadow=0.4) for k in range(1, 6)}
TICKN = {k: text_sprite([(str(k), M_HI if k < 6 else RED)], font(F_XBOLD, 30), shadow=0) for k in range(0, 9)}
CARD = {}
for key, l1, l2, col in [('old', 'NARRATOR #1', 'PART 1', GREY), ('new', 'NARRATOR #2', 'NEW GUY', YEL)]:
    CARD[key] = (text_sprite([(l1, WHITE)], font(F_BLACK, 56), shadow=0.4),
                 text_sprite([(l2, col)], font(F_XBOLD, 32), tracking=4, shadow=0.3), col)


# ------------------------------------------------------------------ primitives
def gear(img, glow, cx, cy, R, teeth, ang, col, hub=M_DARK, glow_k=0.0):
    poly(img, gear_pts(cx, cy, R, teeth, ang), C3(col))
    circle(img, cx, cy, R * 0.72, C3(mixc(col, (0, 0, 0), 0.18)))
    for k in range(5):
        aa = ang + k * 2 * math.pi / 5
        circle(img, cx + R * 0.45 * math.cos(aa), cy + R * 0.45 * math.sin(aa), R * 0.11, C3(hub))
    circle(img, cx, cy, max(10, R * 0.16), C3(hub))
    if glow_k > 0:
        circle(glow, cx, cy, R + 10, C3(col, glow_k), th=16, s=0.5)


def stripes(img, x0, y0, x1, y1, offset, col, gap=26, horiz=True):
    o = offset % gap
    if horiz:
        x = x0 - gap + o
        while x < x1:
            line(img, max(x0, x), y0 + 3, min(x1, x + 10), y1 - 3, C3(col), 3)
            x += gap
    else:
        y = y0 - gap + o
        while y < y1:
            if y > y0:
                line(img, x0 + 3, y, x1 - 3, y, C3(col), 3)
            y += gap


def car(img, glow, cx, cy, wheel_ang, col=CYAN, scale=1.0):
    s = scale
    body = [(-260, 40), (-250, -20), (-200, -45), (-110, -55), (-60, -120), (90, -122), (150, -60), (240, -45),
            (265, -10), (265, 40)]
    poly(img, [(cx + x * s, cy + y * s) for x, y in body], C3(col))
    poly(img, [(cx - 45 * s, cy - 108 * s), (cx + 10 * s, cy - 108 * s), (cx + 10 * s, cy - 60 * s), (cx - 90 * s, cy - 60 * s)], C3((14, 22, 40)))
    poly(img, [(cx + 25 * s, cy - 108 * s), (cx + 82 * s, cy - 108 * s), (cx + 125 * s, cy - 60 * s), (cx + 25 * s, cy - 60 * s)], C3((14, 22, 40)))
    for wx in (-150, 160):
        x, y = cx + wx * s, cy + 40 * s
        circle(img, x, y, 62 * s, C3((14, 22, 40)))
        circle(img, x, y, 48 * s, C3(M_DARK))
        circle(img, x, y, 48 * s, C3(M_LIGHT), th=6)
        for k in range(5):
            a = wheel_ang + k * 2 * math.pi / 5
            line(img, x, y, x + 40 * s * math.cos(a), y + 40 * s * math.sin(a), C3(M_LIGHT), 6)
        circle(img, x, y, 10 * s, C3(M_HI))


def road(img, y, offset):
    line(img, 60, y, 1020, y, C3(M_MID), 4)
    x = 60 - (offset % 120)
    while x < 1020:
        line(img, max(60, x), y + 40, min(1020, x + 60), y + 40, C3(M_DARK), 6)
        x += 120


def smoke(img, cx, cy, t, k):
    for j in range(7):
        ph = (t * 1.3 + j / 7) % 1.0
        r = 20 + 50 * ph
        g = int(150 - 90 * ph)
        circle(img, cx - 140 * ph + 10 * math.sin(j * 3 + t * 4), cy - 160 * ph, r * k, (g, g, g + 6))


def tacho(img, glow, cx, cy, R, rpm, gear_n, shake=0.0, sweet=False, t=0.0):
    circle(img, cx, cy, R + 14, C3((14, 22, 40)))
    circle(img, cx, cy, R + 14, C3(M_MID), th=5)
    a0, a1 = math.radians(140), math.radians(400)

    def ang(v):
        return a0 + (a1 - a0) * v / 8.0
    if sweet:
        for k in range(24):
            v0, v1 = 2.0 + k * 2.0 / 24, 2.0 + (k + 1) * 2.0 / 24
            line(img, cx + (R - 16) * math.cos(ang(v0)), cy + (R - 16) * math.sin(ang(v0)),
                 cx + (R - 16) * math.cos(ang(v1)), cy + (R - 16) * math.sin(ang(v1)), C3(GREEN), 16)
    for k in range(24):
        v0, v1 = 6.0 + k * 2.0 / 24, 6.0 + (k + 1) * 2.0 / 24
        line(img, cx + (R - 16) * math.cos(ang(v0)), cy + (R - 16) * math.sin(ang(v0)),
             cx + (R - 16) * math.cos(ang(v1)), cy + (R - 16) * math.sin(ang(v1)), C3(RED), 16)
    for v in range(0, 9):
        a = ang(v)
        line(img, cx + (R - 36) * math.cos(a), cy + (R - 36) * math.sin(a), cx + (R - 4) * math.cos(a),
             cy + (R - 4) * math.sin(a), C3(M_HI), 5)
        blit(img, TICKN[v], cx + (R - 72) * math.cos(a), cy + (R - 72) * math.sin(a))
    blit(img, SPR_RPM, cx, cy + R * 0.42)
    v = max(0.0, min(8.2, rpm + shake * math.sin(t * 61) * 0.25))
    a = ang(v)
    col = RED if rpm > 6 else WHITE
    line(img, cx - 30 * math.cos(a), cy - 30 * math.sin(a), cx + (R - 30) * math.cos(a), cy + (R - 30) * math.sin(a), C3(col), 9)
    circle(img, cx, cy, 20, C3(M_HI))
    if rpm > 6:
        circle(glow, cx, cy, R + 20, C3(RED, 0.5 + 0.3 * math.sin(t * 20)), th=20, s=0.5)
    # gear indicator
    gx = cx + R + 110
    rrect(img, gx - 60, cy - 65, gx + 60, cy + 65, 18, C3((14, 22, 40)))
    rrect_outline(img, gx - 60, cy - 65, gx + 60, cy + 65, 18, C3(YEL), 4)
    blit(img, SPR_GEARLBL, gx, cy - 90)
    blit(img, DIGITS[str(gear_n)], gx, cy)


def card(img, cx, cy, key, a=1.0, cross=0.0):
    l1, l2, col = CARD[key]
    rrect(img, cx - 330, cy - 95, cx + 330, cy + 95, 30, C3((18, 28, 50), a))
    rrect_outline(img, cx - 330, cy - 95, cx + 330, cy + 95, 30, C3(col, a), 5)
    # mic icon
    mx, my = cx - 230, cy
    circle(img, mx, my, 62, C3(col, a * 0.25))
    rrect(img, mx - 22, my - 46, mx + 22, my + 14, 22, C3(col, a))
    line(img, mx, my + 22, mx, my + 44, C3(col, a), 6)
    line(img, mx - 22, my + 44, mx + 22, my + 44, C3(col, a), 6)
    blit(img, l1, cx + 60, cy - 22, opacity=a)
    blit(img, l2, cx + 60, cy + 40, opacity=a)
    if cross > 0:
        L = 300 * cross
        line(img, cx - L, cy - L * 0.3, cx + L, cy + L * 0.3, C3(RED), 14)
        line(img, cx - L, cy + L * 0.3, cx + L, cy - L * 0.3, C3(RED), 14)


# ------------------------------------------------------------------ scenes
def scene_intro(img, glow, t):
    k = ease_out3(t / 0.4)
    gear(img, glow, 470, 800, 150, 16, t * 2.2, YEL, glow_k=0.35)
    gear(img, glow, 470 + 150 + 95 + 14, 800 - 10, 95, 10, -t * 2.2 * 150 / 95 + 0.3, M_LIGHT)
    gear(img, glow, 470 - 60, 800 + 150 + 80 + 14, 80, 9, -t * 2.2 * 150 / 80 + 0.2, M_LIGHT)
    blit(img, BIG['GEARS?'], 650, 1150, opacity=k, scale=1.5 - 0.5 * k)


def scene_title(img, glow, t):
    k = ease_out3((t - HERE_S + 0.1) / 0.3)
    blit(img, SPR_HEAD1, 540, 700, opacity=k, scale=2.0 - k)
    k2 = ease_out3((t - HERE_S - 0.15) / 0.3)
    blit(img, SPR_HEAD2, 540, 880, opacity=k2, scale=2.0 - k2)
    # stopwatch
    cx, cy = 540, 1130
    circle(img, cx, cy, 80, C3(M_DARK))
    circle(img, cx, cy, 80, C3(CYAN), th=8)
    f = min(1.0, (t - HERE_S) / 3.0)
    for j in range(int(60 * f)):
        a = -math.pi / 2 + j * 2 * math.pi / 60
        line(img, cx + 58 * math.cos(a), cy + 58 * math.sin(a), cx + 70 * math.cos(a), cy + 70 * math.sin(a), C3(CYAN), 4)
    blit(img, SPR_60, cx, cy)


def scene_drive(img, glow, t):
    """C: 5th gear from stop (stall).  D: 1st gear on the highway (redline)."""
    if t < T['D'] - 0.2:
        stalled = t >= STALL_S
        jerk = 0.0 if stalled else 14 * math.sin(t * 38) * ramp(t, T['C'] + 0.5, 0.4)
        rpm = 0.9 if t < T['C'] + 0.5 else (max(0.0, 0.9 - (t - T['C'] - 0.5) * 0.35) if not stalled else 0.0)
        road(img, 1265, 0)
        car(img, glow, 540 + jerk, 1165, 0.0, CYAN, 0.95)
        tacho(img, glow, 430, 690, 220, rpm, 5, t=t)
        if stalled:
            k = ramp(t, STALL_S, 0.2)
            blit(img, BIG['STALLED!'], 540, 985, opacity=k, scale=1.5 - 0.5 * k)
    else:
        rpm = min(7.9, 3 + (t - T['D']) * 3.0)
        shake = 1.0 if rpm > 6 else 0.0
        road(img, 1265, t * 2600)
        for j in range(8):
            yy = 1040 + j * 26
            x = (1100 - (t * 3000 + j * 400) % 1300)
            line(img, x, yy, x + 150, yy, C3(M_MID), 4)
        car(img, glow, 540 + 4 * shake * math.sin(t * 70), 1165 + 3 * shake * math.sin(t * 53), t * 40, CYAN, 0.95)
        if t >= SCREAM_S:
            smoke(img, 540 - 270, 1150, t, 1.0)
        tacho(img, glow, 430, 690, 220, rpm, 1, shake=shake, t=t)
        if t >= SCREAM_S:
            k = ramp(t, SCREAM_S, 0.15)
            blit(img, BIG['REDLINE!'], 540, 985, opacity=k, scale=1.4 - 0.4 * k)


def scene_sweet(img, glow, t):
    # needle climbs, shift, drops back into the green - repeated through gears
    dt = t - T['E']
    seq = [1, 2, 3, 4, 5]
    period = 0.75
    if t < KEEP_S:
        rpm = 1.2 + 0.4 * math.sin(dt * 2)
        g = 1
    else:
        u = (t - KEEP_S) / period
        g = seq[min(4, int(u))]
        f = u - int(u) if int(u) < 4 else min(1.0, u - 4)
        rpm = 2.4 + 1.5 * f if int(u) < 4 else 3.0
    tacho(img, glow, 440, 820, 280, rpm, g, sweet=True, t=t)


def gear_pair(img, glow, t, r_in, r_out, y=860, w_in=3.2):
    teeth_in, teeth_out = max(8, int(r_in / 9)), max(8, int(r_out / 9))
    dist = r_in + r_out + 14
    x_in = 540 - dist / 2
    x_out = x_in + dist
    ang_in = w_in * t
    ang_out = -ang_in * r_in / r_out + math.pi / teeth_out
    gear(img, glow, x_out, y, r_out, teeth_out, ang_out, M_LIGHT)
    gear(img, glow, x_in, y, r_in, teeth_in, ang_in, YEL, glow_k=0.35)
    return x_in, x_out


def meter(img, x, y, label, frac, col):
    blit(img, TXT[label], x - 250, y)
    rrect(img, x - 160, y - 18, x + 260, y + 18, 18, C3(M_DARK))
    rrect(img, x - 160, y - 18, x - 160 + max(36, 420 * frac), y + 18, 18, C3(col))


def scene_pair(img, glow, t):
    small_first = t < BIG_S
    if small_first:
        x_in, x_out = gear_pair(img, glow, t, 80, 180)
    else:
        x_in, x_out = gear_pair(img, glow, t, 180, 80)
    blit(img, TXT['ENGINE'], x_in, 620 if small_first else 600)
    blit(img, TXT['WHEELS'], x_out, 600 if small_first else 620)
    k = ramp(t, T['F'] if small_first else BIG_S, 0.5)
    f_force, f_speed = (0.9, 0.25) if small_first else (0.25, 0.9)
    meter(img, 560, 1170, 'FORCE', f_force * k, GREEN if small_first else M_LIGHT)
    meter(img, 560, 1250, 'SPEED', f_speed * k, M_LIGHT if small_first else BLUE)


def draw_clutch(img, glow, t):
    press = ease_io((t - PRESS_S) / 0.45) if t >= PRESS_S else 0.0
    gap = 60 * press
    spin_e = t * 260
    spin_g = min(t, PRESS_S) * 260 + 260 * max(0.0, t - PRESS_S) * max(0.0, 1 - press * 1.2)
    rrect(img, 140, 820, 330, 900, 10, C3(M_MID))
    stripes(img, 140, 820, 330, 900, spin_e * 0.2, M_HI)
    rrect(img, 330, 660, 380, 1060, 12, C3(M_LIGHT))
    stripes(img, 330, 660, 380, 1060, spin_e, M_HI, horiz=False)
    blit(img, TXT['ENGINE'], 240, 620)
    cx = 400 + gap
    rrect(img, cx, 690, cx + 34, 1030, 10, C3(ORANGE))
    stripes(img, cx, 690, cx + 34, 1030, spin_g, (255, 214, 170), horiz=False)
    rrect(img, cx + 34, 835, 860, 885, 8, C3(M_MID))
    stripes(img, cx + 34, 835, 860, 885, spin_g * 0.2, M_HI)
    blit(img, TXT['CLUTCH'], cx + 17, 1095)
    rrect(img, 760, 720, 960, 1000, 20, C3(M_DARK))
    rrect_outline(img, 760, 720, 960, 1000, 20, C3(M_LIGHT), 3)
    blit(img, TXT['GEARBOX'], 860, 660)
    if press > 0.5:
        circle(glow, cx - gap / 2 + 5, 860, 60, C3(ORANGE, 0.5), s=0.5)
    px, py = 250, 1230
    ang = math.radians(-35 + 30 * press)
    ex, ey = px + 150 * math.cos(ang), py + 150 * math.sin(ang)
    line(img, px, py, ex, ey, C3(M_LIGHT), 14)
    rrect(img, ex - 10, ey - 30, ex + 30, ey + 30, 8, C3(M_HI))
    circle(img, px, py, 14, C3(M_MID))
    blit(img, SPR_PEDAL, px + 60, py + 90)
    for k in range(10):
        f0, f1 = k / 10, (k + 0.5) / 10
        line(img, ex + (cx + 17 - ex) * f0, ey + (1040 - ey) * f0, ex + (cx + 17 - ex) * f1, ey + (1040 - ey) * f1, C3(ORANGE, 0.7), 4)


SY_IN, SY_OUT = 780, 1080
PAIRS = [(360, 80, 220, '1ST', GREEN), (700, 130, 170, '2ND', BLUE)]
SURF = 340.0


def collar_x(t):
    left, right = PAIRS[0][0] + 60, PAIRS[1][0] - 60
    if t < COLLAR_S:
        return left
    return left + (right - left) * ease_io((t - COLLAR_S) / max(0.4, LOCK_S + 0.3 - COLLAR_S))


def draw_box(img, glow, t):
    grinding = NOCL_S <= t < T['K']
    cx = collar_x(t)
    if grinding:
        cx = PAIRS[1][0] - 60 - 26 - 10 * abs(math.sin(t * 47))
    engaged = 0 if t < COLLAR_S + 0.05 else 1 if t >= LOCK_S + 0.25 else -1
    if grinding:
        engaged = -1
    rrect(img, 120, SY_IN - 14, 960, SY_IN + 14, 8, C3(M_MID))
    stripes(img, 120, SY_IN - 14, 960, SY_IN + 14, t * 160, M_HI)
    blit(img, TXT['ENGINE'], 150, SY_IN - 140)
    out_speed = 0.0 if engaged < 0 else SURF / PAIRS[engaged][2]
    rrect(img, 120, SY_OUT - 14, 960, SY_OUT + 14, 8, C3(M_MID))
    stripes(img, 120, SY_OUT - 14, 960, SY_OUT + 14, t * out_speed * 60, M_HI)
    mesh_glow = 0.5 + 0.5 * math.sin((t - SPIN_S) * 6) if SPIN_S - 0.1 <= t < PICK_S else 0.0
    for i, (x, r_in, r_out, name, col) in enumerate(PAIRS):
        locked = engaged == i
        gcol = col if locked else M_LIGHT
        rrect(img, x - 24, SY_IN - r_in, x + 24, SY_IN + r_in, 8, C3(M_LIGHT))
        stripes(img, x - 24, SY_IN - r_in, x + 24, SY_IN + r_in, t * SURF * 0.3, M_HI, gap=18, horiz=False)
        rrect(img, x - 24, SY_OUT - r_out, x + 24, SY_OUT + r_out, 8, C3(gcol))
        stripes(img, x - 24, SY_OUT - r_out, x + 24, SY_OUT + r_out, -t * SURF * 0.3, (235, 240, 245), gap=18, horiz=False)
        side = 1 if i == 0 else -1
        for k in range(4):
            yy = SY_OUT - 40 + k * 26
            rrect(img, x + side * 24 - (0 if side > 0 else 14), yy, x + side * 24 + (14 if side > 0 else 0), yy + 14, 3, C3(gcol))
        if locked:
            rrect(glow, x - 30, SY_OUT - r_out, x + 30, SY_OUT + r_out, 10, C3(col, 0.7), s=0.5)
        if mesh_glow > 0:
            circle(glow, x, (SY_IN + SY_OUT) / 2, 70, C3(YEL, 0.45 * mesh_glow), s=0.5)
        blit(img, TXT[name], x, SY_OUT + r_out + 50)
    ccol = RED if grinding else (YEL if engaged >= 0 else M_HI)
    rrect(img, cx - 34, SY_OUT - 52, cx + 34, SY_OUT + 52, 10, C3(ccol))
    line(img, cx, SY_OUT - 52, cx, SY_OUT + 52, C3(M_DARK), 8)
    if PICK_S <= t < T['J']:
        rrect(glow, cx - 40, SY_OUT - 60, cx + 40, SY_OUT + 60, 12, C3(YEL, 0.8), s=0.5)
    if SYN_S <= t < NOCL_S:
        k = 0.6 + 0.4 * math.sin((t - SYN_S) * 8)
        rrect(glow, cx - 50, SY_OUT - 70, PAIRS[1][0] + 40, SY_OUT + 70, 14, C3(GREEN, 0.8 * k), s=0.5)
        rrect_outline(img, cx + 36, SY_OUT - 60, PAIRS[1][0] - 26, SY_OUT + 60, 8, C3(GREEN), 5)
    if grinding:
        rng = np.random.default_rng(int(t * 30))
        for _ in range(14):
            a = rng.uniform(-math.pi, math.pi)
            L = rng.uniform(30, 110)
            sx, sy = cx + 34, SY_OUT + rng.uniform(-40, 40)
            line(img, sx, sy, sx + L * math.cos(a), sy + L * math.sin(a), C3((255, 200, 80)), 4)
        circle(glow, cx + 30, SY_OUT, 90, C3(ORANGE, 0.8), s=0.5)
    rod_y = 600
    line(img, 140, rod_y, 940, rod_y, C3(M_MID), 12)
    line(img, cx, rod_y, cx, SY_OUT - 60, C3(ORANGE), 10)
    rrect(img, cx - 40, SY_OUT - 72, cx + 40, SY_OUT - 56, 4, C3(ORANGE))
    base_x, base_y = 540, 545
    tip_x = base_x - 60 + 120 * ease_io((t - COLLAR_S) / max(0.4, LOCK_S + 0.3 - COLLAR_S)) if t >= COLLAR_S else base_x - 60
    line(img, base_x, base_y, tip_x, base_y - 70, C3(M_LIGHT), 12)
    circle(img, tip_x, base_y - 78, 22, C3((30, 34, 44)))
    circle(img, tip_x, base_y - 78, 22, C3(M_HI), th=3)
    rrect(img, base_x - 40, base_y - 6, base_x + 40, base_y + 14, 6, C3(M_MID))
    if WHEELS_S - 0.2 <= t < T['J']:
        k = min(1.0, (t - WHEELS_S + 0.2) / 0.3)
        line(img, 960, SY_OUT, 1040, SY_OUT, C3(YEL, k), 10)
        poly(img, [(1040, SY_OUT - 22), (1040, SY_OUT + 22), (1070, SY_OUT)], C3(YEL, k))
        circle(glow, 1000, SY_OUT, 60, C3(YEL, 0.5 * k), s=0.5)
    if grinding and t >= GRIND_S:
        k = ramp(t, GRIND_S, 0.15)
        blit(img, BIG['GRIND!'], 540, 1300, opacity=k, scale=(1.3 - 0.3 * k) * (1 + 0.04 * math.sin(t * 40)))


LABELS = [('STICK', YEL, 840, 480, lambda t: (560, 480), STICK_S, T['I'] - 0.2),
          ('FORK', ORANGE, 860, 700, lambda t: (collar_x(t) + 6, 700), FORK_S, T['I'] - 0.2),
          ('COLLAR', YEL, 170, 1250, lambda t: (collar_x(t) - 30, SY_OUT + 50), COLLAR_S, T['J'] - 0.2),
          ('OUTPUT SHAFT', CYAN, 880, 1190, lambda t: (900, SY_OUT + 12), SHAFT_S, T['J'] - 0.2),
          ('SYNCHRO', GREEN, 880, 1250, lambda t: (PAIRS[1][0] - 40, SY_OUT + 60), SYN_S + 0.2, NOCL_S - 0.1)]


def draw_labels(frame, t):
    for text, col, lx, ly, target, t_on, t_off in LABELS:
        if t < t_on or t > t_off + 0.3:
            continue
        a = min(1.0, (t - t_on) / 0.25) * (1.0 if t < t_off else max(0.0, 1 - (t - t_off) / 0.3))
        if a <= 0.01:
            continue
        tx, ty = target(t)
        spr = label_sprite(text, col)
        w = (spr.shape[1] - 60) / 2
        edge_x = lx + w + 14 if lx < tx else lx - w - 14
        grow = min(1.0, (t - t_on) / 0.35)
        ex, ey = edge_x + (tx - edge_x) * grow, ly + (ty - ly) * grow
        x0 = int(max(0, min(lx - w - 14, ex) - 24))
        x1 = int(min(W, max(lx + w + 14, ex) + 24))
        y0 = int(max(0, min(ly - 30, ey) - 24))
        y1 = int(min(H, max(ly + 30, ey) + 24))
        before = frame[y0:y1, x0:x1].copy()
        line(frame, edge_x, ly, ex, ey, C3(col), 3)
        circle(frame, ex, ey, 7, C3(col))
        rrect(frame, lx - w - 14, ly - 26, lx + w + 14, ly + 26, 12, C3((10, 16, 30)))
        rrect_outline(frame, lx - w - 14, ly - 26, lx + w + 14, ly + 26, 12, C3(col), 2)
        blit(frame, spr, lx, ly + 2)
        if a < 0.999:
            after = frame[y0:y1, x0:x1].astype(np.float32)
            frame[y0:y1, x0:x1] = (before.astype(np.float32) * (1 - a) + after * a).astype(np.uint8)


def scene_teaser(img, glow, t):
    cx, cy = 540, 840
    ang = t * 1.2
    circle(img, cx, cy, 250, C3(M_MID), th=34)
    for k in range(48):
        aa = -ang * 0.4 + k * 2 * math.pi / 48
        circle(img, cx + 228 * math.cos(aa), cy + 228 * math.sin(aa), 9, C3(M_MID))
    gear(img, glow, cx, cy, 70, 10, ang, YEL, glow_k=0.4)
    for k in range(3):
        aa = ang * 0.35 + k * 2 * math.pi / 3
        gear(img, glow, cx + 145 * math.cos(aa), cy + 145 * math.sin(aa), 62, 9, -ang * 1.2 + k, M_LIGHT)
    blit(img, SPR_PART3, W / 2, 1160)


SCENES = [(0.0, scene_intro), (HERE_S - 0.15, scene_title), (T['C'] - 0.15, scene_drive), (T['E'] - 0.15, scene_sweet), (T['F'] - 0.15, scene_pair), (T['G'] - 0.15, draw_clutch), (T['H'] - 0.15, draw_box), (T['K'] - 0.15, scene_teaser)]
FADE = 0.25


# ------------------------------------------------------------------ captions
def make_chunks():
    chunks, cur = [], []
    for i, w in enumerate(TL.words):
        cur.append(i)
        if len(cur) >= 4 or w['brk'] >= 0.45 or w.get('last'):
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    return chunks


CHUNKS = make_chunks()
_cap = {}


def caption_sprite(ci, active):
    if (ci, active) not in _cap:
        parts = []
        hl = YEL
        for j, wi in enumerate(CHUNKS[ci]):
            txt = TL.words[wi]['text'].upper()
            parts.append((txt + (' ' if j < len(CHUNKS[ci]) - 1 else ''), hl if wi == active else WHITE))
        size = 68
        while True:
            spr = text_sprite(parts, font(F_BLACK, size), stroke=7, shadow=0.7)
            if spr.shape[1] - 60 <= 980 or size <= 44:
                break
            size -= 4
        _cap[(ci, active)] = spr
    return _cap[(ci, active)]


def draw_caption(frame, t):
    for ci, ch in enumerate(CHUNKS):
        s = TL.words[ch[0]]['start']
        e = TL.words[CHUNKS[ci + 1][0]]['start'] if ci + 1 < len(CHUNKS) else TL.words[ch[-1]]['end'] + 0.6
        e = min(e, TL.words[ch[-1]]['end'] + 0.9)
        if s - 0.05 <= t < e:
            active = ch[0]
            for wi in ch:
                if TL.words[wi]['start'] <= t:
                    active = wi
            blit(frame, caption_sprite(ci, active), W / 2, 1460, scale=1.0 + 0.06 * max(0.0, 1 - (t - s) / 0.12))
            return


# ------------------------------------------------------------------ frame
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
        rrect(frame, W / 2 - bw, 1290 - bh, W / 2 + bw, 1290 + bh, 52, C3(YEL, fa))
        circle(glow, W / 2, 1290, 200, C3(YEL, 0.35 * fa), th=40, s=0.5)
        blit(frame, SPR_FOLLOW, W / 2, 1292, opacity=fa, scale=pulse)
    g = cv2.GaussianBlur(glow, (0, 0), 8)
    frame = cv2.add(frame, cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR))
    if T['H'] - 0.15 <= t < T['K']:
        draw_labels(frame, t)
    # screen shake + red flash on the big moments
    shake = 0.0
    for t0, d, amp in ((STALL_S, 0.35, 8), (SCREAM_S, 0.5, 6), (GRIND_S, 0.7, 8)):
        if t0 <= t < t0 + d:
            shake = max(shake, amp * (1 - (t - t0) / d))
    if shake > 0:
        dx, dy = int(shake * math.sin(t * 71)), int(shake * math.cos(t * 57))
        frame = np.roll(frame, (dy, dx), axis=(0, 1))
    if GRIND_S <= t < GRIND_S + 0.5:
        blend_rect(frame, 0, 0, W, H, RED, 0.18 * (1 - (t - GRIND_S) / 0.5))
    blit(frame, SPR_SERIES, W / 2, 168)
    blit(frame, SPR_TITLE, W / 2, 238)
    prog = min(1.0, t / max(DUR - 0.5, 1))
    rrect(frame, 140, 300, 940, 310, 5, C3(M_DARK))
    rrect(frame, 140, 300, 140 + max(12, 800 * prog), 310, 5, C3(CYAN))
    for b0, b1, spr in BADGES:
        if b0 <= t < b1:
            blit(frame, spr, W / 2, 395, opacity=min(1.0, (t - b0 + 0.05) / 0.25), scale=0.9 + 0.1 * ease_out3((t - b0) / 0.25))
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
