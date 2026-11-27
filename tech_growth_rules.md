# Tech-Takt: Wann kommt das nächste Tech-Video? (TikTok tech.nik4)

Ziel Nr. 1: Geld verdienen → Reichweite, Zuschauerbindung, Abos. Ein neues Tech-Video kommt erst, wenn das letzte
TikTok-Video von tech.nik4 langsam aufhört zu wachsen. TikTok gibt oft erst nach einer Verzögerung („Sock-Delay“)
plötzlich einen Schub – deshalb lieber etwas zu spät als zu früh posten.
Jedes NEUE Tech-Video geht auf alle 3 Kanäle: YouTube techtbe24, TikTok tech.nik4, Instagram technik96.

## Ablauf jede Stunde
1. Windsor get_data: connector tiktok_organic (einziges Konto: „Tech Nik“ = tech.nik4), fields [video_id,
   video_create_datetime, video_caption, video_views_count, video_likes, video_shares, video_average_time_watched,
   video_full_watched_rate, video_new_followers, data_fetched_at], date_preset last_7dT, KEIN force_refresh.
2. Ergebnis-JSON als Datei speichern (Scratchpad) und ausführen:
   `python3 tools/tech/growth_check.py --append <datei.json>`
   → hängt für jedes Video der letzten 3 Tage eine Zeile an tech_growth_log.csv an und schreibt als letzte Zeile
   `ENTSCHEIDUNG: POSTEN|WARTEN - Grund`. Zahlen kurz auf Plausibilität prüfen.
3. Log committen und pushen (bei Konflikt `git pull --rebase`). Bei POSTEN: genau ein Video, danach unten im
   Post-Protokoll eintragen (Zeit in UTC, Video, Kanäle, Grund mit Aufrufen/Kurve des vorherigen Videos).

## Regeln (aktuell)
1. **Sock-Delay:** Nicht posten, solange das letzte Video jünger als 4 h ist.
2. **Nachtruhe:** Nicht posten zwischen 00:00 und 07:59 Uhr Europe/Berlin.
3. **Stillstand → posten:** Alter ≥ 4 h UND Aufrufe-Zuwachs der letzten 3 h (frische Snapshots)
   < max(5, 5 % der aktuellen Aufrufe) UND Zuwachs der letzten Stunde nicht größer als der der Stunde davor
   (kein beginnender Schub).
4. **Schub hat Vorrang:** Wächst das Video noch, NICHT posten.
5. **Cache:** Ist data_fetched_at gleich wie in der letzten Zeile desselben Videos, ist es veralteter Cache: Zeile
   trotzdem loggen, aber als „unbekannt“ werten, nicht als Stillstand. Stehen die Daten mehrere Stunden
   (Datenalter ≥ 3 h), gilt ab Alter ≥ 8 h Zuwachs 0 als Stillstand.
6. **Notbremse:** Alter ≥ 24 h → posten (zur nächsten erlaubten Uhrzeit). Nur ein laufender Schub mit frischen
   Daten (Zuwachs 3 h ≥ Schwelle) hält sie auf (Regel 4).
7. **Abstand:** Mindestens 4 h zwischen zwei Tech-Posts, auch bei TikTok-only Nachhol-Posts. Zählt der neuere
   Zeitpunkt aus „neuestes TikTok-Video“ und „letzter Eintrag im Post-Protokoll“. Ist ein gerade gepostetes Video
   noch nicht in den Windsor-Daten, wird gewartet (sonst droht ein Doppel-Post auf alten Cache-Daten).

## So rechnet growth_check.py
- Zeiten: video_create_datetime und data_fetched_at sind UTC (geprüft am 2026-11-26: Short 06 um 16:59:11 UTC
  committet, TikTok-Erstellzeit 16:59:58).
- Kurve = (Veröffentlichung, 0 Aufrufe) + alle eindeutigen Snapshots (gleiches data_fetched_at = ein Snapshot),
  dazwischen linear. Zuwächse werden vom neuesten Snapshot aus zurückgerechnet (3 h, letzte Stunde, Stunde davor).
- Die Parameter stehen oben im Skript. Regeländerung = Skript UND diese Datei anpassen und unten eintragen.

## Kurven früherer Videos (Beobachtungen)
- Short 01 Red vs Blue (TikTok 2026-11-25 12:26 UTC): 74 Aufrufe nach ~35 h, nach ~41 h immer noch 74 (steht);
  Ø 9,2 s gesehen, 1,2 % bis zum Ende, 1 Follower.
- Short 06 Perfect Sync (TikTok 2026-11-26 16:59 UTC): 150 Aufrufe nach ~6,5 h, 155 nach ~12,6 h → nach ~6 h fast
  flach; Ø 7,9 s gesehen, 15,6 % bis zum Ende.
- Short 03 Ball Grows (TikTok 2026-11-26 23:23 UTC): 11 Aufrufe nach 3 min, 200 nach ~6,2 h (Snapshot 27.11. 05:38 UTC;
  dazwischen nur Cache, Verlauf unbekannt); Ø 8,3 s gesehen, 2,7 % bis zum Ende.
- Offen (mit den Stunden-Snapshots klären): Wann kommt der Schub, wann flacht die Kurve ab? Erst dann Regeln anpassen.

## Änderungen an den Regeln (Datum – was – warum)
- 2026-11-26: Datei mit den Startregeln angelegt. Festgelegt: Notbremse gegen laufenden Schub (Regel 6) und Abstand
  über das Post-Protokoll (Regel 7), damit nie zwei Posts kurz hintereinander rausgehen, wenn Windsor alte Daten liefert.

## Post-Protokoll (neueste unten)
Format: `- JJJJ-MM-TTTHH:MM:SSZ | Video | Kanäle | Grund (Aufrufe/Kurve des vorherigen Videos)`
- 2026-11-25T12:26:35Z | Short 01 Red vs Blue | TikTok | vor Einführung des Takts (Zeit laut Windsor)
- 2026-11-26T16:59:58Z | Short 06 Perfect Sync | TikTok | vor Einführung des Takts (Zeit laut Windsor)
- 2026-11-26T23:23:15Z | Short 03 Ball Grows | TikTok | vor Einführung des Takts (Zeit laut Windsor)
