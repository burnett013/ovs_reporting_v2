from utils import llm_parser

text = llm_parser.extract_text_from_pdf("ug_toc_2526.pdf")
search_term = "Biomedical Sciences for Early Admission Students"
idx = text.find(search_term)

print(f"'{search_term}' found at index: {idx}")

if idx != -1:
    start = max(0, idx - 200)
    end = min(len(text), idx + 200)
    print(f"\nContext around '{search_term}':\n{text[start:end]}")
else:
    print("Exact search term not found.")
