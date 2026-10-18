# Horizon scenery notes

The module adds estimated racecourse geometry, sampled terrain, a ridge silhouette, and 21 estimated city towers.

The racecourse point comes from `gis/scripts/export_web.py`. Its oval is estimated from historian frames `JWNowpO44rw_000004.933` and `JWNowpO44rw_001232.600`, plus `engineering/environment_from_drone_2026-10-17.md`. The road and building GeoPackages have no racecourse outline. The footage decides the layout. Concept renders set the look only.

The terrain raster comes from Copernicus GLO-30 DSM (2011-2015), as recorded in `gis/derived/heightmap_glo30_far_12km_30m.json`. The raster is a 12 km square. It reaches 6 km from the site on each cardinal axis and about 8.49 km at the corners. Terrain bands use that coverage only. The requested 12 km radial terrain and matching ridge heights remain unresolved.

The Ngong Hills ridge position comes from `engineering/environment_from_drone_2026-10-17.md`. The silhouette height and shape are estimated. The CBD point comes from `gis/scripts/export_web.py`. Upper Hill is placed by estimate from the environment notes. Tower positions and heights are estimated. Their geometry is for visualization.
