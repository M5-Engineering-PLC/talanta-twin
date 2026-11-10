"""Encode a render_scroll_frames.py sequence for the web and report the sizes (scroll-scrub test, 2026-10-25).

Run from the repo root:  python3 blender/scroll_test/encode_frames.py <frames_dir>
Writes <frames_dir>/web/: frames as WebP (q 82) and AVIF (q 60) at 1920 and 960 px wide (phones), plus two H.264
videos (every frame a keyframe, for exact scrubbing; and a normal GOP of 12 for comparison). Prints and saves
sizes.json. The page plays image frames (decode cost per frame is small and scrubbing is exact); the video is the
fallback to compare against.
"""
import json, subprocess, sys
from pathlib import Path
from PIL import Image

d = Path(sys.argv[1]); w = d / "web"; w.mkdir(exist_ok=True)
frames = sorted(d.glob("frame_*.png"))
sizes = {"frames": len(frames)}
for fmt, q in (("webp", 82), ("avif", 60)):
    for width in (1920, 960):
        out = w / f"{fmt}_{width}"; out.mkdir(exist_ok=True); tot = 0
        for f in frames:
            im = Image.open(f).convert("RGB")
            if im.width != width: im = im.resize((width, width * im.height // im.width), Image.LANCZOS)
            p = out / f"{f.stem}.{fmt}"; im.save(p, quality=q, method=6) if fmt == "webp" else im.save(p, quality=q)
            tot += p.stat().st_size
        sizes[f"{fmt}_{width}"] = {"total_bytes": tot, "per_frame_bytes": tot // max(len(frames), 1), "quality": q}
for name, gop in (("h264_intra", 1), ("h264_gop12", 12)):
    p = w / f"{name}.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", str(d / "frame_%03d.png"), "-c:v", "libx264",
                    "-preset", "slow", "-crf", "20", "-g", str(gop), "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(p)], check=True)
    sizes[name] = {"total_bytes": p.stat().st_size, "crf": 20, "gop": gop}
(w / "sizes.json").write_text(json.dumps(sizes, indent=1) + "\n")
print(json.dumps(sizes, indent=1))
