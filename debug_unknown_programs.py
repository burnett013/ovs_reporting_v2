import pypdf
import re
import os

pdf_path = "z_extra/cat_gr_2526.pdf"

def get_page_offset(page_text):
    match = re.search(r'(\d+)\s*\|\s*Page', page_text)
    if match:
        return int(match.group(1))
    return None

def extract_program_text(target_printed_page, program_name):
    print(f"\n--- Debugging: {program_name} (Page {target_printed_page}) ---")
    
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        return

    try:
        reader = pypdf.PdfReader(pdf_path)
        total_pages = len(reader.pages)
        
        # 1. Start with Naive Index
        naive_idx = max(0, target_printed_page - 1)
        
        if naive_idx >= total_pages:
            print("   Naive index out of bounds.")
            return

        naive_text = reader.pages[naive_idx].extract_text()
        found_printed_page = get_page_offset(naive_text)
        
        current_idx = naive_idx
        
        # 2. Calculate Offset
        if found_printed_page is not None:
            if found_printed_page != target_printed_page:
                shift = target_printed_page - found_printed_page
                current_idx = naive_idx + shift
                print(f"   Shifted by {shift} pages. New PDF Index: {current_idx}")
            else:
                print("   No shift needed.")
        else:
            print("   Could not find printed page number. Using naive index.")

        # 3. Extract 4 pages (to cover multi-page descriptions)
        print(f"   Extracting 4 pages starting from PDF Index {current_idx}...\n")
        print("="*50)
        
        full_text = ""
        for i in range(4):
            page_idx = current_idx + i
            if page_idx < total_pages:
                page_text = reader.pages[page_idx].extract_text()
                p_num = get_page_offset(page_text)
                print(f"\n--- PDF Page {page_idx + 1} | Printed Page {p_num if p_num else 'Unknown'} ---\n")
                print(page_text)
                print("\n" + "-"*50)
                full_text += page_text
            else:
                print(f"Index {page_idx} out of bounds.")

        print("="*50)
        return full_text

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Big Data Analytics, Ph.D. - Page 156
    extract_program_text(156, "Big Data Analytics, Ph.D.")
    
    # Comparative Literary Studies Graduate Certificate - Page 192
    extract_program_text(192, "Comparative Literary Studies Graduate Certificate")
    
    # Creative Writing Graduate Certificate - Page 194
    extract_program_text(194, "Creative Writing Graduate Certificate")
    
    # Cyber Intelligence Graduate Certificate - Page 196
    extract_program_text(196, "Cyber Intelligence Graduate Certificate")
