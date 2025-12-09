# OVS Reporting V2 - Catalog Analysis & Comparison Tool

This Streamlit application is designed to assist in the analysis, processing, and comparison of university academic catalogs (specifically for USF). It leverages the Google Gemini LLM for extracting structure and data from PDF documents and provides powerful tools for tracking changes across academic years.

## Features

### 1. ToC Generator
*   **Purpose**: Extracts a structured Table of Contents (ToC) from raw PDF catalog files.
*   **Functionality**:
    *   Uses Gemini LLM to identify program names, page numbers, and types (Undergraduate/Graduate).
    *   Generates an Excel file listing all programs and their locations.
    *   Supports defining page ranges to target specific sections of large PDF files.

### 2. Catalog Report
*   **Purpose**: Generates detailed data reports based on the extracted Table of Contents.
*   **Functionality**:
    *   Parses program-specific details such as Credit Hours, Concentrations, and Descriptions.
    *   Outputs a comprehensive dataset for further analysis or reporting.

### 3. Comparison Report
*   **Purpose**: Compares catalog data between two different academic years to identify changes.
*   **Functionality**:
    *   **Upload & Compare**: Upload Excel files from two different years (e.g., 2024-2025 vs. 2025-2026).
    *   **Intelligent Matching**: Matches programs based on name, handling slight variations in Catalog Name.
    *   **Change Detection**: Automatically flags programs that have been added, removed, or modified.
    *   **Detailed Statuses**:
        *   *New*: Program found in the new year but not the old.
        *   *Likely Removed - Verify*: Program found in the old year but not the new.
        *   *Changed - Verify*: Program exists in both but has differences in columns like Credit Hours or Concentrations.
        *   *Still Approved*: Program exists in both with identical key data (ignores Page Number and Catalog Name changes).
    *   **Interactive Review**: Edit statuses and data directly within the application.
    *   **Flexible Exports**:
        *   *Full Report*: All programs and their statuses.
        *   *Changes Only*: Filtered list excluding "Still Approved" programs.
        *   *Evaluate Changes*: Targeted report showing exactly which columns changed, with side-by-side "Previous Value" vs. "New Value" comparison (e.g., `License Prep: Yes` -> `License Prep: No`).

## Usage

1.  **Setup**: Ensure you have Python installed and the necessary dependencies (listed in `requirements.txt`).
2.  **Run**: Execute `streamlit run Home.py` (or the main entry point file) to launch the web interface.
3.  **Navigate**: Use the sidebar to switch between the ToC Generator, Catalog Report, and Comparison Report pages.

## Technologies

*   **Python**: Core programming language.
*   **Streamlit**: Web application framework.
*   **Pandas**: Data manipulation and analysis.
*   **Google Gemini API**: LLM for intelligent text extraction and parsing.
