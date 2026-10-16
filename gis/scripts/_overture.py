"""Read Overture Maps GeoParquet from the public AWS bucket with a bbox filter."""
import pyarrow.dataset as ds
import pyarrow.fs as pafs
import geopandas as gpd
import shapely

REL = "2026-09-23.0"
_FS = pafs.S3FileSystem(anonymous=True, region="us-west-2")

def read(theme, typ, bbox, columns=None):
    xmin, ymin, xmax, ymax = bbox
    d = ds.dataset(f"overturemaps-us-west-2/release/{REL}/theme={theme}/type={typ}/",
                   filesystem=_FS, format="parquet")
    f = ((ds.field("bbox", "xmin") < xmax) & (ds.field("bbox", "xmax") > xmin) &
         (ds.field("bbox", "ymin") < ymax) & (ds.field("bbox", "ymax") > ymin))
    t = d.to_table(filter=f, columns=columns)
    df = t.to_pandas()
    df["geometry"] = shapely.from_wkb(df["geometry"])
    return gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
