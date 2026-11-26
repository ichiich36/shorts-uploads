import math, subprocess, sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import lfilter
import story as E
SR = 48000
N = int(math.ceil(E.DUR * SR)) + SR
FX = np.zeros((N, 2))
MU = np.zeros((N, 2))
rng = np.random.default_rng(7)
EV, T = E.EV, E.T


def tt(d):
    return np.arange(int(d * SR)) / SR


def add(buf, sig, t0, g=1.0, pan=0.0):
    i0 = int(round(t0 * SR))
    if i0 < 0 or i0 >= N:
        return
    sig = sig[:N - i0] * g
    a = (pan + 1) * math.pi / 4
    buf[i0:i0 + len(sig), 0] += sig * math.cos(a)
    buf[i0:i0 + len(sig), 1] += sig * math.sin(a)


def lp(x, fc):
    a = math.exp(-2 * math.pi * fc / SR)
    return lfilter([1 - a], [1, -a], x)


def hz(m):
    return 440 * 2 ** ((m - 69) / 12)


def thump(f0=110, f1=45, dec=0.12):
    t = tt(0.4)
    fr = f1 + (f0 - f1) * np.exp(-t / 0.03)
    ph = 2 * np.pi * np.cumsum(fr) / SR
    return np.sin(ph) * np.exp(-t / dec) + 0.3 * lp(rng.standard_normal(len(t)), 2500) * np.exp(-t / 0.02)


def pluck(f, d=0.35, bright=0.4):
    t = tt(d)
    s = np.sin(2 * np.pi * f * t) + bright * np.sin(4 * np.pi * f * t) + 0.2 * bright * np.sin(6 * np.pi * f * t)
    return s * np.exp(-t / 0.09) * np.minimum(1, t / 0.003)


def pop(f=700):
    t = tt(0.12)
    return np.sin(2 * np.pi * f * t * (1 + 3 * t)) * np.exp(-t / 0.03)


def whoosh(d=0.45, fc=2500):
    t = tt(d)
    n = lp(rng.standard_normal(len(t)), fc)
    return n / (np.abs(n).max() + 1e-9) * np.sin(np.pi * t / d) ** 2


def clank():
    t = tt(0.5)
    s = sum(np.sin(2 * np.pi * f * t) * np.exp(-t / dd) for f, dd in ((523, 0.25), (1385, 0.12), (2210, 0.08)))
    return s / 2 + 0.4 * lp(rng.standard_normal(len(t)), 4000) * np.exp(-t / 0.01)


def boing(f0=180):
    t = tt(0.5)
    f = f0 * (1 + 0.5 * np.sin(2 * np.pi * 9 * t) * np.exp(-t / 0.25))
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.18)


def shot():
    t = tt(0.09)
    return lp(rng.standard_normal(len(t)), 3000) * np.exp(-t / 0.018) + 0.6 * np.sin(2 * np.pi * 90 * t) * np.exp(-t / 0.03)


def pew():
    t = tt(0.25)
    f = 2200 * np.exp(-t / 0.08) + 400
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.08)


def click():
    t = tt(0.03)
    return rng.standard_normal(len(t)) * np.exp(-t / 0.004)


def trombone(m, d):
    t = tt(d)
    f = hz(m) * (1 + 0.012 * np.sin(2 * np.pi * 5.5 * t) * np.minimum(1, t / 0.2))
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = sum(np.sin(k * ph) / k ** 1.1 for k in range(1, 8))
    env = np.minimum(1, t / 0.04) * np.minimum(1, (d - t) / 0.08)
    return lp(s, 1800) * env


def ding(f=1320):
    t = tt(1.0)
    return (np.sin(2 * np.pi * f * t) + 0.4 * np.sin(2 * np.pi * 2.76 * f * t) * np.exp(-t / 0.1)) * np.exp(-t / 0.35)


# ---------------- music: comic oom-pah march, 112 bpm
bpm = 112.0
beat = 60 / bpm
prog = [(48, [60, 64, 67]), (43, [59, 62, 67]), (45, [60, 64, 69]), (41, [60, 65, 69]),
        (48, [60, 64, 67]), (43, [59, 62, 65]), (48, [60, 64, 67]), (43, [55, 59, 62])]
mel = [72, None, 74, 76, 77, None, 76, 74, 72, None, 71, None, 67, None, None, None]
t0 = 0.0
bar = 0
end_music = EV['lost'] - 0.1
while t0 < end_music:
    root, ch = prog[bar % len(prog)]
    for b in range(4):
        tb = t0 + b * beat
        if tb >= end_music:
            break
        if b % 2 == 0:
            add(MU, pluck(hz(root - 12 + (7 if b == 2 else 0)), 0.3, 0.8), tb, 0.30)
        else:
            for m in ch:
                add(MU, pluck(hz(m), 0.18, 0.3), tb, 0.07, 0.2)
        if bar % 4 in (1, 3):
            n = mel[(bar // 2 % 2) * 8 + b * 2]
            if n:
                add(MU, pluck(hz(n), 0.25, 0.6), tb, 0.08, -0.2)
    t0 += 4 * beat
    bar += 1
# gate music during the gun jam gag
gate = np.ones(N)
i, j = int(EV['jammed'] * SR), int((EV['jammed'] + 0.8) * SR)
gate[i:j] = 0.2
MU *= gate[:, None]

# ---------------- sfx
add(FX, thump(), EV['war'], 0.6)
add(FX, thump(140, 60, 0.1), 0.15, 0.4)
add(FX, thump(130, 60, 0.1), EV['thousand'] - 0.15, 0.45)
for ts in (T['B'], T['C'], T['D'], T['E'], T['G'], T['H'], T['I'], T['J'], T['K'], T['L']):
    add(FX, whoosh(), ts - 0.35, 0.10)
for i in range(3):
    add(FX, pop(600 + 150 * i), EV['three'] + i * 0.18, 0.25)
for i in range(2):
    add(FX, clank(), EV['two'] + i * 0.15, 0.12)
add(FX, thump(120, 50, 0.1), EV['ten'], 0.45)
# rattle until jam
tt0 = EV['fire']
while tt0 < EV['jammed'] - 0.05:
    add(FX, shot(), tt0, 0.35, 0.2)
    tt0 += 1 / 13
add(FX, clank(), EV['jammed'], 0.3)
add(FX, boing(220), EV['jammed'] + 0.25, 0.25)
add(FX, whoosh(0.6, 4000), EV['ran'], 0.25)
for k in range(10):
    add(FX, click() * 0.6, EV['ran'] + 0.15 + k * 0.07, 0.25, 0.5)
# truck engine through G
d = T['H'] - T['G']
t = tt(d)
f = 55 + 6 * np.sin(2 * np.pi * 0.7 * t)
ph = 2 * np.pi * np.cumsum(f) / SR
eng = (np.sign(np.sin(ph)) * 0.4 + 0.3 * np.sin(2 * ph)) * (0.7 + 0.3 * np.sin(2 * np.pi * 7 * t))
eng = lp(eng, 700) * np.minimum(1, t / 0.3) * np.minimum(1, (d - t) / 0.3)
add(FX, eng, T['G'], 0.10)
k = 0
tb = EV['bumpy']
while tb < T['H'] - 0.2:
    add(FX, thump(90, 40, 0.06), tb, 0.25)
    tb += math.pi / 14
    k += 1
for k in range(4):
    add(FX, pew(), EV['aim'] + 0.1 + k * 0.22, 0.12, 0.4 - 0.25 * k)
# calendar + counter
last = -1
for i in range(1, 6):
    add(FX, click(), T['H'] + i * 0.25, 0.4)
for k in range(14):
    add(FX, click(), EV['fired'] + k * 0.1, 0.2)
add(FX, ding(), EV['mostly'], 0.2)
add(FX, whoosh(), EV['came'] - 0.1, 0.12)
add(FX, whoosh(), EV['again'] - 0.1, 0.12)
add(FX, pop(900), EV['perbird'], 0.25)
add(FX, thump(), EV['lost'], 0.45)
# sad trombone after "birds."
tb = [w for w in E.WORDS if w['key'] == 'birds'][-1]['end'] + 0.15
for m, dd in ((58, 0.32), (57, 0.32), (56, 0.32), (55, 1.0)):
    add(FX, trombone(m, dd), tb, 0.12)
    tb += dd + 0.04
add(FX, pop(1000), EV['follow'], 0.25)

voice = np.zeros(N)
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', sys.argv[1], '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
v = np.frombuffer(raw, np.float32).astype(np.float64)
v = v / (np.sqrt(np.mean(v[np.abs(v) > 0.01] ** 2)) + 1e-9) * 0.17
n = min(len(v), N)
voice[:n] = v[:n]
a = math.exp(-1 / (0.12 * SR))
env = lfilter([1 - a], [1, -a], np.abs(voice))
duck = (1 - 0.55 * np.clip(env / 0.05, 0, 1))[:, None]
mix = voice[:, None] + FX * (0.6 + 0.4 * duck) + MU * duck
mix = mix[:int(math.ceil(E.DUR * SR))]
f = int(0.5 * SR)
mix[-f:] *= np.linspace(1, 0, f)[:, None]
mix = mix / max(1.0, np.abs(mix).max() / 0.95)
wavfile.write('mix.wav', SR, (mix * 32767).astype(np.int16))
print('wrote mix.wav', round(len(mix) / SR, 2))
