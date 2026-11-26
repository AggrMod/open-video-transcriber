# Open Video Transcriber: let your AI agent watch videos

**Lightning-fast video transcription for AI agents, with a local voice recognition model.** No API key, no cloud, no rate limits, free.

Give your agent (Claude Code, Codex, Cursor, Gemini CLI, OpenClaw, or any agent with a shell) a link from **YouTube, TikTok, Instagram, Facebook reels, X, Vimeo**, or [1,800+ other sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md). It gets back:

- a **timestamped transcript** from [faster-whisper](https://github.com/SYSTRAN/faster-whisper), running on your own machine
- **timestamped frames and a contact sheet**, so it can read on-screen text, tool names and UI the speaker points at

### ⚡ 43× real time on a GPU, 18× on a plain CPU
**An hour-long podcast transcribes in about 90 seconds on a gaming GPU, or about 3½ minutes on CPU only.**

| Model | CPU (Ryzen 5 4600G) | GPU (GTX 1660 Super) |
|---|---|---|
| `tiny.en` | 18.3× real time (58 s) | **43.0× real time (25 s)** |
| `base.en` (default) | 10.1× (1 min 46 s) | **28.4× (38 s)** |
| `small.en` | 3.4× (5 min 11 s) | 10.5× (1 min 42 s) |
| `turbo` (near-best accuracy, multilingual) | not tested | 3.5× (5 min 1 s) |

<sub>Benchmark: JFK's full "We choose to go to the Moon" speech (17.8 min). CPU = int8, GPU = float16. ×real time = audio length ÷ transcription time (download and model load not counted). Every run prints its own speed, so you can benchmark your machine.</sub>

```
$ python scripts/vt.py transcribe "https://www.youtube.com/watch?v=jNQXAC9IVRw"
speed: 19.0s of audio transcribed in 2.1s = 9.1x real time (base.en, cpu; download 4.4s, model load 2.0s)
[0:00] Alright, so here we are, one of the elephants, cool thing about these guys is that they have
[0:08] really, really, really long fums, and that's cool, and that's pretty much all there is to say.
```

---

## 🤖 Share this with your agent

Copy this prompt and paste it to your AI agent:

```text
Install the Open Video Transcriber skill so you can watch videos for me:

1. Clone https://github.com/AggrMod/open-video-transcriber into your skills folder
   (Claude Code: ~/.claude/skills/open-video-transcriber; other agents: anywhere you keep tools).
2. Install the requirements: `pip install -r requirements.txt`, and make sure `ffmpeg` is on PATH
   (winget install ffmpeg / brew install ffmpeg / apt install ffmpeg).
3. Read SKILL.md and follow it whenever I share a video link.
4. Test it: transcribe https://www.youtube.com/watch?v=jNQXAC9IVRw and tell me what he says about elephants.
```

Then just say "watch this" and paste a link.

---

## Manual install

```bash
git clone https://github.com/AggrMod/open-video-transcriber
cd open-video-transcriber
pip install -r requirements.txt     # faster-whisper, yt-dlp, pillow
# plus ffmpeg on PATH

# optional, NVIDIA GPU (2-4x faster):
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12   # then add --device cuda
```

The first run downloads the Whisper model (~150 MB for `base.en`) and caches it.

## Usage

```bash
# speech → text
python scripts/vt.py transcribe <url-or-file>                        # [m:ss] lines
python scripts/vt.py transcribe <url> --format srt --out subs.srt    # subtitles
python scripts/vt.py transcribe <url> --format json                  # segments for code
python scripts/vt.py transcribe <url> --model large-v3 --device cuda # max accuracy on a GPU

# what's on screen
python scripts/vt.py frames <url> --out frames --sheet               # frame every 2 s + sheet.jpg
python scripts/vt.py frames <url> --out frames --start 40 --end 55 --every 1

# metadata
python scripts/vt.py info <url>
```

| Model | Speed | RAM | Notes |
|---|---|---|---|
| `tiny.en` | fastest | <1 GB | rough |
| `base.en` | fast | ~1 GB | **default**, good for reels and talking heads |
| `small.en` / `medium.en` | slower | 2–5 GB | better names and jargon |
| `large-v3` / `turbo` | slowest on CPU | 6 GB+ | best, multilingual (use with `--device cuda`) |

## Why local?
Cloud video APIs have free-tier caps, 503 "high demand" errors, and send your links to someone else's servers. This runs entirely on your machine, works offline once the model is cached, and never stops for a quota.

## What it's good for
- "Watch this and give me the gems with timestamps": mining creators' videos for tips
- Turning tutorials into step-by-step notes
- Subtitles for your own videos
- Reading the tool or site a creator flashes on screen but never says out loud

## Notes
- Media goes to a temp folder and is deleted right after. Only process videos you're allowed to access.
- Some sites hide most of a profile from logged-out visitors; single public video links still work.

MIT licensed. Built on [yt-dlp](https://github.com/yt-dlp/yt-dlp), [faster-whisper](https://github.com/SYSTRAN/faster-whisper) and [ffmpeg](https://ffmpeg.org).
