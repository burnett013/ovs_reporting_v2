import os
from dotenv import load_dotenv
import google.generativeai as genai
from pypdf import PdfReader
from utils import llm_parser

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def debug_single_program(pdf_path, program_name, page_num, academic_year="2024-2025", model_choice="Gemini 1.5 Flash"):
    print(f"--- Debugging Program: {program_name} (Page {page_num}) ---")
    print(f"PDF: {pdf_path}")
    print(f"Model: {model_choice}")
    
    # 1. Extract All Pages (Simulate pre-loading)
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
    
    if naive_idx >= len(pages_text):
        print("   Error: Page number out of range.")
        return

    # 3. Check Page Content & Offset
    page_content = pages_text[naive_idx]
    print(f"\n3. Content of Naive Page (First 500 chars):\n   {page_content[:500]}...")
    
    # Simulate get_page_offset logic
    import re
    found_printed_page = None
    
    # Pattern 1
    match = re.search(r'(\d+)\s*\|\s*Page', page_content)
    if match:
        found_printed_page = int(match.group(1))
        print(f"   Found Printed Page (Pattern 1): {found_printed_page}")
    
    # Pattern 2
    match2 = re.search(r'2024-2025 USF (?:Undergraduate|Graduate) Catalog\s+(\d+)', page_content)
    if match2:
        found_printed_page = int(match2.group(1))
        print(f"   Found Printed Page (Pattern 2): {found_printed_page}")

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
    print(f"   {program_text[:1000]}...") # Print first 1000 chars

    # 5. Call LLM
    print("\n5. Calling LLM...")
    try:
        # We need to manually construct the prompt to see it, or just call the function
        # Let's call the function to see the result
        details = llm_parser.parse_program_details(
            program_text, 
            program_name, 
            "Degree", # Placeholder credential
            "ug" if "Undergraduate" in pdf_path else "gr", 
            academic_year, 
            model_choice
        )
        print("\n6. LLM Result:")
        print(details)
    except Exception as e:
        print(f"   Error calling LLM: {e}")

if __name__ == "__main__":
    # HARDCODED TEST VALUES - USER CAN EDIT THESE
    # Replace with a real path from the user's workspace
    pdf_path = "/Users/andyburnett/Library/Mobile Documents/com~apple~CloudDocs/Desktop/X03.27.25/OVS/Special Projects/catalog/catalog_v6/z_extra/2425/cat_full/cat_ug_2425.pdf" 
    
    # Pick a program that failed (e.g., one that returned "Unknown")
    # Example: "Accounting" on page 141 (adjust as needed)
    program_name = "Accounting" 
    page_num = 141 
    
    debug_single_program(pdf_path, program_name, page_num)
