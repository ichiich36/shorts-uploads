# shorts-uploads

Videos in `videos/` are public on purpose: Buffer and Windsor fetch them from
`https://raw.githubusercontent.com/ichiich36/shorts-uploads/main/videos/<file>.mp4`.

## Channels
- **Tech (satisfying simulations, no voice, English text):**
  YouTube techtbe24 (Buffer channel 6b0804e28541f09ecbad7767),
  TikTok tech.nik4 (Buffer channel 6b080aac8541f09ecbadb10f),
  Instagram technik96 (Windsor connector instagram, account 17841466978824968, action create_video_post).
  Files: `videos/Short_NN_<Name>.mp4`. Generators in `tools/tech/` (pure python + cv2 + ffmpeg, 1080x1920, 30 fps).
- **How Cars Work (English, 65-75 s since Part 4 because TikTok only pays for videos over 1 min, voice Todd g14YnDYCsy3k7XLlcKlO, eleven_v4, 1 take):**
  TikTok factpulse084 (Buffer channel 6b0812458541f09ecbadfdb0),
  Instagram fact.pulse90 (Windsor instagram account 17841438794736046; log of posted parts in posted_instagram_cars.txt). Files: `videos/HowCarsWork_PartN_<Topic>.mp4`.
  Framework in `tools/cars/` (Part 4 version; render_part2/3_reference.py keep older scenes): script.py (SEGMENTS), align.py voice.mp3 -> timeline.json,
  render.py (scenes), sfx.py voice.mp3 -> mix.wav. Professional tone, no gags. Each part ends with a teaser for the next.
  YouTube FactPulse90 via Make scenario 8829633 (on-demand; inputs video_url, title, description, privacy, publish_at).
- YouTube techtbe24 via Make scenario 8829688 (same inputs). Make: eu1, org 9757895, team 3788512.
  For a scheduled YouTube post use privacy "private" + publish_at (ISO 8601 with offset).
- Buffer organization 6b07fd269d5a54e153d3cd07 (timezone Europe/Berlin). Windsor YouTube upload is broken (always "rate-limited"): do not use.

- **Stories (ichiichii631@gmail.com, English, stick-figure cartoon, voice Brian nPczCjzI2devNBz1zQrb):**
  YouTube (Make scenario 8829688 with channel "story"), TikTok tinytales.584 (Buffer channel 6b0866ce8541f09ecbb2852a),
  Instagram tinytales.584 (Windsor instagram account 17841445178149404). Files: videos/Story_NN_<Name>.mp4, tools in tools/story/.
- Make scenario 8829688 = "YouTube Upload (alle Kanäle)": input channel "" or "tech" -> techtbe24, "autos" -> FactPulse90, "story" -> story channel.

## Pipeline
1. Voice only from ElevenLabs (creative_generate_speech, generations_count 1, flow xot9linTH2GumUUt2pV3);
   download the mp3 from creative_get_generations full_res_url with curl. Never render in the ElevenLabs sandbox.
2. Render locally, loudnorm -14 LUFS, check stills.
3. Commit to `videos/`, push, then post via Buffer / Windsor using the raw URL.

## Series plan (How Cars Work)
1 Engine, 2 Manual gearbox, 3 Automatic, 4 Differential, 5 Brakes, 6 Steering, 7 Suspension, 8 Turbocharger,
9 Electric motor, 10 EV battery, 11 ABS, 12 Airbags, 13 Cooling system, 14 Fuel injection, 15 Hybrid.
