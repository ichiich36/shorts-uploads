#!/usr/bin/env python3
"""Rueckblick-Test fuer Regelaenderungen am Tech-Takt: Was haette growth_check.py frueher entschieden?

  python3 tools/tech/growth_replay.py                         jeder Eintrag im Post-Protokoll, 30 s vorher
  python3 tools/tech/growth_replay.py 2026-11-27T08:38:30     bestimmte Zeitpunkte (UTC)
  python3 tools/tech/growth_replay.py --script alt.py ...     andere Skript-Version (z. B. aus git show) zum Vergleich

Nimmt nur Log-Zeilen mit fetched_at <= Zeitpunkt und Post-Protokoll-Eintraege vor dem Zeitpunkt. Ein Snapshot aus
der letzten Stunde zaehlt nur einmal (so wie im echten Lauf, der ihn gerade erst geloggt hat).
Grenze: Das Log speichert nicht, wann eine Cache-Zeile geloggt wurde - Wiederholungen aelterer Snapshots zaehlen
alle mit. Fuer die Cache-Erkennung reicht das (sie prueft nur, ob die letzten zwei Zeilen gleich sind).
"""
import argparse
import contextlib
import csv
import importlib.util
import io
import os
import sys
from datetime import timedelta

sys.dont_write_bytecode = True   # kein __pycache__ im Repo

HERE = os.path.dirname(os.path.abspath(__file__))


def load(path):
    spec = importlib.util.spec_from_file_location("growth_check_replay", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("at", nargs="*", help="Zeitpunkte UTC, z. B. 2026-11-27T08:38:30")
    ap.add_argument("--script", default=os.path.join(HERE, "growth_check.py"))
    a = ap.parse_args()
    gc = load(a.script)
    repo = os.path.abspath(os.path.join(HERE, "..", ".."))       # Log/Regeln immer aus diesem Repo
    with open(os.path.join(repo, "tech_growth_log.csv"), newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    posts = gc.logged_posts(os.path.join(repo, "tech_growth_rules.md"))
    # Standard: 30 s vor jedem Post (der entscheidende Lauf hatte seinen Windsor-Abruf 2-3 min vor dem Post)
    times = [gc.utc(t) for t in a.at] or [p - timedelta(seconds=30) for p in posts]
    for now in times:
        rs, seen = [], set()
        for r in rows:
            t = gc.utc(r["fetched_at_utc"])
            if t > now:
                continue
            key = (r["video_id"], r["fetched_at_utc"])
            if now - t < timedelta(hours=1) and key in seen:
                continue
            seen.add(key)
            rs.append(r)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            decision, why = gc.decide(rs, now, [p for p in posts if p < now])
        status = next((l for l in buf.getvalue().splitlines() if l.startswith("Status")), "Status: -")
        print(f"{gc.iso(now)} UTC | {status}\n    -> {decision}: {why}")


if __name__ == "__main__":
    main()
