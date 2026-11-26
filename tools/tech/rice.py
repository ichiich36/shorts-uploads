"""What-if short: 1 grain of rice doubled on every chessboard square. Tech-niche look.
python3 rice.py stills t1 t2 ... | video | audio
"""
import sys, os, math, subprocess, wave
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, SR = 1080, 1920, 30, 44100
FB = '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
CYAN = (255, 230, 60)      # BGR
GREEN = (170, 255, 90)
GOLD = (80, 210, 255)
WHITE = (255, 255, 255)

# ---------- timeline ----------
INTRO = 2.2
MILE = {8: ("128 grains", "a pinch of rice"),
        15: ("16,384 grains", "about one bag of rice (0.4 kg)"),
        22: ("2.1 million grains", "about as heavy as a person"),
        30: ("537 million grains", "a full truck (13 t)"),
        40: ("550 billion grains", "a cargo ship (13,700 t)"),
        50: ("563 trillion grains", "14 million tonnes"),
        }
PAUSE = 2.4
T = []   # start time of each square 1..64
t = INTRO
for n in range(1, 65):
    T.append(t)
    d = max(0.17, 0.85 * 0.88 ** (n - 1))
    t += d
    if n in MILE: t += PAUSE
T_END_SQ = t
FINAL = T_END_SQ + 0.4
DURATION = FINAL + 8.5

def square_at(tt):
    n = 0
    for i, s in enumerate(T):
        if tt >= s: n = i + 1
    return n

def fmt(n):
    return f"{n:,}"

# ---------- layout ----------
CELL = 100
BX, BY = (W - 8 * CELL) // 2, 700
def cell_xy(n):  # n 1..64, snake order bottom-left start like classic
    i = n - 1
    row = i // 8; col = i % 8
    if row % 2: col = 7 - col
    return BX + col * CELL, BY + (7 - row) * CELL

_fc = {}
def font(sz):
    if sz not in _fc: _fc[sz] = ImageFont.truetype(FB, sz)
    return _fc[sz]

def txt(img, s, y, sz, col, alpha=1.0, x=None):
    """draw centered text onto BGR float img via PIL layer"""
    if alpha <= 0: return
    f = font(sz)
    tmp = Image.new('L', (1, 1)); d = ImageDraw.Draw(tmp)
    bb = d.textbbox((0, 0), s, font=f)
    w, h = bb[2] - bb[0] + 20, bb[3] - bb[1] + 30
    m = Image.new('L', (w, h), 0); ImageDraw.Draw(m).text((10 - bb[0], 10 - bb[1]), s, font=f, fill=255)
    a = np.array(m).astype(np.float32)[..., None] / 255 * alpha
    x0 = int((W - w) / 2) if x is None else int(x - w / 2)
    y0 = int(y)
    x1, y1 = min(W, x0 + w), min(H, y0 + h)
    a = a[:y1 - y0, :x1 - x0]
    sh = img[y0 + 4:y1 + 4, x0:x1]
    if sh.shape[:2] == a.shape[:2]:
        img[y0 + 4:y1 + 4, x0:x1] = sh * (1 - a * 0.6)
    reg = img[y0:y1, x0:x1]
    img[y0:y1, x0:x1] = reg * (1 - a) + np.array(col, np.float32) * a

def hsh(*v):
    h = 2166136261
    for x in v: h = ((h ^ (int(x * 997) & 0xffffffff)) * 16777619) & 0xffffffff
    return h / 0xffffffff

BG = None
def bg():
    global BG
    if BG is None:
        y = np.linspace(0, 1, H)[:, None, None]
        BG = (np.array([22, 8, 6]) + np.array([30, 14, 10]) * y).repeat(W, 1).astype(np.float32)
        rng = np.random.default_rng(3)
        for _ in range(140):
            x, yy = rng.integers(0, W), rng.integers(0, H)
            cv2.circle(BG, (int(x), int(yy)), int(rng.integers(1, 3)), (90, 80, 80), -1)
    return BG

def ease(x): x = min(1, max(0, x)); return 1 - (1 - x) ** 3

# ---------- illustrations ----------
_tex = None
def rice_tex():
    global _tex
    if _tex is None:
        _tex = np.full((H, W, 3), (150, 170, 180), np.float32)
        rng = np.random.default_rng(11)
        for _ in range(60000):
            x, y = int(rng.integers(0, W)), int(rng.integers(0, H))
            c = int(rng.integers(200, 255))
            cv2.ellipse(_tex, (x, y), (6, 2), float(rng.uniform(0, 180)), 0, 360, (c - 10, c, c), -1, cv2.LINE_AA)
    return _tex
_sand = None
def sand_tex():
    global _sand
    if _sand is None:
        _sand = np.full((H, W, 3), (70, 150, 200), np.float32)
        rng = np.random.default_rng(5)
        for _ in range(90000):
            x, y = int(rng.integers(0, W)), int(rng.integers(0, H))
            c = rng.uniform(0.7, 1.15)
            _sand[y, x] = np.clip(np.array([90, 185, 235]) * c, 0, 255)
    return _sand

def fill_poly(img, poly, prog, al, tex=None):
    poly = np.array(poly, np.int32)
    m = np.zeros((H, W), np.uint8); cv2.fillPoly(m, [poly], 255)
    y0, y1 = poly[:, 1].min(), poly[:, 1].max()
    lvl = int(y1 - (y1 - y0) * prog)
    m[:max(0, lvl)] = 0
    sel = m > 0
    t = rice_tex() if tex is None else tex
    img[sel] = img[sel] * (1 - al) + t[sel] * al

def outline(glow, img, poly, col, al, th=4):
    poly = np.array(poly, np.int32)
    cv2.polylines(img, [poly], True, tuple(c * al for c in col), th, cv2.LINE_AA)
    cv2.polylines(glow, [poly], True, tuple(c * 0.8 * al for c in col), th + 2, cv2.LINE_AA)

def il_pinch(img, glow, y, p, al):
    cx = W // 2; base = y + 300
    heap = [(cx - 110, base), (cx - 70, base - 45), (cx - 20, base - 70), (cx + 20, base - 70), (cx + 70, base - 45), (cx + 110, base)]
    fill_poly(img, heap, p, al)
    cv2.line(img, (cx - 260, base + 2), (cx + 260, base + 2), tuple(c * al for c in CYAN), 3)

def il_bag(img, glow, y, p, al):
    cx = W // 2
    bag = [(cx - 150, y + 330), (cx - 170, y + 120), (cx - 90, y + 60), (cx - 40, y + 30), (cx + 40, y + 30), (cx + 90, y + 60), (cx + 170, y + 120), (cx + 150, y + 330)]
    fill_poly(img, bag, p, al)
    outline(glow, img, bag, CYAN, al)
    txt(img, "RICE 0.4 kg", y + 190, 40, (40, 40, 200), al * min(1, p * 2))

def il_scale(img, glow, y, p, al):
    cx = W // 2; py = y + 170
    tilt = (1 - p) * 0.25
    lx, rx = cx - 260, cx + 260
    ly, ry = py - int(260 * math.sin(tilt)), py + int(260 * math.sin(tilt))
    ly, ry = py + int(260 * math.sin(tilt)), py - int(260 * math.sin(tilt))
    cv2.line(img, (cx, py), (cx, y + 340), tuple(c * al for c in WHITE), 5)
    cv2.line(img, (lx, ly), (rx, ry), tuple(c * al for c in CYAN), 6, cv2.LINE_AA)
    # person on left pan
    px, pb = lx, ly - 5
    col = tuple(c * al for c in WHITE)
    cv2.circle(img, (px, pb - 140), 22, col, 4, cv2.LINE_AA)
    cv2.line(img, (px, pb - 118), (px, pb - 50), col, 5); cv2.line(img, (px, pb - 50), (px - 25, pb), col, 5); cv2.line(img, (px, pb - 50), (px + 25, pb), col, 5)
    cv2.line(img, (px, pb - 100), (px - 35, pb - 70), col, 5); cv2.line(img, (px, pb - 100), (px + 35, pb - 70), col, 5)
    # rice pile on right pan
    heap = [(rx - 100, ry - 3), (rx - 70, ry - 80), (rx - 20, ry - 120), (rx + 20, ry - 120), (rx + 70, ry - 80), (rx + 100, ry - 3)]
    fill_poly(img, heap, p, al)

def il_truck(img, glow, y, p, al):
    x0 = 170; base = y + 300
    bed = [(x0, base - 200), (x0 + 520, base - 200), (x0 + 520, base - 40), (x0, base - 40)]
    fill_poly(img, bed, p, al)
    outline(glow, img, bed, CYAN, al)
    cab = [(x0 + 540, base - 150), (x0 + 650, base - 150), (x0 + 720, base - 90), (x0 + 720, base - 40), (x0 + 540, base - 40)]
    outline(glow, img, cab, CYAN, al)
    for wx in (x0 + 100, x0 + 420, x0 + 640):
        cv2.circle(img, (wx, base - 10), 38, tuple(c * al for c in WHITE), 5, cv2.LINE_AA)

def il_ship(img, glow, y, p, al):
    base = y + 280
    hull = [(130, base - 150), (950, base - 150), (880, base), (200, base)]
    cargo = [(200, base - 260), (820, base - 260), (820, base - 150), (200, base - 150)]
    fill_poly(img, cargo, p, al)
    outline(glow, img, cargo, GOLD, al, 3)
    outline(glow, img, hull, CYAN, al)
    cv2.rectangle(img, (840, base - 250), (900, base - 150), tuple(c * al for c in WHITE), 4)
    for i in range(3):
        yy = base + 25 + i * 18
        pts = np.array([(x, yy + int(6 * math.sin(x / 40 + i))) for x in range(100, 980, 10)], np.int32)
        cv2.polylines(img, [pts], False, tuple(c * al * 0.8 for c in (255, 160, 60)), 3, cv2.LINE_AA)

def il_mountain(img, glow, y, p, al):
    base = y + 340
    mt = [(160, base), (420, y + 40), (540, y + 120), (640, y + 10), (920, base)]
    fill_poly(img, mt, p, al)
    outline(glow, img, mt, CYAN, al)
    # tiny person for scale
    px = 900; col = tuple(c * al for c in WHITE)
    cv2.circle(img, (px, base - 34), 6, col, 2); cv2.line(img, (px, base - 28), (px, base - 10), col, 2)
    cv2.line(img, (px, base - 10), (px - 6, base), col, 2); cv2.line(img, (px, base - 10), (px + 6, base), col, 2)

def beach(img, glow, y, p, al):
    # sea + sand that grows from left to right
    sea = [(80, y), (1000, y), (1000, y + 170), (80, y + 230)]
    ov = img.copy(); cv2.fillPoly(ov, [np.array(sea, np.int32)], (120, 60, 20))
    img[:] = img * (1 - al * 0.8) + ov * al * 0.8
    for i in range(4):
        yy = y + 60 + i * 40
        pts = np.array([(x, yy + int(10 * math.sin(x / 50 + i * 1.3))) for x in range(80, 1000, 10)], np.int32)
        cv2.polylines(img, [pts], False, tuple(c * al for c in (255, 200, 120)), 3, cv2.LINE_AA)
    sand = [(80, y + 230), (1000, y + 170), (1000, y + 400), (80, y + 400)]
    xr = int(80 + 920 * p)
    sand_c = [(80, y + 230), (xr, y + 230 - int(60 * (xr - 80) / 920)), (xr, y + 400), (80, y + 400)]
    fill_poly(img, sand_c, 1.0, al, sand_tex())
    outline(glow, img, sand, GOLD, al * 0.6, 2)

ILLU = {8: il_pinch, 15: il_bag, 22: il_scale, 30: il_truck, 40: il_ship, 50: il_mountain}

def frame(tt):
    img = bg().copy()
    glow = np.zeros_like(img)
    n = square_at(tt)

    # title
    txt(img, "1 grain of rice.", 245, 64, WHITE)
    txt(img, "Double it on every square.", 330, 50, (200, 200, 200))

    # board
    for k in range(1, 65):
        x, y = cell_xy(k)
        base = (40, 30, 30) if ((k - 1) // 8 + (k - 1) % 8) % 2 else (55, 42, 40)
        cv2.rectangle(img, (x + 2, y + 2), (x + CELL - 2, y + CELL - 2), base, -1)
        if k <= n:
            age = tt - T[k - 1]
            lvl = (k - 1) / 63
            col = tuple(int(CYAN[i] * (1 - lvl) + GOLD[i] * lvl) for i in range(3))
            fill = 0.25 + 0.55 * lvl
            inner = tuple(int(c * fill) for c in col)
            cv2.rectangle(img, (x + 4, y + 4), (x + CELL - 4, y + CELL - 4), inner, -1)
            pop = max(0.0, 1 - age / 0.35)
            cv2.rectangle(glow, (x + 4, y + 4), (x + CELL - 4, y + CELL - 4), tuple(c * (0.35 + 1.2 * pop) for c in col), 3)
            if k <= 7:   # draw actual grains
                cnt = 2 ** (k - 1)
                for g in range(cnt):
                    gx = x + 14 + hsh(k, g) * (CELL - 28)
                    gy = y + 14 + hsh(g, k, 7) * (CELL - 28)
                    ang = hsh(k, g, 3) * 180
                    cv2.ellipse(img, (int(gx), int(gy)), (7, 3), ang, 0, 360, (235, 245, 250), -1, cv2.LINE_AA)
            else:
                # pile: number of digits shown as label
                lab = f"2^{k-1}"
                f = font(22)
            # current square highlight
            if k == n:
                cv2.rectangle(glow, (x, y), (x + CELL, y + CELL), (255, 255, 255), 4)
    # labels on later squares (cheap: only text for filled squares > 7)
    for k in range(8, n + 1):
        x, y = cell_xy(k)
        txt(img, f"2^{k-1}", y + 28, 24, (230, 230, 230), 0.85, x=x + CELL / 2)

    # counter
    if n >= 1:
        cnt = 2 ** (n - 1)
        txt(img, f"Square {n}", 440, 40, (190, 190, 190))
        s = fmt(cnt)
        sz = 74 if len(s) < 14 else (60 if len(s) < 20 else 48)
        txt(img, s + " grains", 500, sz, GREEN)
    else:
        txt(img, "Guess the total before it ends!", 470, 44, GREEN, ease((tt - 0.2) / 0.4))

    # milestone popup with illustration
    for k, (a, b) in MILE.items():
        st = T[k - 1] + 0.15
        if st <= tt < st + PAUSE + 0.1:
            p = tt - st
            al = min(1, p / 0.2) * min(1, (st + PAUSE + 0.1 - tt) / 0.25)
            yb = BY - 10
            glow[yb:yb + 561, 70:W - 69] *= (1 - al)
            ov = img.copy()
            cv2.rectangle(ov, (70, yb), (W - 70, yb + 560), (28, 16, 12), -1)
            img[:] = img * (1 - 0.9 * al) + ov * 0.9 * al
            cv2.rectangle(glow, (70, yb), (W - 70, yb + 560), tuple(c * al for c in GOLD), 4)
            txt(img, f"Square {k}: {a}", yb + 25, 44, WHITE, al)
            txt(img, "= " + b, yb + 95, 46, GOLD, al)
            prog = ease((p - 0.25) / 1.4)
            ILLU[k](img, glow, yb + 180, prog, al)
    # final reveal
    if tt >= FINAL:
        p = tt - FINAL
        al = ease(p / 0.5)
        dark = img * (1 - 0.9 * al)
        glow *= (1 - al)
        img[:] = dark
        txt(img, "Total on the board:", 545, 46, (210, 210, 210), al)
        txt(img, "18,446,744,073,709,551,615", 615, 54, GREEN, ease((p - 0.3) / 0.5))
        txt(img, "grains of rice  (~460 billion tonnes)", 700, 38, GREEN, ease((p - 0.3) / 0.5))
        bal = ease((p - 1.6) / 0.5)
        if bal > 0:
            beach(img, glow, 790, ease((p - 1.8) / 2.0), bal)
        txt(img, "More grains than all the sand", 1225, 50, WHITE, ease((p - 3.4) / 0.5))
        txt(img, "on every beach on Earth*", 1292, 50, WHITE, ease((p - 3.4) / 0.5))
        txt(img, "*common scientific estimate: ~7.5 quintillion", 1365, 26, (170, 170, 170), ease((p - 3.8) / 0.5))
        txt(img, "Did you guess that high?", 1415, 44, CYAN, ease((p - 5.2) / 0.5))

    g = cv2.GaussianBlur(cv2.resize(glow, (W // 4, H // 4)), (0, 0), 5)
    img = img + glow + cv2.resize(g, (W, H)) * 1.6
    return np.clip(img, 0, 255).astype(np.uint8)

# ---------- audio ----------
def audio(path):
    n = int((DURATION + 0.5) * SR); L = np.zeros(n); R = np.zeros(n)
    tt = np.arange(n) / SR
    # soft pad (Am - F - C - G), 2 bars of 4 s
    chords = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
    for i in range(int(DURATION / 4) + 1):
        c = chords[i % 4]; s = int(i * 4 * SR); e = min(n, s + int(4.6 * SR))
        seg = np.arange(e - s) / SR
        env = np.minimum(1, seg / 0.8) * np.minimum(1, (4.6 - seg) / 0.8)
        for m in c:
            f = 440 * 2 ** ((m - 69) / 12)
            for det in (-0.003, 0.003):
                v = np.sin(2 * np.pi * f * (1 + det) * seg) * 0.5 + 0.2 * np.sin(2 * np.pi * 2 * f * seg)
                L[s:e] += v * env * 0.03; R[s:e] += np.roll(v, 50)[:len(seg)] * env * 0.03
    # soft kick pulse at 120 bpm after intro, builds
    for b in np.arange(INTRO, T_END_SQ, 0.5):
        s = int(b * SR); seg = np.arange(int(0.25 * SR)) / SR
        k = np.sin(2 * np.pi * (50 + 80 * np.exp(-seg * 30)) * seg) * np.exp(-seg * 14) * 0.25
        e = min(n, s + len(k)); L[s:e] += k[:e - s]; R[s:e] += k[:e - s]
    # tick per square, rising pitch
    for k in range(1, 65):
        s = int(T[k - 1] * SR); f = 400 * 2 ** ((k - 1) / 20)
        seg = np.arange(int(0.12 * SR)) / SR
        v = np.sin(2 * np.pi * f * seg) * np.exp(-seg * 40) * 0.22
        e = min(n, s + len(v)); L[s:e] += v[:e - s]; R[s:e] += v[:e - s]
    # milestone chime
    for k in MILE:
        s = int((T[k - 1] + 0.15) * SR); seg = np.arange(int(1.0 * SR)) / SR
        v = sum(np.sin(2 * np.pi * f * seg) for f in (880, 1320, 1760)) * np.exp(-seg * 5) * 0.08
        e = min(n, s + len(v)); L[s:e] += v[:e - s]; R[s:e] += v[:e - s]
    # final: riser + boom
    s = int((FINAL - 1.2) * SR); seg = np.arange(int(1.2 * SR)) / SR
    rng = np.random.default_rng(1)
    rz = rng.standard_normal(len(seg)) * (seg / 1.2) ** 2 * 0.12
    L[s:s + len(rz)] += rz; R[s:s + len(rz)] += rz
    s = int(FINAL * SR); seg = np.arange(int(2.5 * SR)) / SR
    boom = np.sin(2 * np.pi * (40 + 60 * np.exp(-seg * 8)) * seg) * np.exp(-seg * 2.2) * 0.7
    L[s:s + len(boom)] += boom; R[s:s + len(boom)] += boom
    st = np.stack([L, R], 1)
    endi = int(DURATION * SR); fade = int(1.5 * SR)
    st[endi - fade:endi] *= np.linspace(1, 0, fade)[:, None]
    st = st[:endi]; st /= np.abs(st).max() * 1.1
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())

if __name__ == '__main__':
    os.makedirs('out', exist_ok=True)
    m = sys.argv[1]
    if m == 'stills':
        for s in sys.argv[2:]: cv2.imwrite(f'out/s_{s}.png', frame(float(s)))
        print('dur', DURATION, 'final', FINAL, {k: round(T[k-1], 2) for k in MILE})
    elif m == 'audio':
        audio('out/audio.wav')
    elif m == 'video':
        nf = int(DURATION * FPS)
        p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS),
                              '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', 'out/v_tmp.mp4'], stdin=subprocess.PIPE)
        for i in range(nf): p.stdin.write(frame(i / FPS).tobytes())
        p.stdin.close(); p.wait(); os.replace('out/v_tmp.mp4', 'out/video.mp4')
