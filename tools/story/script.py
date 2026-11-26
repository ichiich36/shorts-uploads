"""Narration script for 'How Cars Work - Part 2 (v3): The Gearbox' and timing helpers."""
import json
import re

SEGMENTS = [
    ("A", "In 1932, Australia declared war."),
    ("B", "The enemy? Twenty thousand emus."),
    ("C", "The birds were eating the farmers' wheat."),
    ("D", "So the army sent its finest: three soldiers, two machine guns, and ten thousand bullets."),
    ("E", "Day one. The soldiers waited until the emus came close. Fire!"),
    ("F", "The gun jammed. The emus ran away."),
    ("G", "So they mounted a gun on a truck. But the emus were faster, and the road was so bumpy, nobody could aim."),
    ("H", "After six days, they had fired two and a half thousand bullets. The emus? Mostly fine."),
    ("I", "The army went home. Then came back. Then went home again."),
    ("J", "In the end: almost ten thousand bullets, for less than a thousand emus. Ten bullets per bird."),
    ("K", "And the emus? Still there. Australia lost a war... to birds."),
    ("L", "Follow for more crazy true stories!"),
]


def norm(w):
    return re.sub(r"[^a-z0-9'-]", "", w.lower())


def syllables(word):
    if any(ch.isdigit() for ch in word):
        return 5
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
