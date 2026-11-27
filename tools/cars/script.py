"""Narration script for 'How Cars Work - Part 4: The Differential' and timing helpers."""
import json
import re

SEGMENTS = [
    ("A", "Your wheels spin at different speeds in every corner. So how can one engine drive both? Part four of our car series."),
    ("B", "The outside wheel has farther to go. On a solid axle, both would turn at the same speed, so one tire would skid."),
    ("C", "The fix is the differential. The driveshaft spins a small pinion gear, which turns a big ring gear."),
    ("D", "Bolted to the ring gear is a cage holding small spider gears. They mesh with two side gears, one per wheel."),
    ("E", "Going straight, the spider gears don't turn on their pin. The whole cage spins as one block, so both wheels turn equally."),
    ("F", "In a corner, the inside wheel slows down. The spider gears start to turn, and the outside wheel speeds up by exactly that much."),
    ("G", "Ring gear at one hundred RPM? Ninety inside, one hundred ten outside. The average stays one hundred."),
    ("H", "But there's a catch: an open differential sends equal torque to both wheels. If one is on ice, it spins, and the other gets almost nothing."),
    ("I", "That's why many sports cars and off-roaders use limited-slip or locking differentials."),
    ("K", "Next: the brakes, and how one foot can stop a two-ton car. Follow for part five!"),
]


def norm(w):
    return re.sub(r"[^a-z0-9'-]", "", w.lower())


SYL_OVERRIDE = {"rpm": 3, "ev": 2, "abs": 3, "ecu": 3}  # abbreviations are spoken letter by letter


def syllables(word):
    w = re.sub(r"[^a-z]", "", word.lower())
    if w in SYL_OVERRIDE:
        return SYL_OVERRIDE[w]
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
