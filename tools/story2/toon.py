"""Flat vector cartoon toolkit (cv2, anti-aliased). Characters + drawing helpers."""
import math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

AA = cv2.LINE_AA

def C(hexs):  # '#rrggbb' -> BGR tuple
    h = hexs.lstrip('#'); return (int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16))

def shade(c, f):
    return tuple(int(max(0, min(255, v * f))) for v in c)

def P(*pts):
    return np.array([[int(round(x)), int(round(y))] for x, y in pts], np.int32)

def poly(img, pts, col):
    cv2.fillPoly(img, [P(*pts)], col, AA)

def circ(img, x, y, r, col, th=-1):
    cv2.circle(img, (int(round(x)), int(round(y))), max(1, int(round(r))), col, th, AA)

def ell(img, x, y, rx, ry, col, ang=0, a0=0, a1=360, th=-1):
    cv2.ellipse(img, (int(round(x)), int(round(y))), (max(1, int(round(rx))), max(1, int(round(ry)))), ang, a0, a1, col, th, AA)

def line(img, p0, p1, col, th):
    th = max(1, int(round(th)))
    cv2.line(img, (int(round(p0[0])), int(round(p0[1]))), (int(round(p1[0])), int(round(p1[1]))), col, th, AA)

def limb(img, p0, p1, col, th):
    line(img, p0, p1, col, th)
    circ(img, p0[0], p0[1], th / 2, col); circ(img, p1[0], p1[1], th / 2, col)

def rr(img, x0, y0, x1, y1, r, col):
    x0, y0, x1, y1 = [int(round(v)) for v in (x0, y0, x1, y1)]
    r = int(max(1, min(r, (x1 - x0) // 2, (y1 - y0) // 2)))
    cv2.rectangle(img, (x0 + r, y0), (x1 - r, y1), col, -1, AA)
    cv2.rectangle(img, (x0, y0 + r), (x1, y1 - r), col, -1, AA)
    for cx, cy in ((x0 + r, y0 + r), (x1 - r, y0 + r), (x0 + r, y1 - r), (x1 - r, y1 - r)):
        cv2.circle(img, (cx, cy), r, col, -1, AA)

def rect(img, x0, y0, x1, y1, col):
    cv2.rectangle(img, (int(x0), int(y0)), (int(x1), int(y1)), col, -1)

# ---------------- text (cached) ----------------
FONTS = {
    'bold': '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf',
    'serif': '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',
}
_fc, _tc = {}, {}
def font(name, sz):
    k = (name, sz)
    if k not in _fc: _fc[k] = ImageFont.truetype(FONTS[name], sz)
    return _fc[k]

def text_img(s, sz, col, fname='bold', stroke=0, stroke_col=(0, 0, 0)):
    k = (s, sz, col, fname, stroke, stroke_col)
    if k in _tc: return _tc[k]
    f = font(fname, sz)
    d = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    bb = d.textbbox((0, 0), s, font=f, stroke_width=stroke)
    w, h = bb[2] - bb[0] + 8, bb[3] - bb[1] + 8
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((4 - bb[0], 4 - bb[1]), s, font=f, fill=(col[2], col[1], col[0], 255),
                            stroke_width=stroke, stroke_fill=(stroke_col[2], stroke_col[1], stroke_col[0], 255))
    a = np.array(im).astype(np.float32)
    res = (a[..., [2, 1, 0]], a[..., 3:4] / 255)
    _tc[k] = res
    return res

def blit_text(img, s, cx, y, sz, col, alpha=1.0, fname='bold', stroke=0, stroke_col=(0, 0, 0), scale=1.0, left=None):
    if alpha <= 0.01: return
    rgb, a = text_img(s, sz, col, fname, stroke, stroke_col)
    if scale != 1.0:
        h0, w0 = a.shape[:2]
        nw, nh = max(1, int(w0 * scale)), max(1, int(h0 * scale))
        rgb = cv2.resize(rgb, (nw, nh)); a = cv2.resize(a, (nw, nh))[..., None]
    h, w = a.shape[:2]
    x0 = int(cx - w / 2) if left is None else int(left)
    y0 = int(y - (h - (a.shape[0])) / 2) if scale == 1.0 else int(y - (h - text_img(s, sz, col, fname, stroke, stroke_col)[1].shape[0]) / 2)
    H, W = img.shape[:2]
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb: return
    sub_a = a[ya - y0:yb - y0, xa - x0:xb - x0] * alpha
    sub = rgb[ya - y0:yb - y0, xa - x0:xb - x0]
    reg = img[ya:yb, xa:xb].astype(np.float32)
    img[ya:yb, xa:xb] = (reg * (1 - sub_a) + sub * sub_a).astype(np.uint8)

def text_w(s, sz, fname='bold'):
    return text_img(s, sz, (255, 255, 255), fname)[1].shape[1]

# ---------------- character ----------------
SKIN = [C('#f2c29b'), C('#d99a6c'), C('#a86b45'), C('#ffd8b8')]
OUTL = (40, 30, 30)

ARM_POSES = {
    'idle': ((10, 4), (10, 4)),
    'wave': ((120, 30), (10, 4)),
    'point': ((92, 0), (10, 4)),
    'point2': ((10, 4), (92, 0)),
    'hips': ((40, -95), (40, -95)),
    'shrug': ((55, -105), (55, -105)),
    'think': ((18, -150), (10, 4)),
    'hold': ((20, -75), (20, -75)),
    'up': ((160, 5), (160, 5)),
    'face': ((25, -158), (25, -158)),
    'present': ((115, 10), (10, 4)),
    'present2': ((10, 4), (115, 10)),
    'finger': ((15, -150), (10, 4)),
    'cheer': ((140, 15), (140, 15)),
}

class Char:
    def __init__(self, skin, hair, hair_col, top, top2, pants, shoes=C('#3a3340'),
                 belly=1.0, mustache=False, glasses=False, hat=None, beard=False, tie=None,
                 lashes=False, brow_col=None, height=1.0):
        self.__dict__.update(locals()); del self.__dict__['self']
        self.brow_col = brow_col or shade(hair_col, 0.8)

    def draw(self, img, x, fy, s=1.0, look=0.0, mouth=0.0, blink=0.0, arms='idle', arm_anim=0.0,
             walk=0.0, walking=False, bounce=0.0, brows=0.0, blush=0.0, tilt=0.0, smile=0.4, face=1):
        s = s * self.height
        u = s
        fy = fy - bounce
        L, TH, TW = 150 * u, 175 * u, 140 * u * self.belly
        hip_y = fy - L
        sh_y = hip_y - TH + 22 * u
        neck_y = hip_y - TH
        hr = 92 * u
        hx, hy = x + tilt * 10 * u, neck_y - hr * 0.86
        # legs
        sw = math.sin(walk) if walking else 0.0
        for side, ph in ((-1, sw), (1, -sw)):
            lx = x + side * 32 * u
            foot_x = lx + ph * 38 * u
            foot_y = fy - (max(0, -ph) * 14 * u if walking else 0)
            limb(img, (lx, hip_y), (foot_x, foot_y - 12 * u), self.pants, 44 * u)
            ell(img, foot_x + side * 10 * u, foot_y - 6 * u, 32 * u, 15 * u, self.shoes)
        # torso
        tw2 = TW / 2
        pts = [(x - tw2 * 0.86, sh_y - 18 * u), (x + tw2 * 0.86, sh_y - 18 * u),
               (x + tw2, hip_y - 60 * u), (x + tw2 * 0.95, hip_y + 6 * u), (x - tw2 * 0.95, hip_y + 6 * u), (x - tw2, hip_y - 60 * u)]
        # arms (behind torso edges drawn after for front look)
        pa, pb = ARM_POSES.get(arms, ARM_POSES['idle'])
        hands = []
        for side, (a1, a2) in ((-1, pa), (1, pb)):
            if arms == 'wave' and side == -1: a2 = a2 + 25 * math.sin(arm_anim * 9)
            if arms == 'cheer': a1 = a1 + 10 * math.sin(arm_anim * 8 + side)
            if walking and arms in ('idle',):
                a1 = 10 + side * 0 + 18 * math.sin(walk + (0 if side < 0 else math.pi))
            shx, shy = x + side * (tw2 * 0.86 + 4 * u), sh_y
            r1, r2 = math.radians(a1), math.radians(a1 + a2)
            ex, ey = shx + side * math.sin(r1) * 72 * u, shy + math.cos(r1) * 72 * u
            hx2, hy2 = ex + side * math.sin(r2) * 70 * u, ey + math.cos(r2) * 70 * u
            front = hy2 < sh_y + 10 * u
            hands.append((hx2, hy2, (shx, shy, ex, ey), front))
        for hxp, hyp, (shx, shy, ex, ey), front in hands:
            if not front:
                limb(img, (shx, shy), (ex, ey), shade(self.top, 0.9), 36 * u)
                limb(img, (ex, ey), (hxp, hyp), shade(self.top, 0.9), 32 * u)
        poly(img, pts, self.top)
        # top details
        if self.top2 is not None:
            if self.tie is not None:  # suit: shirt V + tie
                poly(img, [(x - 30 * u, sh_y - 18 * u), (x + 30 * u, sh_y - 18 * u), (x, sh_y + 60 * u)], C('#f4f1ea'))
                poly(img, [(x - 9 * u, sh_y - 12 * u), (x + 9 * u, sh_y - 12 * u), (x + 12 * u, sh_y + 55 * u), (x, sh_y + 70 * u), (x - 12 * u, sh_y + 55 * u)], self.tie)
                line(img, (x - 30 * u, sh_y - 18 * u), (x - 8 * u, sh_y + 75 * u), shade(self.top, 0.75), 4 * u)
                line(img, (x + 30 * u, sh_y - 18 * u), (x + 8 * u, sh_y + 75 * u), shade(self.top, 0.75), 4 * u)
            else:  # hoodie pocket + strings
                rr(img, x - tw2 * 0.6, hip_y - 70 * u, x + tw2 * 0.6, hip_y - 20 * u, 14 * u, self.top2)
                line(img, (x - 14 * u, sh_y - 10 * u), (x - 16 * u, sh_y + 40 * u), C('#ffffff'), 4 * u)
                line(img, (x + 14 * u, sh_y - 10 * u), (x + 16 * u, sh_y + 40 * u), C('#ffffff'), 4 * u)
        for hxp, hyp, _, front in hands:
            if not front: circ(img, hxp, hyp, 19 * u, self.skin)
        self.hands = [(h[0], h[1]) for h in hands]
        # neck
        rr(img, x - 18 * u, neck_y - 20 * u, x + 18 * u, sh_y - 10 * u, 8 * u, shade(self.skin, 0.9))
        # back hair
        hc = self.hair_col
        if self.hair == 'curly':
            for i in range(11):
                a = math.pi * (0.85 + 1.3 * i / 10)
                circ(img, hx + math.cos(a) * hr * 1.05, hy - 10 * u + math.sin(a) * hr * 1.0, hr * 0.42, hc)
            for sx in (-1, 1):
                for k in range(3):
                    circ(img, hx + sx * hr * 0.98, hy + (10 + k * 38) * u, hr * 0.36, hc)
        if self.hair == 'long':
            rr(img, hx - hr * 1.05, hy - hr * 0.6, hx + hr * 1.05, hy + hr * 1.25, int(hr * 0.5), hc)
        # ears
        for sx in (-1, 1):
            circ(img, hx + sx * hr * 0.95, hy + 8 * u, 18 * u, shade(self.skin, 0.95))
        # head
        ell(img, hx, hy, hr, hr * 1.02, self.skin)
        # front hair
        if self.hair == 'short':
            poly(img, [(hx - hr * 0.98, hy - 5 * u), (hx - hr * 0.95, hy - hr * 0.55), (hx - hr * 0.5, hy - hr * 1.02),
                       (hx + hr * 0.3, hy - hr * 1.1), (hx + hr * 0.9, hy - hr * 0.75), (hx + hr * 1.0, hy - 10 * u),
                       (hx + hr * 0.82, hy - hr * 0.42), (hx + hr * 0.1, hy - hr * 0.62), (hx - hr * 0.55, hy - hr * 0.45), (hx - hr * 0.8, hy - hr * 0.2)], hc)
        elif self.hair == 'spiky':
            pts2 = [(hx - hr, hy - 5 * u)]
            for i in range(7):
                a = math.pi * (1.05 + 0.9 * i / 6)
                pts2.append((hx + math.cos(a) * hr * 1.22, hy + math.sin(a) * hr * 1.22))
                a2 = a + 0.9 * math.pi / 12
                pts2.append((hx + math.cos(a2) * hr * 0.92, hy + math.sin(a2) * hr * 0.92))
            pts2.append((hx + hr, hy - 5 * u)); pts2.append((hx + hr * 0.7, hy - hr * 0.45)); pts2.append((hx - hr * 0.7, hy - hr * 0.45))
            poly(img, pts2, hc)
        elif self.hair == 'curly':
            for i in range(7):
                a = math.pi * (1.1 + 0.8 * i / 6)
                circ(img, hx + math.cos(a) * hr * 0.75, hy - 12 * u + math.sin(a) * hr * 0.8, hr * 0.3, hc)
        elif self.hair == 'slick':
            ell(img, hx, hy - hr * 0.35, hr * 1.02, hr * 0.72, hc, 0, 180, 360)
            line(img, (hx - hr * 0.2, hy - hr * 0.95), (hx + hr * 0.6, hy - hr * 0.7), shade(hc, 1.6), 3 * u)
        elif self.hair == 'bald':
            for sx in (-1, 1):
                ell(img, hx + sx * hr * 0.86, hy - 10 * u, hr * 0.22, hr * 0.38, hc)
        elif self.hair == 'long':
            ell(img, hx, hy - hr * 0.4, hr * 1.02, hr * 0.68, hc, 0, 180, 360)
            poly(img, [(hx - hr, hy - hr * 0.35), (hx - hr * 0.2, hy - hr * 0.95), (hx + hr * 0.3, hy - hr * 0.45), (hx - hr * 0.9, hy + 10 * u)], hc)
        # face
        lk = look * 9 * u
        ey_ = hy + 2 * u
        for sx in (-1, 1):
            ex_ = hx + sx * 34 * u + tilt * 4 * u
            if blink > 0.5:
                line(img, (ex_ - 16 * u, ey_), (ex_ + 16 * u, ey_), OUTL, 4 * u)
            else:
                ell(img, ex_, ey_, 21 * u, 25 * u, (255, 255, 255))
                circ(img, ex_ + lk, ey_ + 3 * u, 12 * u, (45, 35, 40))
                circ(img, ex_ + lk + 4 * u, ey_ - 3 * u, 4 * u, (255, 255, 255))
                if self.lashes:
                    line(img, (ex_ + sx * 16 * u, ey_ - 20 * u), (ex_ + sx * 26 * u, ey_ - 28 * u), OUTL, 3 * u)
            by = ey_ - 38 * u - brows * 10 * u
            bt = brows * sx * 6 * u
            line(img, (ex_ - 16 * u, by + bt), (ex_ + 16 * u, by - bt), self.brow_col, 6 * u)
        if self.glasses:
            for sx in (-1, 1):
                circ(img, hx + sx * 34 * u, ey_, 30 * u, (50, 40, 40), int(5 * u))
            line(img, (hx - 6 * u, ey_), (hx + 6 * u, ey_), (50, 40, 40), 4 * u)
        # nose
        ell(img, hx + tilt * 5 * u, hy + 30 * u, 9 * u, 7 * u, shade(self.skin, 0.85))
        if blush > 0:
            for sx in (-1, 1):
                ov = img.copy(); ell(ov, hx + sx * 52 * u, hy + 35 * u, 20 * u, 11 * u, C('#ff6f7d'))
                cv2.addWeighted(ov, 0.55 * blush, img, 1 - 0.55 * blush, 0, img)
        # mouth
        my = hy + 58 * u
        if mouth > 0.08:
            h = 6 * u + 26 * u * min(1, mouth)
            ell(img, hx, my, 20 * u, h * 0.5, C('#7a2633'))
            ell(img, hx, my + h * 0.22, 12 * u, h * 0.22, C('#e36a7a'))
        else:
            if smile >= 0:
                ell(img, hx, my - 8 * u, 18 * u, 10 * u + smile * 6 * u, (60, 40, 120), 0, 20, 160, int(4 * u))
            else:
                ell(img, hx, my + 4 * u, 16 * u, 8 * u, (60, 40, 120), 0, 200, 340, int(4 * u))
        if self.mustache:
            poly(img, [(hx - 38 * u, my - 4 * u), (hx - 18 * u, my - 20 * u), (hx, my - 14 * u), (hx + 18 * u, my - 20 * u), (hx + 38 * u, my - 4 * u),
                       (hx + 20 * u, my - 10 * u), (hx, my - 6 * u), (hx - 20 * u, my - 10 * u)], self.hair_col)
        if self.beard:
            ell(img, hx, hy + 52 * u, hr * 0.8, hr * 0.55, self.hair_col, 0, 0, 180)
            ell(img, hx, my, 18 * u, 8 * u, C('#7a2633') if mouth > 0.08 else self.skin)
        # hat
        if self.hat == 'fedora':
            hc2 = C('#2b2b33')
            ell(img, hx, hy - hr * 0.62, hr * 1.35, hr * 0.2, hc2)
            poly(img, [(hx - hr * 0.78, hy - hr * 0.62), (hx - hr * 0.7, hy - hr * 1.25), (hx, hy - hr * 1.12), (hx + hr * 0.7, hy - hr * 1.25), (hx + hr * 0.78, hy - hr * 0.62)], hc2)
            rect(img, hx - hr * 0.78, hy - hr * 0.82, hx + hr * 0.78, hy - hr * 0.66, C('#8c2f39'))
        elif self.hat == 'police':
            hc2 = C('#1f2d5c')
            rr(img, hx - hr * 0.95, hy - hr * 1.25, hx + hr * 0.95, hy - hr * 0.62, 18 * u, hc2)
            ell(img, hx, hy - hr * 0.6, hr * 1.0, hr * 0.16, C('#111111'))
            circ(img, hx, hy - hr * 0.95, 14 * u, C('#f2c94c'))
        for hxp, hyp, (shx, shy, ex, ey), front in hands:
            if front:
                limb(img, (shx, shy), (ex, ey), shade(self.top, 0.9), 36 * u)
                limb(img, (ex, ey), (hxp, hyp), shade(self.top, 0.9), 32 * u)
                circ(img, hxp, hyp, 19 * u, self.skin)
        return (hx, hy, hr)

# ---------------- props ----------------
def money_bag(img, x, y, s, col=C('#c9a15b')):
    ell(img, x, y, 55 * s, 60 * s, col)
    poly(img, [(x - 22 * s, y - 52 * s), (x + 22 * s, y - 52 * s), (x + 34 * s, y - 85 * s), (x - 34 * s, y - 85 * s)], col)
    line(img, (x - 24 * s, y - 55 * s), (x + 24 * s, y - 55 * s), shade(col, 0.6), 6 * s)
    blit_text(img, '$', x, y - 30 * s, int(60 * s), shade(col, 0.45))

def bill(img, x, y, s, ang=0):
    w, h = 70 * s, 34 * s
    c, sn = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    pts = [(x + dx * c - dy * sn, y + dx * sn + dy * c) for dx, dy in ((-w, -h), (w, -h), (w, h), (-w, h))]
    poly(img, pts, C('#7cc47f'))
    circ(img, x, y, 13 * s, C('#4f9a55'))

def suitcase(img, x, y, s):
    rr(img, x - 70 * s, y - 50 * s, x + 70 * s, y + 50 * s, 10 * s, C('#8a5a3c'))
    rr(img, x - 25 * s, y - 70 * s, x + 25 * s, y - 50 * s, 6 * s, C('#5a3a28'))
    rect(img, x - 70 * s, y - 4 * s, x + 70 * s, y + 4 * s, C('#5a3a28'))

def eiffel(img, cx, base_y, h, col=C('#5b4a63'), lw=3):
    w = h * 0.42
    top = (cx, base_y - h)
    def X(t, side):  # leg outline x at height fraction t (0 bottom, 1 top)
        return cx + side * (w / 2) * (1 - t) ** 1.9
    pts_l = [(X(t, -1), base_y - t * h) for t in np.linspace(0, 1, 30)]
    pts_r = [(X(t, 1), base_y - t * h) for t in np.linspace(1, 0, 30)]
    poly(img, pts_l + pts_r, col)
    # arch cutout
    bg_hole = None
    ell(img, cx, base_y, w * 0.26, h * 0.16, (0, 0, 0), 0, 180, 360) if False else None
    # platforms
    for t, ww in ((0.24, 1.15), (0.5, 1.2)):
        y = base_y - t * h
        x0, x1 = X(t, -1) * 1 - 0, X(t, 1)
        rect(img, x0 - (x1 - x0) * 0.08, y - 6 * h / 600, x1 + (x1 - x0) * 0.08, y + 6 * h / 600, shade(col, 0.75))
    circ(img, cx, base_y - h - 6, 4, shade(col, 0.75))
    line(img, (cx, base_y - h), (cx, base_y - h - 30 * h / 600), shade(col, 0.75), 3)
    # lattice
    for t in np.linspace(0.04, 0.92, 14):
        y = base_y - t * h; y2 = base_y - (t + 0.06) * h
        line(img, (X(t, -1), y), (X(t + 0.06, 1), y2), shade(col, 1.35), lw)
        line(img, (X(t, 1), y), (X(t + 0.06, -1), y2), shade(col, 1.35), lw)
