# /backend/check_netcdf.py
import netCDF4 as nc
import os

# --- IMPORTANT ---
# Change this to the exact name of the file you downloaded
FILE_NAME = "TEMPO_NO2_L2_V03_20250916T214329Z_S012G07.nc"
FILE_PATH = os.path.join("data", FILE_NAME)

def print_group_structure(group, indent=''):
    """ A helper function to recursively print the structure of a group. """
    print(f"{indent}Group: {group.name}")
    
    # Print Dimensions
    if group.dimensions:
        print(f"{indent}  Dimensions:")
        for dimname, dim in group.dimensions.items():
            print(f"{indent}    - {dimname}: {len(dim)}")
    
    # Print Variables
    if group.variables:
        print(f"{indent}  Variables:")
        for varname, var in group.variables.items():
            print(f"{indent}    - {varname} {var.dimensions} {var.shape}")
            
    # Print Subgroups (and recurse)
    if group.groups:
        print(f"{indent}  Subgroups:")
        for grpname, grp in group.groups.items():
            print(f"{indent}    - {grpname}")
            print_group_structure(grp, indent + '    ')

# --- Main script execution ---
if not os.path.exists(FILE_PATH):
    print(f"Error: File not found at {FILE_PATH}")
else:
    try:
        print(f"--- Structure of file: {FILE_NAME} ---\n")
        with nc.Dataset(FILE_PATH, 'r') as rootgrp:
            print_group_structure(rootgrp)
    except Exception as e:
        print(f"An error occurred: {e}")