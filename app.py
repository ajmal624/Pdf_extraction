from docx import Document
import re

def normalize_text(text):
    if not text:
        return ""
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text.strip(' "\'`')

def is_probable_section_title(text):
    if not text:
        return False
    keywords = ['information', 'info', 'details', 'section', 'form', 'appraisal']
    return any(k in text.lower() for k in keywords)

def extract_from_table(table):
    pairs = []
    for row in table.rows:
        # Take first non-empty cell as field, second as value
        cells = [normalize_text(c.text) for c in row.cells if normalize_text(c.text)]
        if len(cells) >= 2:
            field, value = cells[0], cells[1]
            if not is_probable_section_title(field):
                pairs.append((field, value))
    return pairs

def extract_from_paragraphs(paragraphs):
    pairs = []
    for p in paragraphs:
        line = normalize_text(p)
        if not line:
            continue
        # Try common separators
        if ":" in line:
            field, value = line.split(":", 1)
        elif "-" in line:
            field, value = line.split("-", 1)
        else:
            continue
        field, value = normalize_text(field), normalize_text(value)
        if field and not is_probable_section_title(field):
            pairs.append((field, value))
    return pairs

def extract_docx_auto(docx_file):
    doc = Document(docx_file)
    pairs = []

    for table in doc.tables:
        pairs.extend(extract_from_table(table))

    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    pairs.extend(extract_from_paragraphs(paragraphs))

    # Deduplicate, last value wins
    cleaned = {}
    for k, v in pairs:
        cleaned[k] = v

    return list(cleaned.items()), cleaned
