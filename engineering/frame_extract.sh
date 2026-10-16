#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
python3 - "$ROOT" "$@" <<'PY'
import csv
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

root = Path(sys.argv[1])
preview_only = len(sys.argv) > 2 and sys.argv[2] == "--preview-gaps"
if len(sys.argv) > 2 and not preview_only:
    raise RuntimeError(f"Unknown argument: {sys.argv[2]}")
video_roots = [root / "archive/video/gaps"] if preview_only else [
    root / "archive/video/main", root / "archive/video/shorts", root / "archive/video/gaps"
]
frames_root = root / "research/frames"
index_root = root / "research/video_index"
frames_root.mkdir(parents=True, exist_ok=True)
index_root.mkdir(parents=True, exist_ok=True)
started = time.monotonic()
threshold = 5
excluded_ids = {"0WDh71itqrU"}
excluded_frame_counts = {"0WDh71itqrU": 5}
view_classes = (
    "aerial_overview", "exterior_facade", "roof_canopy", "bowl_seating", "pitch",
    "floodlights", "gates_entrances", "concourse_interior", "landscaping_fountain",
    "roads_parking", "night_lighting", "construction", "other",
)
manual_path = index_root / "labels_manual.csv"
if not manual_path.is_file():
    raise RuntimeError(f"Missing manual frame labels: {manual_path}")
with manual_path.open(encoding="utf-8", newline="") as handle:
    manual_rows = list(csv.DictReader(handle))
manual_labels = {}
for label in manual_rows:
    name = label.get("file", "")
    if not name or name in manual_labels:
        raise RuntimeError(f"Missing or duplicate manual label path: {name}")
    if label.get("view_class") not in view_classes:
        raise RuntimeError(f"Invalid view class for {name}: {label.get('view_class')}")
    if label.get("keep") not in {"yes", "no"}:
        raise RuntimeError(f"Invalid keep value for {name}: {label.get('keep')}")
    subject_words = label.get("subject", "").split()
    if not 3 <= len(subject_words) <= 8:
        raise RuntimeError(f"Subject must contain 3 to 8 words: {name}")
    if label["keep"] == "no" and not label.get("reason", "").strip():
        raise RuntimeError(f"Rejected frame needs a reason: {name}")
    manual_labels[name] = label
indices = np.arange(32)
frequencies = indices[:, None]
positions = indices[None, :]
dct = np.cos(np.pi * (positions + 0.5) * frequencies / 32)
dct[0, :] *= 1 / math.sqrt(2)
dct *= math.sqrt(2 / 32)

def perceptual_hash(image):
    pixels = np.asarray(image.resize((32, 32)), dtype=np.float64)
    coefficients = dct @ pixels @ dct.T
    low = coefficients[:8, :8].flatten()[1:]
    median = float(np.median(low))
    value = 0
    for bit in low >= median:
        value = (value << 1) | int(bit)
    return value

def video_id(path):
    match = re.match(r"^\d{8}_([A-Za-z0-9_-]{11})_", path.name)
    if not match:
        raise RuntimeError(f"Cannot read the video ID from {path.name}")
    return match.group(1)

def classify(title, seconds, main):
    text = title.lower()
    if any(word in text for word in ("fountain", "illuminated", "lights", "light show")):
        return "landscaping_fountain" if "fountain" in text else "night_lighting", "stadium fountain and light display"
    if any(word in text for word in ("aerial", "drone", "overview", "bird's eye", "birds eye")):
        return "aerial_overview", "stadium and surrounding site from above"
    if "seat" in text:
        return "bowl_seating", "stadium seating and bowl"
    if any(word in text for word in ("inside", "tour", "exploring", "vibes")):
        return "concourse_interior", "stadium interior and bowl"
    if "stadium lights" in text or "stadium light" in text:
        return "night_lighting", "stadium lights at night"
    if any(word in text for word in ("progress", "nears completion", "construction", "percent", "70 percent")):
        return "construction", "stadium construction and finished areas"
    if main:
        windows = [
            (40, "roof_canopy", "roof trusses and canopy panels"),
            (100, "pitch", "pitch and lower seating bowl"),
            (170, "night_lighting", "stadium lighting and exterior at night"),
            (340, "aerial_overview", "stadium site model and approach roads"),
            (460, "exterior_facade", "stadium facade and exterior apron"),
            (560, "concourse_interior", "interior concourse and seating access"),
            (640, "bowl_seating", "seating bowl and roof structure"),
            (720, "night_lighting", "stadium lights and fountain display"),
            (860, "pitch", "pitch surface and maintenance work"),
            (1040, "bowl_seating", "seating bowl and pitch"),
            (1200, "night_lighting", "stadium exterior lighting and fountains"),
            (1320, "concourse_interior", "interior corridors and public spaces"),
            (1500, "bowl_seating", "seats, aisles, and bowl edge"),
            (1600, "exterior_facade", "stadium facade and site landscaping"),
            (1710, "bowl_seating", "seating bowl and pitch"),
            (1865, "aerial_overview", "stadium overview and site at night"),
        ]
        for end, cls, subject in windows:
            if seconds < end:
                return cls, subject
        return "other", "stadium reference view"
    if any(word in text for word in ("ruto", "kindiki", "test match", "stadium vibes")):
        return "bowl_seating", "stadium bowl with visitor or event activity"
    return "exterior_facade", "stadium exterior and nearby site"

videos = []
preview_frames = {}
for folder in video_roots:
    for path in sorted(folder.iterdir()):
        if path.suffix.lower() not in (".mp4", ".webm"):
            continue
        vid = video_id(path)
        info_path = path.with_suffix(".info.json")
        if not info_path.is_file():
            raise RuntimeError(f"Missing video information file: {info_path}")
        info = json.loads(info_path.read_text(encoding="utf-8"))
        title = info.get("title") or info.get("fulltitle") or path.stem
        url = info.get("webpage_url") or f"https://www.youtube.com/watch?v={vid}"
        duration = float(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=nk=1:nw=1", str(path)
        ], text=True).strip())
        frame_rate = subprocess.check_output([
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=avg_frame_rate", "-of", "default=nk=1:nw=1", str(path)
        ], text=True).strip()
        is_main = folder.name == "main"
        rate_num, rate_den = map(float, frame_rate.split("/"))
        videos.append((vid, path, title, url, duration, is_main, rate_num / rate_den))

for excluded in excluded_ids:
    excluded_dir = frames_root / excluded
    if excluded_dir.exists():
        shutil.rmtree(excluded_dir)
    (index_root / f"{excluded}.csv").unlink(missing_ok=True)

expected_local_videos = 11 if preview_only else 34
if len(videos) != expected_local_videos:
    raise RuntimeError(f"Expected {expected_local_videos} local videos, found {len(videos)}")

with tempfile.TemporaryDirectory(prefix="talanta_frames_") as temp_name:
    temp_root = Path(temp_name)
    all_rows = []
    by_video = {}
    for number, (vid, source, title, base_url, duration, is_main, frame_rate) in enumerate(videos, 1):
        if vid in excluded_ids:
            continue
        output_dir = frames_root / vid
        expected_keep = {
            label["file"].split("/")[-1]
            for label in manual_rows
            if label["file"].split("/")[2] == vid and label["keep"] == "yes"
        }
        actual_keep = {path.name for path in output_dir.glob("*.jpg")} if output_dir.is_dir() else set()
        if not preview_only and actual_keep == expected_keep:
            csv_path = index_root / f"{vid}.csv"
            if csv_path.is_file():
                with csv_path.open(encoding="utf-8", newline="") as handle:
                    rows = list(csv.DictReader(handle))
                if {row["file"].split("/")[-1] for row in rows} == expected_keep:
                    by_video[vid] = rows
                    all_rows.extend(rows)
                    print(f"SKIPPED_COMPLETE: {vid} frames={len(rows)}", flush=True)
                    continue
        temp_dir = temp_root / vid
        temp_dir.mkdir()
        is_gap = source.parent.name == "gaps"
        interval = 4 if is_main else (2 if is_gap else 1)
        frame_step = max(1, round(frame_rate * interval))
        crop_filter = ""
        if is_gap:
            dimension_text = subprocess.check_output([
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height", "-of", "csv=p=0", str(source),
            ], text=True).strip().splitlines()[0]
            source_width, source_height = map(int, dimension_text.split(","))
            detected = []
            for sample_time in (duration * 0.25, duration * 0.65):
                crop_result = subprocess.run([
                    "ffmpeg", "-hide_banner", "-ss", f"{sample_time:.3f}", "-i", str(source),
                    "-vf", "cropdetect=24:16:0", "-frames:v", "60", "-f", "null", "-",
                ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
                if crop_result.returncode:
                    raise RuntimeError(f"Crop detection failed for {vid}: ffmpeg={crop_result.returncode}")
                detected.extend(re.findall(r"crop=(\d+:\d+:\d+:\d+)", crop_result.stderr))
            if detected:
                crop = Counter(detected).most_common(1)[0][0]
                crop_width, crop_height, crop_x, crop_y = map(int, crop.split(":"))
                if crop_width < source_width * 0.95 or crop_height < source_height * 0.95:
                    crop_filter = f"crop={crop_width}:{crop_height}:{crop_x}:{crop_y},"
        filter_expr = f"{crop_filter}scale=320:-1,select='gt(scene,0.30)+not(mod(n,{frame_step}))',showinfo"
        command = [
            "ffmpeg", "-hide_banner", "-loglevel", "info", "-i", str(source),
            "-vf", filter_expr, "-fps_mode", "vfr", "-q:v", "2",
            str(temp_dir / "candidate_%05d.jpg")
        ]
        result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        pts = [float(value) for value in re.findall(r"pts_time:([0-9.]+)", result.stderr)]
        candidates = sorted(temp_dir.glob("candidate_*.jpg"))
        if result.returncode or len(candidates) != len(pts):
            raise RuntimeError(f"Decode or timestamp error for {vid}: ffmpeg={result.returncode}, images={len(candidates)}, times={len(pts)}")

        measured = []
        for image_path, seconds in zip(candidates, pts):
            image = Image.open(image_path).convert("L").resize((128, 72))
            pixels = np.asarray(image, dtype=np.int16)
            laplacian = (4 * pixels[1:-1, 1:-1] - pixels[1:-1, :-2] - pixels[1:-1, 2:]
                         - pixels[:-2, 1:-1] - pixels[2:, 1:-1])
            sharpness = float(laplacian.var())
            if sharpness < 45:
                continue
            phash = perceptual_hash(image)
            measured.append((image_path, seconds, sharpness, phash))

        target = 160 if is_main else (24 if is_gap else min(12, max(5, int(math.ceil(duration / 6)))))
        selected = []
        selected_hashes = []
        # Pick the sharpest candidate from each equal time bin, then fill gaps.
        bins = [[] for _ in range(target)]
        for item in measured:
            slot = min(target - 1, int(item[1] / max(duration, 0.001) * target))
            bins[slot].append(item)
        for group in bins:
            for item in sorted(group, key=lambda row: (-row[2], row[1])):
                if all((item[3] ^ value).bit_count() > threshold for value in selected_hashes):
                    selected.append(item)
                    selected_hashes.append(item[3])
                    break
        if len(selected) < target:
            for item in sorted(measured, key=lambda row: (-row[2], row[1])):
                if all((item[3] ^ value).bit_count() > threshold for value in selected_hashes):
                    selected.append(item)
                    selected_hashes.append(item[3])
                if len(selected) == target:
                    break
        if len(selected) < (150 if is_main else 5):
            raise RuntimeError(f"Only {len(selected)} distinct sharp frames for {vid}")
        selected.sort(key=lambda row: row[1])

        if preview_only:
            review_dir = Path("/tmp/talanta_gap_review_selected") / vid
            review_dir.mkdir(parents=True, exist_ok=True)
            preview_frames[vid] = []
            for image_path, seconds, sharpness, phash in selected:
                hh = int(seconds // 3600)
                mm = int(seconds // 60) % 60
                ss = int(seconds) % 60
                ms = int((seconds - int(seconds)) * 1000)
                filename = f"{vid}_{hh:02d}{mm:02d}{ss:02d}.{ms:03d}.jpg"
                preview_path = review_dir / filename
                shutil.copyfile(image_path, preview_path)
                preview_frames[vid].append((filename, preview_path))
            print(f"PREVIEW: {vid} candidates={len(selected)} crop={crop_filter or 'none'}", flush=True)
            continue

        output_dir = frames_root / vid
        output_dir.mkdir(parents=True, exist_ok=True)
        for old in output_dir.glob("*.jpg"):
            old.unlink()
        rows = []
        for image_path, seconds, sharpness, phash in selected:
            hh = int(seconds // 3600)
            mm = int(seconds // 60) % 60
            ss = int(seconds) % 60
            ms = int((seconds - int(seconds)) * 1000)
            filename = f"{vid}_{hh:02d}{mm:02d}{ss:02d}.{ms:03d}.jpg"
            output = output_dir / filename
            relative_file = f"research/frames/{vid}/{filename}"
            label = manual_labels.get(relative_file)
            if label is None:
                raise RuntimeError(f"No manual label exists for extracted frame: {relative_file}")
            if label["keep"] != "yes":
                continue
            if is_gap:
                highres_filter = crop_filter[:-1] if crop_filter else "null"
                highres = subprocess.run([
                    "ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{seconds:.3f}",
                    "-i", str(source), "-frames:v", "1", "-vf", highres_filter,
                    "-q:v", "2", str(output),
                ], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
                if highres.returncode or not output.is_file():
                    raise RuntimeError(f"Full-resolution seek failed for {vid} at {seconds:.3f}s: ffmpeg={highres.returncode}, {highres.stderr}")
            else:
                shutil.copyfile(image_path, output)
            note = "site unconfirmed" if label.get("reason", "").strip().lower() == "site unconfirmed" else f"Frame from the source video at {seconds:.3f} seconds."
            if vid == "PWj9s_v3G6U":
                note = "Nyayo Stadium drone and light-show reference; not Talanta geometry."
            elif vid == "VHZ0-of7cLM":
                note = "Site unconfirmed; stadium view from a different venue."
            elif vid == "CuS83a44PG8":
                note = "Site unconfirmed; fountain-light reference."
            url = base_url.split("&t=")[0] + f"&t={int(seconds)}s"
            rows.append({
                "file": relative_file,
                "video_id": vid,
                "timestamp_s": f"{seconds:.3f}",
                "source_url_with_t": url,
                "view_class": label["view_class"],
                "subject": label["subject"],
                "notes": note,
                "_hash": phash,
            })
        by_video[vid] = rows
        all_rows.extend(rows)
        print(f"{number}/{len(videos)} {vid}: {len(rows)} frames", flush=True)

    if preview_only:
        for vid, items in preview_frames.items():
            for batch_number in range((len(items) + 11) // 12):
                batch = items[batch_number * 12:(batch_number + 1) * 12]
                sheet = Image.new("RGB", (2000, 930), "#dddddd")
                for index, (filename, image_path) in enumerate(batch):
                    image = Image.open(image_path).convert("RGB")
                    image.thumbnail((480, 270))
                    tile = Image.new("RGB", (500, 310), "white")
                    tile.paste(image, ((500 - image.width) // 2, 0))
                    ImageDraw.Draw(tile).text((8, 275), filename, fill="black")
                    sheet.paste(tile, ((index % 4) * 500, (index // 4) * 310))
                sheet.save(f"/tmp/talanta_gap_review_selected/{vid}_sheet_{batch_number + 1}.jpg", quality=90)
        print(f"PREVIEW_COMPLETE: videos={len(preview_frames)} sheets={sum((len(items) + 11) // 12 for items in preview_frames.values())}")
        sys.exit(0)

    columns = ["file", "video_id", "timestamp_s", "source_url_with_t", "view_class", "subject", "notes"]
    for vid, rows in by_video.items():
        csv_path = index_root / f"{vid}.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            writer.writerows({key: row[key] for key in columns} for row in rows)
    with (index_root / "MASTER_INDEX.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows({key: row[key] for key in columns} for row in all_rows)

    counts = Counter(row["view_class"] for row in all_rows)
    gaps_by_class = {
        "aerial_overview": "No clear high-altitude view shows the full site boundary.",
        "exterior_facade": "No view shows the full facade without vehicles or trees.",
        "roof_canopy": "No close view shows every roof connection detail.",
        "bowl_seating": "No view confirms exact seat dimensions or row counts.",
        "pitch": "No frame provides measured pitch dimensions.",
        "floodlights": "No clear frame isolates the floodlight assemblies.",
        "gates_entrances": "No clear frame shows the west gates or their full layout.",
        "concourse_interior": "No frame shows the complete concourse circulation paths.",
        "landscaping_fountain": "No daylight view shows the full fountain and planting plan.",
        "roads_parking": "No view shows a complete parking layout.",
        "night_lighting": "No frame records calibrated light colors or brightness.",
        "construction": "No frame verifies dimensions of unfinished construction areas.",
        "other": "Reference views do not establish Talanta geometry.",
    }
    over_limit = [cls for cls in view_classes if all_rows and counts.get(cls, 0) / len(all_rows) > 0.40]
    with (index_root / "COVERAGE.txt").open("w", encoding="utf-8") as handle:
        handle.write("Frame count by view class\n")
        for cls in view_classes:
            handle.write(f"{cls}: {counts.get(cls, 0)}\n")
        handle.write("\nCoverage gaps by view class\n")
        for cls in view_classes:
            if counts.get(cls, 0) == 0:
                handle.write(f"{cls}: no kept frame. {gaps_by_class[cls]}\n")
            else:
                handle.write(f"{cls}: {gaps_by_class[cls]}\n")
        if over_limit:
            handle.write("\nView classes above 40 percent\n")
            for cls in over_limit:
                handle.write(f"{cls}: the main source has repeated views in this category.\n")

    # Acceptance check: one index row per frame, and every row points to a file.
    master = list(csv.DictReader((index_root / "MASTER_INDEX.csv").open(encoding="utf-8", newline="")))
    jpeg_paths = sorted(frames_root.glob("*/*.jpg"))
    relative = [str(path.relative_to(root)) for path in jpeg_paths]
    row_files = [row["file"] for row in master]
    exists = all((root / name).is_file() for name in row_files)
    unique_rows = len(set(row_files)) == len(row_files)
    same_set = set(relative) == set(row_files)
    if not (exists and unique_rows and same_set):
        raise RuntimeError(f"Index check failed: jpeg={len(relative)} rows={len(master)} exists={exists} unique={unique_rows} same_set={same_set}")
    print(f"INDEX_CHECK: JPEGs={len(relative)} rows={len(master)} all_exist={exists} unique_rows={unique_rows} exact_match={same_set}")
    print(f"HASH_THRESHOLD: pHash Hamming distance <= {threshold} is a near-duplicate")
    for vid in sorted(by_video):
        kept = len(by_video[vid])
        deleted = sum(1 for label in manual_rows if label["file"].split("/")[2] == vid and label["keep"] == "no")
        print(f"FRAME_COUNTS: {vid} kept={kept} deleted={deleted}")
    for vid, deleted in sorted(excluded_frame_counts.items()):
        print(f"FRAME_COUNTS: {vid} kept=0 deleted={deleted} excluded=yes")
    print(f"TOTAL_SIZE_BYTES: {sum(path.stat().st_size for path in jpeg_paths)}")
    print("VIEW_CLASS_COUNTS: " + json.dumps(dict(counts), sort_keys=True))
    print(f"VIEW_CLASS_OVER_40_PERCENT: {over_limit}")
    print(f"RUN_SECONDS: {time.monotonic() - started:.1f}")
PY
