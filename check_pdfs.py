from utils import llm_parser
import os

# Paths provided by user/found in z_extra
ug_pdf_2526 = "/Users/andyburnett/Library/Mobile Documents/com~apple~CloudDocs/Desktop/X03.27.25/OVS/Special Projects/catalog/catalog_v6/z_extra/2526/full/cat_ug_2526.pdf"
gr_pdf_2526 = "/Users/andyburnett/Library/Mobile Documents/com~apple~CloudDocs/Desktop/X03.27.25/OVS/Special Projects/catalog/catalog_v6/z_extra/2526/full/cat_gr_2526.pdf"

ug_pdf_2425 = "/Users/andyburnett/Library/Mobile Documents/com~apple~CloudDocs/Desktop/X03.27.25/OVS/Special Projects/catalog/catalog_v6/z_extra/2425/cat_full/cat_ug_2425.pdf"
gr_pdf_2425 = "/Users/andyburnett/Library/Mobile Documents/com~apple~CloudDocs/Desktop/X03.27.25/OVS/Special Projects/catalog/catalog_v6/z_extra/2425/cat_full/cat_gr_2425.pdf"

def check_pdf(path, name):
    print(f"--- Checking {name} ---")
    if not os.path.exists(path):
        print(f"ERROR: File not found: {path}")
        return
    
    try:
        pages = llm_parser.extract_all_pages(path)
        print(f"Success! Extracted {len(pages)} pages.")
        if len(pages) > 0:
            print(f"First page content length: {len(pages[0])} chars")
        else:
            print("WARNING: PDF has 0 pages.")
    except Exception as e:
        print(f"ERROR extracting PDF: {e}")

print("=== 2025-2026 Catalogs ===")
check_pdf(ug_pdf_2526, "UG 2526")
check_pdf(gr_pdf_2526, "GR 2526")

print("\n=== 2024-2025 Catalogs ===")
check_pdf(ug_pdf_2425, "UG 2425")
check_pdf(gr_pdf_2425, "GR 2425")
