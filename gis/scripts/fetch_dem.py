"""W1: Copernicus GLO-30 DSM (public AWS COG) clipped to a 12 km box for the far ring
and the 3 km box for the site. GLO-30 is a surface model from TanDEM-X data of 2011-2015,
so it predates the stadium. Copernicus DEM, free; credit required."""
import sys
from pathlib import Path
import rasterio
from rasterio.warp import reproject, Resampling, calculate_default_transform
sys.path.insert(0, str(Path(__file__).parent))
from _aoi import box_utm, gdal_env, CRS

gdal_env()
URL = "/vsicurl/https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_S02_00_E036_00_DEM/Copernicus_DSM_COG_10_S02_00_E036_00_DEM.tif"
OUT = Path(__file__).resolve().parents[1] / "raw" / "dem"

def clip(half, res, name):
    x0, y0, x1, y1 = box_utm(half)
    W, H = int((x1 - x0) / res), int((y1 - y0) / res)
    tr = rasterio.transform.from_origin(x0, y1, res, res)
    import numpy as np
    dst = np.zeros((H, W), dtype="float32")
    with rasterio.open(URL) as s:
        reproject(rasterio.band(s, 1), dst, dst_transform=tr, dst_crs=CRS, resampling=Resampling.bilinear)
    OUT.mkdir(parents=True, exist_ok=True)
    with rasterio.open(OUT / name, "w", driver="GTiff", width=W, height=H, count=1, dtype="float32",
                       crs=CRS, transform=tr, compress="deflate") as o:
        o.write(dst, 1)
    print(name, dst.min(), dst.max())

if __name__ == "__main__":
    clip(1500, 10, "glo30_site_3km_10m.tif")
    clip(6000, 30, "glo30_far_12km_30m.tif")
