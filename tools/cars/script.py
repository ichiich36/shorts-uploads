"""Narration script for 'How Cars Work - Part 3: The Automatic' and timing helpers."""
import json
import re

SEGMENTS = [
    ("A", "No clutch pedal. No gear stick. So how does an automatic shift by itself? Part three of our car series."),
    ("B", "First, the clutch is replaced by a torque converter: two fans facing each other, sealed in oil."),
    ("C", "The engine spins one fan. It throws oil at the other one, and that one turns the wheels."),
    ("D", "At a red light, the oil simply slips. That's why the car can sit in drive without stalling."),
    ("E", "Second, the gears. An automatic uses planetary gear sets: a sun gear in the middle, planets around it, and a ring gear outside."),
    ("F", "Hold one part still, drive another, and the third turns at a new speed. That's a new gear."),
    ("G", "Small clutches inside decide which part is held. They're squeezed together by oil pressure."),
    ("H", "And a computer decides when. It reads your speed and the gas pedal, then shifts in a fraction of a second."),
    ("K", "Next: the differential, and why your wheels never turn at the same speed in a corner. Follow for part four!"),
]


def norm(w):
    return re.sub(r"[^a-z0-9'-]", "", w.lower())


def syllables(word):
    w = re.sub(r"[^a-z]", "", word.lower())
    if not w:
        return 1
    groups = re.findall(r"[aeiouy]+", w)
    n = len(groups)
    if w.endswith("e") and not w.endswith(("le", "ee")) and n > 1:
        n -= 1
    return max(1, n)


def tokens():
    """List of dicts: seg, text (with punctuation), key, syl, brk (pause weight after word)."""
    out = []
    for seg, text in SEGMENTS:
        words = text.split()
        for i, w in enumerate(words):
            syl = sum(syllables(p) for p in w.split("-"))
            brk = 0.0
            if w.endswith((".", "?", "!")):
                brk = 1.0
            elif w.endswith(":"):
                brk = 0.7
            elif w.endswith(","):
                brk = 0.45
            out.append(dict(seg=seg, text=w, key=norm(w), syl=syl, brk=brk, last=(i == len(words) - 1)))
    return out


def estimate_timeline(rate_syl=4.6, pause_s=0.38, lead=0.15):
    """Rough timings (preview only): syllables per second plus pauses at punctuation."""
    t = lead
    tl = []
    for tok in tokens():
        d = tok["syl"] / rate_syl + 0.04
        tl.append(dict(tok, start=round(t, 3), end=round(t + d, 3)))
        t += d + pause_s * tok["brk"]
    return tl


def load_timeline(path="timeline.json"):
    with open(path) as f:
        return json.load(f)


class Timeline:
    def __init__(self, words, duration):
        self.words = words
        self.duration = duration

    def seg_range(self, seg):
        ws = [w for w in self.words if w["seg"] == seg]
        return ws[0]["start"], ws[-1]["end"]

    def seg_start(self, seg):
        return self.seg_range(seg)[0]

    def word(self, seg, key, nth=1):
        """(start, end) of the nth occurrence of key inside segment seg."""
        c = 0
        for w in self.words:
            if w["seg"] == seg and w["key"] == key:
                c += 1
                if c == nth:
                    return w["start"], w["end"]
        raise KeyError((seg, key, nth))


if __name__ == "__main__":
    tl = estimate_timeline()
    print(len(tl), "words, est. end", tl[-1]["end"])
    for seg, _ in SEGMENTS:
        ws = [w for w in tl if w["seg"] == seg]
        print(seg, ws[0]["start"], ws[-1]["end"])
