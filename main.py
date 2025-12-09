import streamlit as st
from pypdf import PdfReader, PdfWriter
from io import BytesIO

st.set_page_config(
    page_title="Make ToC PDF",
    page_icon="📚",
    layout="wide"
)

st.title("Make ToC PDF")

# Academic Year Selector
academic_year = st.selectbox(
    "Select Academic Year",
    ["2024-2025", "2025-2026"],
    index=1  # Default to 2025-2026
)

def extract_pages(file, start_page, end_page):
    """Extracts pages from a PDF file."""
    try:
        reader = PdfReader(file)
        writer = PdfWriter()
        
        # Validate page range
        if start_page > end_page:
            return None, "Start page cannot be greater than end page."
        if end_page >= len(reader.pages):
            return None, f"End page {end_page} is out of range. Max page is {len(reader.pages) - 1}."
            
        for page_num in range(start_page, end_page + 1):
            writer.add_page(reader.pages[page_num])
            
        output_buffer = BytesIO()
        writer.write(output_buffer)
        output_buffer.seek(0)
        return output_buffer, None
    except Exception as e:
        return None, str(e)

# Initialize session state for ToCs if not present
if "ug_toc_pdf" not in st.session_state:
    st.session_state.ug_toc_pdf = None
if "gr_toc_pdf" not in st.session_state:
    st.session_state.gr_toc_pdf = None

# Abbreviate academic year for filenames (e.g., "2024-2025" -> "2425")
abbr_year = academic_year.replace("20", "").replace("-", "")

# Determine default page ranges based on academic year
if academic_year == "2025-2026":
    ug_def_start, ug_def_end = 0, 32
    gr_def_start, gr_def_end = 0, 21
elif academic_year == "2024-2025":
    ug_def_start, ug_def_end = 0, 33
    gr_def_start, gr_def_end = 0, 18
else:
    # Defaults for others
    ug_def_start, ug_def_end = 0, 0
    gr_def_start, gr_def_end = 0, 0

# Create two columns for Undergraduate and Graduate
col1, col2 = st.columns(2)

# Buttons for Undergraduate
with col1:
    with st.form("ug_form"):
        st.header("Undergraduate")
        ug_file = st.file_uploader("Upload Undergraduate Catalog (PDF)", type="pdf", key="ug_uploader")
        ug_start = st.number_input("ToC Start Page", min_value=0, value=ug_def_start, key="ug_start")
        ug_end = st.number_input("ToC End Page", min_value=0, value=ug_def_end, key="ug_end")
        ug_submitted = st.form_submit_button("Make UG ToC")

    if ug_submitted:
        if ug_file:
            ug_pdf, ug_error = extract_pages(ug_file, ug_start, ug_end)
            if ug_error:
                st.error(f"Error: {ug_error}")
            elif ug_pdf:
                st.session_state.ug_toc_pdf = ug_pdf
                st.success("UG ToC generated!")
        else:
            st.warning("Please upload UG catalog.")

    if st.session_state.ug_toc_pdf:
        st.download_button(
            label="Download UG ToC PDF",
            data=st.session_state.ug_toc_pdf,
            file_name=f"toc_ug_{abbr_year}.pdf",
            mime="application/pdf"
        )

# Buttons for Graduate
with col2:
    with st.form("gr_form"):
        st.header("Graduate")
        gr_file = st.file_uploader("Upload Graduate Catalog (PDF)", type="pdf", key="gr_uploader")
        gr_start = st.number_input("ToC Start Page", min_value=0, value=gr_def_start, key="gr_start")
        gr_end = st.number_input("ToC End Page", min_value=0, value=gr_def_end, key="gr_end")
        gr_submitted = st.form_submit_button("Make GR ToC")

    if gr_submitted:
        if gr_file:
            gr_pdf, gr_error = extract_pages(gr_file, gr_start, gr_end)
            if gr_error:
                st.error(f"Error: {gr_error}")
            elif gr_pdf:
                st.session_state.gr_toc_pdf = gr_pdf
                st.success("GR ToC generated!")
        else:
            st.warning("Please upload GR catalog.")

    if st.session_state.gr_toc_pdf:
        st.download_button(
            label="Download GR ToC PDF",
            data=st.session_state.gr_toc_pdf,
            file_name=f"toc_gr_{abbr_year}.pdf",
            mime="application/pdf"
        )
