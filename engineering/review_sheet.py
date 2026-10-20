#!/usr/bin/env python3
"""Make internal render review sheets. Use one image pair or a CSV with --pairs."""

import argparse
import csv
import html
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


INTERNAL_LABEL = "INTERNAL - reference frame, not for public use"
PANEL_HEIGHT = 44
BACKGROUND = (25, 29, 35)
TEXT = (245, 247, 250)


def parse_crop(value):
    """Read four crop coordinates in frame pixels."""
    try:
        values = tuple(int(part.strip()) for part in value.split(","))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Crop must contain four integers: x0,y0,x1,y1") from exc
    if len(values) != 4:
        raise argparse.ArgumentTypeError("Crop must contain four integers: x0,y0,x1,y1")
    x0, y0, x1, y1 = values
    if x0 < 0 or y0 < 0 or x1 <= x0 or y1 <= y0:
        raise argparse.ArgumentTypeError("Crop must have non-negative start points and positive size")
    return values


def _sobel_edges(image):
    """Return a Sobel edge mask for an RGB image."""
    gray = np.asarray(image.convert("L"), dtype=np.float32)
    padded = np.pad(gray, 1, mode="edge")
    gx = (
        -padded[:-2, :-2] + padded[:-2, 2:]
        - 2 * padded[1:-1, :-2] + 2 * padded[1:-1, 2:]
        - padded[2:, :-2] + padded[2:, 2:]
    )
    gy = (
        -padded[:-2, :-2] - 2 * padded[:-2, 1:-1] - padded[:-2, 2:]
        + padded[2:, :-2] + 2 * padded[2:, 1:-1] + padded[2:, 2:]
    )
    return np.hypot(gx, gy) >= 180


def _edge_overlay(render, frame):
    """Draw render edges in grey and frame edges in cyan over the render."""
    pixels = np.asarray(render.convert("RGB")).copy()
    render_edges = _sobel_edges(render)
    frame_edges = _sobel_edges(frame)
    pixels[render_edges] = (205, 205, 205)
    pixels[frame_edges] = (0, 220, 235)
    return Image.fromarray(pixels, "RGB")


def _crop_pair(render, frame, crop):
    if crop is None:
        return render, frame
    x0, y0, x1, y1 = crop
    if x1 > frame.width or y1 > frame.height:
        raise ValueError(f"Crop {crop} is outside frame size {frame.width}x{frame.height}")
    box = (x0, y0, x1, y1)
    return render.crop(box), frame.crop(box)


def create_sheet(render_path, frame_path, output_path, label="", crop=None):
    """Resize, compare, label, and save one internal PNG sheet."""
    render_path = Path(render_path)
    frame_path = Path(frame_path)
    with Image.open(render_path) as source:
        render = source.convert("RGB").resize(
            Image.open(frame_path).size, Image.Resampling.LANCZOS
        )
    with Image.open(frame_path) as source:
        frame = source.convert("RGB")
    render, frame = _crop_pair(render, frame, crop)
    blend = Image.blend(render, frame, 0.5)
    edge = _edge_overlay(render, frame)
    panels = [
        ("Render", render, render_path.name),
        ("Reference frame", frame, frame_path.name),
        ("50% blend", blend, f"{render_path.name} + {frame_path.name}"),
        ("Sobel edges: render grey, frame cyan", edge, f"{render_path.name} + {frame_path.name}"),
    ]
    width, height = render.size
    sheet = Image.new("RGB", (width * len(panels), height + PANEL_HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, (title, image, filename) in enumerate(panels):
        left = index * width
        sheet.paste(image, (left, PANEL_HEIGHT))
        panel_label = label.strip() or title
        draw.text((left + 8, 5), f"{panel_label} | {title}", fill=TEXT, font=font)
        draw.text((left + 8, 21), filename[:150], fill=TEXT, font=font)
        draw.text((left + 8, 33), INTERNAL_LABEL, fill=(255, 195, 90), font=font)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path, format="PNG")
    return output_path, sheet.size


def _safe_output_dir(output_dir):
    resolved = Path(output_dir).expanduser().resolve()
    repo_root = Path(__file__).resolve().parents[1]
    try:
        relative = resolved.relative_to(repo_root)
    except ValueError:
        relative = None
    if relative is not None and relative.parts and relative.parts[0].lower() == "app":
        raise ValueError("Output directory cannot be inside app/")
    if any(part.lower() == "public" for part in resolved.parts):
        raise ValueError("Output directory cannot be inside a public folder")
    return resolved


def _slug(value):
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip()).strip("._-")
    return text[:80] or "pair"


def _read_pairs(csv_path):
    with Path(csv_path).open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not {"render", "frame", "label"}.issubset(reader.fieldnames):
            raise ValueError("Pairs CSV must have render,frame,label columns")
        rows = list(reader)
    for row_number, row in enumerate(rows, 2):
        if not row.get("render") or not row.get("frame"):
            raise ValueError(f"Pairs CSV row {row_number} needs render and frame values")
    return rows


def _write_index(output_dir, entries):
    links = "\n".join(
        f'<li><a href="{html.escape(filename, quote=True)}">'
        f'{html.escape(label or filename)}</a></li>'
        for filename, label in entries
    )
    page = (
        "<!doctype html>\n<html lang=\"en\"><meta charset=\"utf-8\">"
        "<title>Internal render review sheets</title>"
        f"<h1>{INTERNAL_LABEL}</h1><ul>{links}</ul></html>\n"
    )
    (output_dir / "index.html").write_text(page, encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Make internal render review sheets.")
    parser.add_argument("render", nargs="?", help="Path to the render image")
    parser.add_argument("frame", nargs="?", help="Path to the reference frame")
    parser.add_argument("--pairs", help="CSV with render,frame,label columns")
    parser.add_argument("--output-dir", default="./review_out", help="Directory for PNG sheets")
    parser.add_argument("--label", default="", help="Label for a single image pair")
    parser.add_argument("--crop", type=parse_crop, help="Crop in frame pixels: x0,y0,x1,y1")
    args = parser.parse_args(argv)
    try:
        output_dir = _safe_output_dir(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        if args.pairs:
            if args.render or args.frame:
                parser.error("Use --pairs or one render/frame pair")
            entries = []
            for index, row in enumerate(_read_pairs(args.pairs), 1):
                name = f"{index:03d}_{_slug(row['label'])}.png"
                path, size = create_sheet(row["render"], row["frame"], output_dir / name, row["label"], args.crop)
                print(f"Wrote {path} ({size[0]}x{size[1]})")
                entries.append((name, row["label"]))
            _write_index(output_dir, entries)
            print(f"Wrote {output_dir / 'index.html'}")
        else:
            if not args.render or not args.frame:
                parser.error("Provide render and frame paths, or use --pairs")
            name = f"{_slug(Path(args.render).stem)}__{_slug(Path(args.frame).stem)}.png"
            path, size = create_sheet(args.render, args.frame, output_dir / name, args.label, args.crop)
            print(f"Wrote {path} ({size[0]}x{size[1]})")
    except (OSError, ValueError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
