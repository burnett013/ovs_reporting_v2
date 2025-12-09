import pandas as pd

# Path to the file found in z_extra/2526/full
file_path = "/Users/andyburnett/Library/Mobile Documents/com~apple~CloudDocs/Desktop/X03.27.25/OVS/Special Projects/catalog/catalog_v6/z_extra/2526/full/truth_2526.xlsx"

try:
    df = pd.read_excel(file_path)
    print(f"--- Inspecting: {file_path} ---")
    print(f"Columns: {df.columns.tolist()}")
    
    if 'Catalog Name' in df.columns:
        unique_names = df['Catalog Name'].unique()
        print(f"\nUnique Catalog Names found:\n{unique_names}")
        
        # Check for exact matches required by the app
        has_ug = any("Undergraduate" in str(name) for name in unique_names)
        has_gr = any("Graduate" in str(name) for name in unique_names)
        
        print(f"\nContains 'Undergraduate': {has_ug}")
        print(f"Contains 'Graduate': {has_gr}")
    else:
        print("\nERROR: 'Catalog Name' column not found!")

except Exception as e:
    print(f"Error reading file: {e}")
