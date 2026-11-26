# Qualitäts-Checkliste (für alle Kanäle)

Feedback des Nutzers: Design und Stimmen sind super und sollen BLEIBEN. Jedes neue Video soll in Kleinigkeiten
etwas besser werden. Kein Redesign, nur Details polieren.

Vor dem finalen Rendern immer 8–12 Standbilder an den wichtigsten Momenten anschauen und prüfen:

1. **Jede Aktion, die im Text vorkommt, ist im Bild sichtbar.**
   Beispiel aus dem Emu-Video: „Fire!“ / Schüsse waren nicht zu sehen. Bei Schüssen: Mündungsfeuer (gelb-orange Stern
   am Lauf, 2–3 Frames), sichtbare Projektil-Linien/Tracer, kleine Staubwölkchen beim Einschlag, leichter Rückstoß.
   Allgemein: Explosion → Blitz + Partikel, Bremsen → Bremslicht + Funken, Aufprall → kurzer Squash/Shake.
2. **Timing:** Das Bild-Ereignis passiert genau auf dem Wort (Wort-Timestamps aus timeline.json nutzen), Sound-Effekt
   ebenfalls darauf.
3. **Lesbarkeit:** Kein Text überlappt Figuren oder Bildschirmränder; Captions immer im sicheren Bereich
   (nicht in den oberen 11 % und unteren 22 %, nicht ganz rechts).
4. **Bewegung:** Keine Szene länger als ~3 s komplett statisch — kleine Idle-Animation (Atmen, Blinzeln, Wolken, Rotation).
5. **Ton:** Effekte hörbar, aber Stimme immer klar darüber (Ducking). Lautheit -14 LUFS.
6. **Kleine Verbesserung pro Video:** Notiere am Ende in IMPROVEMENTS.md eine Zeile: Datum, Kanal, was diesmal
   verbessert wurde — und beim nächsten Video der Nische darauf aufbauen.

# Ziel: Klicks und Abos (Wachstums-Regeln – gelten für JEDES Video)

Alles wird danach ausgerichtet, dass Leute zuschauen, bis zum Ende bleiben, liken und folgen.
CTAs (Like/Follow/Kommentar) immer kurz, eingebaut in den Inhalt, nie mehr als 2 pro Video, nie in den ersten 3 Sekunden
außer als Mitmach-Frage.

## 1. Die ersten 1–2 Sekunden (entscheidet über Klicks)
- Sofort Bewegung und Text im Bild ab Frame 0 – kein Intro, kein leerer Hintergrund, kein Logo.
- Hook als Frage oder Behauptung, die man auflösen will („Can it escape?“, „Australia lost a war… to birds“).
- Titel/Caption = dieselbe Neugier-Lücke, nicht den Ausgang verraten.

## 2. Zuschauer halten (Retention)
- Sichtbarer Fortschritt (Zähler, Balken, „RINGS LEFT 3“) – man will das Ende sehen.
- Alle 3–5 Sekunden etwas Neues (Szenenwechsel, Pop-Text, Soundeffekt).
- Spannung bis zum Schluss: Höhepunkt erst in den letzten 15 %.
- Loop-Ende wo möglich: letztes Bild passt optisch zum ersten, damit das Video nahtlos neu startet (mehr Wiedergaben).
- Länge: Tech 20–35 s, Autos/Storys 50–60 s. Lieber kürzer als Leerlauf.

## 3. Mitmachen ohne zu nerven
- **Tech:** am Anfang kleine Einblendung „Pick a color 👇“ / „Guess the bounces 👇“ (Kommentare = Reichweite);
  am Ende kurz „Follow for a new one every day“ auf dem Ergebnisbild.
- **Autos:** Follow ist Teil der Serie („Follow for part N+1!“ + Teaser) – das bleibt. In der Caption eine Frage
  („What part should we explain next?“).
- **Storys:** Am Ende kurze Frage, die zum Kommentieren einlädt („Would you have joined the emu war? 👇“), dann
  „Follow for more crazy true stories!“.
- Nach dem Posten auf Instagram einen ersten Kommentar mit der Frage setzen (Windsor create_comment auf die neue
  Media-ID), z. B. „Which one should we do next? 👇“.
- Nie: „Smash that like button“, Betteln, CTA mitten in der Spannung.

## 4. Titel, Caption, Hashtags
- YouTube-Titel: max. ~60 Zeichen sichtbar, Neugier + 1 Emoji + #shorts.
- Caption: erste Zeile = Hook, dann 1 Satz Kontext, dann Frage, dann 4–8 passende Hashtags (Mix aus groß und nischig).

## 5. Lernen aus Zahlen (bei jedem Lauf)
- Vor der Ideenwahl die letzten Videos der eigenen Nische prüfen: Buffer list_posts / get_post mit includeMetrics
  (TikTok), Windsor get_data (Instagram, Felder vorher mit get_fields prüfen). Wenn Daten verfügbar sind:
  Welches Format/Thema hatte die meisten Aufrufe? Mehr davon machen, Schwaches nicht wiederholen.
- Erkenntnis als eine Zeile in IMPROVEMENTS.md notieren („Ringe-Format > Wachstums-Format, öfter nutzen“).

## 6. Uhrzeiten (Zielgruppe englischsprachig, v. a. USA)
- Gepostet wird am späten Nachmittag/Abend deutscher Zeit = Mittag/Nachmittag in den USA:
  Tech ~17:45, Autos 18:30, Storys ~21:00 (deutsche Zeit).
