#!/usr/bin/env python3
"""Tech-Takt fuer TikTok tech.nik4: Wachstums-Log fuehren und entscheiden, ob jetzt ein neues Tech-Video kommt.

Regeln und Hintergrund: tech_growth_rules.md (die Parameter unten muessen dazu passen).

  python3 tools/tech/growth_check.py --append windsor.json
      haengt fuer jedes Video der letzten 3 Tage eine Zeile an tech_growth_log.csv an
      (windsor.json = Ergebnis von Windsor get_data, als {"data": [...]} oder als Liste)
      und gibt danach die Entscheidung aus.
  python3 tools/tech/growth_check.py
      nur entscheiden (aus dem vorhandenen Log)

  --now 2026-11-27T10:00:00   Referenzzeit in UTC (fuer Tests), Standard: jetzt
  --log / --rules PATH        andere Dateien (fuer Tests)
  --dry-run                   nichts schreiben

Letzte Zeile der Ausgabe: "ENTSCHEIDUNG: POSTEN - ..." oder "ENTSCHEIDUNG: WARTEN - ...". Exit-Code immer 0.
"""
import argparse
import csv
import json
import os
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
LOG = os.path.join(REPO, "tech_growth_log.csv")
RULES = os.path.join(REPO, "tech_growth_rules.md")
HEADER = ["fetched_at_utc", "video_id", "created_at_utc", "caption_short", "views", "likes", "shares",
          "avg_watch_s", "full_watch_rate", "new_followers"]
BERLIN = ZoneInfo("Europe/Berlin")

# --- Parameter (gleich wie in tech_growth_rules.md; Aenderungen dort mit Datum + Grund eintragen) ---
KEEP_DAYS = 3              # nur Videos der letzten 3 Tage loggen
MIN_AGE_H = 4.0            # Sock-Delay: vorher nie posten
MIN_GAP_H = 4.0            # Mindestabstand zwischen zwei Tech-Posts (auch TikTok-only Nachhol-Posts)
QUIET_UNTIL = 8            # 00:00-07:59 Uhr Berlin: nicht posten
WIN_H = 3.0                # Zeitfenster fuer den Zuwachs
MIN_ABS, MIN_REL = 5, 0.05  # Stillstand: Zuwachs in WIN_H < max(5, 5 % der aktuellen Aufrufe)
STALE_H = 3.0              # Daten aelter als das = "stehen mehrere Stunden" (Cache)
STALE_AGE_H = 8.0          # ... dann ab diesem Alter Zuwachs 0 = Stillstand (seit 28.11. nur, wenn das Video beim
                           #     letzten frischen Snapshot schon flach war, sonst WAECHST_ZULETZT -> warten)
EMERGENCY_H = 24.0         # Notbremse
MISSING_TOL_H = 0.25       # Post-Protokoll neuer als neuestes Video + Toleranz -> Video fehlt noch in den Daten

# Seit 2026-11-27 liefert Windsor tiktok_organic 3 Konten (Tech Nik, FactPulse = Autos, Tiny Tales = Storys).
# Abruf deshalb mit accounts [TECH_ACCOUNT_ID]. Liefert der nur Cache, Ersatz-Abruf ohne Filter (eigener Windsor-Cache,
# siehe tech_growth_rules.md) - dann greift dieser Schutz:
TECH_ACCOUNT = "Tech Nik"                                   # = tech.nik4
TECH_ACCOUNT_ID = "_000O2MjrBlBL3ioBnyTn44UQykVqxO0TFdj"
FOREIGN_TAGS = ("#howcarswork", "#truestory", "#storytime")  # Autos (FactPulse) / Storys (Tiny Tales)


def utc(s):
    d = datetime.fromisoformat(str(s).strip().replace("Z", "+00:00"))
    return d.replace(tzinfo=timezone.utc) if d.tzinfo is None else d.astimezone(timezone.utc)


def iso(d):
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def hours(td):
    return td.total_seconds() / 3600.0


def short(caption, n=40):
    text = " ".join(re.sub(r"#\S+", " ", caption or "").split())
    if len(text) <= n:
        return text
    cut = text[:n]
    space = cut.rfind(" ")
    return (cut[:space] if space > n // 2 else cut).rstrip(" ,.;:-")


def cell(v):
    return "" if v is None else str(v)


def read_log(path):
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ensure_log(path):
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(HEADER)


def append(path, payload, now, dry):
    data = payload.get("data", []) if isinstance(payload, dict) else payload
    rows = read_log(path)
    last_fetch = {r["video_id"]: r["fetched_at_utc"] for r in rows}   # letzte Zeile je Video
    new, foreign, older = [], [], []
    for d in data or []:
        acc = d.get("account_name")
        cap = (d.get("video_caption") or "").lower()
        if (acc is not None and acc != TECH_ACCOUNT) or (acc is None and any(t in cap for t in FOREIGN_TAGS)):
            foreign.append(f"{acc or '?'}: {short(d.get('video_caption'), 30)}")
            continue
        created = utc(d["video_create_datetime"])
        if hours(now - created) > KEEP_DAYS * 24:
            continue
        if d.get("data_fetched_at"):
            fetched = iso(utc(d["data_fetched_at"]))
        else:
            fetched = iso(now)
            print("WARNUNG: data_fetched_at fehlt - Laufzeit statt Abrufzeit geloggt")
        vid = str(d["video_id"])
        if last_fetch.get(vid) and utc(fetched) < utc(last_fetch[vid]):
            # z. B. Ersatz-Abruf ohne accounts-Filter liefert aelteren Cache als schon im Log -> nicht loggen,
            # sonst stimmen "letzte Zeile" (Cache-Erkennung) und Kurve nicht mehr
            older.append(short(d.get("video_caption"), 30))
            continue
        row = {"fetched_at_utc": fetched, "video_id": vid, "created_at_utc": iso(created),
               "caption_short": short(d.get("video_caption")), "views": cell(d.get("video_views_count")),
               "likes": cell(d.get("video_likes")), "shares": cell(d.get("video_shares")),
               "avg_watch_s": cell(d.get("video_average_time_watched")),
               "full_watch_rate": cell(d.get("video_full_watched_rate")),
               "new_followers": cell(d.get("video_new_followers"))}
        if last_fetch.get(vid) == fetched:
            print(f"Cache: '{row['caption_short']}' hat dasselbe data_fetched_at ({fetched}) wie die letzte Zeile"
                  " -> zaehlt als unbekannt, nicht als Stillstand")
        new.append(row)
    if foreign:
        print(f"Hinweis: {len(foreign)} Video(s) anderer Konten uebersprungen ({'; '.join(foreign)}) - normal beim"
              f" Ersatz-Abruf ohne accounts-Filter, sonst Windsor-Abruf mit accounts [\"{TECH_ACCOUNT_ID}\"] machen")
    if older:
        print(f"WARNUNG: {len(older)} Zeile(n) nicht geloggt, weil aelter als die letzte Log-Zeile desselben Videos"
              f" ({'; '.join(older)}) - frischeres Abruf-Ergebnis verwenden")
    new.sort(key=lambda r: r["created_at_utc"])
    if not dry:
        ensure_log(path)
        with open(path, "a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=HEADER).writerows(new)
    print(f"{len(new)} Zeile(n) an {os.path.basename(path)} angehaengt" + (" (dry-run, nicht geschrieben)" if dry else ""))
    return rows + new


def logged_posts(path):
    """Zeitpunkte aus dem Post-Protokoll in tech_growth_rules.md (Zeilen '- JJJJ-MM-TTTHH:MM:SSZ | ...')."""
    out = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                m = re.match(r"\s*-\s*(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ)\s*\|", line)
                if m:
                    out.append(utc(m.group(1)))
    return out


def views_at(pts, t):
    """Aufrufe zum Zeitpunkt t, linear zwischen den Punkten; vor der Veroeffentlichung 0."""
    if t <= pts[0][0]:
        return 0.0
    for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
        if t <= t1:
            span = max((t1 - t0).total_seconds(), 1e-9)
            return v0 + (v1 - v0) * (t - t0).total_seconds() / span
    return pts[-1][1]


def decide(rows, now, posts):
    berlin = now.astimezone(BERLIN)
    quiet = berlin.hour < QUIET_UNTIL
    if not rows:
        return "WARTEN", "keine Daten im Log"
    by = {}
    for r in rows:
        by.setdefault(r["video_id"], []).append(r)
    vid = max(by, key=lambda k: utc(by[k][-1]["created_at_utc"]))
    rs = by[vid]
    created = utc(rs[-1]["created_at_utc"])
    name = rs[-1]["caption_short"]
    age = hours(now - created)

    snaps = {}                                   # gleiches data_fetched_at = derselbe (Cache-)Snapshot
    for r in rs:
        try:
            snaps[utc(r["fetched_at_utc"])] = float(r["views"])
        except (KeyError, ValueError):
            pass
    pts = [(created, 0.0)] + sorted((t, v) for t, v in snaps.items() if t > created)
    t_last, v_last = pts[-1]
    have = len(pts) > 1
    data_age = hours(now - t_last) if have else float("inf")
    stale_run = len(rs) >= 2 and rs[-1]["fetched_at_utc"] == rs[-2]["fetched_at_utc"]
    fresh = have and not stale_run and data_age < STALE_H
    g3 = max(0.0, v_last - views_at(pts, t_last - timedelta(hours=WIN_H)))
    g1 = max(0.0, v_last - views_at(pts, t_last - timedelta(hours=1)))
    g0 = max(0.0, views_at(pts, t_last - timedelta(hours=1)) - views_at(pts, t_last - timedelta(hours=2)))
    thr = max(MIN_ABS, MIN_REL * v_last)

    if not have:
        status, why = "UNBEKANNT", "noch kein Snapshot"
    elif fresh:
        if g3 >= thr:
            status, why = "WAECHST", f"+{g3:.0f} Aufrufe in 3 h (Schwelle {thr:.0f})"
        elif g1 > g0:
            status, why = "SCHUB_BEGINNT", f"letzte Stunde +{g1:.0f} > Stunde davor +{g0:.0f}"
        else:
            status, why = "STILLSTAND", (f"+{g3:.0f} Aufrufe in 3 h (< {thr:.0f}), letzte Stunde +{g1:.0f}"
                                         f" nicht mehr als davor (+{g0:.0f})")
    elif data_age >= STALE_H and age >= STALE_AGE_H and g3 >= thr:
        # seit 2026-11-28: Escape the Rings lag beim letzten frischen Snapshot (3 h) bei 267 und hatte 6 h spaeter 617
        # -> wer beim letzten frischen Stand noch wuchs, gilt nicht als Stillstand, nur weil Windsor nichts Neues liefert
        status, why = "WAECHST_ZULETZT", (f"Daten stehen seit {data_age:.1f} h (Cache), beim letzten frischen Snapshot"
                                          f" aber noch +{g3:.0f} Aufrufe in 3 h (Schwelle {thr:.0f}) -> Schub hat"
                                          " Vorrang, auf frische Daten warten")
    elif data_age >= STALE_H and age >= STALE_AGE_H:
        status, why = "STILLSTAND", (f"Daten stehen seit {data_age:.1f} h (Cache), Alter >= {STALE_AGE_H:.0f} h, beim"
                                     f" letzten frischen Snapshot schon flach (+{g3:.0f} in 3 h < {thr:.0f})"
                                     " -> Zuwachs 0")
    else:
        status, why = "UNBEKANNT", ("veralteter Cache (data_fetched_at wie in der letzten Zeile)" if stale_run
                                    else f"Daten {data_age:.1f} h alt")

    print(f"Letztes Video: '{name}' ({vid}), veroeffentlicht {iso(created)} UTC, Alter {age:.1f} h")
    if have:
        print(f"Aufrufe {v_last:.0f} (Snapshot {iso(t_last)} UTC, Datenalter {data_age:.1f} h,"
              f" {'frisch' if fresh else 'Cache/alt'}, {len(pts) - 1} Snapshot(s))")
        print(f"Zuwachs 3 h: +{g3:.0f} (Schwelle {thr:.0f}) | letzte Stunde: +{g1:.0f} | Stunde davor: +{g0:.0f}")
    print(f"Status: {status} - {why}")
    print(f"Berlin: {berlin:%Y-%m-%d %H:%M}" + (" (Nachtruhe)" if quiet else ""))

    last_post = max([created] + posts)
    gap = hours(now - last_post)
    missing = bool(posts) and max(posts) > created + timedelta(hours=MISSING_TOL_H)
    if missing and gap < EMERGENCY_H:
        return "WARTEN", (f"letzter Post laut Protokoll ({iso(max(posts))} UTC) ist noch nicht in den Windsor-Daten"
                          f" ({gap:.1f} h her)")
    if age < MIN_AGE_H or gap < MIN_GAP_H:
        return "WARTEN", f"Sock-Delay/Abstand: letzter Tech-Post erst {min(age, gap):.1f} h her (< 4 h); {status}"
    want = None
    if age >= EMERGENCY_H and not (fresh and status == "WAECHST"):
        want = f"Notbremse: '{name}' ist {age:.1f} h alt ({status}: {why})"
    elif status == "STILLSTAND":
        want = f"Stillstand bei '{name}' nach {age:.1f} h: {why}"
    if want is None:
        if age >= EMERGENCY_H:
            return "WARTEN", f"Schub hat Vorrang vor der Notbremse: {why}"
        return "WARTEN", f"{status}: {why}"
    if quiet:
        return "WARTEN", f"{want} - aber Nachtruhe ({berlin:%H:%M} Berlin), Post ab 08:00"
    return "POSTEN", want


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--append", metavar="JSON", help="Windsor get_data Ergebnis anhaengen")
    ap.add_argument("--now", help="Referenzzeit UTC (Tests)")
    ap.add_argument("--log", default=LOG)
    ap.add_argument("--rules", default=RULES)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    now = utc(a.now) if a.now else datetime.now(timezone.utc)
    if a.append:
        with open(a.append, encoding="utf-8") as f:
            rows = append(a.log, json.load(f), now, a.dry_run)
    else:
        if not a.dry_run:
            ensure_log(a.log)
        rows = read_log(a.log)
    decision, reason = decide(rows, now, logged_posts(a.rules))
    print(f"ENTSCHEIDUNG: {decision} - {reason}")


if __name__ == "__main__":
    main()
