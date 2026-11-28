# Tech-Takt: Wann kommt das nächste Tech-Video? (TikTok tech.nik4)

Ziel Nr. 1: Geld verdienen → Reichweite, Zuschauerbindung, Abos. Ein neues Tech-Video kommt erst, wenn das letzte
TikTok-Video von tech.nik4 langsam aufhört zu wachsen. TikTok gibt oft erst nach einer Verzögerung („Sock-Delay“)
plötzlich einen Schub – deshalb lieber etwas zu spät als zu früh posten.
Jedes NEUE Tech-Video geht auf alle 3 Kanäle: YouTube techtbe24, TikTok tech.nik4, Instagram technik96.

## Ablauf jede Stunde
1. Windsor get_data: connector tiktok_organic, **accounts ["_000O2MjrBlBL3ioBnyTn44UQykVqxO0TFdj"]** (= „Tech Nik“ =
   tech.nik4), fields [video_id, video_create_datetime, video_caption, video_views_count, video_likes, video_shares,
   video_average_time_watched, video_full_watched_rate, video_new_followers, data_fetched_at], date_preset last_7dT,
   KEIN force_refresh. Seit 27.11. ~20 Uhr UTC hat Windsor 3 TikTok-Konten (Tech Nik, FactPulse = Autos, Tiny Tales =
   Storys) → ohne accounts-Filter kämen Auto- und Story-Videos ins Log und würden als „letztes Video“ gelten.
   Feldliste sonst unverändert lassen (andere Felder = eigener Windsor-Cache mit eigenem data_fetched_at).
   growth_check.py überspringt zur Sicherheit Videos anderer Konten (account_name ≠ „Tech Nik“, falls das Feld
   mitkommt, sonst Captions mit #howcarswork/#truestory/#storytime) und meldet das als Hinweis.
   **Ersatz-Abruf (seit 28.11.):** Liefert der gefilterte Abruf dasselbe data_fetched_at wie die letzte Log-Zeile
   (Cache), denselben Abruf einmal OHNE accounts-Filter wiederholen (sonst alles gleich, auch KEIN force_refresh).
   Das ist ein eigener Windsor-Cache mit eigenem Takt (28.11. 02:38 UTC: gefiltert noch 20:38:30, ungefiltert frisch
   02:37:49). Nur das Ergebnis mit dem neueren data_fetched_at loggen; growth_check.py überspringt die Auto-/Story-
   Videos und loggt nie Daten, die älter sind als die letzte Zeile desselben Videos.
2. Ergebnis-JSON als Datei speichern (Scratchpad) und ausführen:
   `python3 tools/tech/growth_check.py --append <datei.json>`
   → hängt für jedes Video der letzten 3 Tage eine Zeile an tech_growth_log.csv an und schreibt als letzte Zeile
   `ENTSCHEIDUNG: POSTEN|WARTEN - Grund`. Zahlen kurz auf Plausibilität prüfen.
3. Log committen und pushen (bei Konflikt `git pull --rebase`). Bei POSTEN: genau ein Video, danach unten im
   Post-Protokoll eintragen (Zeit in UTC, Video, Kanäle, Grund mit Aufrufen/Kurve des vorherigen Videos).
4. Buffer-Entwurf veröffentlichen (Nachholen): `edit_post` mit postId, mode `shareNow` UND `saveToDraft: false`.
   Nur mode shareNow lässt den Post als Entwurf liegen (getestet 2026-11-27). Danach mit `get_post` prüfen:
   scheduled → sending → sent (dauert ~2 min), externalLink = TikTok-Link.

## Regeln (aktuell)
1. **Sock-Delay:** Nicht posten, solange das letzte Video jünger als 4 h ist.
2. **Nachtruhe:** Nicht posten zwischen 00:00 und 07:59 Uhr Europe/Berlin.
3. **Stillstand → posten:** Alter ≥ 4 h UND Aufrufe-Zuwachs der letzten 3 h (frische Snapshots)
   < max(5, 5 % der aktuellen Aufrufe) UND Zuwachs der letzten Stunde nicht größer als der der Stunde davor
   (kein beginnender Schub).
4. **Schub hat Vorrang:** Wächst das Video noch, NICHT posten.
5. **Cache:** Ist data_fetched_at gleich wie in der letzten Zeile desselben Videos, ist es veralteter Cache: Zeile
   trotzdem loggen, aber als „unbekannt“ werten, nicht als Stillstand. Stehen die Daten mehrere Stunden
   (Datenalter ≥ 3 h), gilt ab Alter ≥ 8 h Zuwachs 0 als Stillstand – **aber nur, wenn das Video schon beim letzten
   frischen Snapshot flach war** (Zuwachs in den 3 h vor diesem Snapshot < Schwelle aus Regel 3). Wuchs es da noch
   (Status WAECHST_ZULETZT), auf den nächsten frischen Snapshot warten – Schub hat Vorrang; Notbremse (Regel 6) gilt.
6. **Notbremse:** Alter ≥ 24 h → posten (zur nächsten erlaubten Uhrzeit). Ein laufender Schub hält sie auf
   (Regel 4): frische Daten mit Zuwachs 3 h ≥ Schwelle (WAECHST) **oder** – seit 28.11. – Cache-Daten, bei denen das
   Video beim letzten Snapshot noch wuchs (WAECHST_ZULETZT), solange dieser Snapshot jünger als 7 h ist (ein
   Windsor-Zyklus ~6 h + 1 h Toleranz). Kommt bis dahin kein frischer Snapshot, greift die Notbremse.
7. **Abstand:** Mindestens 4 h zwischen zwei Tech-Posts, auch bei TikTok-only Nachhol-Posts. Zählt der neuere
   Zeitpunkt aus „neuestes TikTok-Video“ und „letzter Eintrag im Post-Protokoll“. Ist ein gerade gepostetes Video
   noch nicht in den Windsor-Daten, wird gewartet (sonst droht ein Doppel-Post auf alten Cache-Daten).

## So rechnet growth_check.py
- Zeiten: video_create_datetime und data_fetched_at sind UTC (geprüft am 2026-11-26: Short 06 um 16:59:11 UTC
  committet, TikTok-Erstellzeit 16:59:58).
- Kurve = (Veröffentlichung, 0 Aufrufe) + alle eindeutigen Snapshots (gleiches data_fetched_at = ein Snapshot),
  dazwischen linear. Zuwächse werden vom neuesten Snapshot aus zurückgerechnet (3 h, letzte Stunde, Stunde davor).
- Die Parameter stehen oben im Skript. Regeländerung = Skript UND diese Datei anpassen und unten eintragen.
- Vor einer Regeländerung prüfen, was sie früher entschieden hätte: `python3 tools/tech/growth_replay.py` (jeder Post
  im Protokoll) oder mit Zeitpunkten; alte Version zum Vergleich mit `--script` (z. B. aus `git show`).

## Kurven früherer Videos (Beobachtungen)
- Short 01 Red vs Blue (TikTok 2026-11-25 12:26 UTC): 74 Aufrufe nach ~35 h, nach ~41 h immer noch 74 (steht);
  Ø 9,2 s gesehen, 1,2 % bis zum Ende, 1 Follower.
- Short 06 Perfect Sync (TikTok 2026-11-26 16:59 UTC): 150 Aufrufe nach ~6,5 h, 155 nach ~12,6 h, 158 nach ~18,6 h →
  nach ~6 h fast flach; Ø 8,2 s gesehen, 16,8 % bis zum Ende.
- Short 03 Ball Grows (TikTok 2026-11-26 23:23 UTC): 11 Aufrufe nach 3 min, 200 nach ~6,2 h (Snapshot 27.11. 05:38 UTC;
  dazwischen nur Cache, Verlauf unbekannt); Ø 8,3 s gesehen, 2,7 % bis zum Ende. Danach bis 08:38 UTC nur Cache →
  bei Alter 9,3 h nach Regel 5 als Stillstand gewertet (Ball Shrinks nachgeholt). Nächster frischer Snapshot
  (27.11. 11:38 UTC, Alter 12,3 h): 203 → zwischen 6,2 h und 12,3 h nur +3, der Post bei 9,3 h war nicht zu früh.
- Short 04 Ball Shrinks (TikTok 2026-11-27 08:39 UTC, Nachholen): 198 Aufrufe nach 3,0 h (Snapshot 11:38 UTC; Ball Grows
  hatte 200 erst nach 6,2 h); Ø 8,9 s gesehen, 7,4 % bis zum Ende. Nächster frischer Snapshot (17:38 UTC, Alter 9,0 h):
  204 → zwischen 3 h und 9 h nur +6 → schon nach ~3 h flach. Bei 9,0 h nach Regel 3 (frische Daten) als Stillstand
  gewertet, Escape the Rings nachgeholt.
- Stand 27.11. 17:38 UTC (frisch): Ball Grows 204 nach 18,3 h (+1 seit 12,3 h), Perfect Sync 163 nach 24,6 h (+5 seit
  18,6 h), Red vs Blue 74 (steht). Kein Video hat bisher einen späten Schub bekommen.
- Windsor (Trial) liefert TikTok-Daten nur etwa alle 6 h frisch (Snapshots 26.11. 23:26, 27.11. 05:38 und 11:38 UTC);
  die Stundenwerte dazwischen sind linear interpoliert. Bisher flachen alle Videos nach ~6 h ab (Perfect Sync,
  Ball Grows) → Regel 5 (Cache-Stillstand ab 8 h) greift nicht zu früh.
- Beantwortet (27.11.): Legt ein Video mit schnellem Start (Ball Shrinks) nach 6 h noch zu? Nein (198 → 204 zwischen
  3 h und 9 h). Muster bisher: alle Simulationen landen nach 3–6,5 h bei ~150–200 Aufrufen und bleiben dort.
  Keine Regeländerung: die Regeln passen zu den Kurven, und Windsor liefert ohnehin nur alle ~6 h frische Zahlen
  (dazwischen ist die Kurve linear, „letzte Stunde vs. Stunde davor“ ist dann immer gleich). Weiter beobachten, ob ein
  „What if“-Video (Short 07) anders verläuft.
- Short 05 Escape the Rings (TikTok 2026-11-27 17:38 UTC, Nachholen): 267 Aufrufe nach 3,0 h (frischer Snapshot
  20:38 UTC) → bester Start aller Simulationen (Ball Shrinks 198 nach 3,0 h); Ø 10,5 s gesehen (bisher höchster Wert
  der Simulationen), 4,1 % bis zum Ende, 7 Likes. Gleicher Snapshot: Ball Shrinks 204 nach 12,0 h (+0 seit 9,0 h),
  Ball Grows 204 nach 21,3 h, Perfect Sync 163, Red vs Blue 74 → alle älteren flach, kein später Schub.
  Dieser frische Snapshot kam schon 3 h nach dem letzten (17:38 → 20:38 UTC), vorher ~6 h – evtl. weil Windsor beim
  Verbinden der neuen Konten neu geladen hat; nicht als neuen Takt voraussetzen.
- **Erster später Schub (28.11.):** Escape the Rings 267 Aufrufe nach 3,0 h → **617 nach 9,0 h** (frischer Snapshot
  28.11. 02:37 UTC über den Abruf ohne accounts-Filter; gefiltert stand der Cache noch auf 20:38 UTC) = +350 in 6 h,
  mehr als in den ersten 3 h. Wann genau der Schub kam, ist unbekannt (dazwischen keine Daten). Bestes Tech-Video
  bisher; Ø 10,0 s gesehen, 2,9 % bis zum Ende, 9 Likes, 0 Shares, 0 Follower. Gleicher Snapshot: Ball Shrinks 206
  (+2 in 6 h), Ball Grows 205, Perfect Sync 164, Red vs Blue 74 → die anderen bleiben flach. Die Annahme „alle Videos
  flachen nach ~6 h ab“ gilt also nicht immer → Regel 5 geändert (siehe unten). Offene Frage: Wächst Escape the Rings
  beim nächsten frischen Snapshot weiter, und bekommt Short 07 (What if) auch einen späten Schub?
- **Schub läuft weiter (28.11. 08:38 UTC, frisch, diesmal schon über den gefilterten Abruf):** Escape the Rings
  267 nach 3 h → 617 nach 9 h → **1114 nach 15,0 h** = +497 in 6 h, also sogar schneller als zwischen 3 h und 9 h
  (+350). Likes aber unverändert 9, 0 Shares, 0 Follower, Ø 9,6 s gesehen, 2,9 % bis zum Ende → viele neue
  Zuschauer, kaum Interaktion. Gleicher Snapshot: Ball Shrinks 206 (+0 in 6 h), Ball Grows 206 (+1), Perfect Sync 166
  (+2), Red vs Blue 75 (+1) → alle anderen flach. Erste Frage beantwortet: ja, wächst weiter. Windsor erneuert den
  Cache offenbar genau ~6 h nach dem letzten Abruf (02:37:49 → 08:38:50) beim nächsten Abruf → nächster frischer
  Stand frühestens ~14:38 UTC. Hält das Tempo an, wäre Escape the Rings um 17:38 UTC (24 h) noch im Schub → Regel 6
  angepasst (siehe unten). Offene Frage: Wie lange hält so ein später Schub, und bekommt Short 07 (What if) auch einen?
- **Schub hält auch nach 24 h an (28.11. 17:39 UTC, frisch):** Escape the Rings 267 (3 h) → 617 (9 h) → 1114 (15 h) →
  **3532 nach 24,0 h** = +2418 in 9 h (Ø ~270/h; Verlauf dazwischen unbekannt). Likes 9 → 22, 0 Shares, 0 Follower,
  Ø 9,1 s gesehen, 2,4 % bis zum Ende → riesige Reichweite, aber kaum Bindung/Abos. Gleicher Snapshot: Ball Shrinks 211
  (+5 in 9 h), Ball Grows 210 (+4), Perfect Sync 170 (+4), Red vs Blue 76 (+1) → die anderen bleiben flach (minimales
  Plus evtl. durch Profilbesuche). Notbremse (24 h) wurde durch Regel 6 wie vorgesehen aufgehalten (frisch, +806 in 3 h
  ≥ Schwelle 177). Lücke: zwischen 11:38 und 17:38 UTC gibt es keine Tech-Takt-Commits (Läufe 12:38–16:38 fehlen;
  vermutlich auch kein Windsor-Abruf, sonst wäre der Cache schon ~14:38 erneuert worden) → die 9 h zwischen den
  Snapshots sind linear interpoliert. Nächster frischer Stand voraussichtlich nachts (~6 h nach 17:39 UTC, Nachtruhe).

## Änderungen an den Regeln (Datum – was – warum)
- 2026-11-26: Datei mit den Startregeln angelegt. Festgelegt: Notbremse gegen laufenden Schub (Regel 6) und Abstand
  über das Post-Protokoll (Regel 7), damit nie zwei Posts kurz hintereinander rausgehen, wenn Windsor alte Daten liefert.
- 2026-11-27 (20:38 UTC): Keine Regeländerung, aber Datenabruf abgesichert: Windsor liefert jetzt 3 TikTok-Konten.
  Abruf mit accounts-Filter auf Tech Nik (Schritt 1) und Schutz in growth_check.py (fremde Videos werden übersprungen).
  Grund: Sonst wäre die Eiffelturm-Story (Tiny Tales, 19:34 UTC) als „letztes Tech-Video“ gewertet worden und Auto-/
  Story-Zahlen hätten die Kurven verfälscht.
- 2026-11-28 (02:40 UTC): **Regel 5 entschärft + Ersatz-Abruf.** (1) Cache-Stillstand ab 8 h nur noch, wenn das Video
  beim letzten frischen Snapshot schon flach war; wuchs es da noch, wird auf frische Daten gewartet (Status
  WAECHST_ZULETZT; Notbremse 24 h bleibt). Grund: Escape the Rings legte zwischen 3 h und 9 h von 267 auf 617 Aufrufe
  zu, während die gefilterten Daten seit 20:38 UTC standen. Mit der alten Regel wäre heute um 07:38 UTC (08:38 Berlin)
  gepostet worden, egal was der nächste frische Snapshot zeigt – also womöglich mitten in einen Schub. Rückblick-Test
  (growth_replay.py): einzige Änderung früherer Entscheidungen = Ball Shrinks wäre am 27.11. 3 h später nachgeholt
  worden (11:38 statt 08:41 UTC, beim frischen Snapshot 203 Aufrufe); Escape the Rings (Regel 3, frische Daten) gleich.
  Passt zu „lieber etwas zu spät als zu früh“. (2) Ersatz-Abruf ohne accounts-Filter, wenn der gefilterte nur Cache
  liefert (eigener Windsor-Cache, war hier 6 h frischer); growth_check.py loggt keine Daten, die älter sind als die
  letzte Zeile desselben Videos (sonst würde Cache als frisch gewertet).
- 2026-11-28 (08:45 UTC): **Regel 6 – Schub hält die Notbremse auch bei Cache-Daten auf** (Parameter PUSH_HOLD_H = 7 h
  in growth_check.py). Grund: Escape the Rings wächst nach 15 h schneller als je zuvor (+497 in 6 h). Windsor liefert
  nur alle ~6 h frische Zahlen; „frisch“ (< 3 h) ist also nur die Hälfte der Zeit. Mit der alten Regel hätte die
  Notbremse um 18:38 oder 19:38 UTC gepostet, sobald der Snapshot von ~14:38/15:38 UTC 3–4 h alt ist – auch wenn
  dieser Snapshot noch +190 Aufrufe in 3 h zeigt (simuliert; das Skript schrieb dabei selbst „Schub hat Vorrang, auf
  frische Daten warten“ und postete trotzdem). Das widerspricht „ein laufender Schub hat immer Vorrang“ und hinge nur
  vom Cache-Takt ab, nicht vom Video. Jetzt wird bis zum nächsten frischen Snapshot gewartet, höchstens 7 h nach dem
  letzten; kommt keiner, greift die Notbremse wie bisher (simuliert: ohne neuen Snapshot Post um 18:38 UTC wie vorher).
  Rückblick-Test (growth_replay.py, alle Posts im Protokoll und jede Stunde 26.11. 23:38 bis 28.11. 08:38 UTC): keine
  einzige frühere Entscheidung ändert sich.

## Post-Protokoll (neueste unten)
Format: `- JJJJ-MM-TTTHH:MM:SSZ | Video | Kanäle | Grund (Aufrufe/Kurve des vorherigen Videos)`
- 2026-11-25T12:26:35Z | Short 01 Red vs Blue | TikTok | vor Einführung des Takts (Zeit laut Windsor)
- 2026-11-26T16:59:58Z | Short 06 Perfect Sync | TikTok | vor Einführung des Takts (Zeit laut Windsor)
- 2026-11-26T23:23:15Z | Short 03 Ball Grows | TikTok | vor Einführung des Takts (Zeit laut Windsor)
- 2026-11-27T08:41:36Z | Short 04 Ball Shrinks (Nachholen, Buffer-Entwurf) | TikTok | Ball Grows: 200 Aufrufe beim letzten frischen Snapshot (05:38 UTC, 6,2 h alt; davor 11 nach 3 min), seitdem 3,0 h nur Cache, Alter 9,3 h → Regel 5 (Cache-Stillstand ab 8 h). TikTok https://tiktok.com/@tech.nik4/video/7712768294368840999
- 2026-11-27T17:40:39Z | Short 05 Escape the Rings (Nachholen, letzter Buffer-Entwurf) | TikTok (YouTube/Instagram schon online) | Ball Shrinks: 198 Aufrufe nach 3,0 h (11:38 UTC), 204 nach 9,0 h (frischer Snapshot 17:38 UTC) → +6 in 6 h; Zuwachs 3 h +3 < Schwelle 10, letzte Stunde +1 = davor +1 → Regel 3 (Stillstand). TikTok https://tiktok.com/@tech.nik4/video/7712907204097035559
