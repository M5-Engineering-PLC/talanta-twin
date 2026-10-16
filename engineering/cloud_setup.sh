#!/usr/bin/env bash
# Build the talanta-twin tool environment on a cloud Linux machine (Ubuntu 22.04 or 24.04).
#
# Use 1: Claude Code on the web. Paste this file into the environment "Setup script" field.
#        Set network access to "Full", because the script downloads Blender from blender.org.
# Use 2: Any cloud VM. Run: bash engineering/cloud_setup.sh
#
# The script is safe to run again. It skips the tools that are already installed.
# It installs: base build tools, ffmpeg, COLMAP, Node 20 or later, uv, Blender 5.2 (headless),
# a GIS virtual environment, and the Python packages for engineering/frame_extract.sh.
#
# The script does not download the raw videos. YouTube often blocks cloud IP addresses.
# The frames, labels and index are already in git, so most work does not need the videos.

set -euo pipefail

BLENDER_SERIES="${BLENDER_SERIES:-5.2}"
BLENDER_DIR="${BLENDER_DIR:-/opt/blender}"
GIS_VENV="${GIS_VENV:-$HOME/.venvs/gis}"
NODE_MIN_MAJOR=20

log() { printf '\n[cloud_setup] %s\n' "$*"; }

if [ "$(id -u)" -eq 0 ]; then SUDO=""; else SUDO="sudo"; fi
export DEBIAN_FRONTEND=noninteractive

# 1. System packages.
# The X and GL libraries let Blender start in background mode with no display.
log "Install system packages"
$SUDO apt-get update -y
$SUDO apt-get install -y --no-install-recommends \
  ca-certificates curl wget git xz-utils unzip build-essential pkg-config \
  python3 python3-venv python3-pip python3-numpy python3-pil \
  ffmpeg colmap \
  libxi6 libxxf86vm1 libxfixes3 libxrender1 libxkbcommon0 libsm6 libice6 \
  libgl1 libegl1 libglu1-mesa libx11-6 libxext6 \
  gdal-bin

# 2. Node 20 or later. Many cloud images already have it.
node_major=0
if command -v node >/dev/null 2>&1; then
  node_major="$(node -p 'process.versions.node.split(".")[0]')"
fi
if [ "$node_major" -lt "$NODE_MIN_MAJOR" ]; then
  log "Install Node 22 (found major version $node_major)"
  curl -fsSL https://deb.nodesource.com/setup_22.x | $SUDO -E bash -
  $SUDO apt-get install -y nodejs
else
  log "Node $(node -v) is already installed"
fi

# 3. uv, for the Python environments and for uvx yt-dlp.
if ! command -v uv >/dev/null 2>&1; then
  log "Install uv"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
else
  log "uv $(uv --version) is already installed"
fi

# 4. Blender, the latest patch release in the $BLENDER_SERIES series, from blender.org.
if [ -x "$BLENDER_DIR/blender" ]; then
  log "Blender is already installed in $BLENDER_DIR"
else
  log "Find the latest Blender $BLENDER_SERIES release"
  base="https://download.blender.org/release/Blender${BLENDER_SERIES}/"
  tarball="$(curl -fsSL "$base" \
    | grep -oE "blender-${BLENDER_SERIES}\.[0-9]+-linux-x64\.tar\.xz" \
    | sort -uV | tail -n 1)"
  if [ -z "$tarball" ]; then
    echo "[cloud_setup] ERROR: no Linux build found at $base" >&2
    exit 1
  fi
  log "Download $tarball"
  tmp="$(mktemp -d)"
  curl -fL --retry 3 -o "$tmp/$tarball" "$base$tarball"
  $SUDO mkdir -p "$BLENDER_DIR"
  $SUDO tar -xJf "$tmp/$tarball" -C "$BLENDER_DIR" --strip-components=1
  rm -rf "$tmp"
fi
$SUDO ln -sf "$BLENDER_DIR/blender" /usr/local/bin/blender

# 5. GIS virtual environment for work orders W2 and W4.
if [ ! -x "$GIS_VENV/bin/python" ]; then
  log "Create the GIS virtual environment in $GIS_VENV"
  uv venv "$GIS_VENV"
fi
uv pip install --python "$GIS_VENV/bin/python" \
  geopandas rasterio shapely pyproj numpy pillow

# 6. Check the result.
log "Tool versions"
printf 'node     %s\n' "$(node -v)"
printf 'npm      %s\n' "$(npm -v)"
printf 'uv       %s\n' "$(uv --version)"
printf 'ffmpeg   %s\n' "$(ffmpeg -version | head -n 1)"
printf 'colmap   %s\n' "$(command -v colmap || echo MISSING)"
printf 'blender  %s\n' "$(blender -b --version 2>/dev/null | head -n 1)"
"$GIS_VENV/bin/python" -c 'import geopandas, rasterio, shapely, pyproj; print("gis      ok")'
python3 -c 'import numpy, PIL; print("frames   ok")'

log "Done. Blender has no GPU here. Render with Cycles on the CPU, or EEVEE with the EGL backend."
