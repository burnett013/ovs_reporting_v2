import pandas as pd

file_path = "/Users/andyburnett/Library/Mobile Documents/com~apple~CloudDocs/Desktop/X03.27.25/OVS/Special Projects/catalog/catalog_v6/z_extra/2526/full/truth_2526.xlsx"

try:
    df = pd.read_excel(file_path)
    print(f"--- Inspecting Page Numbers: {file_path} ---")
    
    if 'Page Number' in df.columns and 'Catalog Name' in df.columns:
        # Undergraduate Stats
        ug_df = df[df['Catalog Name'].str.contains("Undergraduate", na=False)]
        if not ug_df.empty:
            print(f"\nUndergraduate Programs: {len(ug_df)}")
            print(f"Min Page: {ug_df['Page Number'].min()}")
            print(f"Max Page: {ug_df['Page Number'].max()}")
        else:
            print("\nNo Undergraduate programs found.")

        # Graduate Stats
        gr_df = df[df['Catalog Name'].str.contains("Graduate", na=False)]
        if not gr_df.empty:
            print(f"\nGraduate Programs: {len(gr_df)}")
            print(f"Min Page: {gr_df['Page Number'].min()}")
            print(f"Max Page: {gr_df['Page Number'].max()}")
        else:
            print("\nNo Graduate programs found.")
            
    else:
        print("\nERROR: Required columns not found!")

except Exception as e:
    print(f"Error reading file: {e}")
