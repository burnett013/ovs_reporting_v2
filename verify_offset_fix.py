import pypdf
import re

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

def verify_offset_logic(target_printed_page):
    print(f"Verifying offset logic for Target Printed Page: {target_printed_page}")
    
    try:
        reader = pypdf.PdfReader(pdf_path)
        
        # 1. Naive Approach (Index = Page - 1)
        naive_idx = target_printed_page - 1
        print(f"Naive PDF Index: {naive_idx} (PDF Page {naive_idx + 1})")
        
        if naive_idx >= len(reader.pages):
            print("Naive index out of bounds.")
            return

        naive_page_text = reader.pages[naive_idx].extract_text()
        found_printed_page = get_page_offset(naive_page_text)
        
        if found_printed_page is None:
            print("Could not find printed page number on the naive page.")
            return
            
        print(f"Found Printed Page Number on Naive Page: {found_printed_page}")
        
        # 2. Calculate Shift
        shift = target_printed_page - found_printed_page
        print(f"Calculated Shift: {shift} pages")
        
        # 3. Apply Shift
        corrected_idx = naive_idx + shift
        print(f"Corrected PDF Index: {corrected_idx} (PDF Page {corrected_idx + 1})")
        
        if corrected_idx >= len(reader.pages):
            print("Corrected index out of bounds.")
            return

        # 4. Verify Content on Corrected Page
        corrected_page_text = reader.pages[corrected_idx].extract_text()
        found_printed_page_corrected = get_page_offset(corrected_page_text)
        print(f"Found Printed Page Number on Corrected Page: {found_printed_page_corrected}")
        
        if found_printed_page_corrected == target_printed_page:
            print("SUCCESS: Landed on the correct printed page!")
        else:
            print(f"FAILURE: Expected {target_printed_page}, found {found_printed_page_corrected}")
            
        # Check for Program Name
        if "Artificial Intelligence" in corrected_page_text:
            print("CONFIRMED: 'Artificial Intelligence' found on the corrected page.")
        else:
            print("WARNING: 'Artificial Intelligence' NOT found on the corrected page.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Test for Artificial Intelligence, M.S.A.I. which is on Printed Page 153
    verify_offset_logic(153)
