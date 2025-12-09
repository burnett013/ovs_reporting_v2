import pypdf
import os

pdf_path = "z_extra/cat_gr_2526.pdf"

def extract_text_from_pages(pdf_path, start_page, num_pages):
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        return

    try:
        reader = pypdf.PdfReader(pdf_path)
        print(f"Extracting text from {pdf_path}...")
        
        # pypdf pages are 0-indexed, so page 153 is index 152
        start_index = start_page - 1
        
        for i in range(num_pages):
            page_index = start_index + i
            if page_index < len(reader.pages):
                page = reader.pages[page_index]
                text = page.extract_text()
                print(f"\n--- Page {start_page + i} ---\n")
                print(text)
                print("\n" + "="*50 + "\n")
            else:
                print(f"Page {start_page + i} is out of range.")
                
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Extract pages 170 to 180 (10 pages)
    extract_text_from_pages(pdf_path, 170, 10)
