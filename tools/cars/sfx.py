import math, subprocess, sys
import numpy as np
from scipy.io import wavfile
from scipy.signal import lfilter
import render as E
SR = 48000
N = int(math.ceil(E.DUR * SR)) + SR
FX = np.zeros((N, 2)); MU = np.zeros((N, 2))
rng = np.random.default_rng(4)
def tt(d): return np.arange(int(d * SR)) / SR
def add(buf, sig, t0, g=1.0, pan=0.0):
    i0 = int(round(t0 * SR))
    if i0 < 0 or i0 >= N: return
    sig = sig[:N - i0] * g; a = (pan + 1) * math.pi / 4
    buf[i0:i0 + len(sig), 0] += sig * math.cos(a); buf[i0:i0 + len(sig), 1] += sig * math.sin(a)
def lp(x, fc):
    a = math.exp(-2 * math.pi * fc / SR); return lfilter([1 - a], [1, -a], x)
def thump(f0=95, f1=48, dec=0.09):
    t = tt(0.3); fr = f1 + (f0 - f1) * np.exp(-t / 0.03); ph = 2 * np.pi * np.cumsum(fr) / SR
    return np.sin(ph) * np.exp(-t / dec) + 0.4 * np.sin(2 * ph) * np.exp(-t / 0.05) + 0.25 * lp(rng.standard_normal(len(t)), 1800) * np.exp(-t / 0.015)
def swell(d, fc):
    t = tt(d); n = lp(rng.standard_normal(len(t)), fc); return n / (np.abs(n).max() + 1e-9) * np.sin(np.pi * t / d) ** 1.5
def hz(m): return 440 * 2 ** ((m - 69) / 12)
def pluck(f, d=0.5):
    t = tt(d); return (np.sin(2*np.pi*f*t) + 0.35*np.sin(4*np.pi*f*t) + 0.12*np.sin(6*np.pi*f*t)) * np.exp(-t/0.22) * np.minimum(1, t/0.004)
def pad(fs, d):
    t = tt(d); return sum(np.sin(2*np.pi*f*t) for f in fs) / len(fs) * np.minimum(1, t/0.6) * np.minimum(1, (d-t)/0.6)
def engine(f_start, f_end, d, rough=0.0):
    t = tt(d); f = f_start + (f_end - f_start) * (t / d) ** 1.3
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = 0.6 * np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.2 * np.sign(np.sin(0.5 * ph)) * 0.5
    s += rough * lp(rng.standard_normal(len(t)), 2500)
    return s * np.minimum(1, t / 0.1) * np.minimum(1, (d - t) / 0.15)
def scratch(d=0.35):
    t = tt(d); f = 900 * (1 - t / d) + 150
    ph = 2 * np.pi * np.cumsum(f) / SR
    return (np.sin(ph) * 0.5 + 0.5 * lp(rng.standard_normal(len(t)), 3000)) * np.exp(-t / 0.15)
# music bed (stops for gags)
beat = 0.5; ch = [[57,60,64,69],[53,57,60,65],[48,52,55,60],[55,59,62,67]]
t0, bar = 0.0, 0
while t0 < E.DUR:
    c = ch[bar % 4]
    add(MU, pad([hz(m-12) for m in c[:3]], 4*beat+0.4), t0, 0.1)
    for k in range(8):
        if True:
            add(MU, pluck(hz(c[[0,1,2,3,2,1,2,3][k]]+12)), t0+k*beat/2, 0.07, 0.3 if k % 2 else -0.3)
    add(MU, thump(70, 40, 0.12), t0, 0.14); add(MU, thump(70, 40, 0.12), t0+2*beat, 0.12)
    t0 += 4*beat; bar += 1
add(FX, thump(130, 60, 0.15), E.PART_S - 0.05, 0.5)                  # title slam
for ts in (E.T['B'], E.T['C'], E.T['D'], E.T['E'], E.T['F'], E.T['G'], E.T['H'], E.T['K']):
    add(FX, swell(0.5, 3000), ts - 0.4, 0.12)
for ts in (E.CLUTCH_S, E.STICK_S):
    add(FX, thump(220, 90, 0.05), ts, 0.35)                         # X stamps
add(FX, thump(150, 70, 0.1), E.AUTO_S, 0.35)
# torque converter: engine rises, then idles at the red light
add(FX, engine(60, 70, E.SPINS_S - E.T['B'] + 0.2), E.T['B'], 0.07)
add(FX, engine(70, 200, E.RED_S - E.SPINS_S, rough=0.05), E.SPINS_S, 0.1)
add(FX, engine(200, 60, 0.6), E.RED_S - 0.3, 0.1)
add(FX, engine(60, 62, E.T['E'] - E.RED_S - 0.3), E.RED_S + 0.3, 0.07)
add(FX, swell(1.4, 700), E.OILB_S, 0.12)                            # oil slosh
add(FX, pluck(hz(76), 0.6) + 0.6 * pluck(hz(83), 0.6), E.STALL_S, 0.2)
# planetary: lock clunk and gear change
add(FX, thump(160, 70, 0.08), E.HOLD_S, 0.4)
add(FX, thump(160, 70, 0.08), E.THATS_S, 0.4)
add(FX, pluck(hz(79), 0.5), E.THATS_S + 0.02, 0.15)
# clutch pack: hiss + clamp
hiss = lp(rng.standard_normal(int(0.7 * SR)), 5000) * np.sin(np.pi * tt(0.7) / 0.7)
add(FX, hiss, E.SQUEEZE_S - 0.1, 0.06)
add(FX, thump(130, 60, 0.1), E.SQUEEZE_S + 0.45, 0.45)
# computer: data blips, then quick upshifts
for k in range(6):
    add(FX, pluck(hz(88 + (k % 3) * 2), 0.12), E.COMP_S + 0.1 + k * 0.12, 0.06)
for k in range(1, 6):
    add(FX, thump(170, 80, 0.05), E.SHIFTS_S + 0.55 * k, 0.3)
add(FX, engine(90, 190, 0.55 * 5, rough=0.03), E.SHIFTS_S, 0.06)
add(FX, pluck(hz(81), 0.8) + 0.6*pluck(hz(88), 0.8), E.FOLLOW_S, 0.25)
voice = np.zeros(N)
for path, t0 in ((sys.argv[1], 0.0),):
    raw = subprocess.run(['ffmpeg','-v','error','-i',path,'-ac','1','-ar',str(SR),'-f','f32le','-'], capture_output=True, check=True).stdout
    v = np.frombuffer(raw, np.float32).astype(np.float64)
    v = v / (np.sqrt(np.mean(v[np.abs(v) > 0.01]**2)) + 1e-9) * 0.16
    i0 = int(t0 * SR); n = min(len(v), N - i0); voice[i0:i0+n] += v[:n]
a = math.exp(-1/(0.12*SR)); env = lfilter([1-a], [1, -a], np.abs(voice))
duck = (1 - 0.55*np.clip(env/0.05, 0, 1))[:, None]
mix = voice[:, None] + FX*(0.6+0.4*duck) + MU*duck
mix = mix[:int(math.ceil(E.DUR*SR))]
f = int(0.4*SR); mix[-f:] *= np.linspace(1, 0, f)[:, None]
mix = mix / max(1.0, np.abs(mix).max()/0.95)
wavfile.write('mix.wav', SR, (mix*32767).astype(np.int16)); print('wrote mix.wav', round(len(mix)/SR, 2))
