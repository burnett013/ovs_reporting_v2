import pandas as pd
import os

file_path = "z_extra/2425/full/toc.xlsx"

if os.path.exists(file_path):
    try:
        df = pd.read_excel(file_path)
        
        # Filter for Exploratory programs
        # Check both "Program" and "Program Name" columns to be safe
        col_name = 'Program' if 'Program' in df.columns else 'Program Name'
        
        if col_name in df.columns:
            exploratory = df[df[col_name].astype(str).str.contains("Exploratory", case=False, na=False)]
            
            if not exploratory.empty:
                print(f"Found {len(exploratory)} entries for 'Exploratory':")
                print(exploratory[[col_name, 'Page Number', 'Catalog Name']].to_string())
            else:
                print("No entries found containing 'Exploratory'.")
                
            # Also print columns to check for any hidden spaces or issues
            print("\nColumns and Types:")
            print(df.dtypes)
            
        else:
            print(f"Column '{col_name}' not found. Available columns: {df.columns.tolist()}")

    except Exception as e:
        print(f"Error reading file: {e}")
else:
    print(f"File not found: {file_path}")
