import yt_dlp
import subprocess
import os
import sys

MAX_WIDTH = 1920
MAX_HEIGHT = 1080
MAX_FPS = 30
MAX_BITRATE_BPS = 10_000_000  # 10 Mbps


def download_video(url: str, output_dir: str = "downloads") -> str:
    """
    Download the best available video+audio and mux to mp4.
    Resolution/fps/bitrate/codec enforcement happens later via ffmpeg
    (enforce_spec), not here — this avoids format-selector failures on
    sites like Facebook where height/fps/ext metadata is inconsistent
    or where videos are portrait-oriented (e.g. Reels).
    """
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        "format": "bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "outtmpl": os.path.join(output_dir, "%(title).100B [%(id)s].%(ext)s"),
        "noplaylist": True,
        "remote_components": ["ejs:github"],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filepath = ydl.prepare_filename(info)
        base, _ = os.path.splitext(filepath)
        mp4_path = base + ".mp4"
        return mp4_path if os.path.exists(mp4_path) else filepath


def enforce_spec(input_path: str, output_path: str) -> None:
    """
    Re-encode to guarantee H.264, <=1920x1080 (preserving orientation/aspect
    ratio -- portrait sources stay portrait, just scaled down), <=30fps,
    <=10Mbps, regardless of what the source actually was.
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-vf",
        f"scale='min({MAX_WIDTH},iw)':'min({MAX_HEIGHT},ih)':force_original_aspect_ratio=decrease",
        "-r", str(MAX_FPS),
        "-c:v", "libx264",
        "-b:v", f"{MAX_BITRATE_BPS}",
        "-maxrate", f"{MAX_BITRATE_BPS}",
        "-bufsize", f"{MAX_BITRATE_BPS * 2}",
        "-c:a", "aac",
        "-b:a", "192k",
        output_path,
    ]
    subprocess.run(cmd, check=True)


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <url>")
        sys.exit(1)

    url = sys.argv[1]
    raw_path = download_video(url)
    print(f"Downloaded: {raw_path}")

    final_path = raw_path.replace(".mp4", "_spec.mp4")
    enforce_spec(raw_path, final_path)
    print(f"Spec-compliant output: {final_path}")


if __name__ == "__main__":
    main()