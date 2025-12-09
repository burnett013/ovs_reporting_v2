import pandas as pd
import os
import glob

root_dir = "/Users/andyburnett/Library/Mobile Documents/com~apple~CloudDocs/Desktop/X03.27.25/OVS/Special Projects/catalog/catalog_v6/z_extra"

print(f"{'File Path':<80} | {'Rows':<5}")
print("-" * 90)

for filepath in glob.glob(os.path.join(root_dir, "**/*.xlsx"), recursive=True):
    # skip temp files
    if "~$" in filepath: continue
    
    try:
        df = pd.read_excel(filepath)
        print(f"{filepath.replace(root_dir, '') :<80} | {len(df):<5}")
    except Exception as e:
        pass
