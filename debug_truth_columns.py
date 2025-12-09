import pandas as pd
import os

file_path = "z_extra/2425/full/truth_cat_full_2425.xlsx"
required_columns = [
    'Program Name', 'Accredited', 'Educational Objective', 'Concentrations', 
    'School Reported Approval Status', 'Effective Date', 'Total Credit Hours', 
    'Program Length Measure', 'Full-Time Enrollment', 'Classroom Theory Clock Hours', 
    'Lab or Shop Clock Hours', 'Total Clock Hours in Program', 'Catalog Name', 
    'Page Number', 'License Prep', 'Modality', 'Contracted Program', 
    'Enrollment Limit', 'Comments', 'FOR SAA INTERNAL USE ONLY'
]

if os.path.exists(file_path):
    try:
        df = pd.read_excel(file_path)
        existing_columns = df.columns.tolist()
        missing_columns = [col for col in required_columns if col not in existing_columns]
        
        print("Existing Columns:")
        for col in existing_columns:
            print(f" - {col}")
            
        print("\nMissing Columns:")
        for col in missing_columns:
            print(f" - {col}")
            
    except Exception as e:
        print(f"Error reading file: {e}")
else:
    print(f"File not found: {file_path}")
