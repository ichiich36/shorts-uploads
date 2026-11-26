"""Satisfying short: a ball breaks out of spinning rings, one gap at a time.

python3 rings.py sim | stills t... | audio out.wav | range a b out.mp4
"""
import colorsys
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
CX, CY = 540.0, 1000.0
NR = int(os.environ.get("NR", 10))
R_IN, R_OUT = 105.0, 455.0
RADII = [R_IN + k * (R_OUT - R_IN) / (NR - 1) for k in range(NR)]
GAP_DEG = 46.0
BALL_R = 17.0
G = 1300.0
VMIN, VMAX = 950.0, 1500.0
SEED = int(os.environ.get("SEED", 7))
OUTRO = 2.6
SH = 4
SC = 1 << SH

rng = np.random.default_rng(SEED)
OMEGA = [(1 if k % 2 == 0 else -1) * (0.9 + 0.12 * k + 0.25 * rng.random()) for k in range(NR)]
PHASE = [rng.random() * 2 * math.pi for k in range(NR)]


def gap_center(k, t):
    return PHASE[k] + OMEGA[k] * t


def angdiff(a, b):
    return (a - b + math.pi) % (2 * math.pi) - math.pi


# ---------------------------------------------------------------- simulation
def simulate():
    dt = 1 / 2400
    x, y = 0.0, -20.0
    a0 = rng.random() * 2 * math.pi
    vx, vy = 1000 * math.cos(a0), 1000 * math.sin(a0) - 300
    t = 0.0
    cur = 0
    frames, bounces, breaks = [], [], []
    nf = 0.0
    escaped = None
    while True:
        while t >= nf - 1e-9:
            frames.append((x, y, cur))
            nf += 1 / FPS
        vy += G * dt
        x += vx * dt
        y += vy * dt
        t += dt
        if escaped is not None:
            if t - escaped > OUTRO:
                return frames, bounces, breaks, escaped
            continue
        R = RADII[cur]
        d = math.hypot(x, y)
        if d > R - BALL_R:
            ang = math.atan2(y, x)
            half = math.radians(GAP_DEG) / 2 - math.asin(BALL_R / R)
            if abs(angdiff(ang, gap_center(cur, t))) < half:
                breaks.append((t, cur, x, y))
                cur += 1
                if cur == NR:
                    escaped = t
                continue
            nx, ny = x / d, y / d
            vn = vx * nx + vy * ny
            if vn > 0:
                vx -= 2 * vn * nx
                vy -= 2 * vn * ny
                # tiny tangential kick so it never settles into a loop
                vx += -ny * 25 * math.sin(t * 7.3)
                vy += nx * 25 * math.sin(t * 7.3)
                sp = math.hypot(vx, vy)
                tgt = min(VMAX, max(VMIN, sp))
                vx, vy = vx / sp * tgt, vy / sp * tgt
                bounces.append((t, x, y, cur))
            x, y = nx * (R - BALL_R), ny * (R - BALL_R)
        if t > 120:
            return frames, bounces, breaks, None


FRAMES, BOUNCES, BREAKS, T_END = simulate()
N_FRAMES = len(FRAMES)
DUR = N_FRAMES / FPS
BREAK_T = {k: t for (t, k, _, _) in BREAKS}


def hue_col(h, s=0.75, v=1.0):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


def ring_col(k):
    return hue_col(0.0 + k / NR * 0.85)


# shards: each ring becomes ~28 arc pieces flying outward
SHARDS = {}
for k in range(NR):
    tb = BREAK_T.get(k)
    if tb is None:
        continue
    r2 = np.random.default_rng(100 + k)
    pcs = []
    gc = gap_center(k, tb)
    n = 26
    span = 2 * math.pi - math.radians(GAP_DEG)
    for j in range(n):
        a = gc + math.radians(GAP_DEG) / 2 + span * (j + 0.5) / n
        sp = 260 + 380 * r2.random()
        pcs.append(dict(a=a, len=span / n * 0.8, vx=math.cos(a) * sp + r2.normal() * 120,
                        vy=math.sin(a) * sp - 250 + r2.normal() * 120, rot=r2.normal() * 9, R=RADII[k]))
    SHARDS[k] = pcs


# ---------------------------------------------------------------- drawing
def P(x, y):
    return (int(round(x * SC)), int(round(y * SC)))


def circ(img, x, y, r, c, th=-1):
    cv2.circle(img, P(x, y), max(1, int(round(r * SC))), c, th, cv2.LINE_AA, SH)


def _font(size):
    for f in ["/usr/share/fonts/truetype/noto/NotoSans-Black.ttf",
              "/usr/share/fonts/truetype/noto/NotoSans-ExtraBold.ttf",
              "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    raise FileNotFoundError("font")


_spr = {}


def sprite(text, size, col=(245, 245, 245)):
    key = (text, size, col)
    if key not in _spr:
        f = _font(size)
        x0, y0, x1, y1 = f.getbbox(text)
        im = Image.new("RGBA", (x1 - x0 + 20, y1 - y0 + 20), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((10 - x0, 10 - y0), text, font=f, fill=col + (255,))
        _spr[key] = np.asarray(im).astype(np.float32)
    return _spr[key]


def blit(frame, spr, cx, cy, a=1.0, scale=1.0):
    if scale != 1.0:
        h, w = spr.shape[:2]
        im = Image.fromarray(spr.astype(np.uint8), "RGBA").resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.BILINEAR)
        spr = np.asarray(im).astype(np.float32)
    h, w = spr.shape[:2]
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb:
        return
    s = spr[ya - y0:yb - y0, xa - x0:xb - x0]
    al = s[..., 3:4] / 255.0 * a
    reg = frame[ya:yb, xa:xb].astype(np.float32)
    frame[ya:yb, xa:xb] = (reg * (1 - al) + s[..., :3] * al).astype(np.uint8)


def make_bg():
    t = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    top, bot = np.array([14, 14, 24], np.float32), np.array([5, 5, 9], np.float32)
    col = top * (1 - t) + bot * t
    return np.repeat(col[:, None, :], W, axis=1).reshape(H, W, 3).astype(np.uint8)


BG = make_bg()


def arc(f, R, a_from, a_to, col, th):
    cv2.ellipse(f, P(CX, CY), (int(R * SC), int(R * SC)), 0, math.degrees(a_from), math.degrees(a_to), col, th, cv2.LINE_AA, SH)


def render_frame(i):
    t = i / FPS
    x, y, cur = FRAMES[i]
    f = BG.copy()
    glow = np.zeros_like(f)
    # rings
    for k in range(NR):
        tb = BREAK_T.get(k)
        if tb is not None and t >= tb:
            continue
        gc = gap_center(k, t)
        g2 = math.radians(GAP_DEG) / 2
        col = ring_col(k)
        active = k == cur
        th = 11 if active else 8
        arc(glow, RADII[k], gc + g2, gc + 2 * math.pi - g2, col, th + 14)
        arc(f, RADII[k], gc + g2, gc + 2 * math.pi - g2, col if active else tuple(int(c * 0.8) for c in col), th)
    # shards
    for k, pcs in SHARDS.items():
        tb = BREAK_T[k]
        dt = t - tb
        if dt < 0 or dt > 1.6:
            continue
        al = max(0.0, 1 - dt / 1.6)
        col = tuple(int(c * al) for c in ring_col(k))
        for p in pcs:
            ox = p["vx"] * dt
            oy = p["vy"] * dt + 0.5 * G * dt * dt
            mx = CX + math.cos(p["a"]) * p["R"] + ox
            my = CY + math.sin(p["a"]) * p["R"] + oy
            ang = p["a"] + math.pi / 2 + p["rot"] * dt
            hl = p["len"] * p["R"] / 2
            dx, dy = math.cos(ang) * hl, math.sin(ang) * hl
            cv2.line(f, P(mx - dx, my - dy), P(mx + dx, my + dy), col, 7, cv2.LINE_AA, SH)
    # flash at break
    for (tb, k, bx, by) in BREAKS:
        dt = t - tb
        if 0 <= dt < 0.25:
            circ(glow, CX + bx, CY + by, 40 + 260 * dt, (255, 255, 255), 6)
    # ball trail
    for j in range(10, 0, -1):
        if i - j < 0:
            continue
        px, py, _ = FRAMES[i - j]
        a = (1 - j / 11) * 0.5
        circ(f, CX + px, CY + py, BALL_R * (1 - j / 14), tuple(int(255 * a) for _ in range(3)))
    circ(glow, CX + x, CY + y, BALL_R + 10, (255, 255, 255))
    glow = cv2.GaussianBlur(glow, (0, 0), 14)
    f = cv2.add(f, (glow * 0.55).astype(np.uint8))
    circ(f, CX + x, CY + y, BALL_R, (255, 255, 255))
    # HUD
    blit(f, sprite("ESCAPE THE RINGS", 92), W / 2, 260)
    left = NR - cur
    blit(f, sprite("Can the ball break free?", 54, (200, 200, 212)), W / 2, 365, min(1.0, max(0.0, (3.5 - t) / 0.5)))
    if T_END is None or t < T_END:
        pop = 1.0
        if cur > 0:
            tb = BREAK_T[cur - 1]
            pop = 1 + 0.35 * max(0.0, 1 - (t - tb) / 0.25)
        blit(f, sprite(f"RINGS LEFT  {left}", 66, ring_col(min(cur, NR - 1))), W / 2, 1590, 1.0, pop)
        blit(f, sprite(f"{t:4.1f}s", 48, (170, 170, 185)), W / 2, 1680)
    else:
        k = min(1.0, (t - T_END) / 0.25)
        pop = 1 + 0.15 * max(0.0, 1 - (t - T_END) / 0.3)
        blit(f, sprite("ESCAPED!", 160, (255, 210, 70)), W / 2, 1590, k, pop)
        blit(f, sprite(f"in {T_END:.1f} seconds", 60), W / 2, 1720, k)
    return f


# ---------------------------------------------------------------- audio
SR = 48000
SCALE = [0, 2, 4, 7, 9]  # major pentatonic


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def audio(out):
    from scipy.io import wavfile
    from scipy.signal import butter, lfilter
    n = int((DUR + 0.6) * SR)
    L = np.zeros(n)
    Rr = np.zeros(n)
    r2 = np.random.default_rng(3)

    def add(sig, t0, pan, gain):
        i0 = int(t0 * SR)
        if i0 >= n:
            return
        sig = sig[: n - i0] * gain
        a = (pan + 1) * math.pi / 4
        L[i0:i0 + len(sig)] += sig * math.cos(a)
        Rr[i0:i0 + len(sig)] += sig * math.sin(a)

    def bell(f, dur=1.0):
        tt = np.arange(int(SR * dur)) / SR
        env = np.exp(-tt * 6.0) * np.minimum(1, tt / 0.003)
        return (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt) * np.exp(-tt * 10)
                + 0.1 * np.sin(2 * np.pi * 3.01 * f * tt) * np.exp(-tt * 16)) * env

    def glass():
        dur = 1.1
        tt = np.arange(int(SR * dur)) / SR
        noise = r2.normal(size=len(tt))
        b, a = butter(2, [3000 / (SR / 2), 12000 / (SR / 2)], "band")
        s = lfilter(b, a, noise) * np.exp(-tt * 9) * 1.6
        # crackle: random short ticks
        for _ in range(26):
            t0 = r2.random() ** 2 * 0.6
            i0 = int(t0 * SR)
            ln = int(0.012 * SR)
            fr = 2500 + 7000 * r2.random()
            tk = np.sin(2 * np.pi * fr * np.arange(ln) / SR) * np.exp(-np.arange(ln) / SR * 300)
            s[i0:i0 + ln] += tk * 0.5 * (1 - t0)
        # bright pings
        for fr in (2637, 3520, 4186, 5274):
            s += 0.18 * np.sin(2 * np.pi * fr * (1 + 0.003 * r2.normal()) * tt) * np.exp(-tt * (5 + 6 * r2.random()))
        return s

    def thump():
        tt = np.arange(int(SR * 0.5)) / SR
        return np.sin(2 * np.pi * (70 + 60 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9)

    last = -1
    for (t, bx, by, k) in BOUNCES:
        if t - last < 0.06:
            continue
        last = t
        m = 60 + 12 * (k // 5) + SCALE[(k + int(t * 3)) % 5]
        pan = max(-0.8, min(0.8, bx / R_OUT))
        add(bell(hz(m)), t, pan, 0.28)
    for (t, k, bx, by) in BREAKS:
        pan = max(-0.8, min(0.8, bx / R_OUT))
        add(glass(), t, pan, 0.42)
        add(thump(), t, 0.0, 0.45)
    if T_END is not None:
        for m in (60, 67, 72, 76, 79, 84):
            add(bell(hz(m), 3.2), T_END + 0.05, 0.0, 0.17)
        tt = np.arange(int(SR * 1.5)) / SR
        add(np.sin(2 * np.pi * 50 * tt) * np.exp(-tt * 3), T_END, 0.0, 0.55)
    mix = np.stack([L, Rr], 1)
    fade = int(0.6 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)[:, None]
    mix /= max(1e-9, np.abs(mix).max()) / 0.9
    wavfile.write(out, SR, (mix * 32767).astype(np.int16))
    print("audio", round(DUR, 2))


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "sim"
    if cmd == "sim":
        print("seed", SEED, "bounces", len(BOUNCES), "escape", T_END and round(T_END, 2), "dur", round(DUR, 2),
              "breaks", [round(b[0], 1) for b in BREAKS])
        return
    if cmd == "stills":
        for ts in sys.argv[2:]:
            i = min(N_FRAMES - 1, int(float(ts) * FPS))
            Image.fromarray(render_frame(i)).save(f"still_{float(ts):05.1f}.png")
        return
    if cmd == "audio":
        audio(sys.argv[2])
        return
    a, b, out = int(sys.argv[2]), min(int(sys.argv[3]), N_FRAMES), sys.argv[4]
    p = subprocess.Popen(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                          "-crf", "18", "-pix_fmt", "yuv420p", "-threads", "2", out + ".tmp.mp4"], stdin=subprocess.PIPE)
    for i in range(a, b):
        p.stdin.write(render_frame(i).tobytes())
    p.stdin.close()
    if p.wait() == 0:
        os.replace(out + ".tmp.mp4", out)
        print("done", a, b, out)
    else:
        sys.exit("ffmpeg failed")


if __name__ == "__main__":
    main()
