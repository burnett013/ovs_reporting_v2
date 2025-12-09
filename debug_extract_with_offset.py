import pypdf
import re
import os

pdf_path = "z_extra/cat_gr_2526.pdf"

def get_page_offset(page_text):
    """
    Attempts to find the printed page number in the text.
    Returns the printed page number found.
    """
    # Pattern for "131 | Page" or "Page 131"
    match = re.search(r'(\d+)\s*\|\s*Page', page_text)
    if match:
        return int(match.group(1))
    return None

def extract_smart(target_printed_page, num_pages_to_extract=3):
    print(f"--- Smart Extraction for Target Printed Page: {target_printed_page} ---")
    
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        return

    try:
        reader = pypdf.PdfReader(pdf_path)
        total_pages = len(reader.pages)
        
        # 1. Start with Naive Index
        naive_idx = max(0, target_printed_page - 1)
        print(f"1. Checking Naive PDF Index: {naive_idx} (PDF Page {naive_idx + 1})")
        
        if naive_idx >= total_pages:
            print("   Naive index out of bounds.")
            return

        naive_text = reader.pages[naive_idx].extract_text()
        found_printed_page = get_page_offset(naive_text)
        
        current_idx = naive_idx
        
        # 2. Calculate Offset if printed page found
        if found_printed_page is not None:
            print(f"   Found Printed Page Number: {found_printed_page}")
            if found_printed_page != target_printed_page:
                shift = target_printed_page - found_printed_page
                current_idx = naive_idx + shift
                print(f"2. Detected Offset! Shift needed: {shift} pages")
                print(f"   New Target PDF Index: {current_idx} (PDF Page {current_idx + 1})")
            else:
                print("   Printed page matches target! No shift needed.")
        else:
            print("   Could not find printed page number. Proceeding with naive index.")

        # 3. Extract Text from Corrected Index
        print(f"\n3. Extracting {num_pages_to_extract} pages starting from PDF Index {current_idx}...\n")
        print("="*50)
        
        for i in range(num_pages_to_extract):
            page_idx = current_idx + i
            if page_idx < total_pages:
                page_text = reader.pages[page_idx].extract_text()
                
                # Try to find page number on this page for verification
                p_num = get_page_offset(page_text)
                header = f"PDF Page {page_idx + 1} | Printed Page {p_num if p_num else 'Unknown'}"
                
                print(f"\n--- {header} ---\n")
                print(page_text)
                print("\n" + "-"*50)
            else:
                print(f"Index {page_idx} out of bounds.")

        print("="*50)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Target Printed Page 153 (Artificial Intelligence)
    extract_smart(153)
