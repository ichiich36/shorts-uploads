# shorts-uploads

Videos in `videos/` are public on purpose: Buffer and Windsor fetch them from
`https://raw.githubusercontent.com/ichiich36/shorts-uploads/main/videos/<file>.mp4`.

## Channels
- **Tech (satisfying simulations, no voice, English text):**
  YouTube techtbe24 (Buffer channel 6b0804e28541f09ecbad7767),
  TikTok tech.nik4 (Buffer channel 6b080aac8541f09ecbadb10f),
  Instagram technik96 (Windsor connector instagram, account 17841466978824968, action create_video_post).
  Files: `videos/Short_NN_<Name>.mp4`. Generators in `tools/tech/` (pure python + cv2 + ffmpeg, 1080x1920, 30 fps).
- **How Cars Work (English, ~55-60 s, voice Todd g14YnDYCsy3k7XLlcKlO, eleven_v4, 1 take):**
  TikTok factpulse084 (Buffer channel 6b0812458541f09ecbadfdb0). Files: `videos/HowCarsWork_PartN_<Topic>.mp4`.
  Framework in `tools/cars/` (Part 3 version): script.py (SEGMENTS), align.py voice.mp3 -> timeline.json,
  render.py (scenes), sfx.py voice.mp3 -> mix.wav. Professional tone, no gags. Each part ends with a teaser for the next.
- Buffer organization 6b07fd269d5a54e153d3cd07 (timezone Europe/Berlin).

## Pipeline
1. Voice only from ElevenLabs (creative_generate_speech, generations_count 1, flow xot9linTH2GumUUt2pV3);
   download the mp3 from creative_get_generations full_res_url with curl. Never render in the ElevenLabs sandbox.
2. Render locally, loudnorm -14 LUFS, check stills.
3. Commit to `videos/`, push, then post via Buffer / Windsor using the raw URL.

## Series plan (How Cars Work)
1 Engine, 2 Manual gearbox, 3 Automatic, 4 Differential, 5 Brakes, 6 Steering, 7 Suspension, 8 Turbocharger,
9 Electric motor, 10 EV battery, 11 ABS, 12 Airbags, 13 Cooling system, 14 Fuel injection, 15 Hybrid.
