---
name: open-video-transcriber
description: Use when the user shares a video link (YouTube, TikTok, Instagram, Facebook reels, X, Vimeo, or any site yt-dlp supports) or a local video file and wants it watched, transcribed, summarized, quoted, mined for tips, or checked for what is shown on screen. Transcribes speech with a local Whisper model (no API key, no cloud, no rate limits) and grabs timestamped frames so you can read on-screen text.
---

# Open Video Transcriber

You can't watch video, but this skill lets you hear it and see it. Everything runs locally: a Whisper speech model for audio and ffmpeg for frames. There are no API keys and no usage limits. A 30-second reel takes about 10 seconds on a CPU.

```
python scripts/vt.py <command> ...
```
(Path is relative to this skill's folder. Use the absolute path when you run it from elsewhere.)

## Pick the command

| You need | Command |
|---|---|
| What was **said** (summary, quotes, tips) | `transcribe URL` → `[m:ss] text` lines |
| Subtitles | `transcribe URL --format srt --out subs.srt` |
| Machine-readable segments | `transcribe URL --format json` |
| What was **shown** (on-screen text, tool names, UI, search strings) | `frames URL --out DIR --sheet`, then open `DIR/sheet.jpg` |
| Who posted it, date, length, views | `info URL` |

## How to watch a video well
1. Run `info` and `transcribe`. Most talking-head videos are fully covered by the transcript.
2. If the speaker says "this site" or "this tool" or points at the screen, or the transcript is empty (music-only or text-on-screen videos), run `frames --sheet` and look at the sheet. One image is cheaper than many frames.
3. For a specific moment, narrow it: `frames URL --out DIR --start 40 --end 55 --every 1`.
4. Quote with timestamps from the transcript. Keep quotes short.

## Options
- `--model`: `tiny.en` (fastest), `base.en` (default, a good balance), `small.en` / `medium.en` (more accurate, need more RAM), `large-v3` / `turbo` (best, multilingual). Use a non-`.en` model for non-English videos.
- `--device cuda` if there's an NVIDIA GPU.
- `--vad` skips silence. It's faster on long videos but can drop speech under loud music.
- `frames --every N` (seconds between frames, default 2), `--max N` (default 14).

## Gotchas
| Symptom | Fix |
|---|---|
| `no speech detected` | Music or text-only video: use `frames --sheet` |
| `mkl_malloc: failed to allocate memory` | Not enough RAM for that model: use `base.en` or `tiny.en` |
| Proper nouns misspelled (brand names, URLs) | Check them against `frames`, since Whisper guesses names it doesn't know |
| yt-dlp fails on a site | `pip install -U yt-dlp` (sites change often); private or login-only videos won't download |
| Profile/page shows only a few videos | That's the site hiding content from logged-out visitors, not a bug |

## Rules
- Media is downloaded to a temp folder and deleted automatically. Don't keep full copies of other people's videos.
- Only process videos the user can lawfully access.
