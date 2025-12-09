import os
from dotenv import load_dotenv
import google.generativeai as genai
from utils import llm_parser
import pandas as pd

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def verify_catalog_report():
    print("Starting verification...")
    
    # Use existing ToC PDFs as proxies for full catalogs
    ug_file_path = "ug_toc_2526.pdf"
    gr_file_path = "gr_toc_2526.pdf"
    
    if not os.path.exists(ug_file_path) or not os.path.exists(gr_file_path):
        print("Error: Test files not found.")
        return

    print(f"Processing {ug_file_path}...")
    with open(ug_file_path, "rb") as f:
        ug_text = llm_parser.extract_text_from_pdf(f)
    
    print(f"Processing {gr_file_path}...")
    with open(gr_file_path, "rb") as f:
        gr_text = llm_parser.extract_text_from_pdf(f)

    print("Parsing with Gemini (this might take a moment)...")
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
    print(df.head(10).to_markdown(index=False))
    
    # Check for specific expected values
    print("\nChecking logic...")
    
    # Check Educational Objective
    bachelors = df[df['Educational Objective'] == 'Bachelor']
    masters = df[df['Educational Objective'] == 'Masters']
    doctorates = df[df['Educational Objective'] == 'Doctorate']
    
    print(f"Bachelors count: {len(bachelors)}")
    print(f"Masters count: {len(masters)}")
    print(f"Doctorates count: {len(doctorates)}")
    
    # Check Concentrations
    with_conc = df[df['Concentrations'] == 'Yes']
    print(f"Programs with Concentrations: {len(with_conc)}")
    if len(with_conc) > 0:
        print("Sample Concentration:")
        print(with_conc.iloc[0]['Program Name'])

    print("\nVerification complete.")

if __name__ == "__main__":
    verify_catalog_report()
