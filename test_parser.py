import os
from dotenv import load_dotenv
from utils import llm_parser
import pandas as pd

import google.generativeai as genai

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def test_parser():
    print("Starting parser test...")
    
    # Check for files
    ug_file = "ug_toc_2526.pdf"
    gr_file = "gr_toc_2526.pdf"
    
    if not os.path.exists(ug_file) or not os.path.exists(gr_file):
        print("Error: Sample files not found.")
        return

    # 1. Extract Text
    print("Extracting text from UG...")
    ug_text = llm_parser.extract_text_from_pdf(ug_file)
    print(f"UG Text length: {len(ug_text)}")
    
    print("Extracting text from GR...")
    gr_text = llm_parser.extract_text_from_pdf(gr_file)
    print(f"GR Text length: {len(gr_text)}")

    # 2. Parse with Gemini
    print("Parsing UG with Gemini...")
    ug_programs = llm_parser.parse_catalog_toc(ug_text, "USF Undergraduate 2025-2026")
    print(f"Found {len(ug_programs)} UG programs.")
    if ug_programs:
        print(f"Sample UG: {ug_programs[0].get('original_text', 'N/A')}")
        
        # Check for missing programs
        missing_keywords = ["World Languages and Cultures", "Interdisciplinary Classical Civilizations", "Exploratory Curriculum"]
        found_missing = [p for p in ug_programs if any(k in p.get('original_text', '') for k in missing_keywords)]
        print(f"Found {len(found_missing)} 'World Languages' or 'Exploratory' programs.")
        for p in found_missing:
            print(f"  - {p.get('original_text', 'N/A')} (Cred: {p.get('credential', 'N/A')})")

    print("Parsing GR with Gemini...")
    gr_programs = llm_parser.parse_catalog_toc(gr_text, "USF Graduate 2025-2026")
    print(f"Found {len(gr_programs)} GR programs.")
    if gr_programs:
        print(f"Sample GR: {gr_programs[0].get('original_text', 'N/A')}")

    # 3. Filter (Simulate user input)
    ug_filtered = llm_parser.filter_programs(ug_programs, 0, 1000)
    gr_filtered = llm_parser.filter_programs(gr_programs, 0, 1000)

    # Validate Credentials
    print("Validating credentials...")
    ug_final = llm_parser.validate_catalog_type(ug_filtered, 'ug')
    gr_final = llm_parser.validate_catalog_type(gr_filtered, 'gr')
    
    print(f"UG after validation: {len(ug_final)} (was {len(ug_filtered)})")
    print(f"GR after validation: {len(gr_final)} (was {len(gr_filtered)})")

    # 4. Aggregate
    all_programs = ug_final + gr_final
    print(f"Total aggregated programs: {len(all_programs)}")
    
    # 5. Create DataFrame
    df = pd.DataFrame(all_programs)
    print("DataFrame Head:")
    print(df.head())

if __name__ == "__main__":
    test_parser()
