from utils import llm_parser

text = llm_parser.extract_text_from_pdf("gr_toc_2526.pdf")
print(f"Total text length: {len(text)}")

# Find indices
idx_ai = text.find("Artificial Intelligence")
idx_acc = text.find("Accountancy")

print(f"'Artificial Intelligence' found at index: {idx_ai}")
print(f"'Accountancy' found at index: {idx_acc}")

# Print context around Accountancy
if idx_acc != -1:
    start = max(0, idx_acc - 200)
    end = min(len(text), idx_acc + 200)
    print(f"\nContext around 'Accountancy':\n{text[start:end]}")
