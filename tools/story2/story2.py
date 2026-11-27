"""Story pilot: 'The man who SOLD the Eiffel Tower' – two hosts (Mia & Leo) walk through the story.
python3 story2.py stills t1 t2 ... | audio | video [start end part]
"""
import sys, os, math, subprocess, wave, json
import numpy as np, cv2
from toon import *

W, H, FPS, SR = 1080, 1920, 30, 44100
HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------- cast ----------------
MIA = Char(SKIN[0], 'curly', C('#c9502e'), C('#1f9e9a'), C('#178a86'), C('#2f3a6b'), lashes=True)
LEO = Char(SKIN[1], 'short', C('#3b2a22'), C('#e8b636'), C('#d4a020'), C('#36415e'))
LUS = Char(SKIN[3], 'slick', C('#2a221f'), C('#3a3f52'), C('#000000'), C('#2e3242'), mustache=True, hat='fedora', tie=C('#a8323e'))
POI = Char(SKIN[0], 'bald', C('#6b5444'), C('#7a5c3e'), C('#000000'), C('#4a3b2e'), glasses=True, belly=1.3, tie=C('#2d5f8a'), height=0.95)
DEAL1 = Char(SKIN[2], 'short', C('#1d1d1d'), C('#5b6e4a'), C('#000000'), C('#333333'), mustache=True, tie=C('#c4a24a'))
DEAL2 = Char(SKIN[0], 'slick', C('#8a8a8a'), C('#4b4f6b'), C('#000000'), C('#333333'), beard=True, tie=C('#7a2a2a'))

# ---------------- script / timeline ----------------
LINES = [  # file, speaker, captions (rel_start, text)
    ('01', 'M', [(0, "Leo, would you ever buy the Eiffel Tower?")]),
    ('02', 'L', [(0, "What? Nobody can buy the Eiffel Tower.")]),
    ('03', 'M', [(0, "In 1925, a man named Victor Lustig sold it anyway.")]),
    ('04', 'L', [(0, "Wait... he SOLD it? How?")]),
    ('05', 'M', [(0, "He read that the tower needed expensive repairs."), (3.0, "So he faked papers from the French government."),
                 (6.3, "Then he invited scrap metal dealers to a luxury hotel..."), (10.7, "...the tower will be torn down and sold for scrap."),
                 (13.8, "7,300 tons of iron."), (17.1, "Top secret!")]),
    ('06', 'L', [(0, "And they believed him?")]),
    ('07', 'M', [(0, "One dealer, André Poisson, wanted it so badly that he paid him."), (4.7, "Plus a bribe!")]),
    ('08', 'L', [(0, "So Lustig got caught, right?")]),
    ('09', 'M', [(0, "Nope. He grabbed the money and fled to Austria.")]),
    ('10', 'L', [(0, "Then Poisson went to the police!")]),
    ('11', 'M', [(0, "Nope! He was too embarrassed to tell anyone.")]),
    ('12', 'L', [(0, "No way.")]),
    ('13', 'M', [(0, "And later... Lustig came back and tried to sell it AGAIN.")]),
    ('14', 'L', [(0, "This guy is unbelievable."), (2.6, "Would YOU have fallen for it?"), (4.6, "Follow for more crazy true stories!")]),
]
SCENE_OF = {'01': 'room', '02': 'room', '03': 'paris', '04': 'paris', '05': 'cafe', '06': 'hotel', '07': 'deal', '08': 'deal',
            '09': 'road', '10': 'poisson', '11': 'poisson', '12': 'poisson', '13': 'again', '14': 'end'}

def load_audio(path, sr=SR):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()

VO = []
t = 0.5
for i, (fid, spk, caps) in enumerate(LINES):
    a = load_audio(os.path.join(HERE, 'voice', fid + '.mp3'))
    dur = len(a) / SR
    hop = SR // FPS
    env = np.array([np.sqrt(np.mean(a[k * hop:(k + 1) * hop] ** 2) + 1e-12) for k in range(len(a) // hop + 1)])
    env = np.nan_to_num(env)
    env = np.clip(env / (np.percentile(env, 95) + 1e-6), 0, 1.2)
    VO.append(dict(id=fid, spk=spk, caps=caps, t0=t, dur=dur, audio=a, env=env))
    nxt = LINES[i + 1][0] if i + 1 < len(LINES) else None
    gap = 0.3 if nxt and SCENE_OF[nxt] == SCENE_OF[fid] else 0.55
    t += dur + gap
END_SPEECH = t
DURATION = END_SPEECH + 2.6
L = {v['id']: v for v in VO}

# scene time ranges
def T(fid, rel=0.0): return L[fid]['t0'] + rel
SCENES = [
    ('room', 0.0), ('paris', T('03') - 0.25), ('cafe', T('05') - 0.25), ('papers', T('05', 3.0)), ('hotel', T('05', 6.2)),
    ('deal', T('07') - 0.25), ('road', T('09') - 0.2), ('poisson', T('10') - 0.25), ('again', T('13') - 0.25), ('end', T('14') - 0.25),
]
def scene_at(tt):
    cur = SCENES[0]
    for i, s in enumerate(SCENES):
        if tt >= s[1]: cur = (s[0], s[1], i)
    return cur

def speaking(spk, tt):
    for v in VO:
        if v['spk'] == spk and v['t0'] <= tt < v['t0'] + v['dur']:
            k = int((tt - v['t0']) * FPS)
            return float(v['env'][min(k, len(v['env']) - 1)])
    return 0.0

def caption_at(tt):
    for v in VO:
        if v['t0'] - 0.05 <= tt < v['t0'] + v['dur'] + 0.25:
            rel = tt - v['t0']
            cur = None
            for i, (cs, txt) in enumerate(v['caps']):
                if rel >= cs - 0.05: cur = (txt, v['t0'] + cs, v['spk'])
            return cur
    return None

def blink(tt, seed):
    p = (tt + seed * 1.37) % 3.7
    return 1.0 if p < 0.12 else 0.0

def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def easeio(x): x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def pop(tt, t0, d=0.35):
    x = (tt - t0) / d
    if x <= 0: return 0.0
    if x >= 1: return 1.0
    return 1 + 0.25 * math.sin(x * math.pi) * (1 - x) + (ease(x) - 1)

# ---------------- backgrounds ----------------
_bg = {}
def vgrad(c0, c1, y0=0, y1=H):
    g = np.zeros((H, W, 3), np.float32)
    ys = np.clip((np.arange(H) - y0) / max(1, (y1 - y0)), 0, 1)[:, None, None]
    return (np.array(c0, np.float32) * (1 - ys) + np.array(c1, np.float32) * ys).repeat(W, 1)

def floor_planks(img, y0, col):
    rect(img, 0, y0, W, H, col)
    for y in range(y0, H, 70):
        line(img, (0, y), (W, y), shade(col, 0.85), 3)
        off = ((y - y0) // 70) % 2 * 120
        for x in range(off, W, 240):
            line(img, (x, y), (x, y + 70), shade(col, 0.85), 3)

def bg_room():
    img = np.full((H, W, 3), C('#f3dcaa'), np.uint8)
    for x in range(0, W, 64): rect(img, x, 0, x + 30, 1060, C('#ecd197'))
    rect(img, 0, 1000, W, 1080, C('#c98f5b')); rect(img, 0, 1000, W, 1012, C('#a8703f'))
    floor_planks(img, 1080, C('#b5734a'))
    ell(img, 540, 1500, 470, 120, C('#c4524a')); ell(img, 540, 1500, 400, 92, C('#d9694f'), th=8)
    # window
    rect(img, 610, 380, 990, 690, C('#4b3c86'))
    for i, (x, h) in enumerate([(620, 120), (690, 180), (760, 90), (820, 150), (900, 200), (950, 110)]):
        rect(img, x, 690 - h, x + 60, 690, C('#2e2556'))
        for wy in range(690 - h + 20, 690, 36): rect(img, x + 15, wy, x + 25, wy + 12, C('#f2c94c'))
    circ(img, 920, 440, 28, C('#f5f0d6'))
    rect(img, 610, 525, 990, 537, C('#ffffff')); rect(img, 793, 380, 807, 690, C('#ffffff'))
    cv2.rectangle(img, (604, 374), (996, 696), C('#ffffff'), 12)
    rect(img, 590, 696, 1010, 716, C('#f3f3f3'))
    for x0 in (560, 960): rect(img, x0, 350, x0 + 60, 760, C('#ec7a64'))
    rect(img, 545, 345, 1035, 360, C('#a8703f'))
    # TV
    rr(img, 90, 400, 510, 660, 16, C('#2b2b33')); rect(img, 108, 418, 492, 642, C('#87b6e0'))
    eiffel(img, 300, 640, 200, C('#4a4a6a'), 2)
    rect(img, 200, 660, 400, 680, C('#2b2b33')); rr(img, 120, 900, 480, 1000, 10, C('#7a4e32'))
    # plant + lamp
    rr(img, 990, 900, 1070, 1000, 8, C('#e0784e'))
    for a in range(-60, 61, 30):
        ell(img, 1030 + a * 0.6, 840, 22, 70, C('#3f9a5c'), a)
    line(img, (540, 0), (540, 230), C('#333333'), 4)
    poly(img, [(470, 300), (610, 300), (580, 230), (500, 230)], C('#f2c94c'))
    # clock
    circ(img, 540, 480, 52, C('#ffffff')); circ(img, 540, 480, 52, C('#c4524a'), 8)
    line(img, (540, 480), (540, 448), C('#333333'), 5); line(img, (540, 480), (565, 492), C('#333333'), 5)
    return img

def buildings(img, x0, x1, top, base, col, roof):
    rect(img, x0, top, x1, base, col)
    poly(img, [(x0 - 10, top), (x1 + 10, top), (x1 - 20, top - 90), (x0 + 20, top - 90)], roof)
    for y in range(top + 40, base - 160, 120):
        for x in range(x0 + 30, x1 - 60, 95):
            rect(img, x, y, x + 50, y + 80, C('#6f86a8')); rect(img, x - 6, y + 80, x + 56, y + 90, C('#3d3d4a'))
            rect(img, x + 23, y, x + 27, y + 80, C('#e9dcc4'))

def bg_paris():
    img = vgrad(C('#5b6fc7'), C('#ffc994'), 0, 1150).astype(np.uint8)
    circ(img, 820, 520, 70, C('#fff1c9'))
    ell(img, 250, 420, 140, 40, C('#ffe3c4')); ell(img, 700, 300, 170, 45, C('#ffe3c4'))
    eiffel(img, 540, 1150, 920, C('#5b4a63'), 3)
    buildings(img, -20, 300, 520, 1150, C('#eadcc2'), C('#55607a'))
    buildings(img, 790, 1100, 600, 1150, C('#f0e3cc'), C('#55607a'))
    rect(img, 0, 1150, W, H, C('#9d8f86'))
    for y in range(1170, H, 46):
        off = (y // 46) % 2 * 40
        for x in range(-40 + off, W, 80): ell(img, x, y, 36, 18, C('#8a7d75'))
    # lamp post
    rect(img, 318, 800, 330, 1160, C('#2b2b33')); rr(img, 300, 760, 348, 810, 10, C('#2b2b33')); rect(img, 308, 770, 340, 800, C('#ffe58a'))
    # cafe awning on right building
    for i in range(6):
        poly(img, [(800 + i * 50, 950), (850 + i * 50, 950), (850 + i * 50, 1010), (800 + i * 50, 1010)], C('#c94a4a') if i % 2 else C('#f5efe0'))
    return img

def bg_cafe():
    img = np.full((H, W, 3), C('#2f5d50'), np.uint8)
    for x in range(0, W, 90): rect(img, x, 0, x + 6, 1000, C('#29524a'))
    rect(img, 240, 330, 840, 900, C('#ffd7a0'))
    eiffel(img, 540, 900, 480, C('#7a6a82'), 2)
    for x in (240, 535, 840): rect(img, x - 6, 330, x + 6, 900, C('#5c3b28'))
    rect(img, 230, 610, 850, 622, C('#5c3b28')); cv2.rectangle(img, (234, 324), (846, 906), C('#5c3b28'), 14)
    rect(img, 0, 1000, W, 1060, C('#5c3b28'))
    for y in range(1060, H, 90):
        for x in range(0, W, 90):
            rect(img, x, y, x + 90, y + 90, C('#e9e2d0') if ((x + y) // 90) % 2 else C('#3c3c44'))
    return img

def bg_papers():
    img = np.full((H, W, 3), C('#8a5b3c'), np.uint8)
    for x in range(0, W, 180): rect(img, x, 0, x + 8, 1000, C('#7a4f33'))
    rr(img, 360, 330, 720, 640, 8, C('#c9a15b')); rect(img, 380, 350, 700, 620, C('#d9cfb8'))
    blit_text(img, 'RÉPUBLIQUE', 540, 420, 40, C('#4a3b2e'), fname='serif')
    blit_text(img, 'FRANÇAISE', 540, 480, 40, C('#4a3b2e'), fname='serif')
    rect(img, 0, 1000, W, H, C('#5a3a28'))
    return img

def bg_hotel():
    img = np.full((H, W, 3), C('#7d2534'), np.uint8)
    for y in range(40, 1000, 110):
        for x in range((y // 110) % 2 * 60, W, 120):
            ell(img, x, y, 16, 26, C('#9a3b48')); circ(img, x, y, 6, C('#c9a15b'))
    rect(img, 0, 1000, W, H, C('#5a1f2a'))
    for y in range(1030, H, 60): line(img, (0, y), (W, y), C('#4c1924'), 3)
    # curtains
    for x0, x1 in ((0, 110), (970, W)):
        rect(img, x0, 0, x1, 1000, C('#d6a73c'))
        for x in range(x0 + 20, x1, 30): line(img, (x, 0), (x, 1000), C('#b88a28'), 5)
    # chandelier
    line(img, (540, 0), (540, 150), C('#c9a15b'), 5)
    ell(img, 540, 200, 150, 40, C('#c9a15b'))
    for i in range(7):
        x = 420 + i * 40
        line(img, (x, 200), (x, 250), C('#c9a15b'), 4); ell(img, x, 260, 9, 16, C('#fff1b0'))
    return img

def bg_road():
    img = vgrad(C('#79b8ef'), C('#d7f0ff'), 0, 900).astype(np.uint8)
    for (cx, cy, r) in ((200, 1000, 520), (800, 1050, 600), (520, 1100, 500)):
        circ(img, cx, cy, r, C('#7cc06a') if cx != 520 else C('#6aac5a'))
    rect(img, 0, 1100, W, H, C('#6aac5a'))
    poly(img, [(0, 1180), (W, 1180), (W, 1500), (0, 1500)], C('#6b6b75'))
    for x in range(0, W, 140): rect(img, x, 1335, x + 80, 1345, C('#f5f5f5'))
    ell(img, 250, 330, 120, 36, C('#ffffff')); ell(img, 760, 250, 150, 40, C('#ffffff'))
    # signpost
    rect(img, 836, 760, 852, 1180, C('#6e4a30'))
    poly(img, [(700, 780), (960, 780), (1010, 830), (960, 880), (700, 880)], C('#2f7d4a'))
    blit_text(img, 'AUSTRIA', 845, 805, 50, (255, 255, 255))
    poly(img, [(990, 900), (730, 900), (680, 945), (730, 990), (990, 990)], C('#3a5a8c'))
    blit_text(img, 'PARIS', 835, 918, 46, (255, 255, 255))
    return img

def bg_poisson():
    img = np.full((H, W, 3), C('#9fb3c8'), np.uint8)
    for x in range(0, W, 70): rect(img, x, 0, x + 35, 1000, C('#95a9be'))
    rect(img, 0, 1000, W, H, C('#6b5444'))
    for y in range(1020, H, 64): line(img, (0, y), (W, y), C('#5c4738'), 3)
    rr(img, 130, 380, 430, 640, 10, C('#ffffff')); rect(img, 145, 395, 415, 625, C('#bfe1ff'))
    eiffel(img, 280, 625, 210, C('#8a7d95'), 2)
    return img

BG_FN = {'room': bg_room, 'paris': bg_paris, 'cafe': bg_cafe, 'papers': bg_papers, 'hotel': bg_hotel, 'deal': bg_hotel,
         'road': bg_road, 'poisson': bg_poisson, 'again': bg_paris, 'end': bg_room}
def BG(name):
    if name not in _bg: _bg[name] = BG_FN[name]()
    return _bg[name]

# ---------------- props drawn per frame ----------------
def table(img, x0, x1, y):
    rect(img, x0, y, x1, y + 34, C('#f4efe4')); rect(img, x0, y + 34, x1, y + 150, C('#ece3d1'))
    for x in range(x0 + 20, x1, 60): line(img, (x, y + 40), (x, y + 150), C('#ddd2bc'), 3)

def desk(img, y):
    rect(img, 60, y, 1020, y + 40, C('#6e4a30')); rect(img, 90, y + 40, 1000, y + 330, C('#5c3b28'))

def stamp_mark(img, cx, cy, txt, col, al, ang=-12, sz=56):
    if al <= 0: return
    tw = text_w(txt, sz) + 40
    ov = img.copy()
    box = cv2.boxPoints(((cx, cy), (tw, sz * 1.5), ang)).astype(np.int32)
    cv2.polylines(ov, [box], True, col, 8, AA)
    rgb, a = text_img(txt, sz, col)
    p_ = 40
    rgb = cv2.copyMakeBorder(rgb, p_, p_, p_, p_, cv2.BORDER_CONSTANT, value=0)
    a = cv2.copyMakeBorder(a[..., 0], p_, p_, p_, p_, cv2.BORDER_CONSTANT, value=0)[..., None]
    hh, ww = a.shape[:2]
    M = cv2.getRotationMatrix2D((ww / 2, hh / 2), -ang, 1.0)
    rgb2 = cv2.warpAffine(rgb, M, (ww, hh)); a2 = cv2.warpAffine(a[..., 0], M, (ww, hh))[..., None]
    x0, y0 = int(cx - ww / 2), int(cy - hh / 2)
    reg = ov[y0:y0 + hh, x0:x0 + ww].astype(np.float32)
    ov[y0:y0 + hh, x0:x0 + ww] = (reg * (1 - a2) + rgb2 * a2).astype(np.uint8)
    cv2.addWeighted(ov, al, img, 1 - al, 0, img)

def paper(img, cx, cy, s=1.0):
    rect(img, cx - 230 * s, cy - 150 * s, cx + 230 * s, cy + 150 * s, C('#fbf6e8'))
    blit_text(img, 'MINISTÈRE DES POSTES', cx, cy - 125 * s, int(30 * s), C('#2d3a5c'), fname='serif')
    blit_text(img, 'ET TÉLÉGRAPHES', cx, cy - 88 * s, int(30 * s), C('#2d3a5c'), fname='serif')
    for i in range(5):
        rect(img, cx - 190 * s, cy - 30 * s + i * 30 * s, cx + (150 - 40 * (i % 2)) * s, cy - 22 * s + i * 30 * s, C('#c9c2b0'))

def newspaper_card(img, al):
    if al <= 0: return
    ov = img.copy()
    rr(ov, 180, 390, 900, 810, 10, C('#f2ecdc'))
    blit_text(ov, 'LE JOURNAL', 540, 410, 52, C('#222222'), fname='serif')
    rect(ov, 210, 480, 870, 486, C('#222222'))
    blit_text(ov, 'EIFFEL TOWER', 540, 510, 64, C('#222222'))
    blit_text(ov, 'REPAIRS COST A FORTUNE!', 540, 600, 46, C('#a8323e'))
    for i in range(4): rect(ov, 220, 690 + i * 26, 860 - (i % 2) * 120, 702 + i * 26, C('#b8b2a2'))
    cv2.addWeighted(ov, al, img, 1 - al, 0, img)

def easel(img, phase, tl):
    line(img, (760, 830), (720, 1170), C('#6e4a30'), 14); line(img, (940, 830), (980, 1170), C('#6e4a30'), 14)
    rect(img, 680, 540, 1020, 840, C('#6e4a30')); rect(img, 696, 556, 1004, 824, C('#fbf6e8'))
    if phase == 0:
        eiffel(img, 850, 815, 240, C('#5b4a63'), 2)
    elif phase == 1:
        eiffel(img, 850, 815, 240, C('#5b4a63'), 2)
        k = ease(tl / 0.4)
        line(img, (720, 580), (720 + 260 * k, 580 + 220 * k), C('#d33b3b'), 14)
        line(img, (980, 580), (980 - 260 * k, 580 + 220 * k), C('#d33b3b'), 14)
        blit_text(img, 'SCRAP', 850, 760, 48, C('#d33b3b'), alpha=k)
    else:
        blit_text(img, '7,300', 850, 600, 96, C('#2d3a5c'), scale=max(0.01, pop(tl, 0)))
        blit_text(img, 'TONS OF IRON', 850, 720, 44, C('#2d3a5c'), alpha=ease(tl / 0.4))

def bubble(img, x, y, r, al):
    if al <= 0: return
    ov = img.copy()
    ell(ov, x, y, r * 1.25, r, (255, 255, 255))
    for k, (dx, dy, rr_) in enumerate(((-r * 0.9, r * 1.1, 26), (-r * 1.25, r * 1.5, 16))):
        circ(ov, x + dx, y + dy, rr_, (255, 255, 255))
    cv2.addWeighted(ov, al, img, 1 - al, 0, img)

def follow_button(img, tt, t0):
    s = pop(tt, t0, 0.4)
    if s <= 0.01: return
    w, h = 520 * s, 120 * s
    cx, cy = 540, 735
    rr(img, cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, int(60 * s), C('#fe2c55'))
    blit_text(img, '+ FOLLOW', cx, cy - 34 * s, max(10, int(64 * s)), (255, 255, 255))

# ---------------- hosts ----------------
def hosts(img, tt, mode='side', mia_arms='idle', leo_arms='idle', mia_look=1, leo_look=-1, leo_brows=0.0, mia_brows=0.0, leo_smile=0.4, mia_smile=0.5):
    mm, lm = speaking('M', tt), speaking('L', tt)
    if mode == 'side':
        MIA.draw(img, 150, 1610, 0.95, look=mia_look, mouth=mm, blink=blink(tt, 1), arms=mia_arms, arm_anim=tt, bounce=6 * mm, brows=mia_brows, smile=mia_smile)
        LEO.draw(img, 930, 1610, 0.95, look=leo_look, mouth=lm, blink=blink(tt, 2), arms=leo_arms, arm_anim=tt, bounce=6 * lm, brows=leo_brows, smile=leo_smile)
    else:
        MIA.draw(img, 330, 1440, 1.08, look=mia_look, mouth=mm, blink=blink(tt, 1), arms=mia_arms, arm_anim=tt, bounce=8 * mm, brows=mia_brows, smile=mia_smile)
        LEO.draw(img, 760, 1440, 1.08, look=leo_look, mouth=lm, blink=blink(tt, 2), arms=leo_arms, arm_anim=tt, bounce=8 * lm, brows=leo_brows, smile=leo_smile)

# ---------------- scenes ----------------
def scene(name, tt, ts):
    img = BG(name).copy()
    tl = tt - ts
    cap_y = 1440
    if name == 'room':
        # TV pops SOLD stamp
        stamp_mark(img, 300, 540, 'SOLD?', C('#d33b3b'), ease((tt - 0.2) / 0.25), sz=52)
        la = 'shrug' if T('02') <= tt < T('02') + 2.5 else 'idle'
        hosts(img, tt, 'center', mia_arms='point2' if tt < T('01') + 2.5 else 'hips', leo_arms=la,
              leo_brows=1.0 if T('02') <= tt < T('02') + 1.0 else 0.0, leo_smile=0.8)
        cap_y = 580
    elif name == 'paris':
        x = 1200 - 620 * easeio(tl / 2.2)
        walking = tl < 2.2
        arms = 'wave' if 2.3 < tl < 3.6 else 'idle'
        LUS.draw(img, x, 1240, 1.0, look=-1 if walking else 0.5, walk=tl * 7, walking=walking, arms=arms, arm_anim=tl, blink=blink(tt, 3), smile=0.8)
        blit_text(img, 'Victor Lustig', 540, 560, 52, (255, 255, 255), alpha=ease((tl - 2.2) / 0.3), stroke=3, stroke_col=C('#2b2b33'))
        hosts(img, tt, 'side', mia_arms='point' if T('03') + 2 < tt < T('03') + 4.4 else 'idle', leo_arms='up' if tt >= T('04') else 'idle',
              leo_brows=1.0 if tt >= T('04') else 0.0, mia_look=1, leo_look=-1)
        blit_text(img, 'PARIS, 1925', 540, 380, 48, (255, 255, 255), alpha=ease(tl / 0.4), stroke=4, stroke_col=C('#2b2b33'))
    elif name == 'cafe':
        LUS.draw(img, 540, 1240, 1.05, look=0, arms='hold', blink=blink(tt, 3), brows=1.0 if tl > 1.8 else 0, smile=0.9 if tl > 1.8 else 0.3)
        # newspaper in hands
        nx, ny = (LUS.hands[0][0] + LUS.hands[1][0]) / 2, LUS.hands[0][1]
        rr(img, nx - 150, ny - 100, nx + 150, ny + 80, 4, C('#f2ecdc')); rect(img, nx - 130, ny - 80, nx + 130, ny - 70, C('#444444'))
        for i in range(4): rect(img, nx - 130, ny - 50 + i * 26, nx + 110 - (i % 2) * 60, ny - 40 + i * 26, C('#b8b2a2'))
        newspaper_card(img, ease((tl - 0.4) / 0.3) * (1 - ease((tl - 2.7) / 0.2)))
        hosts(img, tt, 'side')
    elif name == 'papers':
        LUS.draw(img, 540, 1200, 1.0, look=0.6, arms='hold', blink=blink(tt, 3), smile=0.9, brows=0.6)
        desk(img, 1000)
        paper(img, 540, 1110, 0.95)
        # stamp comes down at tl 0.7
        sd = tl - 0.6
        if sd < 0.25:
            yy = 700 + 330 * ease(max(0, sd) / 0.25)
            rr(img, 470, yy - 120, 610, yy - 60, 12, C('#6e4a30')); rect(img, 520, yy - 60, 560, yy, C('#3a3a3a')); rect(img, 480, yy, 600, yy + 18, C('#a8323e'))
        else:
            stamp_mark(img, 560, 1150, 'OFFICIAL', C('#a8323e'), 0.9, sz=50)
            if sd < 0.9:
                yy = 1030 - 330 * ease((sd - 0.25) / 0.5)
                rr(img, 470, yy - 120, 610, yy - 60, 12, C('#6e4a30')); rect(img, 520, yy - 60, 560, yy, C('#3a3a3a')); rect(img, 480, yy, 600, yy + 18, C('#a8323e'))
        blit_text(img, 'FAKE!', 860, 760, 64, C('#ffde59'), alpha=ease((tl - 1.4) / 0.3), stroke=5, stroke_col=C('#2b2b33'), scale=max(0.01, pop(tt, ts + 1.4)))
        hosts(img, tt, 'side', leo_brows=0.8)
    elif name in ('hotel',):
        r5 = tt - T('05')
        # dealers behind table
        DEAL1.draw(img, 210, 1200, 0.75, look=1, blink=blink(tt, 4), mouth=0.0, smile=0.5)
        DEAL2.draw(img, 370, 1200, 0.75, look=1, blink=blink(tt, 5), brows=1.0 if r5 > 13.8 else 0)
        POI.draw(img, 530, 1200, 0.75, look=1, blink=blink(tt, 6), brows=1.0 if r5 > 10.7 else 0, smile=0.9 if r5 > 13.8 else 0.4)
        table(img, 90, 650, 1070)
        phase = 0 if r5 < 10.7 else (1 if r5 < 13.8 else 2)
        pts = (0, 10.7, 13.8)[phase]
        easel(img, phase, r5 - pts)
        arms = 'finger' if r5 > 17.1 and tt < T('06') else 'present2'
        LUS.draw(img, 740, 1270, 0.9, look=-1 if r5 < 10.7 else 1, arms=arms, blink=blink(tt, 3), smile=0.8, mouth=0)
        stamp_mark(img, 540, 470, 'TOP SECRET', C('#d33b3b'), ease((r5 - 17.2) / 0.15), sz=70)
        if tt >= T('06'):
            for i, ch in enumerate((DEAL1, DEAL2)): pass
        hosts(img, tt, 'side', leo_arms='shrug' if tt >= T('06') else 'idle', leo_brows=1.0 if tt >= T('06') else 0)
        blit_text(img, 'Hôtel de Crillon', 540, 330, 40, (255, 255, 255), alpha=ease(tl / 0.4) * (1 - ease((tl - 3) / 0.4)), stroke=4, stroke_col=C('#2b2b33'))
    elif name == 'deal':
        r7 = tt - T('07')
        POI.draw(img, 340, 1250, 1.05, look=1, arms='hold', blink=blink(tt, 6), smile=0.9)
        LUS.draw(img, 750, 1250, 1.05, look=-1, arms='hold', blink=blink(tt, 3), smile=0.9 if r7 > 1.8 else 0.4)
        blit_text(img, 'André Poisson', 340, 500, 48, (255, 255, 255), alpha=ease(r7 / 0.3) * (1 - ease((r7 - 3.5) / 0.4)), stroke=3, stroke_col=C('#2b2b33'))
        # money bag moves from Poisson to Lustig
        k = easeio((r7 - 1.6) / 1.0)
        bx = 350 + 400 * k; by = 1010 - 80 * math.sin(k * math.pi)
        money_bag(img, bx, by, 0.9)
        if r7 > 4.7:
            k2 = easeio((r7 - 4.8) / 0.8)
            ex_, ey_ = 360 + 330 * k2, 1060 - 60 * math.sin(k2 * math.pi)
            rect(img, ex_ - 60, ey_ - 38, ex_ + 60, ey_ + 38, C('#f2ecdc')); poly(img, [(ex_ - 60, ey_ - 38), (ex_ + 60, ey_ - 38), (ex_, ey_)], C('#ddd3bd'))
            blit_text(img, '+ BRIBE', 540, 640, 60, C('#ffde59'), alpha=1 - ease((r7 - 6.6) / 0.3), scale=max(0.01, pop(tt, T('07', 4.7))), stroke=5, stroke_col=C('#2b2b33'))
        if tt >= T('08'):
            blit_text(img, '?', 540, 520, 140, (255, 255, 255), alpha=ease((tt - T('08')) / 0.3), stroke=5, stroke_col=C('#2b2b33'))
        hosts(img, tt, 'side', leo_arms='think' if tt >= T('08') else 'idle', mia_arms='hips')
    elif name == 'road':
        x = -120 + 1350 * (tl / (T('10') - T('09')))
        LUS.draw(img, x, 1330, 0.95, look=1, walk=tl * 13, walking=True, arms='idle', blink=0, smile=0.9)
        suitcase(img, x + 95, 1110, 0.8)
        for i in range(8):
            bt = tl - i * 0.25
            if bt > 0:
                bill(img, x - 60 - bt * 160, 1000 - 220 * bt + 260 * bt * bt * 0.5, 0.7, ang=bt * 220 + i * 40)
        hosts(img, tt, 'side', mia_arms='point', leo_brows=1.0)
    elif name == 'poisson':
        r10 = tt - T('10')
        embarrassed = tt >= T('11')
        POI.draw(img, 520, 1250, 1.1, look=0, arms='face' if embarrassed else 'idle', blush=ease((tt - T('11')) / 0.4), blink=blink(tt, 6), smile=-0.5 if embarrassed else 0.2, brows=1.0)
        # phone on small table
        rect(img, 720, 1080, 900, 1100, C('#6e4a30')); rect(img, 740, 1100, 760, 1200, C('#6e4a30')); rect(img, 860, 1100, 880, 1200, C('#6e4a30'))
        rr(img, 760, 1030, 860, 1080, 10, C('#2b2b33')); ell(img, 810, 1022, 50, 14, C('#2b2b33'))
        bubble(img, 780, 620, 130, ease(r10 / 0.3))
        if r10 > 0.1:
            hat_c = POI  # draw police cap icon
            rr(img, 720, 560, 840, 620, 14, C('#1f2d5c')); ell(img, 780, 625, 70, 12, C('#111111')); circ(img, 780, 588, 13, C('#f2c94c'))
            blit_text(img, 'POLICE?', 780, 640, 40, C('#1f2d5c'))
        if embarrassed:
            k = ease((tt - T('11', 0.8)) / 0.25)
            line(img, (680, 540), (680 + 200 * k, 540 + 180 * k), C('#d33b3b'), 16)
            line(img, (880, 540), (880 - 200 * k, 540 + 180 * k), C('#d33b3b'), 16)
        hosts(img, tt, 'side', leo_arms='up' if tt >= T('12') else ('point2' if tt < T('11') else 'idle'), leo_brows=1.0, mia_arms='shrug' if T('11') <= tt < T('12') else 'idle')
    elif name == 'again':
        x = -150 + 640 * easeio(tl / 1.8)
        walking = tl < 1.8
        LUS.draw(img, x, 1240, 1.0, look=1 if walking else -0.5, walk=tl * 7, walking=walking, arms='hold', blink=blink(tt, 3), smile=1.0, brows=0.6)
        hx, hy = LUS.hands[1]
        rr(img, hx - 10, hy - 170, hx + 230, hy - 40, 8, C('#fbf6e8')); rect(img, hx - 4, hy - 40, hx + 6, hy + 20, C('#6e4a30'))
        blit_text(img, 'FOR SALE', hx + 110, hy - 140, 44, C('#d33b3b'))
        blit_text(img, 'call Victor', hx + 110, hy - 88, 30, C('#2d3a5c'))
        blit_text(img, 'AGAIN?!', 540, 470, 96, C('#ffde59'), scale=max(0.01, pop(tt, T('13', 3.2))), stroke=6, stroke_col=C('#2b2b33'))
        hosts(img, tt, 'side', leo_arms='face' if tt > T('13', 3.2) else 'idle', leo_brows=1.0, mia_arms='point')
    elif name == 'end':
        r14 = tt - T('14')
        hosts(img, tt, 'center', leo_arms='cheer' if r14 < 2.4 else ('point2' if r14 < 4.5 else 'wave'), mia_arms='hips' if r14 < 4.5 else 'wave',
              leo_smile=1.0, mia_smile=1.0, mia_look=1, leo_look=0)
        follow_button(img, tt, T('14', 4.6))
        cap_y = 580
    return img, cap_y

def caption(img, tt, cap_y):
    c = caption_at(tt)
    if not c: return
    txt, t0, spk = c
    col = C('#7fe3dc') if spk == 'M' else C('#ffd35a')
    words = txt.split(); lines = []; cur = ''
    maxw = 860 if cap_y < 1000 else 520
    for w_ in words:
        test = (cur + ' ' + w_).strip()
        if text_w(test, 46) > maxw and cur: lines.append(cur); cur = w_
        else: cur = test
    lines.append(cur)
    s = pop(tt, t0, 0.25)
    if s <= 0.01: return
    name = 'MIA' if spk == 'M' else 'LEO'
    blit_text(img, name, 540, cap_y - 44, 30, col, stroke=3, stroke_col=(20, 20, 20), scale=max(0.01, s))
    for i, ln in enumerate(lines):
        blit_text(img, ln, 540, cap_y + i * 60, 46, (255, 255, 255), stroke=5, stroke_col=(25, 20, 30), scale=max(0.01, s))

def frame(tt):
    name, ts, idx = scene_at(tt)
    img, cap_y = scene(name, tt, ts)
    # transition: quick crossfade from previous scene
    if idx > 0 and tt - ts < 0.22:
        pn, pts_ = SCENES[idx - 1]
        prev, _ = scene(pn, tt, pts_)
        a = (tt - ts) / 0.22
        img = cv2.addWeighted(img, a, prev, 1 - a, 0)
    # slow camera push
    z = 1.0 + 0.035 * min(1, (tt - ts) / 6)
    if z > 1.001:
        M = cv2.getRotationMatrix2D((W / 2, H * 0.55), 0, z)
        img = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    caption(img, tt, cap_y)
    # title
    blit_text(img, 'The man who SOLD', 540, 210, 52, (255, 255, 255), stroke=5, stroke_col=C('#2b2b33'))
    blit_text(img, 'the Eiffel Tower', 540, 272, 52, C('#ffde59'), stroke=5, stroke_col=C('#2b2b33'))
    return img

# ---------------- audio ----------------
def synth_audio(path):
    n = int((DURATION + 0.5) * SR)
    mus = np.zeros(n); vo = np.zeros(n); sfx = np.zeros(n)
    for v in VO:
        a = load_audio(os.path.join(HERE, 'voice', v['id'] + '.mp3'))
        s = int(v['t0'] * SR); vo[s:s + len(a)] += a[:n - s]
    # music: light swing, 120 bpm, Paris-cafe vibe (pizz bass + piano chords + brush hat)
    bpm = 120; beat = 60 / bpm
    prog = [('C', [48, 52, 55, 59]), ('A', [45, 52, 55, 60]), ('D', [50, 53, 57, 60]), ('G', [43, 53, 55, 59])]
    tt = np.arange(n) / SR
    def note(f, dur, kind):
        m = int(dur * SR); x = np.arange(m) / SR
        if kind == 'bass':
            return (np.sin(2 * np.pi * f * x) + 0.3 * np.sin(4 * np.pi * f * x)) * np.exp(-x * 6)
        if kind == 'keys':
            return (np.sin(2 * np.pi * f * x) + 0.4 * np.sin(4 * np.pi * f * x) + 0.15 * np.sin(6 * np.pi * f * x)) * np.exp(-x * 3.5)
        return np.zeros(m)
    hz = lambda m: 440 * 2 ** ((m - 69) / 12)
    nb = int(DURATION / beat) + 1
    rng = np.random.default_rng(3)
    for b in range(nb):
        bar = (b // 4) % 4; root, ch = prog[bar]
        t0 = b * beat
        s = int(t0 * SR)
        walk = [ch[0], ch[0] + 4, ch[0] + 7, ch[0] + 5][b % 4]
        y = note(hz(walk - 12 + 12), beat * 0.95, 'bass') * 0.22
        e = min(n, s + len(y)); mus[s:e] += y[:e - s]
        if b % 2 == 1:  # off-beat chord stabs (swing)
            s2 = int((t0 + beat * 0.0) * SR)
            for m in ch[1:]:
                y = note(hz(m + 12), beat * 0.9, 'keys') * 0.06
                e = min(n, s2 + len(y)); mus[s2:e] += y[:e - s2]
        # brush
        for off in (0, beat * 0.66):
            s3 = int((t0 + off) * SR); m = int(0.07 * SR)
            y = rng.standard_normal(m) * np.exp(-np.arange(m) / (0.015 * SR)) * (0.03 if off else 0.05)
            e = min(n, s3 + m); mus[s3:e] += y[:e - s3]
    # simple melody hook on accordion-ish square over first 4 s and end
    # ducking
    env = np.convolve(np.abs(vo), np.ones(2205) / 2205, 'same')
    duck = 1 - 0.55 * np.clip(env / (env.max() * 0.15 + 1e-9), 0, 1)
    duck = np.convolve(duck, np.ones(4410) / 4410, 'same')
    mus *= duck
    # sfx
    def add(t0, y):
        s = int(t0 * SR); e = min(n, s + len(y)); sfx[s:e] += y[:e - s]
    def whoosh(d=0.35):
        m = int(d * SR); x = np.arange(m) / m
        y = rng.standard_normal(m); y = np.convolve(y, np.ones(20) / 20, 'same')
        return y * np.sin(np.pi * x) ** 2 * 0.18
    def thud():
        m = int(0.4 * SR); x = np.arange(m) / SR
        return np.sin(2 * np.pi * (70 + 120 * np.exp(-x * 30)) * x) * np.exp(-x * 10) * 0.6 + rng.standard_normal(m) * np.exp(-x * 60) * 0.15
    def ding():
        m = int(1.0 * SR); x = np.arange(m) / SR
        return sum(np.sin(2 * np.pi * f * x) for f in (1568, 2093, 2637)) * np.exp(-x * 4) * 0.09
    def kaching():
        m = int(0.8 * SR); x = np.arange(m) / SR
        y = rng.standard_normal(m) * np.exp(-x * 40) * 0.2
        y[int(0.08 * SR):] += (sum(np.sin(2 * np.pi * f * x[:m - int(0.08 * SR)]) for f in (2349, 3136)) * np.exp(-x[:m - int(0.08 * SR)] * 5) * 0.12)
        return y
    def popsnd():
        m = int(0.15 * SR); x = np.arange(m) / SR
        return np.sin(2 * np.pi * (400 + 900 * x / 0.15) * x) * np.exp(-x * 25) * 0.2
    for name, ts in SCENES[1:]: add(ts - 0.1, whoosh())
    add(T('05', 3.0) + 0.85, thud())                    # stamp
    add(T('05', 17.2), thud())                           # top secret stamp
    add(T('05', 10.7), whoosh(0.25))
    add(T('05', 13.8), popsnd())
    add(T('07', 2.6), kaching()); add(T('07', 4.7), popsnd()); add(T('07', 5.5), kaching())
    for k in range(int((T('10') - T('09')) / 0.16)):    # running steps
        m = int(0.05 * SR); x = np.arange(m) / SR
        add(T('09') - 0.1 + k * 0.16, rng.standard_normal(m) * np.exp(-x * 120) * 0.12)
    add(T('11', 0.8), thud())
    add(T('13', 3.2), popsnd()); add(T('13', 3.2), ding())
    add(T('14', 4.6), popsnd())
    add(0.2, thud())
    mix = vo * 1.0 + mus * 0.9 + sfx
    fade = int(1.2 * SR); endi = int(DURATION * SR)
    mix[endi - fade:endi] *= np.linspace(1, 0, fade); mix = mix[:endi]
    mix /= np.abs(mix).max() * 1.05
    st = np.stack([mix, mix], 1)
    with wave.open(path, 'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())

if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
    m = sys.argv[1]
    if m == 'info':
        print('duration', round(DURATION, 2)); print([(s, round(t_, 2)) for s, t_ in SCENES])
    elif m == 'stills':
        for s in sys.argv[2:]: cv2.imwrite(os.path.join(HERE, 'out', f's_{s}.png'), frame(float(s)))
    elif m == 'audio':
        synth_audio(os.path.join(HERE, 'out', 'mix.wav'))
    elif m == 'video':
        a, b, part = float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
        out = os.path.join(HERE, 'out', f'part{part}.mp4'); tmp = out + '.tmp.mp4'
        p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                              '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '19', '-pix_fmt', 'yuv420p', tmp], stdin=subprocess.PIPE)
        for i in range(int(round(a * FPS)), int(round(b * FPS))):
            p.stdin.write(frame(i / FPS).tobytes())
        p.stdin.close(); p.wait(); os.replace(tmp, out)
