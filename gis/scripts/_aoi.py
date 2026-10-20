"""Shared area of interest. All outputs use EPSG:32737 (WGS 84 / UTM 37S)."""
import os
from pyproj import Transformer

CRS = "EPSG:32737"
# Site centre: roof-ellipse centroid measured on Sentinel-2 L2A 2026-10-01
# (scripts/measure_bowl_s2.py). It replaces a first guess at the Jamhuri Park
# Showground centroid, which is 2 km east of the bowl.
CENTRE_LONLAT = (36.74964, -1.30603)
HALF_M = 1500  # 3 km box

_fwd = Transformer.from_crs("EPSG:4326", CRS, always_xy=True)
_inv = Transformer.from_crs(CRS, "EPSG:4326", always_xy=True)

def centre_utm():
    return _fwd.transform(*CENTRE_LONLAT)

def box_utm(half=HALF_M):
    x, y = centre_utm()
    return (x - half, y - half, x + half, y + half)

def box_lonlat(half=HALF_M, pad=0.002):
    x0, y0, x1, y1 = box_utm(half)
    a = _inv.transform(x0, y0); b = _inv.transform(x1, y1)
    return (a[0] - pad, a[1] - pad, b[0] + pad, b[1] + pad)

def gdal_env():
    os.environ.setdefault("CURL_CA_BUNDLE", "/root/.ccr/ca-bundle.crt") if os.path.exists("/root/.ccr/ca-bundle.crt") else None
    os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
    os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "4")
    os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "2")
