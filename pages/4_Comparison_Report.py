import streamlit as st
import pandas as pd
import io

# Initialize Session State
if 'comparison_results' not in st.session_state:
    st.session_state.comparison_results = None

st.title("Comparison Report")

st.markdown("""
This page allows you to compare two years' of Catalog Reports.
Please upload the Excel files for the two years you wish to compare.
""")

# Term Selection
term = st.selectbox("Select Term", ["Fall", "Spring", "Summer"])

col1, col2 = st.columns(2)

year_options = ["2024-2025", "2025-2026"]

with col1:
    st.subheader("Year 1")
    year1 = st.selectbox("Select Year 1", options=year_options, index=0, key="year1")
    file1 = st.file_uploader("Upload Year 1 Report", type=["xlsx"], key="file1")

with col2:
    st.subheader("Year 2")
    year2 = st.selectbox("Select Year 2", options=year_options, index=1, key="year2")
    file2 = st.file_uploader("Upload Year 2 Report", type=["xlsx"], key="file2")

if st.button("Compare Years"):
    if file1 and file2:
        try:
            df1 = pd.read_excel(file1)
            df2 = pd.read_excel(file2)
            
            # Key columns for matching
            key_cols = ['Program Name']
            
            # Verify keys exist
            if not all(k in df1.columns for k in key_cols) or not all(k in df2.columns for k in key_cols):
                 st.error(f"Both files must contain columns: {key_cols}")
            else:
                # Merge
                # Suffixes: _y1 for Year 1, _y2 for Year 2
                merged = pd.merge(df1, df2, on=key_cols, how='outer', suffixes=('_y1', '_y2'), indicator=True)
                
                final_rows = []
                
                for index, row in merged.iterrows():
                    status = ""
                    effective_date = ""
                    
                    changed_cols_list = []
                    previous_values_list = []
                    
                    # Logic
                    if row['_merge'] == 'both':
                        # Check for changes in other columns
                        # We need to compare all columns that are present in both (excluding keys)
                        # Get common columns from original dfs
                        # EXCLUDE 'Catalog Name' and 'Page Number' from content comparison as they will always differ or are irrelevant for approval status
                        common_cols = [c for c in df1.columns if c in df2.columns and c not in key_cols and c != 'Catalog Name' and c != 'Page Number']
                        
                        for col in common_cols:
                            val1 = row[f"{col}_y1"]
                            val2 = row[f"{col}_y2"]
                            
                            # Handle NaNs
                            if pd.isna(val1) and pd.isna(val2):
                                continue
                            if str(val1).strip() != str(val2).strip():
                                changed_cols_list.append(f"{col}: {val2}")
                                previous_values_list.append(f"{col}: {val1}")
                        
                        if changed_cols_list:
                            status = "Changed - Verify"
                        else:
                            status = "Still Approved"
                            
                    elif row['_merge'] == 'right_only': # In Year 2 only
                        status = "New"
                        effective_date = f"{term} {year2}"
                        
                    elif row['_merge'] == 'left_only': # In Year 1 only
                        status = "Likely Removed - Verify"
                    
                    # Construct Result Row
                    # Use Year 2 data if available, else Year 1
                    result_row = {}
                    
                    # Add Keys
                    for k in key_cols:
                        result_row[k] = row[k]
                        
                    # Add Calculated Fields
                    # Add Calculated Fields
                    result_row['School Reported Approval Status'] = status
                    result_row['Effective Date'] = effective_date
                    result_row['Changed Columns'] = ", ".join(changed_cols_list)
                    result_row['Previous Values'] = "; ".join(previous_values_list)
                    
                    # Add other columns (preferring Year 2)
                    # We'll take the union of columns from both
                    all_cols = set(df1.columns) | set(df2.columns)
                    for col in all_cols:
                        if col in key_cols: continue
                        
                        # If it's a calculated field we just set, skip (though they likely aren't in source)
                        if col in ['School Reported Approval Status', 'Effective Date', 'Changed Columns', 'Previous Values']: continue

                        val = None
                        if row['_merge'] == 'both':
                            val = row[f"{col}_y2"] # Default to latest
                        elif row['_merge'] == 'right_only':
                            val = row.get(col, row.get(f"{col}_y2")) # Might be just col if not in df1
                            # Because of suffix, it will be col_y2 if in both, but since it's outer join...
                            # Actually pandas adds suffixes to overlapping columns. Non-overlapping stay as is.
                            # Let's handle this carefully.
                            if f"{col}_y2" in row:
                                val = row[f"{col}_y2"]
                            elif col in row:
                                val = row[col]
                        elif row['_merge'] == 'left_only':
                            if f"{col}_y1" in row:
                                val = row[f"{col}_y1"]
                            elif col in row:
                                val = row[col]
                                
                        result_row[col] = val

                    final_rows.append(result_row)
                
                df_result = pd.DataFrame(final_rows)
                
                # Ensure specific column order if possible, or at least put Keys and Status first
                first_cols = ['Program Name', 'Catalog Name', 'School Reported Approval Status', 'Effective Date']
                other_cols = [c for c in df_result.columns if c not in first_cols]
                df_result = df_result[first_cols + other_cols]
                
                st.session_state.comparison_results = df_result
                st.success(f"Comparison complete! Processed {len(df_result)} programs.")

        except Exception as e:
            st.error(f"Error during comparison: {e}")
            
    else:
        st.error("Please upload both files.")

# Display Results
if st.session_state.comparison_results is not None:
    st.divider()
    st.subheader("Comparison Results")
    st.subheader("Add, edit, or delete rows as needed prior to download")
    
    # Enable editing, adding, and deleting rows
    edited_df = st.data_editor(
        st.session_state.comparison_results,
        num_rows="dynamic",
        use_container_width=True,
        key="comparison_editor"
    )
    
    # Persist changes to session state so they are reflected in the download
    st.session_state.comparison_results = edited_df


    
    # Download Buttons
    col_dl1, col_dl2, col_dl3 = st.columns(3)

    # Abbreviate years for filename: 2024-2025 -> 2425
    y1_short = year1.split('-')[0][-2:] + year1.split('-')[1][-2:]
    y2_short = year2.split('-')[0][-2:] + year2.split('-')[1][-2:]

    # Full Report
    output_full = io.BytesIO()
    with pd.ExcelWriter(output_full, engine='openpyxl') as writer:
        st.session_state.comparison_results.to_excel(writer, index=False, sheet_name='Comparison')
    
    with col_dl1:
        st.download_button(
            label="Download Full Comp Report",
            data=output_full.getvalue(),
            file_name=f"comp_report_{y1_short}_{y2_short}_FULL.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_full"
        )

    # Changes Only Report
    # Filter for non-"Still Approved"
    changes_df = st.session_state.comparison_results[
        st.session_state.comparison_results['School Reported Approval Status'] != 'Still Approved'
    ]
    
    output_changes = io.BytesIO()
    with pd.ExcelWriter(output_changes, engine='openpyxl') as writer:
        changes_df.to_excel(writer, index=False, sheet_name='Changes')
        
    with col_dl2:
        st.download_button(
            label="Download Changes Only Comp Report",
            data=output_changes.getvalue(),
            file_name=f"comp_report_{y1_short}_{y2_short}_CHANGES.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_changes"
        )

    # Evaluate Changes Report
    # Filter for "Changed - Verify"
    evaluate_df = st.session_state.comparison_results[
        st.session_state.comparison_results['School Reported Approval Status'] == 'Changed - Verify'
    ]
    # Select specific columns
    # Ensure columns exist before selecting to avoid errors
    eval_cols = ['Program Name', 'Catalog Name', 'Page Number', 'Changed Columns', 'Previous Values']
    evaluate_df = evaluate_df[[c for c in eval_cols if c in evaluate_df.columns]]
    
    output_evaluate = io.BytesIO()
    with pd.ExcelWriter(output_evaluate, engine='openpyxl') as writer:
        evaluate_df.to_excel(writer, index=False, sheet_name='Evaluate')
        
    with col_dl3:
        st.download_button(
            label="Evaluate Changes",
            data=output_evaluate.getvalue(),
            file_name=f"comp_report_{y1_short}_{y2_short}_EVALUATE.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_evaluate"
        )
    
    # Reset Button
    if st.button("Reset"):
        st.session_state.comparison_results = None
        st.rerun()
