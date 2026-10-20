# Execution plan: Codex-first

Date: 2026-10-16
Status: proposed. Munene approves before work starts.

## Decision

Luna (GPT-6 Luna, Codex) does most of the execution. Sol (GPT-6.1 Sol, Codex) takes the hard engine work. The lead (Claude) writes the work orders and does short reviews only, because the Claude usage limit is low.

## Limits on 2026-10-16

- Codex 5-hour window: 100% left. Reset at 18:50.
- Codex weekly: 58% left. Reset at 10:13 on 22 Oct. Luna and Sol share this limit, so it is the real constraint.
- Measured cost: one Luna labeling job of 6 minutes used about 1% of the 5-hour window. The weekly limit fell from 67% to 58% during the frame work of 15 and 16 Oct.
- Rule: run `codex-status` before each launch and after each result.

## What Luna does well here

- Bounded jobs with a clear finish: GIS clipping and conversion, frame extraction, batch renders, asset compression, test runs, performance benchmarks.
- Scripted 3D work: Blender 5.2 runs headless (`blender -b --python script.py`). Luna can write bpy scripts, render fixed camera views, look at the renders, and fix the script. This replaces the Blender MCP, which needs Claude.
- Scaffolding: the three.js app skeleton, the module registry from the PLAN.md IDs, a performance overlay.

## What goes to Sol

- The crowd system (60,000 GPU instances with vertex animation textures).
- The rain and wet-surface shaders.
- The match logic for SPT-01.
- Read-only review of each Luna change that touches the engine.

## What stays with the lead

- Work orders, acceptance checks, and the final review of each phase.
- Claim labels and anything a buyer reads.
- Decisions on scale and geometry when sources disagree.

## Known constraints

1. Codex has no network access. The lead (or a short shell step) downloads data. Luna processes the local files.
2. COLMAP and the GIS Python libraries (geopandas, rasterio) are not installed. Munene installs them, because installation needs network access and possibly sudo. Commands are in section "Setup for Munene".
3. Laptop sleep stops long jobs. Start long Luna runs detached (`setsid nohup`) and keep the laptop awake and on charge.
4. Run at most two Codex workers at the same time, each in its own git worktree, so that the weekly limit lasts.

## Phase 0 work orders (in order)

| Order | Worker | Work | Done when |
|---|---|---|---|
| W1 | Lead | Download Open Buildings 2.5D, OSM and GLO-30 for a 3 km box around the stadium | Files exist in `gis/raw/` (git-ignored) |
| W1b | Munene or a team member | Measure the site in Google Earth Pro with the ruler tool: stadium outline and axes, pitch size, the eight gates, parking areas, access roads, and the dates of the historical images. Record numbers only. Do not export or trace imagery | `gis/site_measurements.md` holds each measurement with its method and the image date |
| W2 | Luna | Clip and convert the GIS data to GeoJSON footprints with heights, a road network and a 16-bit heightmap | `gis/` holds the outputs and a coverage report |
| W3 | Luna | Structure-from-motion test: extract frames at 2 fps from the drone shorts and run COLMAP | A report states how many images register and whether the bowl and roof form a point cloud |
| W4 | Luna | Scale the site: fit the pitch to 105 m by 68 m in the point cloud or on the plan view, check it against the W1b measurements, and record the stadium outline in meters | `gis/site_scale.md` with the method and the error |
| W5 | Luna | App scaffold: Vite, three.js with WebGPU and a WebGL fallback, module registry, performance overlay, one test scene | `npm run build` passes and the test scene opens |
| W6 | Luna | Blender blockout of the bowl, roof and facade from the scale and the frames, with a render-and-compare loop against reference frames | Renders from 6 fixed views match the reference frames in shape |

Status 2026-10-16 (lead, cloud session): W1 done from free sources. W2 and W4 have first passes from satellite data only. W1b has a form ready. See `gis/coverage_report.md`. The site is at Jamhuri Park, 36.74965 E, 1.30602 S.

After phase 0, phase 1 (the hero slice) splits as follows: Luna for the environment modules and cameras, Sol for the crowd, rain and match, and the lead for the final review.

## Setup for Munene

Run these commands before W2 and W3.

```bash
sudo apt install colmap
```

```bash
uv venv ~/.venvs/gis
```

```bash
uv pip install --python ~/.venvs/gis geopandas rasterio shapely pyproj
```

Luna then uses `~/.venvs/gis/bin/python` for the GIS work.

If apt has no COLMAP package, tell the lead. The lead then gives Luna a fallback method for W3.
