#!/usr/bin/env bash
# Cloud session setup for the Blender track (gate G1 and later).
# download.blender.org is blocked by the cloud proxy; PyPI is not, so Blender
# comes from the official `bpy` wheel (headless, CPU Cycles, OpenImageDenoise).
set -euo pipefail
VENV=~/.venvs/bpy
if ! "$VENV/bin/python" -c "import bpy" 2>/dev/null; then
  python3.13 -m venv "$VENV"
  "$VENV/bin/pip" install -q bpy==5.2.2
fi
"$VENV/bin/python" -c "import bpy; print('bpy', bpy.app.version_string)"
# G1 render test (about 1 minute on 4 CPUs):
#   ~/.venvs/bpy/bin/python blender/scripts/g1_render_test.py blender/renders/g1
