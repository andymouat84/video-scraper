# VideoScraper

A Python script for downloading videos from YouTube and Facebook, and re-encoding them to a consistent spec: **MP4 / H.264, max 1920x1080, max 30fps, max 10 Mbps bitrate.**

The script works in two stages:
1. **Download** — `yt-dlp` grabs the best available video+audio streams and merges them into an MP4.
2. **Enforce spec** — `ffmpeg` re-encodes the downloaded file to guarantee the codec, resolution cap, frame rate cap, and bitrate cap, regardless of what the source actually was (portrait videos stay portrait, just scaled down proportionally).

---

## Requirements

| Tool | Purpose | Install |
|---|---|---|
| Python 3.9+ | Runs the script | Already installed if you're reading this |
| `yt-dlp` | Downloads video/audio | `pip install yt-dlp` |
| `ffmpeg` | Re-encodes to spec | See below |
| Deno | Solves YouTube's JS challenges | `winget install DenoLand.Deno` |

### Installing ffmpeg (Windows)
```powershell
winget install ffmpeg
```
Then **open a new terminal window** — PATH changes don't apply to already-open ones.

Verify:
```powershell
ffmpeg -version
```

### Installing Deno (Windows)
```powershell
winget install DenoLand.Deno
```
Again, open a new terminal afterward and verify:
```powershell
deno --version
```
Deno is required because YouTube increasingly gates format extraction behind JavaScript challenges. Without it, some or all formats may fail to resolve.

---

## Usage

```powershell
python main.py "<video URL>"
```

Examples:
```powershell
python main.py "https://www.youtube.com/watch?v=XXXXXXXX"
python main.py "https://youtu.be/XXXXXXXX?si=..."
python main.py "https://www.facebook.com/watch/?v=XXXXXXXX"
python main.py "https://www.facebook.com/reel/XXXXXXXX"
```

**Always quote the URL** — YouTube URLs often contain `&`, which your shell will otherwise interpret as "run in background," silently truncating the URL.

### Output
Two files land in a `downloads/` folder (created automatically next to the script):
- The raw downloaded file (whatever codec/resolution the source actually was)
- `<name>_spec.mp4` — the version re-encoded to the target spec

---

## Configuration

At the top of `main.py`:

```python
MAX_WIDTH = 1920
MAX_HEIGHT = 1080
MAX_FPS = 30
MAX_BITRATE_BPS = 10_000_000  # 10 Mbps
```

Adjust these to change the target spec.

If a video requires you to be logged in (private/unlisted content), export cookies from your browser (e.g. via the "Get cookies.txt" extension) and uncomment/set this line in `ydl_opts`:
```python
"cookiefile": "cookies.txt",
```

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'yt_dlp'`**
`pip install` and the `python` command are pointing at different environments. Check with `where python` and `python -m pip show yt-dlp` — reinstall via the same interpreter if they don't match.

**`ffmpeg is not installed` / merging error**
ffmpeg isn't installed, or isn't on PATH. Reinstall (see above) and make sure you opened a fresh terminal afterward.

**`yt-dlp: command not found` / not recognized**
`pip install yt-dlp` installs a Python package, not a standalone CLI. Either run it as a module (`python -m yt_dlp ...`) or download the standalone `yt-dlp.exe` from the [GitHub releases page](https://github.com/yt-dlp/yt-dlp/releases).

**`Requested format is not available`**
Usually means the format selector was too strict for the source (e.g. Facebook Reels report metadata differently than YouTube, or are portrait rather than landscape). Run `python -m yt_dlp --list-formats "<url>"` to see what's actually available. The current selector (`bestvideo+bestaudio/best`) is intentionally loose — all spec enforcement happens later via ffmpeg — so this shouldn't recur, but if it does, that command is the first diagnostic step.

**`Unable to open file` / `Invalid argument` on the download path**
Windows has a path length limit (~260 characters by default). Some platforms (notably Facebook, for videos without a real title) use the entire post caption as the filename, which can blow past this limit. The current `outtmpl` truncates titles to 100 bytes and appends the video ID to avoid this. If you still hit it, you can enable long path support system-wide:
```powershell
# Run as Administrator, then reboot
New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
```

**`This video is not available` (YouTube)**
First, confirm the video actually plays in a normal browser — if it's deleted, private, or region-locked, no configuration will fix that. If it does play fine:
1. Make sure Deno is installed and on PATH (see above).
2. Make sure `remote_components: ["ejs:github"]` is set in `ydl_opts` (already included in this script) — this allows yt-dlp to fetch the challenge-solving script it needs.
3. Update yt-dlp, since YouTube's anti-bot measures change frequently:
   ```powershell
   python -m pip install -U yt-dlp
   ```

**yt-dlp extraction errors in general**
YouTube/Facebook change their internal APIs often. Updating yt-dlp usually resolves newly-introduced breakage:
```powershell
python -m pip install -U yt-dlp
```

---

## Notes

- Only use this for content you have the rights to download (your own uploads, licensed content, etc.). Downloading copyrighted material without rights may violate the platform's Terms of Service.
- The `-maxrate`/`-bufsize` approach caps bitrate but allows some variability. For a hard, consistent bitrate target, a two-pass ffmpeg encode is more precise — not currently implemented here.
- Facebook often serves video in VP9 rather than H.264; the ffmpeg re-encode step converts this regardless, so the final `_spec.mp4` output is always H.264.
