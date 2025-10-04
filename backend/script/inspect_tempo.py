import xarray as xr
import os

# --- THIS IS THE CHANGE ---
# The script now uses a hardcoded file name instead of a command-line argument.
# Make sure this file is located in your /backend/data/ folder.
nc_path = os.path.join("data", "TEMPO_NO2_L2_V03_20250916T214329Z_S012G07.nc")

if not os.path.exists(nc_path):
    print(f"Error: File not found at '{nc_path}'")
else:
    try:
        # Open the dataset
        ds = xr.open_dataset(nc_path)
        
        # Print a summary of the file's contents
        print(f"--- Inspecting File: {os.path.basename(nc_path)} ---")
        print(ds)
        
        print("\n--- Data variables ---")
        for name, var in ds.data_vars.items():
            print(f" - {name} : dims={var.dims} shape={var.shape}")
            
        print("\n--- Coordinates ---")
        for name, coord in ds.coords.items():
            print(f" - {name} : dims={coord.dims} shape={coord.shape}")
            
    except Exception as e:
        print(f"An error occurred while opening the file: {e}")
