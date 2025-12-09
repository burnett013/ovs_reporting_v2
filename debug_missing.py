from utils import llm_parser

# The missing programs seem to be from the Undergraduate catalog based on the "B.A." credential.
text = llm_parser.extract_text_from_pdf("ug_toc_2526.pdf")
print(f"Total text length: {len(text)}")

# Search for a substring of the missing program
# "World Languages and Cultures B.A., with Interdisciplinary Classical Civilizations Concentration"
search_term = "World Languages and Cultures"
idx = text.find(search_term)

print(f"'{search_term}' found at index: {idx}")

if idx != -1:
    start = max(0, idx - 100)
    end = min(len(text), idx + 500)
    print(f"\nContext around '{search_term}':\n{text[start:end]}")
else:
    print("Exact search term not found. Trying partial match...")
    # Try searching for just the concentration part if the main name is split weirdly
    search_term_2 = "Interdisciplinary Classical Civilizations Concentration"
    idx_2 = text.find(search_term_2)
    print(f"'{search_term_2}' found at index: {idx_2}")
    if idx_2 != -1:
        start = max(0, idx_2 - 200)
        end = min(len(text), idx_2 + 200)
        print(f"\nContext around '{search_term_2}':\n{text[start:end]}")
