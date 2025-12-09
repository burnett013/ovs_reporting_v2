import os
from dotenv import load_dotenv
import google.generativeai as genai
from utils import llm_parser

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def debug_2526_program():
    # 2526 Paths
    pdf_path = "/Users/andyburnett/Library/Mobile Documents/com~apple~CloudDocs/Desktop/X03.27.25/OVS/Special Projects/catalog/catalog_v6/z_extra/2526/full/cat_ug_2526.pdf"
    program_name = "Accounting"
    page_num = 156
    model_choice = "Gemini 1.5 Flash"
    
    print(f"--- Debugging 2526 Program: {program_name} (Page {page_num}) ---")
    print(f"PDF: {pdf_path}")
    
    # 1. Extract All Pages
    print("\n1. Extracting PDF pages...")
    try:
        pages_text = llm_parser.extract_all_pages(pdf_path)
        print(f"   Extracted {len(pages_text)} pages.")
    except Exception as e:
        print(f"   Error extracting PDF: {e}")
        return

    # 2. Calculate Index
    naive_idx = max(0, page_num - 1)
    print(f"\n2. Page Index Calculation:")
    print(f"   Target Page Number: {page_num}")
    print(f"   Naive Index (0-based): {naive_idx}")
    
    # 3. Check Page Content & Offset
    page_content = pages_text[naive_idx]
    print(f"\n3. Content of Naive Page (First 500 chars):\n   {page_content[:500]}...")
    
    # Simulate get_page_offset logic
    import re
    found_printed_page = None
    
    # Pattern 1 (2526 Format: "156 | Page")
    match = re.search(r'(\d+)\s*\|\s*Page', page_content)
    if match:
        found_printed_page = int(match.group(1))
        print(f"   Found Printed Page (Pattern 1): {found_printed_page}")
    
    current_idx = naive_idx
    if found_printed_page is not None:
        shift = page_num - found_printed_page
        current_idx = naive_idx + shift
        print(f"   Calculated Shift: {shift}")
        print(f"   New Adjusted Index: {current_idx}")
    else:
        print("   No printed page number found. Using naive index.")

    # 4. Extract Program Text (Next 4 pages)
    start_idx = max(0, min(current_idx, len(pages_text) - 1))
    max_pages = 4
    end_idx = min(len(pages_text), start_idx + max_pages)
    program_text = "".join(pages_text[start_idx:end_idx])
    
    print(f"\n4. Extracted Program Text for LLM ({len(program_text)} chars):")
    print(f"   {program_text[:1000]}...")

    # 5. Call LLM
    print("\n5. Calling LLM...")
    try:
        details = llm_parser.parse_program_details(
            program_text, 
            program_name, 
            "Degree", 
            "ug", 
            "2025-2026", 
            model_choice
        )
        print("\n6. LLM Result:")
        print(details)
    except Exception as e:
        print(f"   Error calling LLM: {e}")

if __name__ == "__main__":
    debug_2526_program()
