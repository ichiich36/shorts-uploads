def gear(img, glow, cx, cy, R, teeth, ang, col, hub=M_DARK, glow_k=0.0):
    poly(img, gear_pts(cx, cy, R, teeth, ang), C3(col))
    circle(img, cx, cy, R * 0.72, C3(mixc(col, (0, 0, 0), 0.18)))
    for k in range(5):
        aa = ang + k * 2 * math.pi / 5
        circle(img, cx + R * 0.45 * math.cos(aa), cy + R * 0.45 * math.sin(aa), R * 0.11, C3(hub))
    circle(img, cx, cy, max(10, R * 0.16), C3(hub))
    if glow_k > 0:
        circle(glow, cx, cy, R + 10, C3(col, glow_k), th=16, s=0.5)


def stripes(img, x0, y0, x1, y1, offset, col, gap=26, horiz=True):
    o = offset % gap
    if horiz:
        x = x0 - gap + o
        while x < x1:
            line(img, max(x0, x), y0 + 3, min(x1, x + 10), y1 - 3, C3(col), 3)
            x += gap
    else:
        y = y0 - gap + o
        while y < y1:
            if y > y0:
                line(img, x0 + 3, y, x1 - 3, y, C3(col), 3)
            y += gap




def tacho(img, glow, cx, cy, R, rpm, gear_n, shake=0.0, sweet=False, t=0.0):
    circle(img, cx, cy, R + 14, C3((14, 22, 40)))
    circle(img, cx, cy, R + 14, C3(M_MID), th=5)
    a0, a1 = math.radians(140), math.radians(400)

    def ang(v):
        return a0 + (a1 - a0) * v / 8.0
    if sweet:
        for k in range(24):
            v0, v1 = 2.0 + k * 2.0 / 24, 2.0 + (k + 1) * 2.0 / 24
            line(img, cx + (R - 16) * math.cos(ang(v0)), cy + (R - 16) * math.sin(ang(v0)),
                 cx + (R - 16) * math.cos(ang(v1)), cy + (R - 16) * math.sin(ang(v1)), C3(GREEN), 16)
    for k in range(24):
        v0, v1 = 6.0 + k * 2.0 / 24, 6.0 + (k + 1) * 2.0 / 24
        line(img, cx + (R - 16) * math.cos(ang(v0)), cy + (R - 16) * math.sin(ang(v0)),
             cx + (R - 16) * math.cos(ang(v1)), cy + (R - 16) * math.sin(ang(v1)), C3(RED), 16)
    for v in range(0, 9):
        a = ang(v)
        line(img, cx + (R - 36) * math.cos(a), cy + (R - 36) * math.sin(a), cx + (R - 4) * math.cos(a),
             cy + (R - 4) * math.sin(a), C3(M_HI), 5)
        blit(img, TICKN[v], cx + (R - 72) * math.cos(a), cy + (R - 72) * math.sin(a))
    blit(img, SPR_RPM, cx, cy + R * 0.42)
    v = max(0.0, min(8.2, rpm + shake * math.sin(t * 61) * 0.25))
    a = ang(v)
    col = RED if rpm > 6 else WHITE
    line(img, cx - 30 * math.cos(a), cy - 30 * math.sin(a), cx + (R - 30) * math.cos(a), cy + (R - 30) * math.sin(a), C3(col), 9)
    circle(img, cx, cy, 20, C3(M_HI))
    if rpm > 6:
        circle(glow, cx, cy, R + 20, C3(RED, 0.5 + 0.3 * math.sin(t * 20)), th=20, s=0.5)
    # gear indicator
    gx = cx + R + 110
    rrect(img, gx - 60, cy - 65, gx + 60, cy + 65, 18, C3((14, 22, 40)))
    rrect_outline(img, gx - 60, cy - 65, gx + 60, cy + 65, 18, C3(YEL), 4)
    blit(img, SPR_GEARLBL, gx, cy - 90)
    blit(img, DIGITS[str(gear_n)], gx, cy)




def draw_labels(frame, t):
    for text, col, lx, ly, target, t_on, t_off in LABELS:
        if t < t_on or t > t_off + 0.3:
            continue
        a = min(1.0, (t - t_on) / 0.25) * (1.0 if t < t_off else max(0.0, 1 - (t - t_off) / 0.3))
        if a <= 0.01:
            continue
        tx, ty = target(t)
        spr = label_sprite(text, col)
        w = (spr.shape[1] - 60) / 2
        edge_x = lx + w + 14 if lx < tx else lx - w - 14
        grow = min(1.0, (t - t_on) / 0.35)
        ex, ey = edge_x + (tx - edge_x) * grow, ly + (ty - ly) * grow
        x0 = int(max(0, min(lx - w - 14, ex) - 24))
        x1 = int(min(W, max(lx + w + 14, ex) + 24))
        y0 = int(max(0, min(ly - 30, ey) - 24))
        y1 = int(min(H, max(ly + 30, ey) + 24))
        before = frame[y0:y1, x0:x1].copy()
        line(frame, edge_x, ly, ex, ey, C3(col), 3)
        circle(frame, ex, ey, 7, C3(col))
        rrect(frame, lx - w - 14, ly - 26, lx + w + 14, ly + 26, 12, C3((10, 16, 30)))
        rrect_outline(frame, lx - w - 14, ly - 26, lx + w + 14, ly + 26, 12, C3(col), 2)
        blit(frame, spr, lx, ly + 2)
        if a < 0.999:
            after = frame[y0:y1, x0:x1].astype(np.float32)
            frame[y0:y1, x0:x1] = (before.astype(np.float32) * (1 - a) + after * a).astype(np.uint8)




# ------------------------------------------------------------------ captions
def make_chunks():
    chunks, cur = [], []
    for i, w in enumerate(TL.words):
        cur.append(i)
        if len(cur) >= 4 or w['brk'] >= 0.45 or w.get('last'):
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    return chunks


CHUNKS = make_chunks()
_cap = {}


def caption_sprite(ci, active):
    if (ci, active) not in _cap:
        parts = []
        hl = YEL
        for j, wi in enumerate(CHUNKS[ci]):
            txt = TL.words[wi]['text'].upper()
            parts.append((txt + (' ' if j < len(CHUNKS[ci]) - 1 else ''), hl if wi == active else WHITE))
        size = 68
        while True:
            spr = text_sprite(parts, font(F_BLACK, size), stroke=7, shadow=0.7)
            if spr.shape[1] - 60 <= 980 or size <= 44:
                break
            size -= 4
        _cap[(ci, active)] = spr
    return _cap[(ci, active)]


def draw_caption(frame, t):
    for ci, ch in enumerate(CHUNKS):
        s = TL.words[ch[0]]['start']
        e = TL.words[CHUNKS[ci + 1][0]]['start'] if ci + 1 < len(CHUNKS) else TL.words[ch[-1]]['end'] + 0.6
        e = min(e, TL.words[ch[-1]]['end'] + 0.9)
        if s - 0.05 <= t < e:
            active = ch[0]
            for wi in ch:
                if TL.words[wi]['start'] <= t:
                    active = wi
            blit(frame, caption_sprite(ci, active), W / 2, 1460, scale=1.0 + 0.06 * max(0.0, 1 - (t - s) / 0.12))
            return


