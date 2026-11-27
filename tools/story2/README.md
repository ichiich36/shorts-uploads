# Story-Kanal – Stil v2 (ab 27.11.2026, vom Nutzer freigegeben: „Videos ab jetzt so halten“)

Flacher Vektor-Cartoon (wie CartoonFabric, aber 9:16 Vollbild) mit zwei Moderatoren, die durch die Geschichte gehen und darüber reden.

## Cast (NIE ändern)
- **Mia** – rote Locken, türkiser Hoodie, erzählt. Stimme: Jessica `cgSgspJ2msm6clMCkdW9`
- **Leo** – kurze dunkle Haare, gelber Hoodie, stellt die Zuschauerfragen, reagiert, macht am Ende den CTA. Stimme: Will `bIHbv24MWmeRgasZH58o`
- Modell `eleven_v4`, generations_count 1, Audio-Tags wie [laughs] [surprised] [whispering] sparsam.

## Ablauf pro Story
1. Neue wahre Kuriosität (nicht in stories_done.md), Fakten mit 2+ Quellen prüfen.
2. Dialog 12–16 Zeilen, ~170–200 Wörter, ≤ ~1.000 Zeichen gesamt (≈ 900–1.000 Credits). Muster wie in story2.py LINES:
   Hook-Frage von Mia an Leo → Mia erzählt, Leo fragt nach („Wait... how?“, „And they believed him?“) → Wendung → Pointe → Leo: Frage an Zuschauer + „Follow for more crazy true stories!“
3. creative_create_flow, dann pro Zeile creative_generate_speech (eine Zeile = ein Aufruf, Sprecher-Stimme). Nie wiederholen. MP3s mit curl nach voice/NN.mp3.
4. story2.py kopieren und anpassen: LINES, SCENE_OF, SCENES, Szenen-Funktionen, Story-Figuren (Char aus toon.py), Hintergründe, Requisiten, SFX-Zeitpunkte, Titel oben (2 Zeilen, 2. Zeile gelb).
   Layout bleibt: Moderatoren-Modus 'side' (x 150/930, Fuß 1610, scale 0.95) in Story-Szenen, 'center' im Wohnzimmer (Anfang + Ende), Untertitel mit Sprechername (Mia türkis, Leo gelb) bei y 1440 bzw. 580, Follow-Button am Ende, Musik + Ducking, Crossfade + Whoosh zwischen Szenen, leichter Kamera-Push.
   Toon-Stil: keine Outlines, flache Farben, große Köpfe mit großen Augen, Blinzeln, Lip-Sync aus Lautstärke.
5. Länge > 62 s (TikTok-Bedingung). `python3 story2.py info`, 10–15 Standbilder prüfen (nichts überlappt, Gesichter frei, Text lesbar), dann 4 Teile parallel rendern, concat, mix.wav dazu, loudnorm -14 LUFS.
