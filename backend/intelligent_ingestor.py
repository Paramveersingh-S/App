import xarray as xr
import os
import numpy as np
from sqlalchemy import text, inspect
from database import engine, SessionLocal
from tqdm import tqdm

# --- CONFIGURATION ---
FILE_NAME = "TEMPO_NO2_L2_V03_20250916T214329Z_S012G07.nc"
FILE_PATH = os.path.join("data", FILE_NAME)
DOWNSAMPLE_FACTOR = 10

# This map defines the database column name and the corresponding path and variable name in the NASA file.
# This makes the script easy to adapt for new pollutants.
VARIABLE_MAP = {
    # DB Column Name: [Group in File, Variable Name in File]
    'no2': ['product', 'vertical_column_troposphere'],
    'quality_flag': ['product', 'main_data_quality_flag'],
    'terrain_height': ['support_data', 'terrain_height'],
    'surface_pressure': ['support_data', 'surface_pressure'],
    'wind_speed': ['support_data', 'wind_speed']
}

def intelligent_ingestor():
    if not os.path.exists(FILE_PATH):
        print(f"Error: Data file not found at {FILE_PATH}")
        return

    print(f"--- Starting Intelligent Ingestion for {FILE_NAME} ---")
    
    datasets = {}
    db = None
    try:
        # --- STAGE 1: INSPECT FILE AND DATABASE ---
        print("\n[Stage 1/3] Inspecting file and database schema...")
        
        datasets = {
            'geolocation': xr.open_dataset(FILE_PATH, group='geolocation'),
            'product': xr.open_dataset(FILE_PATH, group='product'),
            'support_data': xr.open_dataset(FILE_PATH, group='support_data')
        }

        found_variables = {}
        for db_col, (group, nasa_var) in VARIABLE_MAP.items():
            if nasa_var in datasets[group]:
                found_variables[db_col] = (group, nasa_var)
        print(f"Found variables in file: {list(found_variables.keys())}")
        
        inspector = inspect(engine)
        db_columns = [col['name'] for col in inspector.get_columns('air_quality_data')]
        
        # --- STAGE 2: DYNAMICALLY UPDATE SCHEMA ---
        print("\n[Stage 2/3] Synchronizing database schema...")
        columns_to_add = []
        for col_name in found_variables:
            if col_name not in db_columns:
                columns_to_add.append(col_name)

        if columns_to_add:
            print(f"Adding missing columns to 'air_quality_data': {columns_to_add}")
            with engine.connect() as connection:
                with connection.begin():
                    for col in columns_to_add:
                        # Use INTEGER for flags, DOUBLE PRECISION for data
                        data_type = "INTEGER" if "flag" in col else "DOUBLE PRECISION"
                        connection.execute(text(f"ALTER TABLE air_quality_data ADD COLUMN IF NOT EXISTS {col} {data_type};"))
            print("Schema update complete.")
        else:
            print("Database schema is already up to date.")

        # --- STAGE 3: INGEST DATA ---
        print("\n[Stage 3/3] Preparing and ingesting data...")
        
        latitude = datasets['geolocation']['latitude'].values
        longitude = datasets['geolocation']['longitude'].values
        time_data = datasets['geolocation']['time'].values
        
        extracted_data = {db_col: datasets[group][nasa_var].values for db_col, (group, nasa_var) in found_variables.items()}

        records_to_insert = []
        for lat_idx in tqdm(range(0, latitude.shape[0], DOWNSAMPLE_FACTOR), desc="Processing Scanlines"):
            time_for_scanline = np.datetime_as_string(time_data[lat_idx])
            for lon_idx in range(0, latitude.shape[1], DOWNSAMPLE_FACTOR):
                
                # --- THIS IS THE FIX ---
                # First, get the raw quality flag value which could be a float or NaN
                if 'quality_flag' in extracted_data:
                    q_flag_raw = extracted_data['quality_flag'][lat_idx, lon_idx]
                    # Check for NaN before converting to integer
                    if np.isnan(q_flag_raw) or int(q_flag_raw) != 0:
                        continue
                # --- END OF FIX ---

                record = {
                    "time": time_for_scanline,
                    "lat": float(latitude[lat_idx, lon_idx]),
                    "lon": float(longitude[lat_idx, lon_idx]),
                    "source": "NASA-TEMPO"
                }
                
                valid_record = True
                for col_name, data_array in extracted_data.items():
                    value = float(data_array[lat_idx, lon_idx])
                    if np.isnan(value):
                        valid_record = False
                        break
                    # Use integer conversion for flags
                    record[col_name] = int(value) if "flag" in col_name else value

                if valid_record:
                    records_to_insert.append(record)
        
        if not records_to_insert:
            print("No valid, high-quality records found to insert.")
            return

        print(f"\nList prepared with {len(records_to_insert)} records. Executing bulk insert...")

        db_cols_str = ", ".join(found_variables.keys())
        values_str = ", ".join([f":{k}" for k in found_variables.keys()])
        update_str = ", ".join([f"{k} = EXCLUDED.{k}" for k in found_variables.keys()])

        insert_query = text(f"""
            INSERT INTO air_quality_data (time, latitude, longitude, source, {db_cols_str})
            VALUES (:time, :lat, :lon, :source, {values_str})
            ON CONFLICT (time, latitude, longitude) DO UPDATE SET {update_str};
        """)
        
        db = SessionLocal()
        db.execute(insert_query, records_to_insert)
        db.commit()
        
        print(f"✅ Successfully ingested {len(records_to_insert)} records.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        for ds in datasets.values():
            ds.close()
        if 'db' in locals() and db and db.is_active:
            db.close()

if __name__ == "__main__":
    intelligent_ingestor()

