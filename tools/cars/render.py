"""How Cars Work - Part 3: The Automatic.  python3 render.py stills t... | range a b out.mp4"""
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


T = {s: TL.seg_start(s) for s in 'ABCDEFGHK'}
GREEN = (74, 222, 128)
BLUE = (96, 165, 250)
ORANGE = (251, 146, 60)
RED = (248, 72, 72)
GREY = (120, 128, 140)
OIL = (37, 99, 235)

CLUTCH_S = ws('A', 'clutch')
STICK_S = ws('A', 'stick')
AUTO_S = ws('A', 'automatic')
PART_S = ws('A', 'part')
TORQUE_S = ws('B', 'torque')
FANS_S = ws('B', 'fans')
OILB_S = ws('B', 'oil')
SPINS_S = ws('C', 'spins')
THROWS_S = ws('C', 'throws')
WHEELS_S = ws('C', 'wheels')
RED_S = ws('D', 'red')
SLIPS_S = ws('D', 'slips')
STALL_S = ws('D', 'stalling')
SUN_S = ws('E', 'sun')
PLAN_S = ws('E', 'planets')
RING_S = ws('E', 'ring')
HOLD_S = ws('F', 'hold')
DRIVE_S = ws('F', 'drive')
THIRD_S = ws('F', 'third')
THATS_S = ws('F', "that's")
CLUTCHES_S = ws('G', 'clutches')
HELD_S = ws('G', 'held')
SQUEEZE_S = ws('G', 'squeezed')
PRESS_S = ws('G', 'pressure')
COMP_S = ws('H', 'computer')
SPEED_S = ws('H', 'speed')
PEDAL_S = ws('H', 'pedal')
SHIFTS_S = ws('H', 'shifts')
DIFF_S = ws('K', 'differential')
CORNER_S = ws('K', 'corner')
FOLLOW_S = ws('K', 'follow')


def ramp(t, t0, d=0.3):
    return min(1.0, max(0.0, (t - t0) / d))


exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_parts.py')).read())

SPR_SERIES = text_sprite([('HOW CARS WORK', CYAN)], font(F_XBOLD, 34), tracking=7, shadow=0.4)
SPR_TITLE = fit(text_sprite([('PART 3: ', WHITE), ('THE AUTOMATIC', YEL)], font(F_BLACK, 76)))


def badge(text, col=WHITE):
    return fit(text_sprite([(text, col)], font(F_XBOLD, 40), tracking=3))


BADGES = [(0.0, PART_S, badge('HOW DOES IT SHIFT BY ITSELF?', YEL)),
          (PART_S, T['B'], badge('EXPLAINED IN 60 SECONDS')),
          (T['B'], T['C'], badge('STEP 1: TORQUE CONVERTER', YEL)),
          (T['C'], T['D'], badge('OIL CARRIES THE POWER', BLUE)),
          (T['D'], T['E'], badge('IDLING IN DRIVE', RED)),
          (T['E'], T['F'], badge('STEP 2: PLANETARY GEARS', YEL)),
          (T['F'], T['G'], badge('HOLD ONE  ·  DRIVE ONE')),
          (T['G'], T['H'], badge('CLUTCH PACKS', ORANGE)),
          (T['H'], T['K'], badge('STEP 3: THE COMPUTER', YEL))]
TXT = {k: text_sprite([(k, c)], font(F_BLACK, 46), shadow=0.6) for k, c in
       [('ENGINE', WHITE), ('WHEELS', WHITE), ('OIL', BLUE), ('SLIP', BLUE), ('INPUT', YEL), ('HELD', RED),
        ('OUTPUT', GREEN), ('COMPUTER', CYAN), ('SPEED', WHITE), ('PEDAL', WHITE), ('SLOWER', BLUE), ('FASTER', ORANGE),
        ('NO CLUTCH', RED), ('NO STICK', RED)]}
BIG = {k: fit(text_sprite([(k, c)], font(F_BLACK, 130), stroke=6, shadow=0.8), 980) for k, c in
       [('AUTOMATIC?', YEL), ('NO STALL', GREEN)]}
SPR_HEAD1 = fit(text_sprite([('THE AUTOMATIC', WHITE)], font(F_BLACK, 110), shadow=0.8))
SPR_HEAD2 = fit(text_sprite([('TRANSMISSION', YEL)], font(F_BLACK, 112), shadow=0.8))
SPR_60 = text_sprite([('60s', WHITE)], font(F_BLACK, 64), shadow=0.5)
SPR_PART4 = fit(text_sprite([('PART 4: ', WHITE), ('THE DIFFERENTIAL', YEL)], font(F_BLACK, 74)))
SPR_FOLLOW = fit(text_sprite([('FOLLOW FOR PART 4', (10, 14, 24))], font(F_BLACK, 54), shadow=0))
SPR_RPM = text_sprite([('RPM x1000', M_LIGHT)], font(F_XBOLD, 26), tracking=2, shadow=0.3)
SPR_GEARLBL = text_sprite([('GEAR', M_LIGHT)], font(F_XBOLD, 26), tracking=3, shadow=0.3)
DIGITS = {str(k): text_sprite([(str(k), YEL)], font(F_BLACK, 96), shadow=0.4) for k in range(1, 7)}
DIGITS['D'] = text_sprite([('D', YEL)], font(F_BLACK, 96), shadow=0.4)
TICKN = {k: text_sprite([(str(k), M_HI if k < 6 else RED)], font(F_XBOLD, 30), shadow=0) for k in range(0, 9)}
PRND = {(c, on): text_sprite([(c, YEL if on else M_LIGHT)], font(F_BLACK, 70), shadow=0.3) for c in 'PRND' for on in (0, 1)}
RATIO = {k: text_sprite([(k, c)], font(F_BLACK, 60), shadow=0.5) for k, c in [('1ST GEAR', GREEN), ('2ND GEAR', BLUE)]}


# ------------------------------------------------------------------ helpers
def red_x(img, cx, cy, r, k):
    L = r * k
    line(img, cx - L, cy - L, cx + L, cy + L, C3(RED), 14)
    line(img, cx - L, cy + L, cx + L, cy - L, C3(RED), 14)


def lock_icon(img, cx, cy, s=1.0, col=RED):
    rrect(img, cx - 26 * s, cy - 6 * s, cx + 26 * s, cy + 34 * s, 6 * s, C3(col))
    circle(img, cx, cy - 6 * s, 18 * s, C3(col), th=7 * s)
    circle(img, cx, cy + 12 * s, 5 * s, C3((14, 22, 40)))


def fan(img, glow, cx, cy, R, ang, col, blades=8, glow_k=0.0):
    circle(img, cx, cy, R, C3(mixc(col, (10, 14, 24), 0.75)))
    circle(img, cx, cy, R, C3(col), th=6)
    for k in range(blades):
        a = ang + k * 2 * math.pi / blades
        pts = []
        for j in range(9):
            f = j / 8
            rr = R * (0.22 + 0.74 * f)
            aa = a + 0.7 * f * f
            pts.append((cx + rr * math.cos(aa), cy + rr * math.sin(aa)))
        polyline(img, pts, C3(col), 9)
    circle(img, cx, cy, R * 0.2, C3(col))
    circle(img, cx, cy, R * 0.08, C3((14, 22, 40)))
    if glow_k > 0:
        circle(glow, cx, cy, R + 10, C3(col, glow_k), th=20, s=0.5)


# ------------------------------------------------------------------ scenes
def scene_intro(img, glow, t):
    # automatic selector P R N D with D lit
    cx, cy = 540, 820
    rrect(img, cx - 90, cy - 250, cx + 90, cy + 250, 40, C3((18, 28, 50)))
    rrect_outline(img, cx - 90, cy - 250, cx + 90, cy + 250, 40, C3(M_MID), 4)
    for i, c in enumerate('PRND'):
        y = cy - 180 + i * 120
        on = c == 'D'
        if on:
            circle(glow, cx, y, 70, C3(YEL, 0.5), s=0.5)
        blit(img, PRND[(c, int(on))], cx, y)
    # left: clutch pedal (crossed)
    k1 = ramp(t, CLUTCH_S - 0.1, 0.25)
    if k1 > 0:
        px, py = 220, 820
        ang = math.radians(-60)
        ex, ey = px + 170 * math.cos(ang), py + 170 * math.sin(ang)
        line(img, px, py + 120, ex, ey, C3(M_LIGHT, k1), 14)
        rrect(img, ex - 45, ey - 18, ex + 45, ey + 18, 8, C3(M_HI, k1))
        blit(img, TXT['NO CLUTCH'], 220, 1010, opacity=k1)
        red_x(img, 220, 780, 110, ease_out3((t - CLUTCH_S - 0.1) / 0.25))
    k2 = ramp(t, STICK_S - 0.1, 0.25)
    if k2 > 0:
        sx, sy = 860, 900
        line(img, sx, sy, sx + 20, sy - 200, C3(M_LIGHT, k2), 14)
        circle(img, sx + 22, sy - 220, 40, C3(M_HI, k2))
        rrect(img, sx - 70, sy - 10, sx + 70, sy + 20, 10, C3(M_MID, k2))
        blit(img, TXT['NO STICK'], 860, 1010, opacity=k2)
        red_x(img, 860, 780, 110, ease_out3((t - STICK_S - 0.1) / 0.25))
    if t >= AUTO_S:
        k = ease_out3((t - AUTO_S) / 0.3)
        blit(img, BIG['AUTOMATIC?'], 540, 1190, opacity=k, scale=1.5 - 0.5 * k)


def scene_title(img, glow, t):
    k = ease_out3((t - PART_S + 0.1) / 0.3)
    blit(img, SPR_HEAD1, 540, 700, opacity=k, scale=2.0 - k)
    k2 = ease_out3((t - PART_S - 0.15) / 0.3)
    blit(img, SPR_HEAD2, 540, 860, opacity=k2, scale=2.0 - k2)
    cx, cy = 540, 1110
    circle(img, cx, cy, 80, C3(M_DARK))
    circle(img, cx, cy, 80, C3(CYAN), th=8)
    f = min(1.0, (t - PART_S) / 2.0)
    for j in range(int(60 * f)):
        a = -math.pi / 2 + j * 2 * math.pi / 60
        line(img, cx + 58 * math.cos(a), cy + 58 * math.sin(a), cx + 70 * math.cos(a), cy + 70 * math.sin(a), C3(CYAN), 4)
    blit(img, SPR_60, cx, cy)


def tc_speeds(t):
    """(impeller angle, turbine angle, impeller rate, turbine rate) - integrated analytically by sampling."""
    def w_i(u):
        if u < SPINS_S:
            return 2.0
        if u < RED_S - 0.3:
            return 2.0 + 6.0 * ease_io((u - SPINS_S) / 0.8)
        return 8.0 - 6.0 * ease_io((u - RED_S + 0.3) / 0.6)

    def w_t(u):
        if u < THROWS_S:
            return 0.0
        if u < RED_S - 0.3:
            return 6.6 * ease_io((u - THROWS_S) / 1.4)
        return 6.6 * (1 - ease_io((u - RED_S + 0.3) / 0.5))
    t0 = T['B'] - 0.3
    n = max(1, int((t - t0) * 60))
    us = np.linspace(t0, t, n + 1)
    ai = sum(w_i(u) for u in us[:-1]) * (t - t0) / n
    at = sum(w_t(u) for u in us[:-1]) * (t - t0) / n
    return ai, at, w_i(t), w_t(t)


def scene_converter(img, glow, t):
    xi, xt, cy, R = 330, 750, 860, 175
    ai, at, wi, wt = tc_speeds(t)
    # housing + oil
    fill = ramp(t, OILB_S, 0.6)
    rrect(img, 110, cy - 250, 970, cy + 250, 60, C3((14, 22, 40)))
    if fill > 0:
        h = 500 * fill
        rrect(img, 116, cy + 244 - h, 964, cy + 244, 56, C3(mixc((14, 22, 40), OIL, 0.35)))
    rrect_outline(img, 110, cy - 250, 970, cy + 250, 60, C3(M_LIGHT), 5)
    # shafts
    rrect(img, 0, cy - 18, 112, cy + 18, 6, C3(M_MID))
    stripes(img, 0, cy - 18, 112, cy + 18, ai * 30, M_HI)
    rrect(img, 968, cy - 18, W, cy + 18, 6, C3(M_MID))
    stripes(img, 968, cy - 18, W, cy + 18, -at * 30, M_HI)
    blit(img, TXT['ENGINE'], 150, cy - 320)
    blit(img, TXT['WHEELS'], 920, cy - 320)
    # oil particles: loop impeller -> turbine (top) and back (bottom)
    if t >= OILB_S:
        flow = max(0.25, wi / 8.0)
        rng = np.random.default_rng(5)
        ph0 = rng.random(28)
        prog = (ai * 0.09)
        for j in range(28):
            p = (ph0[j] + prog) % 1.0
            if p < 0.5:
                f = p / 0.5
                x = xi + (xt - xi) * f
                y = cy - 40 - 150 * math.sin(math.pi * f)
            else:
                f = (p - 0.5) / 0.5
                x = xt - (xt - xi) * f
                y = cy + 40 + 150 * math.sin(math.pi * f)
            circle(img, x, y, 9, C3(BLUE, 0.6 + 0.4 * flow))
            circle(glow, x, y, 14, C3(BLUE, 0.4 * flow), s=0.5)
    fan(img, glow, xi, cy, R, ai, ORANGE, glow_k=0.3 if wi > 3 else 0.0)
    fan(img, glow, xt, cy, R, -at + 0.3, BLUE, glow_k=0.3 if wt > 3 else 0.0)
    if fill > 0.5:
        blit(img, TXT['OIL'], 540, cy + 300, opacity=ramp(t, OILB_S + 0.3, 0.3))
    if t >= RED_S - 0.2:
        k = ramp(t, RED_S - 0.2, 0.3)
        # traffic light
        tx, ty = 660, 530
        rrect(img, tx - 140, ty - 50, tx + 140, ty + 50, 20, C3((20, 24, 32), k))
        for i, c in enumerate([RED, (120, 90, 30), (30, 90, 50)]):
            circle(img, tx - 85 + i * 85, ty, 34, C3(c, k))
        circle(glow, tx - 85, ty, 60, C3(RED, 0.8 * k), s=0.5)
        rrect(img, 380, 480, 480, 580, 20, C3((18, 28, 50), k))
        rrect_outline(img, 380, 480, 480, 580, 20, C3(YEL, k), 4)
        blit(img, DIGITS['D'], 430, 530, opacity=k, scale=0.8)
    if t >= SLIPS_S:
        k = ramp(t, SLIPS_S, 0.25)
        blit(img, TXT['SLIP'], 540, cy - 212, opacity=k, scale=1.2 + 0.1 * math.sin(t * 6))
    if t >= STALL_S:
        k = ease_out3((t - STALL_S) / 0.3)
        blit(img, BIG['NO STALL'], 540, 1240, opacity=k, scale=1.4 - 0.4 * k)


PCX, PCY = 540, 880
RS, RP, RR = 92, 104, 300  # sun, planet, ring pitch radii


def planet_state(t):
    """returns (held, driven, w_sun, w_ring, w_carrier, gear) ; angles integrated piecewise."""
    if t < THATS_S:
        return 'ring', 'sun', 1
    return 'sun', 'ring', 2


def planet_angles(t):
    # integrate in two phases with constant drive rate
    w = 2.2
    t0 = T['E'] - 0.3
    a_s = a_r = a_c = 0.0
    t1 = min(t, THATS_S)
    d1 = max(0.0, t1 - t0)
    # phase 1: ring held, sun driven
    a_s += w * d1
    a_c += w * d1 * RS / (RS + RR)
    if t > THATS_S:
        d2 = t - THATS_S
        a_r += w * 0.8 * d2
        a_c += w * 0.8 * d2 * RR / (RS + RR)
    return a_s, a_r, a_c


def planetary(img, glow, t, cx, cy, sc=1.0, show_roles=True):
    a_s, a_r, a_c = planet_angles(t)
    held, driven, g = planet_state(t)
    roles = show_roles and t >= HOLD_S
    # ring (internal teeth)
    ring_col = M_LIGHT
    if roles:
        ring_col = RED if held == 'ring' else YEL
    rin, rout = RR * sc, (RR + 60) * sc
    circle(img, cx, cy, (rin + rout) / 2, C3(ring_col), th=(rout - rin))
    nt = 66
    for k in range(nt):
        a = a_r + k * 2 * math.pi / nt
        p1 = (cx + (rin + 2) * math.cos(a - 0.035), cy + (rin + 2) * math.sin(a - 0.035))
        p2 = (cx + (rin + 2) * math.cos(a + 0.035), cy + (rin + 2) * math.sin(a + 0.035))
        p3 = (cx + (rin - 14 * sc) * math.cos(a), cy + (rin - 14 * sc) * math.sin(a))
        poly(img, [p1, p2, p3], C3(ring_col))
    # carrier
    car_col = GREEN if roles else CYAN
    orbit = (RS + RP + 8) * sc
    pc = [(cx + orbit * math.cos(a_c + k * 2 * math.pi / 3), cy + orbit * math.sin(a_c + k * 2 * math.pi / 3)) for k in range(3)]
    polyline(img, pc, C3(mixc(car_col, (0, 0, 0), 0.35)), 30 * sc, closed=True)
    # planets
    for k, (px, py) in enumerate(pc):
        # planet spin relative to carrier: (w_s - w_c) * RS = -(w_p - w_c) * RP
        a_p = a_c - (a_s - a_c) * RS / RP + k * 0.7
        gear(img, glow, px, py, RP * sc, 13, a_p, M_LIGHT)
        circle(img, px, py, 16 * sc, C3(car_col))
    # sun
    sun_col = YEL
    if roles:
        sun_col = RED if held == 'sun' else YEL
    gear(img, glow, cx, cy, RS * sc, 11, a_s, sun_col, glow_k=0.35 if (roles and driven == 'sun') else 0.0)
    if roles and driven == 'ring':
        circle(glow, cx, cy, rout + 6, C3(YEL, 0.5), th=26, s=0.5)
    if roles:
        if held == 'ring':
            lock_icon(img, cx + rout * 0.72, cy - rout * 0.72, 1.3 * sc)
        else:
            lock_icon(img, cx, cy - 10, 1.0 * sc)
    return pc


def scene_planet(img, glow, t):
    planetary(img, glow, t, PCX, PCY)
    held, driven, g = planet_state(t)
    if t >= THIRD_S:
        k = ramp(t, THIRD_S, 0.3)
        spr = RATIO['1ST GEAR' if g == 1 else '2ND GEAR']
        pop = 1 + 0.2 * max(0.0, 1 - (t - THATS_S) / 0.3) if t >= THATS_S else 1.0
        blit(img, spr, 540, 1375, opacity=k, scale=pop)


def scene_clutch(img, glow, t):
    # small planetary at top, clutch pack below holding the ring
    planetary(img, glow, t, 540, 700, sc=0.55, show_roles=False)
    y0, y1 = 1000, 1240
    sq = ease_io((t - SQUEEZE_S) / 0.5) if t >= SQUEEZE_S else 0.0
    gap = 26 * (1 - sq)
    # housing
    rrect(img, 150, y0 - 30, 930, y1 + 30, 24, C3((14, 22, 40)))
    rrect_outline(img, 150, y0 - 30, 930, y1 + 30, 24, C3(M_MID), 4)
    # oil chamber + piston
    px = 260 + 7 * 26 * (1 - (1 - sq)) * 0.0
    pist_x = 250 + 150 * sq
    if t >= PRESS_S - 0.6 or sq > 0:
        oil_k = max(ramp(t, SQUEEZE_S - 0.2, 0.4), 0.0)
        rrect(img, 170, y0, pist_x, y1, 12, C3(mixc((14, 22, 40), OIL, 0.75 * oil_k)))
        for j in range(3):
            yy = y0 + 50 + j * 70
            xa = 180 + ((t * 160 + j * 40) % 60)
            if oil_k > 0.1:
                line(img, xa, yy, xa + 40, yy, C3(BLUE, oil_k), 8)
                poly(img, [(xa + 40, yy - 14), (xa + 40, yy + 14), (xa + 62, yy)], C3(BLUE, oil_k))
    rrect(img, pist_x, y0 - 10, pist_x + 50, y1 + 10, 10, C3(CYAN))
    # plates
    x = pist_x + 50 + gap
    for k in range(8):
        col = ORANGE if k % 2 == 0 else M_HI
        rrect(img, x, y0 + (0 if k % 2 else 20), x + 30, y1 - (0 if k % 2 else 20), 6, C3(col))
        x += 30 + gap
    if sq > 0.9:
        circle(glow, pist_x + 300, (y0 + y1) / 2, 160, C3(ORANGE, 0.5), s=0.5)
    # link from pack up to the ring with lock when held
    if t >= HELD_S:
        k = ramp(t, HELD_S, 0.3)
        line(img, 880, y0 - 30, 880, 700, C3(RED, k), 8)
        line(img, 880, 700, 540 + 360 * 0.55, 700, C3(RED, k), 8)
        lock_icon(img, 880, 900, 1.0)


LABELS = [('SUN GEAR', YEL, 820, 470, lambda t: (PCX + 50, PCY - 40), SUN_S, T['G'] - 0.4),
          ('PLANETS', M_HI, 220, 470, lambda t: planet_pos(t, 0), PLAN_S, T['G'] - 0.4),
          ('RING GEAR', BLUE, 230, 1295, lambda t: (PCX - 250, PCY + 230), RING_S, HOLD_S),
          ('CARRIER = OUTPUT', GREEN, 790, 1295, lambda t: planet_pos(t, 1), THIRD_S, T['G'] - 0.4),
          ('CLUTCH PACK', ORANGE, 760, 1330, lambda t: (700, 1120), CLUTCHES_S, T['H'] - 0.4),
          ('PISTON', CYAN, 240, 1330, lambda t: (300 + 150 * (ease_io((t - SQUEEZE_S) / 0.5) if t >= SQUEEZE_S else 0), 1120), SQUEEZE_S - 0.3, T['H'] - 0.4),
          ('OIL PRESSURE', BLUE, 230, 900, lambda t: (230, 1050), PRESS_S - 0.2, T['H'] - 0.4)]


def planet_pos(t, k):
    a_s, a_r, a_c = planet_angles(t)
    orbit = RS + RP + 8
    a = a_c + k * 2 * math.pi / 3
    return PCX + orbit * math.cos(a), PCY + orbit * math.sin(a)


def scene_computer(img, glow, t):
    cx, cy = 540, 640
    # chip
    rrect(img, cx - 110, cy - 110, cx + 110, cy + 110, 18, C3((18, 28, 50)))
    rrect_outline(img, cx - 110, cy - 110, cx + 110, cy + 110, 18, C3(CYAN), 5)
    for k in range(5):
        o = -80 + k * 40
        for (x0, y0, x1, y1) in ((cx + o, cy - 110, cx + o, cy - 140), (cx + o, cy + 110, cx + o, cy + 140),
                                 (cx - 110, cy + o, cx - 140, cy + o), (cx + 110, cy + o, cx + 140, cy + o)):
            line(img, x0, y0, x1, y1, C3(CYAN), 6)
    rrect(img, cx - 60, cy - 60, cx + 60, cy + 60, 10, C3(mixc(CYAN, (0, 0, 0), 0.6)))
    blink = 0.5 + 0.5 * math.sin(t * 9)
    circle(glow, cx, cy, 140, C3(CYAN, 0.25 + 0.25 * blink), s=0.5)
    blit(img, TXT['COMPUTER'], cx, cy + 190)
    # speed sensor (left) + pedal (right)
    for (sx, start, key) in ((170, SPEED_S, 'SPEED'), (910, PEDAL_S, 'PEDAL')):
        on = t >= start - 0.1
        col = YEL if on else M_MID
        if key == 'SPEED':
            circle(img, sx, cy, 75, C3((18, 28, 50)))
            circle(img, sx, cy, 75, C3(col), th=6)
            a = math.radians(200 + 120 * (0.5 + 0.3 * math.sin(t * 1.5)))
            line(img, sx, cy, sx + 55 * math.cos(a), cy + 55 * math.sin(a), C3(col), 6)
        else:
            ang = math.radians(-60 + 8 * math.sin(t * 2))
            ex, ey = sx + 120 * math.cos(ang), cy + 60 + 120 * math.sin(ang)
            line(img, sx - 30, cy + 70, ex - 30, ey, C3(col), 12)
            rrect(img, ex - 60, ey - 16, ex, ey + 16, 8, C3(col))
        blit(img, TXT[key], sx, cy + 130)
        if on:
            x0, x1 = (sx + 80, cx - 145) if sx < cx else (sx - 90, cx + 145)
            line(img, x0, cy, x1, cy, C3(col, 0.6), 5)
            p = ((t - start) * 1.6) % 1.0
            circle(img, x0 + (x1 - x0) * p, cy, 12, C3(YEL))
            circle(glow, x0 + (x1 - x0) * p, cy, 20, C3(YEL, 0.6), s=0.5)
    # tacho with quick upshifts
    if t < SHIFTS_S:
        g, rpm = 1, 1.5 + 0.8 * ramp(t, T['H'] + 1.0, 2.0)
    else:
        u = (t - SHIFTS_S) / 0.55
        g = min(6, 1 + int(u))
        f = u - int(u) if g < 6 else min(1.0, u - 5)
        rpm = 4.6 - 2.0 * min(1.0, f * 6) + 1.8 * f if g < 6 else 2.6
    tacho(img, glow, 430, 1120, 190, rpm, g, t=t)


def scene_teaser(img, glow, t):
    cx, cy, Rc = 540, 1020, 300
    a0, a1 = math.radians(-160), math.radians(-20)
    f = ease_io((t - T['K']) / max(1.0, CORNER_S + 0.6 - T['K']))
    a = a0 + (a1 - a0) * f
    # road
    cv2.ellipse(img, P(cx, cy), (int(Rc * SC), int(Rc * SC)), 0, math.degrees(a0) - 8, math.degrees(a1) + 8, C3(M_DARK), int(190), cv2.LINE_AA, SH)
    for k in range(18):
        aa = a0 + k * (a1 - a0) / 17
        circle(img, cx + Rc * math.cos(aa), cy + Rc * math.sin(aa), 5, C3(M_MID))
    rin, rout = Rc - 55, Rc + 55
    pts_i = [(cx + rin * math.cos(a0 + (a - a0) * j / 30), cy + rin * math.sin(a0 + (a - a0) * j / 30)) for j in range(31)]
    pts_o = [(cx + rout * math.cos(a0 + (a - a0) * j / 30), cy + rout * math.sin(a0 + (a - a0) * j / 30)) for j in range(31)]
    if f > 0.02:
        polyline(img, pts_i, C3(BLUE), 10)
        polyline(img, pts_o, C3(ORANGE), 10)
    # car (top view)
    hx, hy = cx + Rc * math.cos(a), cy + Rc * math.sin(a)
    tx, ty = -math.sin(a), math.cos(a)  # tangent (direction of travel, clockwise on screen)
    nx, ny = math.cos(a), math.sin(a)
    L, Wd = 110, 70

    def P2(u, v):
        return (hx + tx * u + nx * v, hy + ty * u + ny * v)
    poly(img, [P2(-L, -Wd), P2(L, -Wd), P2(L, Wd), P2(-L, Wd)], C3(CYAN))
    poly(img, [P2(10, -Wd + 12), P2(60, -Wd + 12), P2(60, Wd - 12), P2(10, Wd - 12)], C3((14, 22, 40)))
    for u in (-70, 70):
        for v, col in ((-Wd - 6, BLUE), (Wd + 6, ORANGE)):
            p = [P2(u - 24, v - 10), P2(u + 24, v - 10), P2(u + 24, v + 10), P2(u - 24, v + 10)]
            poly(img, p, C3(col))
    if t >= CORNER_S - 0.2:
        k = ramp(t, CORNER_S - 0.2, 0.3)
        blit(img, TXT['SLOWER'], cx, cy - rin + 120, opacity=k)
        blit(img, TXT['FASTER'], cx, cy - rout - 60, opacity=k)
    blit(img, SPR_PART4, W / 2, 1180)


SCENES = [(0.0, scene_intro), (PART_S - 0.15, scene_title), (T['B'] - 0.15, scene_converter),
          (T['E'] - 0.15, scene_planet), (T['G'] - 0.15, scene_clutch), (T['H'] - 0.15, scene_computer),
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
    if T['E'] - 0.15 <= t < T['H']:
        draw_labels(frame, t)
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
