import os
from dotenv import load_dotenv
from utils import llm_parser
import re

# Load environment variables
load_dotenv()

def dump_program_text():
    # Programs to dump
    programs = [
        {"name": "Computer Science Minor", "page": 156, "cred": "Minor", "type": "ug"},
        {"name": "Computer Engineering B.S.C.P.", "page": 164, "cred": "B.S.C.P.", "type": "ug"},
        {"name": "Computer Engineering, M.S.C.P.", "page": 161, "cred": "M.S.C.P.", "type": "gr"}
    ]
    
    ug_pdf = "/Users/andyburnett/Library/Mobile Documents/com~apple~CloudDocs/Desktop/X03.27.25/OVS/Special Projects/catalog/catalog_v6/z_extra/2526/min/ug_cat_min_2526.pdf"
    gr_pdf = "/Users/andyburnett/Library/Mobile Documents/com~apple~CloudDocs/Desktop/X03.27.25/OVS/Special Projects/catalog/catalog_v6/z_extra/2526/min/gr_cat_min_2526.pdf"
    output_file = "debug_text_dump.txt"
    
    print(f"--- Dumping Text ---")

    # Pre-load PDFs
    try:
        ug_pages = llm_parser.extract_all_pages(ug_pdf)
        gr_pages = llm_parser.extract_all_pages(gr_pdf)
        print(f"Extracted UG: {len(ug_pages)} pages, GR: {len(gr_pages)} pages.")
    except Exception as e:
        print(f"Error extracting PDF: {e}")
        return

    with open(output_file, "w") as f:
        f.write(f"DEBUG TEXT DUMP\n")
        f.write("="*80 + "\n\n")

        for prog in programs:
            page_num = prog['page']
            program_name = prog['name']
            cat_type = prog['type']
            
            pages_text = ug_pages if cat_type == 'ug' else gr_pages
            pdf_name = "UG Catalog" if cat_type == 'ug' else "GR Catalog"
            
            f.write(f"PROGRAM: {program_name} ({pdf_name}, Target Page: {page_num})\n")
            f.write("-" * 40 + "\n")
            
            # Offset Logic
            naive_idx = max(0, page_num - 1)
            current_idx = naive_idx
            
            if naive_idx < len(pages_text):
                page_content = pages_text[naive_idx]
                
                # Try to find printed page number
                found_printed_page = None
                match = re.search(r'(\d+)\s*\|\s*Page', page_content)
                if match:
                    found_printed_page = int(match.group(1))
                
                if found_printed_page is not None:
                    shift = page_num - found_printed_page
                    current_idx = naive_idx + shift
                    f.write(f"Offset Calculation: Naive={naive_idx}, Found={found_printed_page}, Shift={shift}, NewIndex={current_idx}\n")
                else:
                    f.write(f"Offset Calculation: No printed page number found. Using Naive={naive_idx}\n")
            else:
                f.write(f"Offset Calculation: Page {page_num} is out of bounds (Total {len(pages_text)})\n")
                current_idx = 0 # Fallback

            # Extract Text (4 pages)
            start_idx = max(0, min(current_idx, len(pages_text) - 1))
            end_idx = min(len(pages_text), start_idx + 4)
            program_text = "".join(pages_text[start_idx:end_idx])
            
            f.write(f"EXTRACTED TEXT (Pages {start_idx+1}-{end_idx}):\n")
            f.write("```\n")
            f.write(program_text)
            f.write("\n```\n\n")
            
            # Construct Prompt (using the function from llm_parser logic)
            # We recreate the prompt string here to show the user
            prompt = f"""
    You are analyzing the catalog entry for the academic program: "{program_name}" with credential "{prog['cred']}".
    
    Based on the provided text, determine the following:
    ... (Prompt Template) ...
    4. **Total_Credit_Hours**: What is the total number of credit hours required for this degree?
       ...
       **How to interpret the text (2024-2025 Format):**
       - Look for the section **"REQUIRED COURSES: (X CREDIT HOURS)"**.
       - Look for **"Total Minimum Hours"** or similar phrases.
       ...
    
    Text to analyze:
    {program_text[:500]}... (truncated for view)
            """
            f.write("GENERATED PROMPT (Snippet):\n")
            f.write(prompt)
            f.write("\n" + "="*80 + "\n\n")

    print(f"Dump saved to {output_file}")

if __name__ == "__main__":
    dump_program_text()
