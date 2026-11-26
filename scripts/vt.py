#!/usr/bin/env python3
"""open-video-transcriber: watch any video link with a local speech model.

  vt.py transcribe <url-or-file> [--model base.en] [--format txt|srt|json] [--out FILE]
  vt.py frames     <url-or-file> --out DIR [--every 2] [--start 0] [--end SECONDS] [--max 14] [--sheet]
  vt.py info       <url>

Audio and video are downloaded to a temp folder and deleted afterwards.
Works with anything yt-dlp supports: YouTube, TikTok, Instagram, Facebook reels, X, Vimeo, ...
"""
import argparse, json, os, shutil, subprocess, sys, tempfile, glob, time

def die(msg):
    print(f"error: {msg}", file=sys.stderr); sys.exit(1)

def need(cmd):
    if not shutil.which(cmd):
        die(f"'{cmd}' not found on PATH. Install it first (see README).")

def is_url(s):
    return s.startswith(("http://", "https://"))

def ytdlp(args):
    r = subprocess.run([sys.executable, "-m", "yt_dlp", "--no-update", "--no-warnings", *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        die("yt-dlp failed: " + (r.stderr.strip().splitlines() or ["unknown"])[-1])
    return r.stdout

def fetch(src, tmp, fmt):
    """Return a local media path: download if src is a URL, else src itself."""
    if not is_url(src):
        if not os.path.exists(src): die(f"no such file: {src}")
        return src
    ytdlp(["-q", "-f", fmt, "-o", os.path.join(tmp, "media.%(ext)s"), src])
    files = glob.glob(os.path.join(tmp, "media.*"))
    if not files: die("download produced no file")
    return files[0]

def to_wav(path, tmp):
    # 16 kHz mono WAV: what Whisper expects, and avoids decoder quirks with odd codecs
    out = os.path.join(tmp, "audio16k.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-ar", "16000", "-ac", "1", out], check=True)
    return out

def ts(t, srt=False):
    h, rem = divmod(t, 3600); m, s = divmod(rem, 60)
    if srt: return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{int((s % 1) * 1000):03d}"
    return f"{int(h)}:{int(m):02d}:{int(s):02d}" if h else f"{int(m)}:{int(s):02d}"

def add_cuda_dlls():
    """On Windows, make pip-installed NVIDIA libs (nvidia-cublas-cu12, nvidia-cudnn-cu12) loadable."""
    if os.name != "nt":
        return
    try:
        import nvidia
    except ImportError:
        return
    for root in nvidia.__path__:
        for b in glob.glob(os.path.join(root, "*", "bin")):
            os.add_dll_directory(b)
            os.environ["PATH"] = b + os.pathsep + os.environ.get("PATH", "")

def cmd_transcribe(a):
    need("ffmpeg")
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        die("pip install faster-whisper")
    with tempfile.TemporaryDirectory() as tmp:
        t0 = time.perf_counter()
        wav = to_wav(fetch(a.src, tmp, "ba/b"), tmp)
        t1 = time.perf_counter()
        device = a.device
        if device == "cuda":
            add_cuda_dlls()
        compute = "float16" if device == "cuda" else "int8"
        model = WhisperModel(a.model, device=device, compute_type=compute)
        t2 = time.perf_counter()
        segs, info = model.transcribe(wav, vad_filter=a.vad, beam_size=5)
        segs = [{"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()} for s in segs]
        t3 = time.perf_counter()
    # speed = audio length / time spent transcribing ("x real time"; higher is faster)
    dur, tx = info.duration, t3 - t2
    speed = {"audio_s": round(dur, 2), "download_s": round(t1 - t0, 2), "model_load_s": round(t2 - t1, 2),
             "transcribe_s": round(tx, 2), "x_realtime": round(dur / tx, 1) if tx else None,
             "model": a.model, "device": device}
    print(f"speed: {dur:.1f}s of audio transcribed in {tx:.1f}s = {speed['x_realtime']}x real time "
          f"({a.model}, {device}; download {t1 - t0:.1f}s, model load {t2 - t1:.1f}s)", file=sys.stderr)
    if a.format == "json":
        out = json.dumps({"language": info.language, "duration": round(info.duration, 2), "speed": speed, "segments": segs}, indent=1)
    elif a.format == "srt":
        out = "\n".join(f"{i}\n{ts(s['start'], True)} --> {ts(s['end'], True)}\n{s['text']}\n" for i, s in enumerate(segs, 1))
    else:
        out = "\n".join(f"[{ts(s['start'])}] {s['text']}" for s in segs)
    if not segs:
        print("(no speech detected - the video may be music or text-only; try `frames`)", file=sys.stderr)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(out + "\n"); print(f"saved {a.out}", file=sys.stderr)
    else:
        print(out)

def cmd_frames(a):
    need("ffmpeg")
    os.makedirs(a.out, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        media = fetch(a.src, tmp, "bv*[height<=720]+ba/b[height<=720]/b")
        vf = f"fps=1/{a.every},scale=480:-2"
        cmd = ["ffmpeg", "-v", "error", "-y", "-ss", str(a.start)]
        if a.end: cmd += ["-to", str(a.end)]
        cmd += ["-i", media, "-vf", vf, "-frames:v", str(a.max), os.path.join(a.out, "frame_%03d.jpg")]
        subprocess.run(cmd, check=True)
    frames = sorted(glob.glob(os.path.join(a.out, "frame_*.jpg")))
    if not frames: die("no frames produced (range past the end of the video?)")
    # rename to timestamps so an agent knows where each frame is
    named = []
    for i, f in enumerate(frames):
        t = a.start + i * a.every
        nf = os.path.join(a.out, f"t{int(t // 60):02d}m{int(t % 60):02d}s.jpg")
        os.replace(f, nf); named.append(nf)
    if a.sheet:
        try:
            from PIL import Image
        except ImportError:
            die("pip install pillow  (needed for --sheet)")
        ims = [Image.open(f) for f in named]; W = 320
        ims = [im.resize((W, int(im.size[1] * W / im.size[0]))) for im in ims]
        h = max(im.size[1] for im in ims); cols = min(7, len(ims)); rows = (len(ims) + cols - 1) // cols
        sheet = Image.new("RGB", (W * cols, h * rows))
        for k, im in enumerate(ims): sheet.paste(im, ((k % cols) * W, (k // cols) * h))
        sp = os.path.join(a.out, "sheet.jpg"); sheet.save(sp, quality=85)
        print(f"contact sheet: {sp}  ({len(ims)} frames, left-to-right, top-to-bottom, every {a.every}s from {a.start}s)")
    for f in named: print(f)

def cmd_info(a):
    fields = "%(uploader)s|%(upload_date)s|%(duration)s|%(view_count)s|%(webpage_url)s|%(title)s"
    keys = ["uploader", "upload_date", "duration_s", "views", "url", "title"]
    print(json.dumps(dict(zip(keys, ytdlp(["--skip-download", "--print", fields, a.src]).strip().split("|", 5))), indent=1, ensure_ascii=False))

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("transcribe", help="speech to text with a local Whisper model")
    t.add_argument("src"); t.add_argument("--model", default="base.en",
        help="tiny.en | base.en (default) | small.en | medium.en | large-v3 | turbo (non-.en models do other languages)")
    t.add_argument("--format", choices=["txt", "srt", "json"], default="txt")
    t.add_argument("--out"); t.add_argument("--device", default="cpu", help="cpu (default) or cuda")
    t.add_argument("--vad", action="store_true", help="skip silent parts (faster on long videos; can drop speech over music)")
    t.set_defaults(fn=cmd_transcribe)
    f = sub.add_parser("frames", help="grab still frames so an agent can SEE on-screen text")
    f.add_argument("src"); f.add_argument("--out", required=True)
    f.add_argument("--every", type=float, default=2, help="seconds between frames (default 2)")
    f.add_argument("--start", type=float, default=0); f.add_argument("--end", type=float)
    f.add_argument("--max", type=int, default=14, help="max frames (default 14)")
    f.add_argument("--sheet", action="store_true", help="also tile all frames into one sheet.jpg")
    f.set_defaults(fn=cmd_frames)
    i = sub.add_parser("info", help="uploader, date, length, views, title")
    i.add_argument("src"); i.set_defaults(fn=cmd_info)
    a = p.parse_args(); a.fn(a)

if __name__ == "__main__":
    main()
