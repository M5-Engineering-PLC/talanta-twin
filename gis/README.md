# gis/

Geodata for the twin. Read `coverage_report.md` first.

| Path | What |
|---|---|
| `accuracy_spec.md` | Tolerance for each geometry item, and where we stand |
| `data_gap_matrix.csv` | One row per item: source, error, owner, status |
| `site_measurements.md` | W1b form for Google Earth Pro measurements (numbers only) |
| `validation_plan.md` | Independent checks with fixed pass marks |
| `heldout_frames.csv` | 20 frames kept out of modelling for check V6 |
| `coverage_report.md` | What was downloaded, what it shows, what it cannot show |
| `scripts/` | Fetch and derive scripts. Run with `~/.venvs/gis/bin/python` |
| `derived/` | Small outputs, committed |
| `raw/` | Downloads. Git-ignored. Rebuild with the fetch scripts |

Setup: `uv venv ~/.venvs/gis && uv pip install --python ~/.venvs/gis geopandas rasterio shapely pyproj pyarrow scipy matplotlib`

Credits required in any product: "Contains modified Copernicus Sentinel data 2023-2026", "Copernicus DEM GLO-30", "© OpenStreetMap contributors (ODbL)", "Overture Maps Foundation", "Google Open Buildings (CC BY 4.0)", "Microsoft Building Footprints".
