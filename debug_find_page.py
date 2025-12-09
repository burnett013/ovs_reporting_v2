import pypdf

pdf_path = "z_extra/cat_gr_2526.pdf"
search_term = "Artificial Intelligence"

def find_page_number(pdf_path, search_term):
    try:
        reader = pypdf.PdfReader(pdf_path)
        print(f"Searching for '{search_term}' in {pdf_path}...")
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if search_term in text:
                print(f"Found '{search_term}' on PDF Page {i + 1} (Index {i})")
                # Print a snippet to confirm
                print(f"Snippet: {text[:200]}...")
                return

        print(f"'{search_term}' not found in the PDF.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    find_page_number(pdf_path, search_term)
