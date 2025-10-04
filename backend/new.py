import os
import json
import numpy as np
import xarray as xr
import rasterio
from rasterio.transform import from_origin
from rasterio.warp import calculate_default_transform, reproject
from scipy.interpolate import griddata
from rio_cogeo.cogeo import cog_translate
from rio_cogeo.profiles import cog_profiles
from rasterio.enums import Resampling

# --- All the original processing functions ---

def find_no2_variable(ds):
    """Finds the main Nitrogen Dioxide data variable in the dataset."""
    for name in ds.data_vars:
        if "NO2" in name.upper() or "nitrogendioxide" in name.lower():
            return name
    return list(ds.data_vars.keys())[0]

def extract_2d_array(ds, varname, time_index=0):
    """Extracts a 2D data slice from a variable."""
    var = ds[varname]
    if "time" in var.dims:
        da = var.isel(time=time_index)
    else:
        da = var
    return da

def handle_swath_grid(da, lat2d, lon2d, out_tif, resolution_deg=0.01):
    """Converts irregular swath data to a regular grid (regridding)."""
    lons = lon2d.flatten()
    lats = lat2d.flatten()
    vals = np.array(da).flatten()

    mask = ~np.isnan(vals) & ~np.isnan(lons) & ~np.isnan(lats)
    points = np.column_stack((lons[mask], lats[mask]))
    values = vals[mask]

    lon_min, lon_max = float(np.nanmin(lons)), float(np.nanmax(lons))
    lat_min, lat_max = float(np.nanmin(lats)), float(np.nanmax(lats))

    xi = np.arange(lon_min, lon_max, resolution_deg)
    yi = np.arange(lat_min, lat_max, resolution_deg)
    xx, yy = np.meshgrid(xi, yi)

    print(f"Regridding to shape {yy.shape} (ny, nx) with res {resolution_deg}°")
    grid_z = griddata(points, values, (xx, yy), method='linear')

    transform = from_origin(xi[0], yi[-1], resolution_deg, resolution_deg)
    profile = {
        'driver': 'GTiff', 'dtype': 'float32', 'count': 1,
        'height': grid_z.shape[0], 'width': grid_z.shape[1],
        'crs': 'EPSG:4326', 'transform': transform, 'nodata': np.nan
    }
    with rasterio.open(out_tif, 'w', **profile) as dst:
        dst.write(grid_z.astype('float32'), 1)
    return out_tif

def reproject_to_3857(src_tif, dst_tif):
    """Reprojects a GeoTIFF from EPSG:4326 to EPSG:3857 (Web Mercator)."""
    with rasterio.open(src_tif) as src:
        dst_crs = 'EPSG:3857'
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()
        kwargs.update({
            'crs': dst_crs, 'transform': transform,
            'width': width, 'height': height
        })
        with rasterio.open(dst_tif, 'w', **kwargs) as dst:
            reproject(
                source=rasterio.band(src, 1),
                destination=rasterio.band(dst, 1),
                src_transform=src.transform, src_crs=src.crs,
                dst_transform=transform, dst_crs=dst_crs,
                resampling=Resampling.bilinear
            )
    return dst_tif

def create_cog(src_tif, cog_tif):
    """Converts a GeoTIFF to a Cloud-Optimized GeoTIFF (COG)."""
    profile = cog_profiles.get("deflate")
    cog_translate(src_tif, cog_tif, profile)
    return cog_tif

def compute_global_stats(tif_path, pct=(2,98)):
    """Computes statistics for color mapping."""
    with rasterio.open(tif_path) as src:
        arr = src.read(1, out_shape=(int(src.height/4), int(src.width/4)))
    arr = arr.astype('float32')
    arr[arr == src.nodata] = np.nan
    vmin = float(np.nanpercentile(arr, pct[0]))
    vmax = float(np.nanpercentile(arr, pct[1]))
    return vmin, vmax

if __name__ == "__main__":
    
    # --- THIS IS THE KEY FIX ---
    # The path now correctly looks for the 'data' folder from inside the 'backend' directory.
    nc_path = os.path.join("data", "TEMPO_NO2_L2_V03_20250916T214329Z_S012G07.nc")
    
    # Set default values for other parameters
    var = None
    time_index = 0
    resolution_deg = 0.01
    out_dir = "tempo_output"

    if not os.path.exists(nc_path):
        print(f"Error: Input file not found at '{nc_path}'")
        exit()

    print(f"Processing file: {nc_path}")
    os.makedirs(out_dir, exist_ok=True)
    
    # Open the dataset, handling the group structure of TEMPO files
    try:
        ds = xr.open_dataset(nc_path, group='product')
        ds_geo = xr.open_dataset(nc_path, group='geolocation')
    except (OSError, KeyError):
        # Fallback if the group structure is different
        ds = xr.open_dataset(nc_path)
        ds_geo = ds

    varname = var or find_no2_variable(ds)
    print("Using variable:", varname)

    da = extract_2d_array(ds, varname, time_index=time_index)
    
    lat_coord = ds_geo['latitude']
    lon_coord = ds_geo['longitude']
    print("Found lat/lon coords:", lat_coord.name, lon_coord.name)
    
    out_4326 = os.path.join(out_dir, "tempo_no2_4326.tif")

    # The TEMPO data uses a 2D swath grid, so we call the correct handler
    handle_swath_grid(da, lat_coord.values, lon_coord.values, out_4326, resolution_deg=resolution_deg)

    out_3857 = os.path.join(out_dir, "tempo_no2_3857.tif")
    reproject_to_3857(out_4326, out_3857)

    out_cog = os.path.join(out_dir, "tempo_no2_3857_cog.tif")
    create_cog(out_3857, out_cog)

    vmin, vmax = compute_global_stats(out_3857)
    metadata = {
        "variable": varname,
        "vmin": vmin,
        "vmax": vmax,
        "cog_path": os.path.abspath(out_cog)
    }
    with open(os.path.join(out_dir, "tempo_metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    print("\n✅ Done. Preprocessed files are in the 'tempo_output' directory.")

