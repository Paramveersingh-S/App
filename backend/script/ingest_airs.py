# /backend/scripts/ingest_airs.py
import h5py
import numpy as np
import os
from sqlalchemy import text
from database import SessionLocal
from tqdm import tqdm

# --- IMPORTANT ---
# Change this to the exact name of the file you downloaded
FILE_NAME = "AIRS.2025.09.28.076.L2.RetStd_IR.v6.0.34.0.R25271044911.hdf"
FILE_PATH = os.path.join("data", FILE_NAME)

# The timestamp for this data granule (from the file name)
# In a real-time system, this would be extracted dynamically
TIMESTAMP = "2025-09-28T07:35:21Z"

def process_airs_file():
    if not os.path.exists(FILE_PATH):
        print(f"Error: Data file not found at {FILE_PATH}")
        return

    print(f"Opening AIRS HDF file: {FILE_PATH}")
    db = SessionLocal()

    try:
        # Open the HDF file for reading
        with h5py.File(FILE_PATH, 'r') as f:
            # Navigate the internal file structure to get to the data
            # This path is standard for AIRS L2 files
            data_fields = f['/HDFEOS/SWATHS/L2_Standard_atmospheric&surface_product/Data Fields/']
            geo_fields = f['/HDFEOS/SWATHS/L2_Standard_atmospheric&surface_product/Geolocation Fields/']

            # Extract the data arrays we need (Latitude, Longitude, and Total CO)
            co_data_raw = data_fields['TotCO_A'][:]
            latitude = geo_fields['Latitude'][:]
            longitude = geo_fields['Longitude'][:]

            # Get the metadata needed to convert the raw values to real units
            # HDF files store this as "attributes" on the dataset
            attrs = data_fields['TotCO_A'].attrs
            fill_value = attrs['_FillValue'][0]
            scale_factor = attrs['scale_factor'][0]
            add_offset = attrs['add_offset'][0]

        print("Preparing records for bulk insert...")
        records_to_insert = []

        # Loop through the 2D data grid
        for lat_idx in tqdm(range(latitude.shape[0]), desc="Processing AIRS Data"):
            for lon_idx in range(latitude.shape[1]):
                co_raw = co_data_raw[lat_idx, lon_idx]

                # Skip invalid data points using the fill value from the metadata
                if co_raw == fill_value:
                    continue

                # Apply the formula to get the real scientific value
                co_value = (co_raw - add_offset) * scale_factor
                lat = float(latitude[lat_idx, lon_idx])
                lon = float(longitude[lat_idx, lon_idx])

                # Skip if coordinates are also invalid
                if np.isnan(lat) or np.isnan(lon):
                    continue

                records_to_insert.append({
                    "time": TIMESTAMP,
                    "lat": lat,
                    "lon": lon,
                    "source": "NASA-AIRS",
                    "value": co_value
                })

        if not records_to_insert:
            print("No valid records found in the file to insert.")
            return

        print(f"\nList prepared with {len(records_to_insert)} records. Executing bulk insert...")

        insert_query = text("""
            INSERT INTO air_quality_data (time, latitude, longitude, source, co)
            VALUES (:time, :lat, :lon, :source, :value)
            ON CONFLICT (time, latitude, longitude) DO UPDATE SET co = :value;
        """)
        
        db.execute(insert_query, records_to_insert)
        db.commit()
        
        print(f"✅ Successfully processed and inserted/updated {len(records_to_insert)} CO records from the AIRS file.")

    except Exception as e:
        print(f"An error occurred: {e}")
        if 'db' in locals() and db.is_active:
            db.rollback()
    finally:
        if 'db' in locals() and db.is_active:
            db.close()

if __name__ == "__main__":
    process_airs_file()