import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import google.generativeai as genai
import io
from utils import llm_parser

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize Session State
if 'catalog_report_data' not in st.session_state:
    st.session_state.catalog_report_data = None

# Initialize Session State
if 'catalog_report_data' not in st.session_state:
    st.session_state.catalog_report_data = None

st.header("Catalog Report")

st.markdown("""
Uses the ToC generated in the last step to find key program data. This is is a near "Copy and Paste" result.
""")

# Sidebar Model Selection
model_choice = st.sidebar.radio(
    "Select Model",
    options=["Gemini 1.5 Flash", "Gemini 2.5 Pro", "Gemini 3 Pro", "ChatGPT 5 mini"],
    index=0
)

# ... (lines 36-230 omitted for brevity in instruction, but I will target specific blocks if possible or use multi_replace)


# ... (lines 36-230 omitted for brevity in instruction, but I will target specific blocks if possible or use multi_replace)


# Academic Year Selector
academic_year = st.selectbox(
    "Academic Year",
    options=["2024-2025", "2025-2026"],
    index=1  # Default to 2025-2026
)

# Default Page Numbers based on Academic Year
# Default Page Numbers based on Academic Year
if academic_year == "2024-2025":
    ug_default_min = 141
    ug_default_max = 1477
    gr_default_min = 132
    gr_default_max = 981
else:
    # Defaults for 2025-2026
    ug_default_min = 155
    ug_default_max = 1474
    gr_default_min = 152
    gr_default_max = 1038

# File Uploaders
st.subheader("1. Upload ToC File (Required)")
toc_file = st.file_uploader("Upload ToC Excel File (from ToC Generator)", type=["xlsx"], key="toc_uploader")

col1, col2 = st.columns(2)

with col1:
    st.subheader("2. Undergraduate Catalog")
    ug_file = st.file_uploader("Undergraduate Catalog (Full PDF)", type="pdf", key="ug_uploader_full")
    ug_min_page = st.number_input("Min Page", min_value=0, value=ug_default_min, key="ug_min_full")
    ug_max_page = st.number_input("Max Page", min_value=0, value=ug_default_max, key="ug_max_full")

with col2:
    st.subheader("3. Graduate Catalog")
    gr_file = st.file_uploader("Graduate Catalog (Full PDF)", type="pdf", key="gr_uploader_full")
    gr_min_page = st.number_input("Min Page", min_value=0, value=gr_default_min, key="gr_min_full")
    gr_max_page = st.number_input("Max Page", min_value=0, value=gr_default_max, key="gr_max_full")

import concurrent.futures

# ... (imports)



def get_page_offset(page_text, expected_page_num):
    """
    Attempts to find the printed page number in the text and calculates the offset
    relative to the PDF page index.
    Returns the calculated offset (PDF Index - Printed Page) or None if not found.
    """
    import re
    # Pattern 1: "131 | Page" or "Page 131" (2025-2026 Format)
    match = re.search(r'(\d+)\s*\|\s*Page', page_text)
    if match:
        return int(match.group(1))
    
    # Pattern 2: "2024-2025 USF ... Catalog \n 137" (2024-2025 Format)
    # Look for the catalog header followed by a number (allowing for newlines or spaces).
    match2 = re.search(r'2024-2025 USF (?:Undergraduate|Graduate) Catalog\s+(\d+)', page_text)
    if match2:
        return int(match2.group(1))
        
    return None

# Helper function for parallel processing
def process_single_program(row, ug_pages, gr_pages, ug_min, ug_max, gr_min, gr_max, academic_year, model_choice):
    try:
        program_name = row['Program']
        page_num = int(row['Page Number'])
        catalog_name = row['Catalog Name']
        
        # Determine which PDF pages to use and apply Page Range Filter
        pages_text = []
        cat_type = 'ug'
        should_process = False

        if "Undergraduate" in catalog_name:
            pages_text = ug_pages
            cat_type = 'ug'
            if ug_min <= page_num <= ug_max:
                should_process = True
        elif "Graduate" in catalog_name:
            pages_text = gr_pages
            cat_type = 'gr'
            if gr_min <= page_num <= gr_max:
                should_process = True
        
        if pages_text and should_process:
            # Smart Page Navigation
            # 1. Try the naive index (Page Num - 1)
            # 2. Check if the printed page number matches
            # 3. If not, calculate offset and adjust
            
            naive_idx = max(0, page_num - 1)
            current_idx = naive_idx
            
            # Check bounds
            if current_idx < len(pages_text):
                page_content = pages_text[current_idx]
                found_printed_page = get_page_offset(page_content, page_num)
                
                if found_printed_page is not None:
                    # Calculate offset: How many pages do we need to shift?
                    # If we are at PDF Index 152 (Naive) and found Printed Page 131.
                    # We want Printed Page 153.
                    # Difference in printed pages = Target (153) - Found (131) = 22.
                    # So we need to shift forward by 22 pages.
                    shift = page_num - found_printed_page
                    current_idx = naive_idx + shift
                    # print(f"Adjusting page for {program_name}: Naive {naive_idx} (Printed {found_printed_page}) -> Target {page_num} (New Index {current_idx})")
            
            # Ensure new index is valid
            start_idx = max(0, min(current_idx, len(pages_text) - 1))
            
            max_pages = 4  # Maximum pages to search
            
            details = None
            for num_pages in range(1, max_pages + 1):
                end_idx = min(len(pages_text), start_idx + num_pages)
                program_text = "".join(pages_text[start_idx:end_idx])
                
                details = llm_parser.parse_program_details(program_text, program_name, "Derived from Program Name", cat_type, academic_year, model_choice)
                
                # If we found credit hours, stop searching
                credit_hours = details.get("Total_Credit_Hours", "Unknown")
                if credit_hours != "Unknown":
                    break
            
        if details:
            return {
                "Program Name": program_name,
                "Accredited": details.get("Accredited", "Yes"),
                "Educational Objective": details.get("Educational_Objective", "Unknown"),
                "Concentrations": details.get("Concentrations", "No"),
                "School Reported Approval Status": "",
                "Effective Date": "",
                "Total Credit Hours": details.get("Total_Credit_Hours", "Unknown"),
                "Program Length Measure": "Semester",
                "Full-Time Enrollment": "12" if "Undergraduate" in str(catalog_name) else "9",
                "Classroom Theory Clock Hours": "",
                "Lab or Shop Clock Hours": "",
                "Total Clock Hours in Program": "",
                "Catalog Name": catalog_name,
                "Page Number": page_num,
                "License Prep": details.get("License_Prep", "No"),
                "Modality": details.get("Modality", "Resident"),
                "Contracted Program": "No",
                "Enrollment Limit": "",
                "Comments": "",
                "FOR SAA INTERNAL USE ONLY": ""
            }
        else:
            print(f"Skipping {program_name}: pages_text empty={not bool(pages_text)}, should_process={should_process} (Page {page_num}, Range {ug_min}-{ug_max} or {gr_min}-{gr_max})")

    except Exception as e:
        print(f"Error processing {row.get('Program', 'Unknown')}: {e}")
        import traceback
        traceback.print_exc()
        return None
    return None

if st.button("Generate Report"):
    if not toc_file:
        st.error("Please upload the ToC Excel File.")
    elif not ug_file and not gr_file:
        st.error("Please upload at least one Catalog PDF (Undergraduate or Graduate).")
    else:
        with st.spinner("Processing... Pre-loading PDFs and starting analysis..."):
            try:
                # Load ToC
                df_toc = pd.read_excel(toc_file)
                
                # Validate ToC Columns
                required_cols = ['Program', 'Page Number', 'Catalog Name']
                if not all(col in df_toc.columns for col in required_cols):
                    st.error(f"ToC file is missing required columns: {required_cols}")
                    st.stop()

                # Pre-load PDFs
                ug_pages = []
                gr_pages = []
                
                if ug_file:
                    ug_pages = llm_parser.extract_all_pages(ug_file)
                if gr_file:
                    gr_pages = llm_parser.extract_all_pages(gr_file)

                processed_data = []
                
                # Progress Bar
                progress_bar = st.progress(0)
                total_programs = len(df_toc)
                
                # Parallel Processing
                # Using ThreadPoolExecutor because the bottleneck is I/O (Network calls to Gemini API)
                with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                    futures = []
                    for index, row in df_toc.iterrows():
                        futures.append(executor.submit(process_single_program, row, ug_pages, gr_pages, ug_min_page, ug_max_page, gr_min_page, gr_max_page, academic_year, model_choice))
                    
                    for i, future in enumerate(concurrent.futures.as_completed(futures)):
                        result = future.result()
                        if result:
                            processed_data.append(result)
                        progress_bar.progress((i + 1) / total_programs)

                # Create DataFrame
                df_final = pd.DataFrame(processed_data)
                
                if not df_final.empty:
                    # Sort Data: Undergraduate first, then Graduate. Within each, sort by Page Number.
                    # Create a temporary column for sorting order
                    df_final['SortOrder'] = df_final['Catalog Name'].apply(lambda x: 0 if "Undergraduate" in str(x) else 1)
                    
                    # Sort by SortOrder and Page Number
                    df_final = df_final.sort_values(by=['SortOrder', 'Page Number'], ascending=[True, True])
                    
                    # Explicitly order columns (excluding SortOrder)
                    cols = ["Program Name", "Accredited", "Educational Objective", "Concentrations", "School Reported Approval Status", "Effective Date", "Total Credit Hours", "Program Length Measure", "Full-Time Enrollment", "Classroom Theory Clock Hours", "Lab or Shop Clock Hours", "Total Clock Hours in Program", "Catalog Name", "Page Number", "License Prep", "Modality", "Contracted Program", "Enrollment Limit", "Comments", "FOR SAA INTERNAL USE ONLY"]
                    df_final = df_final[cols]
                    
                    # Save to Session State
                    st.session_state.catalog_report_data = df_final
                    st.success(f"Processed {len(df_final)} programs!")
                else:
                    st.warning("No programs found matching the criteria.")

            except Exception as e:
                st.error(f"An error occurred: {e}")

# Display Results from Session State
if st.session_state.catalog_report_data is not None:
    st.dataframe(st.session_state.catalog_report_data)

    # Download Button
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        st.session_state.catalog_report_data.to_excel(writer, index=False, sheet_name='CatalogReport')
    
    # Format filename
    y1 = academic_year.split('-')[0][-2:]
    y2 = academic_year.split('-')[1][-2:]
    filename = f"catalog_report_{y1}{y2}.xlsx"

    st.download_button(
        label="Download Excel File",
        data=output.getvalue(),
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # ---------------------------------------------------------------------
    # Truth Comparison Section
    # ---------------------------------------------------------------------
    st.divider()
    st.header("Truth Comparison")
    st.markdown("Compare the Export Catalog Report to a validated file.")

    # Initialize Session State for Truth
    if 'cat_report_truth_results' not in st.session_state:
        st.session_state.cat_report_truth_results = None

    t_col1, t_col2 = st.columns(2)

    with t_col1:
        truth_file = st.file_uploader("Upload Truth File (Excel)", type=["xlsx"], key="truth_uploader_report")

    with t_col2:
        test_file = st.file_uploader("Upload Test File (Excel)", type=["xlsx"], key="test_uploader_report")

    if st.button("Compare Files", key="compare_btn_report"):
        if not truth_file or not test_file:
            st.error("Please upload both files.")
        else:
            try:
                df_truth = pd.read_excel(truth_file)
                df_test = pd.read_excel(test_file)

                # Normalize column names
                required_cols = ['Program Name', 'Accredited', 'Educational Objective', 'Concentrations', 'School Reported Approval Status', 'Effective Date', 'Total Credit Hours', 'Program Length Measure', 'Full-Time Enrollment', 'Classroom Theory Clock Hours', 'Lab or Shop Clock Hours', 'Total Clock Hours in Program', 'Catalog Name', 'Page Number', 'License Prep', 'Modality', 'Contracted Program', 'Enrollment Limit', 'Comments', 'FOR SAA INTERNAL USE ONLY']
                
                # Check if columns exist
                if not all(col in df_truth.columns for col in required_cols):
                    st.error(f"Truth file is missing one of the required columns: {required_cols}")
                elif not all(col in df_test.columns for col in required_cols):
                    st.error(f"Test file is missing one of the required columns: {required_cols}")
                else:
                    # Select only relevant columns for comparison
                    df_truth = df_truth[required_cols]
                    df_test = df_test[required_cols]

                    
                    # Normalize ALL required columns to string to avoid type mismatches during merge
                    # (e.g. invalid 'Contracted Program' as float vs string)
                    for col in required_cols:
                        df_truth[col] = df_truth[col].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)
                        df_test[col] = df_test[col].astype(str).str.strip().str.replace(r'\.0$', '', regex=True)


                    # Matches
                    matches = pd.merge(df_truth, df_test, on=required_cols, how='inner')
                    num_matches = len(matches)

                    # In Truth but NOT in Test
                    merged_truth = pd.merge(df_truth, df_test, on=required_cols, how='left', indicator=True)
                    in_truth_not_test = merged_truth[merged_truth['_merge'] == 'left_only'].drop(columns=['_merge'])
                    num_truth_not_test = len(in_truth_not_test)

                    # In Test but NOT in Truth
                    merged_test = pd.merge(df_truth, df_test, on=required_cols, how='right', indicator=True)
                    in_test_not_truth = merged_test[merged_test['_merge'] == 'right_only'].drop(columns=['_merge'])
                    num_test_not_truth = len(in_test_not_truth)
                    
                    # Save to Session State
                    st.session_state.cat_report_truth_results = {
                        "num_matches": num_matches,
                        "num_truth_not_test": num_truth_not_test,
                        "num_test_not_truth": num_test_not_truth,
                        "in_truth_not_test": in_truth_not_test,
                        "in_test_not_truth": in_test_not_truth
                    }

            except Exception as e:
                st.error(f"An error occurred during comparison: {e}")

    # Display Truth Results
    if st.session_state.cat_report_truth_results is not None:
        results = st.session_state.cat_report_truth_results
        
        st.subheader("Comparison Results")
        
        m_col1, m_col2, m_col3 = st.columns(3)
        m_col1.metric("Matching Programs", results["num_matches"])
        m_col2.metric("Missing from Test", results["num_truth_not_test"], delta=-results["num_truth_not_test"] if results["num_truth_not_test"] > 0 else 0, delta_color="inverse")
        m_col3.metric("Extra in Test", results["num_test_not_truth"], delta=results["num_test_not_truth"] if results["num_test_not_truth"] > 0 else 0, delta_color="off")

        if results["num_truth_not_test"] > 0:
            st.warning(f"Found {results['num_truth_not_test']} programs in Truth File that are MISSING from Test File:")
            st.dataframe(results["in_truth_not_test"])
        else:
            st.success("No programs missing from Test File!")

        if results["num_test_not_truth"] > 0:
            st.info(f"Found {results['num_test_not_truth']} programs in Test File that are NOT in Truth File (New or Incorrect):")
            st.dataframe(results["in_test_not_truth"])
        else:
            st.success("No extra programs in Test File!")
            
        if st.button("Reset Comparison", key="reset_truth_btn"):
            st.session_state.cat_report_truth_results = None
            st.rerun()

    st.divider()
    
    # Reset Button
    if st.button("Reset"):
        st.session_state.catalog_report_data = None
        st.rerun()

