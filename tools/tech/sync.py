"""Satisfying short: 16 balls, 16 speeds - wait for the perfect sync.

Every ball rides its own arc and bounces on the floor; every bounce plays the arc's note.
Ball k makes NCYC[k] full laps in T_SYNC seconds, so all balls hit the floor together
again exactly at T_SYNC (and all at once, split left/right, at T_SYNC / 2).

python3 sync.py info               -> timings / hit counts
python3 sync.py stills t1 t2 ...   -> still_<t>.png
python3 sync.py audio out.wav      -> synthesized soundtrack (limited, peak 0.89)
python3 sync.py range a b out.mp4  -> render frames [a, b)
python3 sync.py build out.mp4      -> 2 parallel render chunks + audio + 2-pass loudnorm -14 LUFS
"""
import colorsys
import json
import math
import os
import subprocess
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
K = int(os.environ.get("K", 16))
T_SYNC = float(os.environ.get("T_SYNC", 27.0))
N_MAX = int(os.environ.get("N_MAX", 24))        # laps of the innermost (fastest) ball until the sync
OUTRO = 2.5
DUR = T_SYNC + OUTRO
N_FRAMES = int(round(DUR * FPS))
CX, FLOOR_Y = 540.0, 1030.0
R_MIN, R_MAX = 100.0, 455.0
RADII = [R_MIN + k * (R_MAX - R_MIN) / (K - 1) for k in range(K)]
NCYC = [N_MAX - k for k in range(K)]            # inner arcs are faster
BALL_R = 10.0
TR, TRDT = 12, 0.008                             # trail segments / spacing in seconds
REF_SRC, REF_H = 470, 210                        # floor reflection: source rows / squashed height
SH = 4
SC = 1 << SH
GOLD = (255, 205, 60)
WHITE = (245, 245, 245)
LINE = os.environ.get("LINE", "0") == "1"        # optional faint line through all balls (shows the wave)


# ---------------------------------------------------------------- kinematics
def half_period(k):
    return T_SYNC / (2 * NCYC[k])


def angle(k, t):
    u = NCYC[k] * t / T_SYNC
    fr = u - math.floor(u)
    tri = 1.0 - abs(2.0 * fr - 1.0)      # 0 at the left end, 1 at the right end
    return math.pi * (1.0 - tri)


def pos(k, t):
    a = angle(k, t)
    return CX + RADII[k] * math.cos(a), FLOOR_Y - RADII[k] * math.sin(a)


def last_hit(k, t):
    hp = half_period(k)
    m = math.floor(t / hp + 1e-9)
    return m * hp, m


HITS = []  # (t, k, side) side -1 = left end, +1 = right end
for _k in range(K):
    _hp = half_period(_k)
    _m = 0
    while _m * _hp <= DUR + 1e-9:
        HITS.append((_m * _hp, _k, -1 if _m % 2 == 0 else 1))
        _m += 1
HITS.sort()


# ---------------------------------------------------------------- colours / particles
def hue_col(h, s=0.78, v=1.0):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


def sc(c, a):
    return tuple(int(v * a) for v in c)


COLS = [hue_col(0.80 * (K - 1 - k) / (K - 1)) for k in range(K)]   # red outside -> violet inside


def make_burst(seed, t0, per_arc, side_of, vy_rng, life_rng):
    r = np.random.default_rng(seed)
    ps = []
    for k in range(K):
        sx = side_of(k)
        for _ in range(per_arc):
            ps.append((k, CX + sx * RADII[k] + r.normal() * 5, FLOOR_Y - 4, r.normal() * 230,
                       -r.uniform(*vy_rng), r.uniform(*life_rng), r.uniform(2.8, 6.0)))
    return t0, ps


BURSTS = [make_burst(11, T_SYNC / 2, 6, lambda k: -1 if NCYC[k] % 2 == 0 else 1, (300, 800), (0.8, 1.3)),
          make_burst(12, T_SYNC, 14, lambda k: -1, (450, 1300), (1.2, 2.1))]


# ---------------------------------------------------------------- drawing helpers
def P(x, y, s=1.0):
    return (int(round(x * s * SC)), int(round(y * s * SC)))


def circ(img, x, y, r, c, th=-1, s=1.0):
    cv2.circle(img, P(x, y, s), max(1, int(round(r * s * SC))), c, th, cv2.LINE_AA, SH)


def arc(img, r, c, th, s=1.0):
    cv2.ellipse(img, P(CX, FLOOR_Y, s), (int(round(r * s * SC)),) * 2, 0, 180, 360, c,
                max(1, int(round(th * s))), cv2.LINE_AA, SH)


def _font(size):
    for f in ["/usr/share/fonts/opentype/inter/InterDisplay-Black.otf",
              "/usr/share/fonts/opentype/inter/Inter-Black.otf",
              "/usr/share/fonts/truetype/noto/NotoSans-Black.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]:
        if os.path.exists(f):
            return ImageFont.truetype(f, size)
    raise FileNotFoundError("font")


def fit(text, size, max_w=960):
    while size > 20:
        x0, _, x1, _ = _font(size).getbbox(text)
        if x1 - x0 <= max_w:
            return size
        size -= 2
    return size


_spr = {}


def sprite(text, size, col=WHITE):
    key = (text, size, col)
    if key not in _spr:
        f = _font(size)
        x0, y0, x1, y1 = f.getbbox(text)
        im = Image.new("RGBA", (x1 - x0 + 20, y1 - y0 + 20), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((10 - x0, 10 - y0), text, font=f, fill=col + (255,))
        _spr[key] = np.asarray(im).astype(np.float32)
    return _spr[key]


def blit(frame, spr, cx, cy, a=1.0, scale=1.0):
    if a <= 0.0:
        return
    if scale != 1.0:
        h, w = spr.shape[:2]
        im = Image.fromarray(spr.astype(np.uint8), "RGBA").resize((max(1, int(w * scale)), max(1, int(h * scale))),
                                                                  Image.BILINEAR)
        spr = np.asarray(im).astype(np.float32)
    h, w = spr.shape[:2]
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb:
        return
    s = spr[ya - y0:yb - y0, xa - x0:xb - x0]
    al = s[..., 3:4] / 255.0 * min(1.0, a)
    reg = frame[ya:yb, xa:xb].astype(np.float32)
    frame[ya:yb, xa:xb] = (reg * (1 - al) + s[..., :3] * al).astype(np.uint8)


def make_bg():
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None]
    top, bot = np.array([17, 15, 30], np.float32), np.array([5, 5, 10], np.float32)
    img = np.repeat((top * (1 - yy) + bot * yy)[:, None, :], W, axis=1)
    Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
    d = np.sqrt(((X - CX) / 640) ** 2 + ((Y - (FLOOR_Y - 180)) / 720) ** 2)
    img += (np.clip(1 - d, 0, 1) ** 2 * 20)[..., None] * np.array([0.55, 0.45, 1.0], np.float32)
    return img.clip(0, 255).astype(np.uint8)


BG = make_bg()
REF_A = (0.30 * (1 - np.linspace(0, 1, REF_H, dtype=np.float32)) ** 1.6)[:, None, None]
BAR_X0, BAR_X1, BAR_Y, BAR_T = 250, 830, 1512, 18
SZ_FINAL = fit("PERFECT SYNC!", 124, 860)      # leaves room for the 15 % pop


def bar(f, frac):
    h = BAR_T / 2
    y = BAR_Y + h
    cv2.line(f, P(BAR_X0 + h, y), P(BAR_X1 - h, y), (45, 45, 60), BAR_T, cv2.LINE_AA, SH)
    if frac > 0:
        xe = BAR_X0 + h + (BAR_X1 - BAR_X0 - 2 * h) * min(1.0, frac)
        cv2.line(f, P(BAR_X0 + h, y), P(xe, y), hue_col(0.80 * min(1.0, frac)), BAR_T, cv2.LINE_AA, SH)


def ease_pop(d, amt, dur):
    return 1 + amt * max(0.0, 1 - d / dur)


# ---------------------------------------------------------------- frame
def render_frame(i):
    t = i / FPS
    f = BG.copy()
    g = np.zeros((H // 2, W // 2, 3), np.uint8)      # glow layer, half resolution
    pts = [pos(k, t) for k in range(K)]
    if LINE:
        cv2.polylines(f, [np.array([P(x, y) for x, y in pts], np.int32)], False, (52, 52, 70), 2, cv2.LINE_AA, SH)
    # arcs (light up on every bounce)
    for k in range(K):
        th, _ = last_hit(k, t)
        lit = math.exp(-(t - th) / 0.30)
        arc(f, RADII[k], sc(COLS[k], 0.32 + 0.68 * lit), 4 + 3 * lit)
        if lit > 0.04:
            arc(g, RADII[k], sc(COLS[k], lit), 12, 0.5)
    # floor impact rings
    for k in range(K):
        th, m = last_hit(k, t)
        d = t - th
        if d < 0.4:
            hx = CX + (-1 if m % 2 == 0 else 1) * RADII[k]
            a = 1 - d / 0.4
            circ(f, hx, FLOOR_Y, 9 + 75 * d, sc(COLS[k], a), 3)
            circ(g, hx, FLOOR_Y, 14 + 40 * d, sc(COLS[k], a), -1, 0.5)
    # trails: smooth tapered tube, drawn tail-first into its own layer and added once (no beading)
    tl = np.zeros_like(f)
    for k in range(K):
        seg = [pos(k, t - j * TRDT) for j in range(TR + 1)]
        for j in range(TR, 0, -1):
            a = 1 - j / (TR + 1)
            cv2.line(tl, P(*seg[j]), P(*seg[j - 1]), sc(COLS[k], 0.6 * a),
                     max(1, int(round(2 * BALL_R * (1 - 0.75 * j / TR)))), cv2.LINE_AA, SH)
    f = cv2.add(f, tl)
    for k in range(K):
        x, y = pts[k]
        circ(g, x, y, BALL_R + 9, COLS[k], -1, 0.5)
        circ(f, x, y, BALL_R, COLS[k])
        circ(f, x, y, BALL_R * 0.55, (255, 255, 255))
    # particle bursts at the syncs
    for t0, ps in BURSTS:
        d = t - t0
        if d < 0 or d > 2.2:
            continue
        for (k, x0, y0, vx, vy, life, rad) in ps:
            if d > life:
                continue
            x, y = x0 + vx * d, y0 + vy * d + 750 * d * d
            if y > FLOOR_Y - 2:
                continue
            a = (1 - d / life) ** 1.5
            circ(f, x, y, rad, sc(COLS[k], a))
            circ(g, x, y, rad + 6, sc(COLS[k], a * 0.8), -1, 0.5)
    # floor glow
    cv2.line(g, P(CX - R_MAX - 40, FLOOR_Y, 0.5), P(CX + R_MAX + 40, FLOOR_Y, 0.5), (90, 90, 110), 6, cv2.LINE_AA, SH)
    g = cv2.GaussianBlur(g, (0, 0), 7)
    f = cv2.add(f, cv2.resize(g, (W, H), interpolation=cv2.INTER_LINEAR))
    # glossy floor reflection
    fy = int(FLOOR_Y)
    ref = cv2.resize(f[fy - REF_SRC:fy][::-1], (W, REF_H), interpolation=cv2.INTER_AREA).astype(np.float32)
    y0 = fy + 5
    f[y0:y0 + REF_H] = (f[y0:y0 + REF_H].astype(np.float32) + ref * REF_A).clip(0, 255).astype(np.uint8)
    cv2.line(f, P(CX - R_MAX - 40, FLOOR_Y), P(CX + R_MAX + 40, FLOOR_Y), (235, 235, 245), 4, cv2.LINE_AA, SH)
    # flashes
    for ts, amp in ((T_SYNC / 2, 0.11), (T_SYNC, 0.42)):
        d = t - ts
        if 0 <= d < 0.9:
            f = cv2.add(f, np.full_like(f, int(255 * amp * math.exp(-d / 0.16))))
    # ---------------- HUD
    blit(f, sprite("WAIT FOR THE", 84), W / 2, 238)
    blit(f, sprite("PERFECT SYNC", 112, GOLD), W / 2, 338)
    blit(f, sprite(f"{K} balls · {K} speeds", 50, (200, 200, 215)), W / 2, 440,
         min(1.0, (3.6 - t) / 0.6) if t > 3.0 else 1.0)
    dh = t - T_SYNC / 2
    if 0 <= dh < 1.4:
        blit(f, sprite("HALF SYNC!", 76), W / 2, 492, min(1.0, dh / 0.1) * min(1.0, (1.4 - dh) / 0.35),
             ease_pop(dh, 0.3, 0.25))
    if t < T_SYNC:
        rem = T_SYNC - t
        blit(f, sprite("PERFECT SYNC IN", 42, (165, 165, 185)), W / 2, 1338)
        if rem > 3.0:
            blit(f, sprite(f"{rem:.1f}s", 118), W / 2, 1428)
        else:
            blit(f, sprite(f"{rem:.1f}s", 118, GOLD), W / 2, 1428, 1.0, ease_pop(1.0 - (rem % 1.0), 0.12, 0.25))
        bar(f, t / T_SYNC)
    else:
        d = t - T_SYNC
        blit(f, sprite("PERFECT SYNC!", SZ_FINAL, GOLD), W / 2, 1385, min(1.0, d / 0.15), ease_pop(d, 0.15, 0.3))
        blit(f, sprite(f"after {T_SYNC:.0f} seconds", 56), W / 2, 1495, min(1.0, max(0.0, (d - 0.3) / 0.25)))
    # impact shake
    d = t - T_SYNC
    if 0 <= d < 0.45:
        amp = 12 * math.exp(-d / 0.12)
        M = np.float32([[1, 0, amp * math.sin(d * 90)], [0, 1, amp * math.cos(d * 70)]])
        f = cv2.warpAffine(f, M, (W, H), borderMode=cv2.BORDER_REPLICATE)
    return f


# ---------------------------------------------------------------- audio
SR = 48000


def penta(n, base=48):
    st = [0, 2, 4, 7, 9]
    return [base + 12 * (j // 5) + st[j % 5] for j in range(n)]


NOTES = penta(K)       # ascending; inner (fast) arc k gets NOTES[K - 1 - k]


def hz(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


def limiter(mix, thr=0.55, look_ms=4, rel_s=0.12):
    from scipy.ndimage import maximum_filter1d
    blk = SR // 1000
    nb = int(math.ceil(len(mix) / blk))
    pad = np.zeros((nb * blk, 2))
    pad[:len(mix)] = mix
    pk = maximum_filter1d(np.abs(pad).reshape(nb, blk, 2).max(axis=(1, 2)), size=2 * look_ms + 1)
    need = np.minimum(1.0, thr / np.maximum(pk, 1e-9))
    g = np.empty(nb)
    cur, rc = 1.0, math.exp(-1.0 / (rel_s * 1000))
    for j in range(nb):
        cur = need[j] if need[j] < cur else need[j] + (cur - need[j]) * rc
        g[j] = cur
    gs = np.interp(np.arange(nb * blk) / blk, np.arange(nb) + 0.5, g)[:len(mix)]
    return mix * gs[:, None]


def audio(out):
    from scipy.io import wavfile
    from scipy.signal import butter, fftconvolve, lfilter
    n = int(round(DUR * SR))
    L = np.zeros(n)
    R = np.zeros(n)
    rng = np.random.default_rng(4)

    def add(sig, t0, pan, gain):
        i0 = int(round(t0 * SR))
        if i0 >= n:
            return
        sig = sig[: n - i0] * gain
        a = (pan + 1) * math.pi / 4
        L[i0:i0 + len(sig)] += sig * math.cos(a)
        R[i0:i0 + len(sig)] += sig * math.sin(a)

    def vib(f, dur=1.6):
        tt = np.arange(int(SR * dur)) / SR
        dec = 2.4 + f / 500.0
        s = np.sin(2 * np.pi * f * tt) * np.exp(-tt * dec)
        if 4 * f < 17000:
            s += 0.30 * np.sin(2 * np.pi * 4 * f * tt) * np.exp(-tt * dec * 3.5)
        if 9.9 * f < 17000:
            s += 0.06 * np.sin(2 * np.pi * 9.9 * f * tt) * np.exp(-tt * 35)
        cl = int(0.004 * SR)
        s[:cl] += rng.normal(size=cl) * np.exp(-np.arange(cl) / SR * 900) * 0.12
        return s * np.minimum(1.0, tt / 0.002)

    tones = [vib(hz(NOTES[K - 1 - k])) for k in range(K)]
    gains = [0.55 + 0.40 * k / (K - 1) for k in range(K)]          # low (outer) notes a bit louder
    for (t, k, side) in HITS:
        boost = 1.35 if abs(t - T_SYNC) < 1e-6 else 1.0          # the final chord rings out louder
        add(tones[k], t, side * (0.2 + 0.55 * RADII[k] / R_MAX), gains[k] * 0.3 * boost)

    # riser into the final sync
    rl = 2.6
    tt = np.arange(int(rl * SR)) / SR
    b, a = butter(2, [1500 / (SR / 2), 9000 / (SR / 2)], "band")
    nz = lfilter(b, a, rng.normal(size=len(tt))) * (tt / rl) ** 3
    sw = np.sin(2 * np.pi * np.cumsum(220 * 4 ** (tt / rl)) / SR) * (tt / rl) ** 2
    add(nz * 0.55 + sw * 0.10, T_SYNC - rl, 0.0, 1.0)

    def boom(dur, f0):
        tt = np.arange(int(SR * dur)) / SR
        return np.sin(2 * np.pi * np.cumsum(f0 + 70 * np.exp(-tt * 18)) / SR) * np.exp(-tt * 2.6) * np.minimum(1, tt / 0.003)

    def crash(dur, seed):
        r2 = np.random.default_rng(seed)
        tt = np.arange(int(SR * dur)) / SR
        b2, a2 = butter(2, 3500 / (SR / 2), "high")
        return lfilter(b2, a2, r2.normal(size=len(tt))) * np.exp(-tt * 3.0)

    add(boom(1.4, 55), T_SYNC / 2, 0.0, 0.20)
    add(boom(1.9, 50), T_SYNC, 0.0, 0.65)
    add(crash(1.8, 21), T_SYNC, -0.5, 0.20)
    add(crash(1.8, 22), T_SYNC, 0.5, 0.20)
    for j, m in enumerate((84, 88, 91, 96)):
        add(vib(hz(m), 1.6), T_SYNC + 0.06 + 0.07 * j, (-0.4, 0.4, -0.2, 0.2)[j], 0.10)

    # small stereo room
    ir_t = np.arange(int(SR * 2.0)) / SR
    bl, al = butter(1, 5500 / (SR / 2))
    irs = []
    for s in (31, 32):
        ir = lfilter(bl, al, np.random.default_rng(s).normal(size=len(ir_t))) * np.exp(-ir_t * 3.4)
        ir[: int(0.015 * SR)] = 0
        irs.append(ir / np.sqrt((ir ** 2).sum()))
    L2 = L + 0.30 * fftconvolve(L, irs[0])[:n]
    R2 = R + 0.30 * fftconvolve(R, irs[1])[:n]
    mix = np.stack([L2, R2], 1)
    mix /= np.percentile(np.abs(mix), 99.9) / 0.35      # body of the track ~6 dB below the climax ceiling
    mix = limiter(mix, thr=0.70)
    fade = int(0.5 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)[:, None] ** 2
    mix *= 0.79 / max(1e-9, np.abs(mix).max())
    for _ in range(2):            # bring it near -14 LUFS with a -3.6 dBFS ceiling (AAC adds ~1.4 dB true peak)
        wavfile.write(out, SR, (mix * 32767).astype(np.int16))
        mix = limiter(mix * 10 ** ((-14.2 - lufs(out)) / 20), thr=0.66)
    mix = np.clip(mix, -0.70, 0.70)
    wavfile.write(out, SR, (mix * 32767).astype(np.int16))
    print("audio", out, round(n / SR, 2), "s", "LUFS", lufs(out))


def lufs(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True)
    s = r.stderr[r.stderr.rindex("Summary:"):]
    return float(s.split("I:")[1].split("LUFS")[0])


# ---------------------------------------------------------------- render / build
def render_range(a, b, out):
    b = min(b, N_FRAMES)
    p = subprocess.Popen(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                          "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast",
                          "-crf", "18", "-pix_fmt", "yuv420p", "-threads", "1", out + ".tmp.mp4"], stdin=subprocess.PIPE)
    for i in range(a, b):
        p.stdin.write(render_frame(i).tobytes())
    p.stdin.close()
    if p.wait() != 0:
        sys.exit("ffmpeg failed")
    os.replace(out + ".tmp.mp4", out)
    print("done", a, b, out)


def build(out):
    me = os.path.abspath(__file__)
    mid = N_FRAMES // 2
    procs = [subprocess.Popen([sys.executable, me, "range", str(a), str(b), f"_part{j}.mp4"])
             for j, (a, b) in enumerate(((0, mid), (mid, N_FRAMES)))]
    audio("_audio.wav")
    if any(p.wait() for p in procs):
        sys.exit("render failed")
    with open("_parts.txt", "w") as fh:
        fh.write("file '_part0.mp4'\nfile '_part1.mp4'\n")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", "_parts.txt",
                    "-c", "copy", "_video.mp4"], check=True)
    ln = "loudnorm=I=-14:TP=-1.0:LRA=11"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", "_audio.wav", "-af", ln + ":print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    js = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    ln2 = (f"{ln}:measured_I={js['input_i']}:measured_TP={js['input_tp']}:measured_LRA={js['input_lra']}"
           f":measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", "_video.mp4", "-i", "_audio.wav",
                    "-map", "0:v", "-map", "1:a", "-af", ln2, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
                    "-shortest", "-movflags", "+faststart", out], check=True)
    print("built", out, "measured", js["input_i"], "LUFS ->", js["output_i"], js["normalization_type"])


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "info"
    if cmd == "info":
        print("K", K, "laps", NCYC[-1], "..", NCYC[0], "T_SYNC", T_SYNC, "dur", DUR, "frames", N_FRAMES,
              "hits", len(HITS), "hits/s", round(len(HITS) / DUR, 1))
        print("notes", NOTES)
        for ts in (T_SYNC / 4, T_SYNC / 3, T_SYNC / 2, T_SYNC):
            same = sum(1 for (t, _, _) in HITS if abs(t - ts) < 1e-6)
            print(f"  t={ts:5.2f}s  balls hitting together: {same}")
        return
    if cmd == "stills":
        for ts in sys.argv[2:]:
            i = min(N_FRAMES - 1, int(round(float(ts) * FPS)))
            Image.fromarray(render_frame(i)).save(f"still_{float(ts):05.2f}.png")
        return
    if cmd == "audio":
        audio(sys.argv[2])
        return
    if cmd == "build":
        build(sys.argv[2])
        return
    render_range(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])


if __name__ == "__main__":
    main()
