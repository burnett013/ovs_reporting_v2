import pandas as pd
import os

directory = "/Users/andyburnett/Library/Mobile Documents/com~apple~CloudDocs/Desktop/X03.27.25/OVS/Special Projects/catalog/catalog_v6/z_extra/2425/full"

files = [
    "truth_cat_full_2425.xlsx",
    "new_truth_toc_all_2425.xlsx",
    "toc.xlsx",
    "new_truth_toc_24225.xlsx",
    "old_truth_toc_full_2425.xlsx"
]

print(f"{'Filename':<35} | {'Rows':<5}")
print("-" * 45)

for f in files:
    path = os.path.join(directory, f)
    try:
        df = pd.read_excel(path)
        print(f"{f:<35} | {len(df):<5}")
    except Exception as e:
        print(f"{f:<35} | Error: {e}")
