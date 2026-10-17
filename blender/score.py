"""Astra critic score: eight categories scored 0-5, weighted to a total out of 100.

Run: python3 blender/score.py <scores.csv>   (columns: category, score, note)
0 = missing, 3 = recognizable with visible defects, 5 = no material discrepancy at review scale.
"""
import csv, sys
W = {"geometry": 30, "materials": 15, "lighting": 15, "atmosphere": 5, "vegetation": 10, "people": 10, "camera": 5, "process": 10}
rows = list(csv.DictReader(open(sys.argv[1])))
tot, appl = 0.0, 0
for r in rows:
    if r["score"].strip().lower() in ("n/a", "unknown"): continue
    tot += W[r["category"]] * float(r["score"]) / 5; appl += W[r["category"]]
print(f"total {tot:.1f} / {appl} applicable weight -> {100 * tot / appl:.1f}/100" if appl < 100 else f"total {tot:.1f}/100")
