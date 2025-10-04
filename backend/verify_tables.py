from sqlalchemy import inspect
from database import engine

def main():
    """
    Connects to the database and prints a full report of all tables and their columns.
    """
    print("Connecting to the database to inspect the full schema...")
    try:
        inspector = inspect(engine)
        
        # Get a list of all table names in the 'public' schema
        tables = inspector.get_table_names(schema='public')
        
        if not tables:
            print("Connection successful, but no tables were found in the 'public' schema.")
            return

        print("\n✅ SUCCESS: Found the following tables and columns:")
        
        # Loop through each table and print its details
        for table_name in sorted(tables):
            print(f"\n--- Table: {table_name} ---")
            columns = inspector.get_columns(table_name, schema='public')
            column_names = [col['name'] for col in columns]
            print(column_names)
            
    except Exception as e:
        print(f"❌ FAILED: An error occurred during inspection: {e}")

if __name__ == "__main__":
    main()

