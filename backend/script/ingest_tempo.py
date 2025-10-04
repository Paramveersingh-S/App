import xarray as xr
import os
import numpy as np
from sqlalchemy import text
from database import SessionLocal
from tqdm import tqdm

# --- CONFIGURATION ---
# Update this to the exact name of the file you have downloaded
FILE_NAME = "TEMPO_NO2_L2_V03_20250916T214329Z_S012G07.nc"
FILE_PATH = os.path.join("data", FILE_NAME)
DOWNSAMPLE_FACTOR = 10

def process_tempo_file_to_grid():
    if not os.path.exists(FILE_PATH):
        print(f"Error: Data file not found at {FILE_PATH}")
        return
        
    print(f"Opening TEMPO file for grid ingestion: {FILE_PATH}")
    db = SessionLocal()
    
    try:
        # Open the different groups within the file based on your confirmed structure
        ds_geo = xr.open_dataset(FILE_PATH, group='geolocation')
        ds_prod = xr.open_dataset(FILE_PATH, group='product')
        ds_support = xr.open_dataset(FILE_PATH, group='support_data')

        # Extract data using the correct variable names
        latitude = ds_geo['latitude'].values
        longitude = ds_geo['longitude'].values
        time_data = ds_geo['time'].values
        no2_data = ds_prod['vertical_column_troposphere'].values
        quality_flag = ds_prod['main_data_quality_flag'].values
        terrain_height = ds_support['terrain_height'].values
        surface_pressure = ds_support['surface_pressure'].values
        
        print("Preparing records for bulk insert (downsampled)...")
        records_to_insert = []

        for lat_idx in tqdm(range(0, latitude.shape[0], DOWNSAMPLE_FACTOR), desc="Processing Scanlines"):
            time_for_scanline = np.datetime_as_string(time_data[lat_idx])
            for lon_idx in range(0, latitude.shape[1], DOWNSAMPLE_FACTOR):
                
                # Safely check the quality flag
                q_flag_raw = quality_flag[lat_idx, lon_idx]
                if np.isnan(q_flag_raw):
                    continue
                
                q_flag = int(q_flag_raw)
                if q_flag != 0:
                    continue

                no2_value = float(no2_data[lat_idx, lon_idx])
                if np.isnan(no2_value) or no2_value < -1e10:
                    continue

                records_to_insert.append({
                    "time": time_for_scanline,
                    "lat": float(latitude[lat_idx, lon_idx]),
                    "lon": float(longitude[lat_idx, lon_idx]),
                    "no2_tropospheric": no2_value,
                    "terrain_height": float(terrain_height[lat_idx, lon_idx]),
                    "surface_pressure": float(surface_pressure[lat_idx, lon_idx]),
                    "quality_flag": q_flag
                })

        if not records_to_insert:
            print("No valid, high-quality records found to insert.")
            return

        print(f"\nList prepared with {len(records_to_insert)} records. Executing bulk insert...")

        # --- THIS IS THE FIX ---
        # The full, correct SQL INSERT statement is now here.
        insert_query = text("""
            INSERT INTO tempo_grid_data (
                time, latitude, longitude, no2_tropospheric, terrain_height, 
                surface_pressure, quality_flag
            )
            VALUES (
                :time, :lat, :lon, :no2_tropospheric, :terrain_height, 
                :surface_pressure, :quality_flag
            )
            ON CONFLICT (time, latitude, longitude) DO UPDATE SET 
                no2_tropospheric = EXCLUDED.no2_tropospheric,
                quality_flag = EXCLUDED.quality_flag;
        """)
        
        db.execute(insert_query, records_to_insert)
        db.commit()
        
        print(f"✅ Successfully ingested {len(records_to_insert)} records into 'tempo_grid_data'.")

    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        if 'db' in locals() and db.is_active: db.close()
        if 'ds_geo' in locals(): ds_geo.close()
        if 'ds_prod' in locals(): ds_prod.close()
        if 'ds_support' in locals(): ds_support.close()

if __name__ == "__main__":
    process_tempo_file_to_grid()
