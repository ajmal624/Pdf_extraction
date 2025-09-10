from docx import Document
import re

# ---------- Helpers ----------
def normalize_text(text: str) -> str:
    """Cleans and normalizes extracted text."""
    if text is None:
        return ""
    text = re.sub(r'[\r\n\t]+', ' ', text)  # replace newlines/tabs with space
    text = re.sub(r'\s+', ' ', text).strip()  # collapse spaces
    return text.strip(' "\'`')  # trim surrounding quotes

def is_probable_section_title(text: str) -> bool:
    """Heuristic to skip generic section titles."""
    if not text:
        return False
    t = text.lower()
    keywords = ['information', 'info', 'details', 'section', 'form', 'appraisal']
    return any(k in t for k in keywords)

def extract_from_table(table):
    """Extract (field, value) pairs from Word table rows."""
    pairs = []
    for row in table.rows:
        cells = [normalize_text(c.text) for c in row.cells]
        non_empty = [c for c in cells if c]
        if not non_empty:
            continue
        if len(non_empty) == 1 and is_probable_section_title(non_empty[0]):
            continue
        i = 0
        while i < len(non_empty):
            text = non_empty[i]
            if is_probable_section_title(text):
                i += 1
                continue
            field = text
            value = non_empty[i + 1] if (i + 1) < len(non_empty) else ""
            pairs.append((field, value))
            i += 2
    return pairs

def extract_from_paragraphs(paragraphs):
    """Extract (field, value) pairs from paragraphs with colon separation."""
    pairs = []
    for p in paragraphs:
        line = normalize_text(p)
        if not line:
            continue
        if ":" in line:
            field, value = line.split(":", 1)
            field, value = normalize_text(field), normalize_text(value)
            if field and not is_probable_section_title(field):
                pairs.append((field, value))
    return pairs

def extract_docx_auto(docx_file):
    """Extract all field-value pairs from DOCX (tables + paragraphs)."""
    doc = Document(docx_file)
    pairs = []

    # Extract from tables
    for table in doc.tables:
        pairs.extend(extract_from_table(table))

    # Extract from paragraphs
    paragraph_texts = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    pairs.extend(extract_from_paragraphs(paragraph_texts))

    # Deduplicate (last value wins)
    cleaned = {}
    for k, v in pairs:
        k, v = normalize_text(k), normalize_text(v)
        if k and not is_probable_section_title(k):
            cleaned[k] = v

    pairs = list(cleaned.items())
    return pairs, cleaned

# ---------- Usage ----------
docx_path = "your_file.docx"
pairs, row_dict = extract_docx_auto(docx_path)

print("Detected Field → Value pairs:")
for f, v in pairs:
    print(f"{f} → {v}")
