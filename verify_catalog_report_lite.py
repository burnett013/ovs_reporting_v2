import os
from dotenv import load_dotenv
import google.generativeai as genai
from utils import llm_parser
import pandas as pd

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def verify_catalog_report_lite():
    print("Starting lite verification...")
    
    # Mock text instead of full file
    ug_text = """
    University of South Florida
    Undergraduate Catalog 2025-2026
    
    College of Arts and Sciences
    
    Department of Criminology
    Criminology B.A., with Cybercrime Concentration
    ...
    Department of English
    English B.A.
    ...
    Department of History
    History Minor
    ...
    """
    
    gr_text = """
    University of South Florida
    Graduate Catalog 2025-2026
    
    College of Engineering
    Artificial Intelligence, M.S.A.I.
    ...
    Computer Engineering, Ph.D.
    ...
    College of Business
    Business Analytics, Graduate Certificate
    ...
    """

    print("Parsing with Gemini (Lite Mode)...")
    ug_programs = llm_parser.parse_full_catalog_programs(ug_text, "USF Undergraduate 2025-2026")
    gr_programs = llm_parser.parse_full_catalog_programs(gr_text, "USF Graduate 2025-2026")
    
    all_programs = ug_programs + gr_programs
    print(f"Found {len(all_programs)} programs.")
    
    if not all_programs:
        print("No programs found. Verification failed.")
        return

    processed_data = []
    for p in all_programs:
        cat_type = 'ug' if 'Undergraduate' in p['catalog_name'] else 'gr'
        
        accredited = "Yes"
        edu_objective = llm_parser.get_educational_objective(p['credential'], cat_type)
        concentrations = llm_parser.has_concentration(p['program_name'])
        
        processed_data.append({
            "Program Name": p['program_name'],
            "Credential": p['credential'],
            "Accredited": accredited,
            "Educational Objective": edu_objective,
            "Concentrations": concentrations,
            "Catalog Name": p['catalog_name']
        })

    df = pd.DataFrame(processed_data)
    print("\nSample Output:")
    print(df)
    
    print("\nVerification complete.")

if __name__ == "__main__":
    verify_catalog_report_lite()
