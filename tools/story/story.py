"""The Great Emu War - cartoon story short. Frame t is a pure function of t.

python3 story.py stills t1 t2 ...   -> still_<t>.png
python3 story.py range a b out.mp4   -> frames [a, b)
"""
import json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, SS = 1080, 1920, 30, 2
INK = (28, 26, 30)
WHITE = (255, 255, 255)
SKY1, SKY2 = (120, 196, 240), (186, 228, 248)
GROUND = (222, 150, 86)
GROUND2 = (204, 128, 70)
KHAKI = (176, 150, 98)
KHAKI_D = (140, 116, 70)
EMU = (92, 72, 54)
EMU_D = (62, 48, 38)
EMU_HEAD = (120, 138, 158)
LEG = (110, 110, 116)
RED = (226, 64, 56)
YEL = (255, 204, 48)
GUN = (60, 64, 70)
WHEAT = (238, 196, 92)
WHEAT_D = (204, 160, 62)

# ------------------------------------------------------------------ timeline
TLD = json.load(open('timeline.json'))
WORDS = TLD['words']
DUR = TLD['duration']
N_FRAMES = int(math.ceil(DUR * FPS))


def seg_start(s):
    return next(w['start'] for w in WORDS if w['seg'] == s)


def ws(seg, key, nth=1):
    c = 0
    for w in WORDS:
        if w['seg'] == seg and w['key'] == key:
            c += 1
            if c == nth:
                return w['start']
    raise KeyError((seg, key, nth))


T = {s: seg_start(s) for s in 'ABCDEFGHIJKL'}
EV = dict(
    war=ws('A', 'war'), thousand=ws('B', 'thousand'), three=ws('D', 'three'), two=ws('D', 'two'),
    ten=ws('D', 'ten'), fire=ws('E', 'fire'), jammed=ws('F', 'jammed'), ran=ws('F', 'ran'),
    faster=ws('G', 'faster'), bumpy=ws('G', 'bumpy'), aim=ws('G', 'nobody'), six=ws('H', 'six'),
    fired=ws('H', 'fired'), mostly=ws('H', 'emus'), came=ws('I', 'came'), again=ws('I', 'went', 2),
    perbird=ws('J', 'ten'), still=ws('K', 'still'), lost=ws('K', 'lost'), birds=ws('K', 'birds'),
    follow=ws('L', 'follow'))


def ramp(t, t0, d=0.3):
    return min(1.0, max(0.0, (t - t0) / d))


def ease(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def pop(t, t0, d=0.25):
    """overshoot scale 0 -> 1.15 -> 1"""
    x = (t - t0) / d
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    return ease(x) * (1 + 0.25 * math.sin(math.pi * x))


# ------------------------------------------------------------------ fonts / text
def _font(size):
    for f in ['/usr/share/fonts/truetype/noto/NotoSans-Black.ttf', '/usr/share/fonts/truetype/noto/NotoSans-ExtraBold.ttf',
              '/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf']:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    raise FileNotFoundError('font')


_fc = {}


def font(size):
    size = int(size)
    if size not in _fc:
        _fc[size] = _font(size)
    return _fc[size]


def text(d, x, y, s, size, fill=WHITE, stroke=None, sw=0, anchor='mm', maxw=None):
    if size < 2:
        return
    size *= SS
    if maxw:
        while font(size).getlength(s) > maxw * SS and size > 20:
            size -= 4
    d.text((x * SS, y * SS), s, font=font(size), fill=fill, anchor=anchor,
           stroke_width=int(sw * SS), stroke_fill=stroke or INK)


# ------------------------------------------------------------------ primitives (coords in 1080x1920 space)
def P(pts):
    return [(x * SS, y * SS) for x, y in pts]


def circ(d, x, y, r, fill=None, outline=INK, w=6):
    d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], fill=fill, outline=outline,
              width=int(w * SS) if outline else 0)


def ell(d, x, y, rx, ry, fill=None, outline=INK, w=6):
    d.ellipse([(x - rx) * SS, (y - ry) * SS, (x + rx) * SS, (y + ry) * SS], fill=fill, outline=outline,
              width=int(w * SS) if outline else 0)


def rect(d, x0, y0, x1, y1, fill=None, outline=INK, w=6, r=0):
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1))
    box = [x0 * SS, y0 * SS, x1 * SS, y1 * SS]
    if r:
        d.rounded_rectangle(box, r * SS, fill=fill, outline=outline, width=int(w * SS) if outline else 0)
    else:
        d.rectangle(box, fill=fill, outline=outline, width=int(w * SS) if outline else 0)


def poly(d, pts, fill=None, outline=INK, w=6):
    d.polygon(P(pts), fill=fill)
    if outline:
        d.line(P(pts + pts[:1]), fill=outline, width=int(w * SS), joint='curve')


def line(d, pts, fill=INK, w=6):
    d.line(P(pts), fill=fill, width=int(w * SS), joint='curve')
    for x, y in (pts[0], pts[-1]):
        r = w / 2
        d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], fill=fill)


def limb(d, a, b, w=9, col=INK):
    line(d, [a, b], col, w)


# ------------------------------------------------------------------ characters
def face(d, x, y, r, expr='smile', look=(0, 0), brow=0):
    ex = r * 0.38
    for sx in (-1, 1):
        circ(d, x + sx * ex, y - r * 0.12, r * 0.3, WHITE, INK, 4)
        circ(d, x + sx * ex + look[0] * r * 0.12, y - r * 0.12 + look[1] * r * 0.12, r * 0.12, INK, None)
    if brow:
        for sx in (-1, 1):
            line(d, [(x + sx * ex - r * 0.28, y - r * 0.5 - sx * brow * r * 0.12),
                     (x + sx * ex + r * 0.28, y - r * 0.5 + sx * brow * r * 0.12)], INK, 5)
    my = y + r * 0.45
    if expr == 'smile':
        d.arc([(x - r * 0.35) * SS, (my - r * 0.3) * SS, (x + r * 0.35) * SS, (my + r * 0.12) * SS], 20, 160, fill=INK, width=int(5 * SS))
    elif expr == 'grin':
        poly(d, [(x - r * 0.38, my - r * 0.1), (x + r * 0.38, my - r * 0.1), (x, my + r * 0.25)], (150, 30, 40), INK, 4)
    elif expr == 'o':
        ell(d, x, my, r * 0.13, r * 0.17, INK, None)
    elif expr == 'sad':
        d.arc([(x - r * 0.3) * SS, (my - r * 0.05) * SS, (x + r * 0.3) * SS, (my + r * 0.35) * SS], 200, 340, fill=INK, width=int(5 * SS))
    elif expr == 'grit':
        rect(d, x - r * 0.3, my - r * 0.1, x + r * 0.3, my + r * 0.12, WHITE, INK, 4)
        for k in (-1, 0, 1):
            line(d, [(x + k * r * 0.1, my - r * 0.1), (x + k * r * 0.1, my + r * 0.12)], INK, 3)
    else:
        line(d, [(x - r * 0.25, my), (x + r * 0.25, my)], INK, 5)


def slouch_hat(d, x, y, r):
    ell(d, x, y - r * 0.55, r * 1.25, r * 0.22, KHAKI, INK, 5)
    poly(d, [(x - r * 0.7, y - r * 0.6), (x - r * 0.55, y - r * 1.15), (x + r * 0.55, y - r * 1.15), (x + r * 0.7, y - r * 0.6)], KHAKI, INK, 5)
    rect(d, x - r * 0.66, y - r * 0.78, x + r * 0.66, y - r * 0.62, KHAKI_D, None)
    poly(d, [(x + r * 0.55, y - r * 0.62), (x + r * 1.2, y - r * 1.05), (x + r * 1.15, y - r * 0.55)], KHAKI, INK, 5)


def straw_hat(d, x, y, r):
    ell(d, x, y - r * 0.6, r * 1.35, r * 0.2, (236, 206, 120), INK, 5)
    rect(d, x - r * 0.62, y - r * 1.15, x + r * 0.62, y - r * 0.62, (236, 206, 120), INK, 5, r=r * 0.2)
    rect(d, x - r * 0.62, y - r * 0.82, x + r * 0.62, y - r * 0.66, RED, None)


def person(d, x, yf, s=1.0, shirt=KHAKI, hat='slouch', expr='smile', look=(0, 0), arms=(-60, -120),
           walk=0.0, brow=0, sit=False, salute=False, face_dir=1, pants=(84, 70, 52)):
    """yf = feet line. arms = angles (deg) of right/left arm from shoulder (0 = right, 90 = down)."""
    hr = 50 * s
    hip_y = yf - 95 * s
    if sit:
        hip_y = yf - 40 * s
    sh_y = hip_y - 105 * s
    hy = sh_y - hr * 0.95
    # legs
    for k, sx in enumerate((-1, 1)):
        ph = math.sin(walk + k * math.pi) if walk else 0.0
        hx = x + sx * 16 * s
        if sit:
            limb(d, (hx, hip_y), (hx + face_dir * 70 * s, hip_y + 4 * s), 10 * s)
            limb(d, (hx + face_dir * 70 * s, hip_y + 4 * s), (hx + face_dir * 70 * s, yf), 10 * s)
        else:
            fx = hx + ph * 34 * s
            fy = yf - max(0.0, -ph) * 18 * s
            limb(d, (hx, hip_y), (fx, fy), 10 * s, pants)
            limb(d, (fx - 2 * s, fy), (fx + face_dir * 18 * s, fy), 10 * s)
    # torso
    rect(d, x - 42 * s, sh_y - 6 * s, x + 42 * s, hip_y + 8 * s, shirt, INK, 5 * s, r=26 * s)
    rect(d, x - 42 * s, hip_y - 8 * s, x + 42 * s, hip_y + 8 * s, pants, INK, 4 * s, r=6 * s)
    # arms
    for sx, ang in zip((1, -1), arms):
        sxp = x + sx * 38 * s
        if salute and sx == 1:
            el = (sxp + 34 * s, sh_y - 30 * s)
            limb(d, (sxp, sh_y + 8 * s), el, 9 * s, shirt)
            limb(d, el, (x + 30 * s, hy - 30 * s), 9 * s, shirt)
            circ(d, x + 30 * s, hy - 30 * s, 9 * s, WHITE, INK, 3 * s)
            continue
        a = math.radians(ang)
        ex = sxp + 62 * s * math.cos(a)
        ey = sh_y + 8 * s + 62 * s * math.sin(a)
        limb(d, (sxp, sh_y + 8 * s), (ex, ey), 9 * s, shirt)
        circ(d, ex, ey, 9 * s, WHITE, INK, 3 * s)
    # head
    circ(d, x, hy, hr, WHITE, INK, 6 * s)
    face(d, x + face_dir * 4 * s, hy, hr, expr, look, brow)
    if hat == 'slouch':
        slouch_hat(d, x, hy, hr)
    elif hat == 'straw':
        straw_hat(d, x, hy, hr)
    return hy


def emu(d, x, yf, s=1.0, phase=0.0, run=0.0, facing=-1, expr='angry', peck=0.0, shades=False, hop=0.0):
    """facing -1 = looks left. run 0..1 = leg swing amount. peck 0..1 head down."""
    yf -= hop * 60 * s
    body_y = yf - 150 * s
    # legs
    for k in (0, 1):
        ph = math.sin(phase + k * math.pi) * run
        hx = x + (k - 0.5) * 20 * s
        kx = hx + facing * -10 * s + ph * 30 * s
        ky = body_y + 70 * s
        fx = hx + ph * 55 * s
        fy = yf - max(0.0, ph * (1 if k else -1)) * 25 * s * run
        line(d, [(hx, body_y + 30 * s), (kx, ky), (fx, fy)], LEG, 8 * s)
        for dx in (-14, 0, 14):
            line(d, [(fx, fy), (fx + (dx + facing * 6) * s, fy + 2 * s)], LEG, 5 * s)
    # body (shaggy)
    pts = []
    for i in range(28):
        a = i / 28 * 2 * math.pi
        rr = 1.0 + (0.12 if i % 2 else 0.0)
        pts.append((x + 92 * s * rr * math.cos(a) - facing * 10 * s, body_y + 62 * s * rr * math.sin(a)))
    poly(d, pts, EMU, INK, 5 * s)
    # tail fluff
    tx = x - facing * 95 * s
    poly(d, [(tx, body_y - 20 * s), (tx - facing * 40 * s, body_y - 50 * s), (tx - facing * 30 * s, body_y + 10 * s)], EMU_D, INK, 4 * s)
    # neck + head
    nx0, ny0 = x + facing * 60 * s, body_y - 30 * s
    hx = x + facing * (95 + 40 * peck) * s
    hy = body_y - (150 - 210 * peck) * s
    mx = (nx0 + hx) / 2 + facing * 10 * s
    my = (ny0 + hy) / 2
    line(d, [(nx0, ny0), (mx, my), (hx, hy)], INK, 30 * s)
    line(d, [(nx0, ny0), (mx, my), (hx, hy)], EMU_HEAD, 20 * s)
    circ(d, hx, hy, 30 * s, EMU_HEAD, INK, 5 * s)
    poly(d, [(hx + facing * 22 * s, hy - 6 * s), (hx + facing * 62 * s, hy + 4 * s), (hx + facing * 22 * s, hy + 12 * s)], (70, 70, 76), INK, 4 * s)
    ex, ey = hx + facing * 6 * s, hy - 8 * s
    if shades:
        rect(d, ex - 26 * s, ey - 10 * s, ex + 26 * s, ey + 10 * s, INK, None, r=8 * s)
        line(d, [(ex - 24 * s, ey - 8 * s), (ex + 24 * s, ey - 8 * s)], INK, 5 * s)
        return
    circ(d, ex, ey, 14 * s, WHITE, INK, 3 * s)
    circ(d, ex + facing * 4 * s, ey + 1 * s, 6 * s, INK, None)
    if expr == 'angry':
        line(d, [(ex - facing * 16 * s, ey - 22 * s), (ex + facing * 14 * s, ey - 12 * s)], INK, 5 * s)
    elif expr == 'happy':
        d.arc([(ex - 12 * s) * SS, (ey - 4 * s) * SS, (ex + 12 * s) * SS, (ey + 14 * s) * SS], 200, 340, fill=INK, width=int(4 * s * SS))


def lewis_gun(d, x, y, s=1.0, facing=1, flash=0.0, smoke=0.0, t=0.0):
    f = facing
    rect(d, min(x, x + f * 220 * s), y - 14 * s, max(x, x + f * 220 * s), y + 14 * s, GUN, INK, 4 * s, r=8 * s)
    rect(d, min(x - f * 70 * s, x), y - 10 * s, max(x - f * 70 * s, x), y + 26 * s, (120, 84, 50), INK, 4 * s, r=6 * s)
    ell(d, x + f * 40 * s, y - 26 * s, 48 * s, 12 * s, (90, 94, 100), INK, 4 * s)
    for k in (-1, 1):
        line(d, [(x + f * 150 * s, y + 10 * s), (x + f * (150 + k * 30) * s, y + 70 * s)], INK, 6 * s)
    if flash > 0:
        mx = x + f * 230 * s
        pts = []
        for i in range(12):
            a = i / 12 * 2 * math.pi
            rr = (60 if i % 2 == 0 else 26) * s * flash
            pts.append((mx + f * abs(math.cos(a)) * rr * 1.4, y + math.sin(a) * rr))
        poly(d, pts, YEL, (240, 120, 30), 4 * s)
    if smoke > 0:
        for k in range(4):
            ph = (t * 1.6 + k / 4) % 1.0
            circ(d, x + f * 60 * s + k * 8 * s, y - 40 * s - ph * 140 * s, (18 + 30 * ph) * s * smoke,
                 (int(150 + 60 * ph),) * 3, INK, 3 * s)


def truck(d, x, yf, s=1.0, facing=1, wheel=0.0, gun=True, bounce=0.0, gunner=True):
    f = facing
    y = yf - bounce
    # bed
    x0, x1 = sorted([x - f * 30 * s, x - f * 300 * s])
    rect(d, x0, y - 120 * s, x1, y - 60 * s, (150, 98, 60), INK, 5 * s)
    # cab
    cx0, cx1 = sorted([x - f * 40 * s, x + f * 120 * s])
    rect(d, cx0, y - 210 * s, cx1, y - 60 * s, (70, 112, 82), INK, 5 * s, r=18 * s)
    wx0, wx1 = sorted([x + f * 10 * s, x + f * 90 * s])
    rect(d, wx0, y - 190 * s, wx1, y - 130 * s, (190, 226, 240), INK, 4 * s, r=8 * s)
    hx0, hx1 = sorted([x + f * 120 * s, x + f * 200 * s])
    rect(d, hx0, y - 140 * s, hx1, y - 60 * s, (70, 112, 82), INK, 5 * s, r=10 * s)
    for wxp in (x + f * 140 * s, x - f * 220 * s):
        circ(d, wxp, yf - 40 * s, 42 * s, (50, 50, 56), INK, 5 * s)
        circ(d, wxp, yf - 40 * s, 16 * s, (180, 180, 186), INK, 3 * s)
        line(d, [(wxp, yf - 40 * s), (wxp + 30 * s * math.cos(wheel), yf - 40 * s + 30 * s * math.sin(wheel))], INK, 5 * s)
    if gunner:
        gx = x - f * 170 * s
        person(d, gx, y - 120 * s, 0.75 * s, expr='grit', arms=(20, 160) if f > 0 else (20, 160), face_dir=f, brow=1)
    if gun:
        lewis_gun(d, x - f * 150 * s, y - 230 * s, 0.7 * s, facing=f)


# ------------------------------------------------------------------ backgrounds
def bg_outback(d, t, ground_y=1100, scroll=0.0, sun=True):
    for i in range(8):
        y0 = i * ground_y / 8
        c = tuple(int(SKY1[k] + (SKY2[k] - SKY1[k]) * i / 7) for k in range(3))
        rect(d, 0, y0, W, y0 + ground_y / 8 + 2, c, None)
    if sun:
        circ(d, 860, 520, 70, (255, 228, 120), None)
    # mesas
    for k, (mx, mw, mh) in enumerate(((150, 260, 120), (520, 180, 80), (860, 300, 150))):
        xx = (mx - scroll * 0.2) % (W + 400) - 200
        poly(d, [(xx - mw / 2, ground_y), (xx - mw / 2 + 40, ground_y - mh), (xx + mw / 2 - 40, ground_y - mh), (xx + mw / 2, ground_y)],
             (196, 112, 72), INK, 5)
    rect(d, 0, ground_y, W, H, GROUND, None)
    line(d, [(0, ground_y), (W, ground_y)], INK, 6)
    for k in range(40):
        rx = (k * 211 + 37 - scroll) % (W + 100) - 50
        ry = ground_y + 40 + (k * 97) % (H - ground_y - 60)
        ell(d, rx, ry, 14, 5, GROUND2, None)
    for k in range(6):
        bx = (k * 260 + 90 - scroll * 1.0) % (W + 200) - 100
        by = ground_y + 30 + (k * 53) % 80
        for j in range(5):
            line(d, [(bx, by), (bx + (j - 2) * 12, by - 30 - (j % 2) * 10)], (120, 120, 60), 4)


def bg_wheat(d, t, ground_y=1080):
    bg_outback(d, t, ground_y, sun=True)
    rect(d, 0, ground_y + 3, W, H, WHEAT, None)
    for row in range(9):
        yy = ground_y + 40 + row * 70
        for k in range(14):
            xx = k * 82 + (row % 2) * 40 + 10 * math.sin(t * 2 + k + row)
            line(d, [(xx, yy + 40), (xx + 6, yy)], WHEAT_D, 5)
            ell(d, xx + 7, yy - 8, 7, 16, WHEAT_D, None)


# ------------------------------------------------------------------ scenes
def emu_crowd(d, t, n, y0, y1, s0, s1, seed=3, run=0.0, dx=0.0, facing=-1, peck_t=None):
    rng = np.random.default_rng(seed)
    pos = sorted([(rng.uniform(0, 1), rng.uniform(-80, W + 80), rng.uniform(0, 6.28)) for _ in range(n)])
    for v, x, ph in pos:
        y = y0 + (y1 - y0) * v
        s = s0 + (s1 - s0) * v
        pk = 0.0
        if peck_t is not None:
            pk = max(0.0, math.sin(t * 3 + ph)) ** 2
        emu(d, x + dx * s, y, s, phase=t * 14 + ph, run=run, facing=facing, peck=pk)


def sc_intro(d, t):
    bg_outback(d, t)
    k = ramp(t, 0.0, 0.4)
    hy = person(d, 540, 1340, 1.6, expr='grit', salute=t > 0.6, brow=1, arms=(80, 100))
    if t >= EV['war']:
        p = pop(t, EV['war'])
        if p > 0:
            text(d, 540, 640, 'WAR!', 210 * p, RED, INK, 10)
    p = pop(t, 0.15)
    if p > 0:
        text(d, 540, 470, '1932', 170 * p, WHITE, INK, 10)


def sc_enemy(d, t):
    bg_outback(d, t)
    dt = t - T['B']
    emu_crowd(d, t, 26, 1110, 1190, 0.25, 0.4, seed=5, run=0.0)
    s = 1.3 + 0.08 * ease(dt / 0.6)
    emu(d, 560, 1400, s, facing=-1, expr='angry', phase=0, run=0)
    if t >= EV['thousand'] - 0.15:
        p = pop(t, EV['thousand'] - 0.15)
        text(d, 540, 560, '20,000', 150 * p, YEL, INK, 9)
        text(d, 540, 690, 'EMUS', 90 * p, WHITE, INK, 7)


def sc_wheat(d, t):
    bg_wheat(d, t)
    emu_crowd(d, t, 7, 1150, 1360, 0.55, 0.85, seed=11, peck_t=True, facing=1)
    hy = person(d, 160, 1400, 1.25, shirt=(80, 120, 200), hat='straw', expr='o', arms=(-115, -65), brow=-1, pants=(60, 80, 150))


def sc_army(d, t):
    bg_outback(d, t)
    for i, x in enumerate((300, 540, 780)):
        tt0 = EV['three'] + i * 0.18
        if t < tt0:
            continue
        p = pop(t, tt0)
        person(d, x, 1250, 1.15 * p if p < 1 else 1.15, expr='grit', salute=True, brow=1, arms=(80, 100))
    if t >= EV['two']:
        for i, x in enumerate((180, 620)):
            p = pop(t, EV['two'] + i * 0.15)
            if p > 0:
                lewis_gun(d, x, 1330, 1.0 * p, facing=1)
    if t >= EV['ten']:
        p = pop(t, EV['ten'])
        for r in range(3):
            for c in range(3 - r):
                bx = 820 + c * 90 + r * 45 - 90
                by = 1380 - r * 70
                rect(d, bx - 42, by - 32, bx + 42, by + 32, (120, 140, 80), INK, 5)
                text(d, bx, by, 'AMMO', 20, WHITE, INK, 2)
        text(d, 540, 600, '10,000', 140 * p, YEL, INK, 9)
        text(d, 540, 720, 'BULLETS', 80 * p, WHITE, INK, 6)


def sc_day1(d, t):
    bg_outback(d, t)
    dt = t - T['E']
    fire = t >= EV['fire']
    jam = t >= EV['jammed']
    ran = t >= EV['ran']
    # emus approaching from right then fleeing
    if not ran:
        dx = 300 - min(dt, EV['fire'] - T['E']) * 60
        emu_crowd(d, t, 9, 1150, 1290, 0.45, 0.7, seed=7, run=0.35, dx=dx, facing=-1)
    else:
        rdt = t - EV['ran']
        emu_crowd(d, t, 9, 1150, 1290, 0.45, 0.7, seed=7, run=1.0, dx=300 - (EV['fire'] - T['E']) * 60 + rdt * 1400, facing=1)
        for k in range(6):
            circ(d, 700 + k * 60 - rdt * 80, 1280 + (k % 2) * 20, 30 + rdt * 30, (230, 196, 150), None)
    flash = 0.0
    if fire and not jam:
        flash = 1.0 if int((t - EV['fire']) * 15) % 2 == 0 else 0.4
    lewis_gun(d, 300, 1320, 1.3, facing=1, flash=flash, smoke=1.0 if jam else 0.0, t=t)
    person(d, 160, 1400, 1.2, expr='o' if jam else 'grit', brow=1 if not jam else -1, arms=(10, 170) if not jam else (-120, -60), sit=True)
    if dt < 1.0:
        text(d, 540, 560, 'DAY 1', 130 * pop(t, T['E']), WHITE, INK, 9)
    if jam and t < EV['ran'] + 0.2:
        p = pop(t, EV['jammed'])
        text(d, 540, 600, 'JAMMED!', 140 * p, RED, INK, 9)


def sc_truck(d, t):
    dt = t - T['G']
    speed = 900
    bg_outback(d, t, scroll=dt * speed)
    bumpy = t >= EV['bumpy']
    bounce = abs(math.sin(dt * (14 if bumpy else 6))) * (60 if bumpy else 12)
    # emus ahead, pulling away after "faster"
    lead = 560 + max(0.0, t - EV['faster']) * 140
    for i in range(4):
        ex = lead + i * 110
        emu(d, ex, 1250 + (i % 2) * 40, 0.6, phase=t * 18 + i, run=1.0, facing=1)
    truck(d, 380, 1390, 1.0, facing=1, wheel=dt * 18, bounce=bounce)
    if t >= EV['aim']:
        for k in range(5):
            ph = ((t - EV['aim']) * 3 + k / 5) % 1.0
            bx = 300 + ph * 700
            by = 1170 - ph * 900 + 120 * math.sin(k * 2.1)
            line(d, [(bx, by), (bx + 40, by - 50)], (90, 90, 90), 6)
        text(d, 540, 600, 'MISSED!', 120 * pop(t, EV['aim']), RED, INK, 8)


def sc_sixdays(d, t):
    bg_outback(d, t)
    day = 1 + int(min(5, max(0.0, (t - T['H']) / 0.25)))
    if t < EV['fired']:
        rect(d, 380, 520, 700, 840, WHITE, INK, 8, r=24)
        rect(d, 380, 520, 700, 610, RED, INK, 8, r=24)
        rect(d, 380, 580, 700, 610, RED, None)
        text(d, 540, 566, 'NOV 1932', 46, WHITE, INK, 0)
        text(d, 540, 730, 'DAY %d' % day, 90, INK)
    if t >= EV['fired'] and t < EV['mostly']:
        n = int(2500 * ease((t - EV['fired']) / 1.4))
        rng = np.random.default_rng(2)
        for k in range(int(70 * n / 2500)):
            x = 540 + rng.normal(0, 150)
            y = 1380 - abs(rng.normal(0, 1)) * 90 * (1 - abs(x - 540) / 600)
            rect(d, x - 7, y - 20, x + 7, y + 20, (214, 170, 70), INK, 3, r=4)
        text(d, 540, 640, '{:,}'.format(n), 150, YEL, INK, 9)
        text(d, 540, 770, 'BULLETS FIRED', 70, WHITE, INK, 6)
    if t >= EV['mostly']:
        p = pop(t, EV['mostly'])
        emu(d, 360, 1390, 1.0, facing=1, expr='happy', shades=True)
        emu(d, 740, 1370, 0.9, facing=-1, expr='happy', peck=0.0)
        text(d, 540, 620, 'EMUS: FINE', 120 * p, (110, 220, 120), INK, 8)


def sc_back_forth(d, t):
    bg_outback(d, t)
    # home (left) -> back (right) -> home again (left)
    if t < EV['came']:
        u = (t - T['I']) / max(0.4, EV['came'] - T['I'])
        x, f = 540 - ease(u) * 900, -1
    elif t < EV['again']:
        u = (t - EV['came']) / max(0.4, EV['again'] - EV['came'])
        x, f = -360 + ease(u) * 900, 1
    else:
        u = (t - EV['again']) / 1.2
        x, f = 540 - ease(u) * 900, -1
    truck(d, x, 1390, 1.0, facing=f, wheel=t * 20, gunner=True)
    emu_crowd(d, t, 5, 1110, 1180, 0.35, 0.45, seed=9, facing=-1, peck_t=True)
    lbl = 'HOME' if t < EV['came'] else ('BACK' if t < EV['again'] else 'HOME AGAIN')
    tt0 = T['I'] if t < EV['came'] else (EV['came'] if t < EV['again'] else EV['again'])
    text(d, 540, 620, lbl, 120 * pop(t, tt0), WHITE, INK, 8)


def bullet_icon(d, x, y, s=1.0):
    rect(d, x - 12 * s, y - 20 * s, x + 12 * s, y + 40 * s, (214, 170, 70), INK, 4 * s, r=4 * s)
    poly(d, [(x - 12 * s, y - 20 * s), (x, y - 50 * s), (x + 12 * s, y - 20 * s)], (180, 110, 60), INK, 4 * s)


def sc_stats(d, t):
    bg_outback(d, t)
    rect(d, 90, 420, 990, 1180, (250, 244, 230), INK, 8, r=40)
    k1 = ease((t - T['J']) / 0.8)
    text(d, 540, 500, 'FINAL SCORE', 70, INK, None, 0)
    # bars
    text(d, 150, 640, '~10,000', 64, INK, anchor='lm')
    text(d, 150, 700, 'bullets', 44, (90, 90, 90), anchor='lm')
    rect(d, 450, 610, 450 + 480 * k1, 690, (214, 170, 70), INK, 6, r=14)
    k2 = ease((t - ws('J', 'less')) / 0.6) if t >= ws('J', 'less') else 0.0
    text(d, 150, 820, '986', 64, INK, anchor='lm')
    text(d, 150, 880, 'emus', 44, (90, 90, 90), anchor='lm')
    rect(d, 450, 790, 450 + 48 * k2 + 2, 870, EMU, INK, 6, r=14)
    if t >= EV['perbird']:
        p = pop(t, EV['perbird'])
        for i in range(10):
            bullet_icon(d, 170 + i * 58, 1040, 0.8 * p)
        text(d, 790, 1050, '=', 80, INK)
        emu(d, 900, 1120, 0.45 * max(p, 0.01), facing=-1)


def sc_end(d, t):
    bg_wheat(d, t)
    for i, x in enumerate((220, 520, 840)):
        hop = abs(math.sin(t * 5 + i)) if t >= EV['still'] else 0.0
        emu(d, x, 1250 + i % 2 * 50, 0.75, facing=-1 if i else 1, expr='happy', hop=hop * 0.8, phase=t * 6, run=0.2)
    person(d, 840, 1400, 1.1, expr='sad', sit=True, arms=(100, 80), face_dir=-1, brow=-1)
    if t >= EV['lost']:
        p = pop(t, EV['lost'])
        rect(d, 170, 470, 910, 720, INK, WHITE, 6, r=30)
        text(d, 540, 540, 'EMUS  1', 100 * p, YEL)
        text(d, 540, 650, 'ARMY  0', 100 * p, WHITE)


def sc_cta(d, t):
    bg_outback(d, t)
    emu(d, 540, 1380, 1.2, facing=-1, expr='happy', peck=0.15 * math.sin(t * 6) + 0.1)
    p = pop(t, EV['follow'])
    if p > 0:
        pulse = 1 + 0.04 * math.sin((t - EV['follow']) * 8)
        rect(d, 540 - 360 * pulse, 560 - 70 * pulse, 540 + 360 * pulse, 560 + 70 * pulse, YEL, INK, 7, r=70)
        text(d, 540, 560, 'FOLLOW FOR MORE', 64 * p * pulse, INK, maxw=640)
        text(d, 540, 700, 'TRUE STORIES', 80 * p, WHITE, INK, 6)


SCENES = [(0.0, sc_intro), (T['B'] - 0.1, sc_enemy), (T['C'] - 0.1, sc_wheat), (T['D'] - 0.1, sc_army),
          (T['E'] - 0.1, sc_day1), (T['G'] - 0.1, sc_truck), (T['H'] - 0.1, sc_sixdays), (T['I'] - 0.1, sc_back_forth),
          (T['J'] - 0.1, sc_stats), (T['K'] - 0.1, sc_end), (T['L'] - 0.1, sc_cta)]

# ------------------------------------------------------------------ captions
CH = []
cur = []
for i, w in enumerate(WORDS):
    cur.append(i)
    if len(cur) >= 3 or w['brk'] >= 0.45 or w.get('last'):
        CH.append(cur)
        cur = []
if cur:
    CH.append(cur)


def caption(d, t):
    for ci, ch in enumerate(CH):
        s = WORDS[ch[0]]['start']
        e = WORDS[CH[ci + 1][0]]['start'] if ci + 1 < len(CH) else WORDS[ch[-1]]['end'] + 0.6
        e = min(e, WORDS[ch[-1]]['end'] + 0.7)
        if s - 0.03 <= t < e:
            txt = ' '.join(WORDS[i]['text'] for i in ch if WORDS[i]['start'] <= t + 0.03)
            sc = 1 + 0.1 * max(0.0, 1 - (t - s) / 0.1)
            text(d, 540, 1470, txt, 74 * sc, WHITE, INK, 9, maxw=960)
            return


def render_frame(t):
    img = Image.new('RGB', (W * SS, H * SS), SKY1)
    d = ImageDraw.Draw(img)
    fn = SCENES[0][1]
    for t0, f in SCENES:
        if t >= t0:
            fn = f
    fn(d, t)
    # title strip
    text(d, 540, 290, 'THE GREAT EMU WAR', 54, WHITE, INK, 6)
    caption(d, t)
    img = img.reduce(SS)
    # whoosh flash on cuts
    for t0, _ in SCENES[1:]:
        if t0 <= t < t0 + 0.08:
            a = np.asarray(img).astype(np.float32)
            img = Image.fromarray((a * 0.6 + 255 * 0.4).astype(np.uint8))
    # shake on hits
    sh = 0.0
    for t0, dd, amp in ((EV['war'], 0.3, 10), (EV['fire'], 0.6, 8), (EV['jammed'], 0.2, 6), (EV['lost'], 0.3, 8)):
        if t0 <= t < t0 + dd:
            sh = max(sh, amp * (1 - (t - t0) / dd))
    if EV['bumpy'] <= t < EV['aim'] + 1.2:
        sh = max(sh, 4)
    a = np.asarray(img)
    if sh > 0:
        a = np.roll(a, (int(sh * math.sin(t * 71)), int(sh * math.cos(t * 53))), axis=(0, 1))
    return a


def main():
    if sys.argv[1] == 'stills':
        for ts in sys.argv[2:]:
            Image.fromarray(render_frame(float(ts))).save('still_%05.2f.png' % float(ts))
        print('DUR', DUR, 'frames', N_FRAMES)
        return
    a, b, out = int(sys.argv[2]), min(int(sys.argv[3]), N_FRAMES), sys.argv[4]
    p = subprocess.Popen(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H),
                          '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p',
                          '-threads', '2', out + '.tmp.mp4'], stdin=subprocess.PIPE)
    for i in range(a, b):
        p.stdin.write(render_frame(i / FPS).tobytes())
    p.stdin.close()
    if p.wait() == 0:
        os.replace(out + '.tmp.mp4', out)
        print('done', a, b, out)
    else:
        sys.exit('ffmpeg failed')


if __name__ == '__main__':
    main()
