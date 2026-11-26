"""Satisfying short: the ball grows every bounce until it fills the circle.

python3 grow.py sim                 -> print duration / bounce count
python3 grow.py stills t1 t2 ...    -> still_<t>.png
python3 grow.py range a b out.mp4   -> render frames [a, b)
python3 grow.py audio melody|sfx out.wav
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
CX, CY, R_ARENA = 540.0, 1010.0, 440.0
R0, DR = 16.0, 5.4
G = 1500.0
V0 = (520.0, -140.0)
P0 = (-120.0, -160.0)
VMIN = 900.0
END_GAP = 3.0
OUTRO = 3.2
SH = 4
SC = 1 << SH


# ---------------------------------------------------------------- simulation
def simulate():
    dt = 1 / 1200
    x, y = P0
    vx, vy = V0
    r = R0
    t = 0.0
    frames = []
    bounces = []
    next_frame = 0.0
    while True:
        while t >= next_frame - 1e-9:
            frames.append((x, y, r, len(bounces)))
            next_frame += 1 / FPS
        vy += G * dt
        x += vx * dt
        y += vy * dt
        t += dt
        d = math.hypot(x, y)
        lim = R_ARENA - r
        if d > lim:
            nx, ny = x / d, y / d
            vn = vx * nx + vy * ny
            if vn > 0:
                vx -= 2 * vn * nx
                vy -= 2 * vn * ny
                sp = math.hypot(vx, vy)
                if sp < VMIN:
                    vx, vy = vx / sp * VMIN, vy / sp * VMIN
                bounces.append((t, x, y, r, sp))
                r = min(R_ARENA, r + DR)
                lim = R_ARENA - r
            x, y = nx * lim, ny * lim
        if R_ARENA - r <= END_GAP:
            r = R_ARENA
            frames.append((0.0, 0.0, r, len(bounces)))
            return frames, bounces, t


FRAMES, BOUNCES, T_END = simulate()
N_SIM = len(FRAMES)
N_FRAMES = N_SIM + int(OUTRO * FPS)
DUR = N_FRAMES / FPS


def state(i):
    if i < N_SIM:
        return FRAMES[i]
    x, y, r, n = FRAMES[-1]
    return 0.0, 0.0, R_ARENA, n


def hue_col(h, s=0.78, v=1.0):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


def hue_at(i):
    return 0.0 + i * 0.0045


# ---------------------------------------------------------------- drawing
def P(x, y):
    return (int(round(x * SC)), int(round(y * SC)))


def circ(img, x, y, r, c, th=-1):
    cv2.circle(img, P(x, y), max(1, int(round(r * SC))), c, th, cv2.LINE_AA, SH)


def _font(size):
    for f in ["/usr/share/fonts/opentype/inter/InterDisplay-Black.otf",
              "/usr/share/fonts/truetype/noto/NotoSans-Black.ttf",
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
    top, bot = np.array([16, 16, 26], np.float32), np.array([6, 6, 10], np.float32)
    col = top * (1 - t) + bot * t
    return np.repeat(col[:, None, :], W, axis=1).reshape(H, W, 3).astype(np.uint8)


BG = make_bg()


def stamp(canvas, i):
    x, y, r, _ = state(i)
    circ(canvas, CX + x, CY + y, r, hue_col(hue_at(i), 0.7, 0.85), 2)


def render_frame(i, canvas):
    t = i / FPS
    x, y, r, n = state(i)
    f = BG.copy()
    # trail canvas inside arena
    mask = canvas.any(axis=2)
    f[mask] = canvas[mask]
    # arena ring
    circ(f, CX, CY, R_ARENA + 7, (245, 245, 245), 8)
    # ball
    done = i >= N_SIM - 1
    col = hue_col(hue_at(i))
    if not done:
        circ(f, CX + x, CY + y, r, col)
        circ(f, CX + x, CY + y, r, (255, 255, 255), 4)
    else:
        k = min(1.0, (i - N_SIM + 1) / (0.6 * FPS))
        fill = tuple(int(c * (1 - 0.35 * k)) for c in col)
        circ(f, CX, CY, R_ARENA, fill)
        circ(f, CX, CY, R_ARENA, (255, 255, 255), 4)
    # HUD
    blit(f, sprite("THE BALL GROWS", 84), W / 2, 250)
    blit(f, sprite("EVERY BOUNCE", 84, (255, 205, 60)), W / 2, 345)
    pct = int(round(100 * (r - R0) / (R_ARENA - R0)))
    blit(f, sprite(f"BOUNCES  {n}", 54), W / 2, 1560)
    rrect_bar(f, 240, 1630, 840, 1652, pct / 100, col)
    blit(f, sprite(f"{pct}%", 46, (190, 190, 200)), W / 2, 1705)
    if t < 3.0:
        a = min(1.0, (3.0 - t) / 0.5)
        blit(f, sprite("Will it fill the circle?", 52, (200, 200, 210)), W / 2, 450, a)
    if done:
        k = min(1.0, (i - N_SIM + 1) / (0.25 * FPS))
        pop = 1 + 0.12 * max(0.0, 1 - (i - N_SIM + 1) / (0.3 * FPS))
        blit(f, sprite("FILLED!", 150), CX, CY - 40, k, pop)
        blit(f, sprite(f"in {n} bounces", 60), CX, CY + 80, k)
    return f


def rrect_bar(f, x0, y0, x1, y1, frac, col):
    h = (y1 - y0) / 2
    cv2.line(f, P(x0 + h, y0 + h), P(x1 - h, y0 + h), (45, 45, 58), int(2 * h), cv2.LINE_AA, SH)
    xe = x0 + h + (x1 - x0 - 2 * h) * max(0.0, min(1.0, frac))
    cv2.line(f, P(x0 + h, y0 + h), P(xe, y0 + h), col, int(2 * h), cv2.LINE_AA, SH)


def build_canvas(upto):
    canvas = np.zeros((H, W, 3), np.uint8)
    for j in range(min(upto, N_SIM)):
        stamp(canvas, j)
    return canvas


# ---------------------------------------------------------------- audio
SR = 48000
ODE = [64, 64, 65, 67, 67, 65, 64, 62, 60, 60, 62, 64, 64, 62, 62,
       64, 64, 65, 67, 67, 65, 64, 62, 60, 60, 62, 64, 62, 60, 60,
       62, 62, 64, 60, 62, 64, 65, 64, 60, 62, 64, 65, 64, 62, 60, 62, 55,
       64, 64, 65, 67, 67, 65, 64, 62, 60, 60, 62, 64, 62, 60, 60]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def audio(mode, out):
    from scipy.io import wavfile
    n = int((DUR + 0.5) * SR)
    L = np.zeros(n)
    Rr = np.zeros(n)

    def add(sig, t0, pan, gain):
        i0 = int(t0 * SR)
        if i0 >= n:
            return
        sig = sig[: n - i0] * gain
        a = (pan + 1) * math.pi / 4
        L[i0:i0 + len(sig)] += sig * math.cos(a)
        Rr[i0:i0 + len(sig)] += sig * math.sin(a)

    def bell(f, dur, bright):
        tt = np.arange(int(SR * dur)) / SR
        env = np.exp(-tt * 5.0) * np.minimum(1, tt / 0.004)
        s = np.sin(2 * np.pi * f * tt) + bright * 0.35 * np.sin(2 * np.pi * 2 * f * tt) * np.exp(-tt * 9) \
            + 0.12 * np.sin(2 * np.pi * 3 * f * tt) * np.exp(-tt * 14)
        return s * env

    def pop(size):
        tt = np.arange(int(SR * 0.09)) / SR
        f0 = 900 - 500 * size
        return np.sin(2 * np.pi * f0 * tt * (1 - tt * 3)) * np.exp(-tt * 45)

    last = -1.0
    for k, (t, x, y, r, sp) in enumerate(BOUNCES):
        size = (r - R0) / (R_ARENA - R0)
        pan = max(-0.8, min(0.8, x / R_ARENA))
        add(pop(size), t, pan, 0.25)
        if mode == "melody" and t - last > 0.055:
            m = ODE[k % len(ODE)] + (12 if k >= len(ODE) else 0)
            add(bell(hz(m), 1.2, 1.0), t, pan * 0.5, 0.33)
            last = t
    # finale
    t_end = N_SIM / FPS
    if mode == "melody":
        for m in (60, 64, 67, 72, 76):
            add(bell(hz(m), 3.0, 0.6), t_end, 0.0, 0.22)
    tt = np.arange(int(SR * 1.2)) / SR
    boom = np.sin(2 * np.pi * 55 * tt) * np.exp(-tt * 3.5)
    add(boom, t_end, 0.0, 0.5)
    mix = np.stack([L, Rr], 1)
    mix /= max(1e-9, np.abs(mix).max()) / 0.9
    wavfile.write(out, SR, (mix * 32767).astype(np.int16))
    print("audio", mode, round(DUR, 2))


# ---------------------------------------------------------------- main
def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "sim"
    if cmd == "sim":
        print("bounces", len(BOUNCES), "t_end", round(T_END, 2), "frames", N_FRAMES, "dur", round(DUR, 2))
        gaps = [BOUNCES[k + 1][0] - BOUNCES[k][0] for k in range(len(BOUNCES) - 1)]
        print("first gaps", [round(g, 2) for g in gaps[:8]], "last", [round(g, 3) for g in gaps[-5:]])
        return
    if cmd == "stills":
        for ts in sys.argv[2:]:
            i = int(float(ts) * FPS)
            Image.fromarray(render_frame(i, build_canvas(i + 1))).save(f"still_{float(ts):05.1f}.png")
        return
    if cmd == "audio":
        audio(sys.argv[2], sys.argv[3])
        return
    a, b, out = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    b = min(b, N_FRAMES)
    canvas = build_canvas(a)
    p = subprocess.Popen(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                          "-crf", "18", "-pix_fmt", "yuv420p", "-threads", "2", out + ".tmp.mp4"], stdin=subprocess.PIPE)
    for i in range(a, b):
        if i < N_SIM:
            stamp(canvas, i)
        p.stdin.write(render_frame(i, canvas).tobytes())
    p.stdin.close()
    if p.wait() == 0:
        os.replace(out + ".tmp.mp4", out)
        print("done", a, b, out)
    else:
        sys.exit("ffmpeg failed")


if __name__ == "__main__":
    main()
