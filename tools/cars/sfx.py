"""Sound design for 'How Cars Work - Part 4: The Differential'.  python3 sfx.py voice.mp3 -> mix.wav"""
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
def hp(x, fc):
    return x - lp(x, fc)
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
def squeal(d=0.6, f0=1250):
    """tyre / brake squeal: wobbling tone + filtered hiss, soft attack and release"""
    t = tt(d); f = f0 * (1 + 0.025 * np.sin(2 * np.pi * 13 * t)) * (1 - 0.08 * t / d)
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = 0.55 * np.sin(ph) + 0.2 * np.sin(2 * ph) + 0.35 * hp(lp(rng.standard_normal(len(t)), 5000), 900)
    return s * np.minimum(1, t / 0.05) * np.minimum(1, (d - t) / 0.2)
def crackle(d=0.5, n=14):
    out = np.zeros(int(d * SR))
    for _ in range(n):
        i = rng.integers(0, len(out) - 600)
        b = hp(rng.standard_normal(500), 3000) * np.exp(-np.arange(500) / 80)
        out[i:i + 500] += b * rng.uniform(0.4, 1.0)
    return out
# music bed (same as the earlier parts)
beat = 0.5; ch = [[57,60,64,69],[53,57,60,65],[48,52,55,60],[55,59,62,67]]
t0, bar = 0.0, 0
while t0 < E.DUR:
    c = ch[bar % 4]
    add(MU, pad([hz(m-12) for m in c[:3]], 4*beat+0.4), t0, 0.1)
    for k in range(8):
        add(MU, pluck(hz(c[[0,1,2,3,2,1,2,3][k]]+12)), t0+k*beat/2, 0.07, 0.3 if k % 2 else -0.3)
    add(MU, thump(70, 40, 0.12), t0, 0.14); add(MU, thump(70, 40, 0.12), t0+2*beat, 0.12)
    t0 += 4*beat; bar += 1
add(FX, thump(130, 60, 0.15), E.PART_S - 0.05, 0.5)                    # title slam
for ts in (E.T['B'], E.T['C'], E.T['D'], E.T['E'], E.T['F'], E.T['G'], E.T['H'], E.T['I'], E.T['K']):
    add(FX, swell(0.5, 3000), ts - 0.4, 0.12)
# intro: car rolling through the corner, two wheel speeds, one engine, "HOW?"
add(FX, engine(55, 70, E.PART_S + 0.3), 0.0, 0.06)
add(FX, pluck(hz(64), 0.5), E.DIFFR_S, 0.12, -0.5); add(FX, pluck(hz(71), 0.5), E.DIFFR_S + 0.12, 0.12, 0.5)
add(FX, thump(110, 50, 0.1), E.ENGINE_S, 0.3)
add(FX, thump(150, 70, 0.1), E.BOTH_S, 0.35)
# outside wheel goes farther: unroll whoosh + highlight ping
add(FX, swell(0.7, 2500), E.FARTHER_S, 0.15)
add(FX, pluck(hz(83), 0.5), E.FARTHER_S + 0.7, 0.14)
# solid axle: lock clunk, equal counters, tyre squeal + skid
add(FX, thump(160, 70, 0.08), E.SOLID_S, 0.4)
add(FX, pluck(hz(72), 0.4), E.SAME_S, 0.1, -0.4); add(FX, pluck(hz(72), 0.4), E.SAME_S + 0.08, 0.1, 0.4)
add(FX, squeal(0.75, 1150), E.SKID_S - 0.12, 0.1, -0.4)
add(FX, thump(220, 90, 0.05), E.SKID_S, 0.25)
# differential build-up
add(FX, thump(120, 55, 0.12), E.DIFF_S, 0.35)
add(FX, engine(65, 80, E.T['H'] - E.DSHAFT_S), E.DSHAFT_S, 0.045)  # drivetrain hum
for ts in (E.PINION_S, E.RING_S, E.ws('D', 'cage'), E.ws('D', 'spider'), E.ws('D', 'side')):
    add(FX, thump(220, 90, 0.05), ts, 0.28); add(FX, pluck(hz(79), 0.3), ts + 0.02, 0.06)
for k in range(3):
    add(FX, thump(260, 120, 0.03), E.BOLTED_S + 0.1 + 0.12 * k, 0.2)       # bolts
add(FX, pluck(hz(76), 0.4), E.PERW_S, 0.1, -0.6); add(FX, pluck(hz(76), 0.4), E.PERW_S + 0.05, 0.1, 0.6)
# straight: not turning, one block, equal speeds
add(FX, pluck(hz(55), 0.5), E.DONT_S, 0.16)
add(FX, pluck(hz(76), 0.6) + 0.6 * pluck(hz(83), 0.6), E.WHOLE_S, 0.14)
add(FX, pluck(hz(72), 0.4), E.BOTHW_S, 0.1, -0.4); add(FX, pluck(hz(72), 0.4), E.BOTHW_S + 0.08, 0.1, 0.4)
# corner: inside down, spider gears whirr, outside up
add(FX, swell(0.6, 2000), E.CORNER_F - 0.2, 0.1)
add(FX, pluck(hz(67), 0.5) + 0.7 * pluck(hz(64), 0.5), E.SLOWS_S, 0.14, -0.5)
add(FX, engine(180, 260, 0.9, rough=0.02), E.START_S, 0.035)
add(FX, pluck(hz(76), 0.5) + 0.7 * pluck(hz(79), 0.5), E.SPEEDS_S, 0.14, 0.5)
# numbers
add(FX, pluck(hz(74), 0.4), E.RING_G, 0.12)
add(FX, pluck(hz(69), 0.4), E.NINETY_S, 0.12, -0.5)
add(FX, pluck(hz(79), 0.4), E.ONETEN_S, 0.12, 0.5)
add(FX, pluck(hz(81), 0.8) + 0.6 * pluck(hz(88), 0.8), E.AVERAGE_S, 0.22)
# the catch: ice, wheel spin, nothing
add(FX, thump(90, 40, 0.15), E.CATCH_S, 0.4)
add(FX, pluck(hz(72), 0.4), E.EQUAL_S, 0.1, -0.4); add(FX, pluck(hz(72), 0.4), E.EQUAL_S + 0.08, 0.1, 0.4)
add(FX, crackle(0.6), E.ICE_S - 0.1, 0.08, -0.5)
add(FX, engine(120, 380, 1.4, rough=0.08), E.SPINS_H - 0.2, 0.09, -0.4)
add(FX, squeal(1.0, 1400), E.SPINS_H, 0.05, -0.5)
add(FX, pluck(hz(50), 0.6), E.NOTHING_S, 0.2)
# the fix: limited-slip clutches clamp, locker clunks
for ts in (E.SPORTS_S, E.OFFR_S):
    add(FX, pluck(hz(84), 0.25), ts, 0.07)
hiss = lp(rng.standard_normal(int(0.6 * SR)), 5000) * np.sin(np.pi * tt(0.6) / 0.6)
add(FX, hiss, E.LSD_S - 0.05, 0.06)
add(FX, thump(130, 60, 0.1), E.LSD_S + 0.45, 0.4)
add(FX, thump(160, 70, 0.08), E.LOCK_S, 0.45)
add(FX, pluck(hz(79), 0.6) + 0.6 * pluck(hz(86), 0.6), E.LOCK_S + 0.05, 0.14)
# teaser: brakes
add(FX, thump(160, 70, 0.08), E.BRAKES_S, 0.3)
add(FX, thump(120, 60, 0.08), E.FOOT_S, 0.3)
add(FX, squeal(0.7, 1700), E.STOP_S - 0.05, 0.05, 0.4)
add(FX, crackle(0.6, 18), E.STOP_S, 0.06, 0.4)
add(FX, thump(90, 40, 0.16), E.TON_S, 0.4)
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
