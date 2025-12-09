import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv
import google.generativeai as genai
from pypdf import PdfReader
import io
from utils import llm_parser

# Load environment variables
load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize Session State
if 'toc_data' not in st.session_state:
    st.session_state.toc_data = None

st.header("ToC Generator")

st.markdown("""
Generates a combined Table of Contents (ToC) for both the undergraduate and graduate catalogs. Results in an XLSX file with two columns, Program Name and Page Number. The ToC is used in the next Catalog Report.
""")

# Sidebar Model Selection
model_choice = st.sidebar.radio(
    "Select Model",
    options=["Gemini 1.5 Flash", "Gemini 2.5 Pro", "Gemini 3 Pro", "ChatGPT 5 mini"],
    index=0
)

# Academic Year Selector
academic_year = st.selectbox(
    "Academic Year",
    options=["2024-2025", "2025-2026"],
    index=1  # Default to 2025-2026
)

# Default Page Numbers based on Academic Year
if academic_year == "2024-2025":
    ug_default_min = 141
    ug_default_max = 1477
    gr_default_min = 132
    gr_default_max = 981
else:
    # Defaults for 2025-2026
    ug_default_min = 155
    ug_default_max = 1475
    gr_default_min = 150
    gr_default_max = 1038

col1, col2 = st.columns(2)

with col1:
    st.subheader("Undergraduate")
    ug_file = st.file_uploader("UG ToC", type="pdf", key="ug_uploader")
    ug_min_page = st.number_input("Min Page", min_value=0, value=ug_default_min, key="ug_min")
    ug_max_page = st.number_input("Max Page", min_value=0, value=ug_default_max, key="ug_max")

with col2:
    st.subheader("Graduate")
    gr_file = st.file_uploader("GR ToC", type="pdf", key="gr_uploader")
    gr_min_page = st.number_input("Min Page", min_value=0, value=gr_default_min, key="gr_min")
    gr_max_page = st.number_input("Max Page", min_value=0, value=gr_default_max, key="gr_max")

# Generate Button
if st.button("Generate Combined ToC"):
    if not ug_file or not gr_file:
        st.error("Please upload both Undergraduate and Graduate ToC files.")
    else:
        with st.spinner("Working..."):
            try:
                # 1. Extract Text
                ug_text = llm_parser.extract_text_from_pdf(ug_file)
                gr_text = llm_parser.extract_text_from_pdf(gr_file)

                # 2. Parse with Gemini
                ug_catalog_name = f"USF Undergraduate {academic_year}"
                gr_catalog_name = f"USF Graduate {academic_year}"

                ug_programs = llm_parser.parse_catalog_toc(ug_text, ug_catalog_name, academic_year, model_choice)
                gr_programs = llm_parser.parse_catalog_toc(gr_text, gr_catalog_name, academic_year, model_choice)

                st.write("Raw UG programs from LLM:", len(ug_programs))
                st.write("Raw GR programs from LLM:", len(gr_programs))

                # 3. Filter
                ug_filtered_range = llm_parser.filter_programs(ug_programs, ug_min_page, ug_max_page)
                gr_filtered_range = llm_parser.filter_programs(gr_programs, gr_min_page, gr_max_page)

                st.write("UG programs after filtering:", len(ug_filtered_range))
                st.write("GR programs after filtering:", len(gr_filtered_range))

                # Validate Credentials
                ug_final = llm_parser.validate_catalog_type(ug_filtered_range, 'ug')
                gr_final = llm_parser.validate_catalog_type(gr_filtered_range, 'gr')

                st.write("UG programs after validation:", len(ug_final))
                st.write("GR programs after validation:", len(gr_final))

                # 4. Aggregate
                all_programs = ug_final + gr_final
                
                if not all_programs:
                    st.warning("No programs found matching the criteria.")
                    st.session_state.toc_data = None # Clear if failed
                else:
                    # 5. Create DataFrame
                    df = pd.DataFrame(all_programs)
                    
                    # Use the 'original_text' field which preserves the exact formatting from the catalog
                    # (e.g. "Computer Engineering B.S.C.P." vs "Artificial Intelligence, M.S.A.I.")
                    df['Program'] = df['original_text']
                    
                    # Select and rename columns to match user request: Col1 (Program), Col2 (Page), Col3 (Catalog)
                    df_final = df[['Program', 'page_number', 'catalog_name']]
                    df_final.columns = ['Program', 'Page Number', 'Catalog Name']
                    
                    # Save to Session State
                    st.session_state.toc_data = df_final

            except Exception as e:
                st.error(f"An error occurred: {e}")

# Display Results from Session State
if st.session_state.toc_data is not None:
    st.success(f"Found {len(st.session_state.toc_data)} programs!")
    st.dataframe(st.session_state.toc_data)

    # 6. Download Button
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        st.session_state.toc_data.to_excel(writer, index=False, sheet_name='ToC')
    
    # Format filename: toc_2526.xlsx
    y1 = academic_year.split('-')[0][-2:]
    y2 = academic_year.split('-')[1][-2:]
    filename = f"toc_{y1}{y2}.xlsx"

    st.download_button(
        label="Download Excel File",
        data=output.getvalue(),
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # ----------------------------------------
    # Add Missing Programs Section (Two-Step Process)
    # ----------------------------------------
    st.divider()
    st.header("Add Missing Programs")
    st.markdown("Use this section to add programs that were missed during the initial generation.")

    # Initialize Session State for Missing Programs List
    if 'missing_programs_list' not in st.session_state:
        st.session_state.missing_programs_list = []

    # Step 1: Create Missing Programs List
    st.subheader("Step 1a: Add Missing Programs - Manual")
    st.markdown("Add programs one by one to create a supplemental list. Full add, edit, and delete functionality is supported.")

    with st.form("create_missing_list_form", clear_on_submit=True):
        col_mp1, col_mp2, col_mp3 = st.columns(3)
        
        with col_mp1:
            new_program_name = st.text_input("Program Name")
        
        with col_mp2:
            new_page_number = st.number_input("Page Number", min_value=1, step=1)
        
        with col_mp3:
            # Dynamic options based on selected academic year
            cat_options = [f"USF Undergraduate {academic_year}", f"USF Graduate {academic_year}"]
            new_catalog_name = st.selectbox("Catalog Name", options=cat_options)

        add_btn = st.form_submit_button("Add to List")
        
        if add_btn:
            if not new_program_name:
                st.error("Please enter a Program Name.")
            else:
                new_entry = {
                    "Program": new_program_name,
                    "Page Number": new_page_number,
                    "Catalog Name": new_catalog_name
                }
                st.session_state.missing_programs_list.append(new_entry)
                st.success(f"Added '{new_program_name}' to the list.")

    # Step 1b: Add Missing Programs - File Upload
    st.subheader("Step 1b: Add Missing Programs - File Upload")
    st.markdown("Upload an Excel file containing missing programs (e.g., from the Comparison Results).")
    
    bulk_upload_file = st.file_uploader("Upload Missing Programs File (Excel)", type=["xlsx"], key="bulk_missing_uploader")
    
    # Process Button Logic (Hidden logic, UI button will be below)
    process_clicked = False
    
    # Display Current List with CRUD capabilities (Moved here)
    if st.session_state.missing_programs_list:
        st.divider()
        st.write("Current Missing Programs List (Edit or Delete entries here):")
        df_missing = pd.DataFrame(st.session_state.missing_programs_list)
        
        # Configure columns for editing
        column_config = {
            "Program": st.column_config.TextColumn("Program Name", required=True),
            "Page Number": st.column_config.NumberColumn("Page Number", min_value=1, step=1, required=True),
            "Catalog Name": st.column_config.SelectboxColumn(
                "Catalog Name",
                options=[f"USF Undergraduate {academic_year}", f"USF Graduate {academic_year}"],
                required=True
            )
        }
        
        edited_df = st.data_editor(
            df_missing,
            column_config=column_config,
            num_rows="dynamic", # Allow adding/deleting rows
            key="missing_programs_editor",
            use_container_width=True
        )
        
        # Sync changes back to session state
        current_data = edited_df.to_dict('records')
        if current_data != st.session_state.missing_programs_list:
            st.session_state.missing_programs_list = current_data
            
    # Action Buttons Row
    st.write("") # Spacer
    b_col1, b_col2, b_col3 = st.columns(3)
    
    with b_col1:
        if bulk_upload_file:
            if st.button("Process & Add to List", use_container_width=True):
                process_clicked = True
        else:
            st.button("Process & Add to List", disabled=True, use_container_width=True, help="Upload a file first.")

    with b_col2:
        if st.session_state.missing_programs_list:
            output_missing = io.BytesIO()
            with pd.ExcelWriter(output_missing, engine='openpyxl') as writer:
                pd.DataFrame(st.session_state.missing_programs_list).to_excel(writer, index=False, sheet_name='ToC')
            
            st.download_button(
                label="Download Supplemental List",
                data=output_missing.getvalue(),
                file_name=f"toc_supplemental_{y1}{y2}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
             st.button("Download Supplemental List", disabled=True, use_container_width=True)

    with b_col3:
        if st.session_state.missing_programs_list:
            if st.button("Clear List", use_container_width=True):
                st.session_state.missing_programs_list = []
                st.rerun()
        else:
             st.button("Clear List", disabled=True, use_container_width=True)

    # Process Logic Execution
    if process_clicked and bulk_upload_file:
        should_rerun = False
        try:
            df_bulk = pd.read_excel(bulk_upload_file)
            
            # Validate columns
            required_cols = ['Program', 'Page Number', 'Catalog Name']
            if not all(col in df_bulk.columns for col in required_cols):
                st.error(f"Uploaded file must contain columns: {required_cols}")
            else:
                # Convert to list of dicts and append
                new_entries = df_bulk[required_cols].to_dict('records')
                
                # Append to session state
                if 'missing_programs_list' not in st.session_state:
                    st.session_state.missing_programs_list = []
                
                st.session_state.missing_programs_list.extend(new_entries)
                st.success(f"Successfully added {len(new_entries)} programs to the list!")
                should_rerun = True
                
        except Exception as e:
            st.error(f"Error processing file: {e}")
        
        if should_rerun:
            st.rerun()

    # Step 2: Merge Lists
    st.divider()
    st.subheader("Step 2: Merge Lists")
    st.markdown("Upload the original ToC and the supplemental list (created above) to combine them.")

    col_merge1, col_merge2 = st.columns(2)
    
    with col_merge1:
        original_toc_file = st.file_uploader("Original Programs (Excel)", type=["xlsx"], key="original_toc_uploader")
    
    with col_merge2:
        supplemental_toc_file = st.file_uploader("Supplemental Programs (Excel)", type=["xlsx"], key="supplemental_toc_uploader")

    if st.button("Add Programs"):
        if not original_toc_file or not supplemental_toc_file:
            st.error("Please upload both the Original and Supplemental files.")
        else:
            try:
                df_original = pd.read_excel(original_toc_file)
                df_supplemental = pd.read_excel(supplemental_toc_file)
                
                # Concatenate
                df_merged = pd.concat([df_original, df_supplemental], ignore_index=True)
                
                # Sort
                # Helper to sort
                if 'Catalog Name' in df_merged.columns:
                    df_merged['SortOrder'] = df_merged['Catalog Name'].apply(lambda x: 0 if "Undergraduate" in str(x) else 1)
                    df_merged = df_merged.sort_values(by=['SortOrder', 'Page Number'], ascending=[True, True])
                    df_merged = df_merged.drop(columns=['SortOrder'])
                else:
                    # Fallback sort if Catalog Name missing (shouldn't happen with correct files)
                    df_merged = df_merged.sort_values(by=['Page Number'], ascending=[True])
                
                st.success(f"Merged successfully! Total programs: {len(df_merged)}")
                
                # Download Button for Merged File
                output_merged = io.BytesIO()
                with pd.ExcelWriter(output_merged, engine='openpyxl') as writer:
                    df_merged.to_excel(writer, index=False, sheet_name='ToC')
                
                st.download_button(
                    label="Download Merged ToC",
                    data=output_merged.getvalue(),
                    file_name=f"toc_{y1}{y2}_merged.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
            except Exception as e:
                st.error(f"Error merging files: {e}")

    # ---------------------------------------------------------------------
    # Truth Comparison Section
    # ---------------------------------------------------------------------
    st.divider()
    st.header("Truth Comparison")
    st.markdown("Compare the Generated ToC to a validated file.")

    # Initialize Session State for Truth
    if 'toc_truth_results' not in st.session_state:
        st.session_state.toc_truth_results = None

    t_col1, t_col2 = st.columns(2)

    with t_col1:
        truth_file = st.file_uploader("Upload Truth File (Excel)", type=["xlsx"], key="truth_uploader_toc")

    with t_col2:
        test_file = st.file_uploader("Upload Test File (Excel)", type=["xlsx"], key="test_uploader_toc")

    if st.button("Compare Files", key="compare_btn_toc"):
        if not truth_file or not test_file:
            st.error("Please upload both files.")
        else:
            try:
                df_truth = pd.read_excel(truth_file)
                df_test = pd.read_excel(test_file)

                # Normalize column names: Allow "Program Name" as alias for "Program"
                if 'Program Name' in df_truth.columns:
                    df_truth = df_truth.rename(columns={'Program Name': 'Program'})
                if 'Program Name' in df_test.columns:
                    df_test = df_test.rename(columns={'Program Name': 'Program'})

                required_cols = ['Program', 'Page Number', 'Catalog Name']
                
                # Check if columns exist
                if not all(col in df_truth.columns for col in required_cols):
                    st.error(f"Truth file is missing one of the required columns: {required_cols}")
                elif not all(col in df_test.columns for col in required_cols):
                    st.error(f"Test file is missing one of the required columns: {required_cols}")
                else:
                    # Select only relevant columns for comparison
                    df_truth = df_truth[required_cols]
                    df_test = df_test[required_cols]

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
                    st.session_state.toc_truth_results = {
                        "num_matches": num_matches,
                        "num_truth_not_test": num_truth_not_test,
                        "num_test_not_truth": num_test_not_truth,
                        "in_truth_not_test": in_truth_not_test,
                        "in_test_not_truth": in_test_not_truth
                    }

            except Exception as e:
                st.error(f"An error occurred during comparison: {e}")

    # Display Results
    if st.session_state.toc_truth_results:
        results = st.session_state.toc_truth_results
        
        st.divider()
        st.subheader("Comparison Results")
        
        col_res1, col_res2, col_res3 = st.columns(3)
        col_res1.metric("Matches", results['num_matches'])
        col_res2.metric("In Truth Only (Missing)", results['num_truth_not_test'])
        col_res3.metric("In Test Only (Extra)", results['num_test_not_truth'])
        
        # Download Buttons for Discrepancies
        st.subheader("Download Discrepancies")
        d_col1, d_col2 = st.columns(2)
        
        with d_col1:
            if results['num_truth_not_test'] > 0:
                df_missing_truth = results['in_truth_not_test']
                output_missing_truth = io.BytesIO()
                with pd.ExcelWriter(output_missing_truth, engine='openpyxl') as writer:
                    df_missing_truth.to_excel(writer, index=False, sheet_name='Missing')
                
                st.download_button(
                    label="Download Missing Programs (In Truth Only)",
                    data=output_missing_truth.getvalue(),
                    file_name="missing_in_test.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Download programs found in Truth file but missing from Test file."
                )
            else:
                st.info("No missing programs found.")

        with d_col2:
            if results['num_test_not_truth'] > 0:
                df_extra_test = results['in_test_not_truth']
                output_extra_test = io.BytesIO()
                with pd.ExcelWriter(output_extra_test, engine='openpyxl') as writer:
                    df_extra_test.to_excel(writer, index=False, sheet_name='Extra')
                
                st.download_button(
                    label="Download Extra Programs (In Test Only)",
                    data=output_extra_test.getvalue(),
                    file_name="extra_in_test.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Download programs found in Test file but not in Truth file."
                )
            else:
                st.info("No extra programs found.")

        # Detailed Tables
        with st.expander("View Details"):
            st.write("In Truth but NOT in Test (Missing):")
            st.dataframe(results['in_truth_not_test'])
            
            st.write("In Test but NOT in Truth (Extra):")
            st.dataframe(results['in_test_not_truth'])
            
        if st.button("Reset Comparison", key="reset_truth_btn_toc"):
            st.session_state.toc_truth_results = None
            st.rerun()

    st.divider()
    
    # Reset Button
    if st.button("Reset"):
        st.session_state.toc_data = None
        st.rerun()
