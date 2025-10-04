# tile_server.py
import os
import json
import numpy as np
import rasterio
from rasterio.enums import Resampling
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from io import BytesIO
from PIL import Image
import mercantile
from pyproj import Transformer
from matplotlib import cm
from matplotlib.colors import Normalize
from functools import lru_cache

# CONFIG - point to the cog and metadata produced earlier
COG_PATH = os.environ.get("AURA_COG_PATH", "tempo_output/tempo_no2_3857_cog.tif")
META_PATH = os.environ.get("AURA_META_PATH", "tempo_output/tempo_metadata.json")
TILE_SIZE = 256

if not os.path.exists(COG_PATH):
    raise RuntimeError(f"COG not found at {COG_PATH}")

with open(META_PATH) as f:
    meta = json.load(f)
VMIN = meta.get("vmin", None)
VMAX = meta.get("vmax", None)

app = FastAPI()

# transformer from WGS84 lon/lat -> WebMercator
transformer = Transformer.from_crs("EPSG:4326", "EPSG:3857", always_xy=True)

# open dataset once
src = rasterio.open(COG_PATH)

def read_tile(z, x, y):
    # mercantile returns bounds in lon/lat
    bounds = mercantile.bounds(x, y, z)  # west, south, east, north
    west, south, east, north = bounds

    # transform to 3857 coordinates
    minx, miny = transformer.transform(west, south)
    maxx, maxy = transformer.transform(east, north)

    # compute window in dataset
    window = rasterio.windows.from_bounds(minx, miny, maxx, maxy, transform=src.transform)
    # read with resampling to TILE_SIZE
    out_shape = (TILE_SIZE, TILE_SIZE)
    data = src.read(1, window=window, out_shape=out_shape, resampling=Resampling.bilinear)
    data = data.astype('float32')
    nodata = src.nodata
    if nodata is not None:
        data[data == nodata] = np.nan
    return data

def colormap_to_png(arr, vmin=VMIN, vmax=VMAX):
    # input: 2D float array
    if vmin is None or vmax is None:
        # fallback to percentiles for the tile
        valid = arr[~np.isnan(arr)]
        if valid.size == 0:
            vmin, vmax = 0.0, 1.0
        else:
            vmin = float(np.nanpercentile(valid, 2))
            vmax = float(np.nanpercentile(valid, 98))

    norm = Normalize(vmin=vmin, vmax=vmax, clip=True)
    cmap = cm.get_cmap('inferno')  # choose your colormap; customize if you want green tones
    rgba = cmap(norm(arr))  # NxMx4 floats [0..1]
    # set alpha 0 where NaN
    mask = np.isnan(arr)
    rgba[..., 3][mask] = 0.0
    img = (rgba * 255).astype(np.uint8)
    pil = Image.fromarray(img, mode="RGBA")
    buf = BytesIO()
    pil.save(buf, format="PNG")
    buf.seek(0)
    return buf

@lru_cache(maxsize=1024)
def generate_tile_bytes(z, x, y):
    try:
        arr = read_tile(z, x, y)
    except Exception as e:
        raise
    buf = colormap_to_png(arr)
    return buf.getvalue()

@app.get("/tiles/{z}/{x}/{y}.png")
async def tile(z: int, x: int, y: int):
    try:
        png_bytes = generate_tile_bytes(int(z), int(x), int(y))
        return StreamingResponse(BytesIO(png_bytes), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metadata")
async def metadata():
    return JSONResponse(content={
        "variable": meta.get("variable"),
        "vmin": meta.get("vmin"),
        "vmax": meta.get("vmax"),
        "cog_path": meta.get("cog_path")
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("tile_server:app", host="0.0.0.0", port=8000, reload=True)
