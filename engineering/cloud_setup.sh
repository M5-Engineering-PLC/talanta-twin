#!/usr/bin/env bash
# talanta-twin cloud tools (Ubuntu). Paste whole into the cloud setup field. Kept under 1.5 KB.
set -euo pipefail
S=""; [ "$(id -u)" -eq 0 ] || S=sudo
export DEBIAN_FRONTEND=noninteractive PATH="$HOME/.local/bin:$PATH"
$S apt-get update -y
$S apt-get install -y --no-install-recommends ca-certificates curl git xz-utils \
 python3-venv python3-numpy python3-pil ffmpeg colmap gdal-bin \
 libxi6 libxxf86vm1 libxfixes3 libxrender1 libxkbcommon0 libsm6 libgl1 libegl1
if [ "$(node -p 'process.versions.node.split(".")[0]' 2>/dev/null || echo 0)" -lt 20 ]; then
 curl -fsSL https://deb.nodesource.com/setup_22.x | $S -E bash -
 $S apt-get install -y nodejs
fi
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
B=/opt/blender
if [ ! -x $B/blender ]; then
 U=https://download.blender.org/release/Blender5.2/
 T=$(curl -fsSL $U | grep -oE 'blender-5\.2\.[0-9]+-linux-x64\.tar\.xz' | sort -uV | tail -n1)
 $S mkdir -p $B
 curl -fL --retry 3 "$U$T" | $S tar -xJ -C $B --strip-components=1
fi
$S ln -sf $B/blender /usr/local/bin/blender
V=$HOME/.venvs/gis
[ -x $V/bin/python ] || uv venv $V
uv pip install --python $V/bin/python geopandas rasterio shapely pyproj numpy pillow
node -v; uv --version; command -v colmap
blender -b --version | head -n1
$V/bin/python -c 'import geopandas,rasterio; print("gis ok")'
echo "cloud_setup done"
