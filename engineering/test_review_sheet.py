import csv
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "engineering" / "review_sheet.py"


def test_pairs_mode_writes_labeled_sheets_and_index(tmp_path):
    render = tmp_path / "render.png"
    frame = tmp_path / "frame.png"
    Image.new("RGB", (32, 20), (180, 30, 20)).save(render)
    pixels = np.zeros((10, 16, 3), dtype=np.uint8)
    pixels[:, :8] = (20, 30, 180)
    Image.fromarray(pixels).save(frame)
    pairs = tmp_path / "pairs.csv"
    with pairs.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["render", "frame", "label"])
        writer.writeheader()
        writer.writerow({"render": str(render), "frame": str(frame), "label": "facade ribs"})
    output = tmp_path / "review_out"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--pairs", str(pairs), "--output-dir", str(output)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Wrote" in result.stdout
    sheets = list(output.glob("*.png"))
    assert len(sheets) == 1
    with Image.open(sheets[0]) as sheet:
        assert sheet.size == (16 * 4, 10 + 44)
    index = (output / "index.html").read_text(encoding="utf-8")
    assert sheets[0].name in index
    assert "facade ribs" in index
    assert "INTERNAL - reference frame, not for public use" in index
