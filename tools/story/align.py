"""Align the known script to the narration audio -> timeline.json (word start/end times).

Pauses in the audio are matched to punctuation in the script (dynamic programming);
words between anchors are spread by syllable count.
Usage: python3 align.py voice.mp3
"""
import json
import math
import subprocess
import sys

import numpy as np

import script as S

SR = 16000


def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32)


def speech_mask(x):
    hop, win = SR // 100, int(0.03 * SR)
    n = max(1, (len(x) - win) // hop)
    idx = np.arange(win)[None, :] + hop * np.arange(n)[:, None]
    e = np.sqrt(np.mean(x[idx] ** 2, axis=1) + 1e-12)
    db = 20 * np.log10(e + 1e-9)
    db = np.convolve(np.pad(db, 2, mode="edge"), np.ones(5) / 5, mode="valid")
    floor, peak = np.percentile(db, 8), np.percentile(db, 95)
    thr = floor + 0.30 * (peak - floor)
    return db > thr, hop / SR


def runs(mask, val):
    out, i = [], 0
    while i < len(mask):
        if mask[i] == val:
            j = i
            while j < len(mask) and mask[j] == val:
                j += 1
            out.append((i, j))
            i = j
        else:
            i += 1
    return out


def analyse(path):
    x = load(path)
    total_len = len(x) / SR
    m, dt = speech_mask(x)
    sp = runs(m, True)
    onset, offset = sp[0][0] * dt, sp[-1][1] * dt
    pauses = [(a * dt, b * dt) for a, b in runs(m, False) if a * dt > onset and b * dt < offset and (b - a) * dt >= 0.10]
    return total_len, onset, offset, pauses


def main(path):
    if path.endswith(".json"):
        d = json.load(open(path))
        total_len, onset, offset, pauses = d["len"], d["onset"], d["offset"], [tuple(p) for p in d["pauses"]]
    else:
        total_len, onset, offset, pauses = analyse(path)

    toks = S.tokens()
    syl = np.array([t["syl"] + 0.6 for t in toks], float)
    cands = [i for i, t in enumerate(toks[:-1]) if t["brk"] > 0]
    M, K = len(cands), len(pauses)
    speech_total = (offset - onset) - sum(b - a for a, b in pauses)
    R = syl.sum() / speech_total                      # global syllable rate
    csum = np.concatenate([[0], np.cumsum(syl)])

    def seg_cost(j0, k0, j1, k1):
        """Cost of matching candidate j1 to pause k1 right after the match (j0, k0); -1 = start, M/K = end."""
        w_from = 0 if j0 < 0 else cands[j0] + 1
        w_to = len(toks) - 1 if j1 >= M else cands[j1]
        S_ = csum[w_to + 1] - csum[w_from]
        t_from = onset if k0 < 0 else pauses[k0][1]
        t_to = offset if k1 >= K else pauses[k1][0]
        skipped_p = pauses[k0 + 1:k1] if k1 > k0 + 1 else []
        T = (t_to - t_from) - sum(b - a for a, b in skipped_p)
        if T <= 0.05:
            return 1e9
        c = 3.0 * math.log((S_ / T) / R) ** 2 * min(1.0, S_ / 10.0)
        skip_w = {1.0: 0.8, 0.7: 0.5, 0.45: 0.12}
        c += sum(skip_w.get(toks[cands[j]]["brk"], 0.3) for j in range(j0 + 1, min(j1, M)))
        c += sum(0.2 if b - a < 0.25 else 0.5 for a, b in skipped_p)
        return c

    INF = 1e18
    best = {(-1, -1): (0.0, None)}
    order = sorted([(j, k) for j in range(M) for k in range(K)]) + [(M, K)]
    for (j, k) in order:
        bc, bp = INF, None
        for (pj, pk), (pc, _) in best.items():
            if pj < j and pk < k and pc < INF:
                c = pc + seg_cost(pj, pk, j, k)
                if c < bc:
                    bc, bp = c, (pj, pk)
        best[(j, k)] = (bc, bp)
    matches, node = [], best[(M, K)][1]
    while node and node != (-1, -1):
        matches.append((cands[node[0]], pauses[node[1]]))
        node = best[node][1]
    matches.reverse()

    # anchors: (word index boundary, time). Word i ends at pause start, i+1 starts at pause end.
    starts = [None] * len(toks)
    ends = [None] * len(toks)
    starts[0] = onset
    ends[-1] = offset
    for wi, (a, b) in matches:
        ends[wi] = a
        starts[wi + 1] = b
    # fill spans between anchors proportionally to syllables
    i = 0
    while i < len(toks):
        j = i
        while ends[j] is None:
            j += 1
        s, e = starts[i], ends[j]
        w = syl[i:j + 1]
        c = np.concatenate([[0], np.cumsum(w)]) / w.sum()
        for n in range(i, j + 1):
            starts[n] = s + (e - s) * c[n - i]
            ends[n] = s + (e - s) * c[n - i + 1]
        i = j + 1

    words = [dict(t, start=round(starts[n], 3), end=round(ends[n], 3)) for n, t in enumerate(toks)]
    duration = round(offset + 1.0, 3)
    with open("timeline.json", "w") as fh:
        json.dump(dict(duration=duration, audio_len=round(total_len, 3), words=words), fh, indent=1)
    print(f"audio {total_len:.2f}s  speech {onset:.2f}-{offset:.2f}  pauses {K}  matched {len(matches)}/{M}")
    for seg, _ in S.SEGMENTS:
        ws = [w for w in words if w["seg"] == seg]
        print(seg, ws[0]["start"], ws[-1]["end"], " ".join(w["text"] for w in ws[:4]))


if __name__ == "__main__":
    main(sys.argv[1])
