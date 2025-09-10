import streamlit as st
import pandas as pd
from docx import Document
import io
import re

st.set_page_config(layout="wide")
st.title("DOCX → CSV Extractor (Fields as Columns)")

# ---------- Helpers ----------
def normalize_text(text):
    """Clean text."""
    if not text:
        return ""
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text.strip(' "\'`')

def is_probable_section_title(text):
    """Skip section headers."""
    if not text:
        return False
    keywords = ['information', 'info', 'details', 'section', 'form', 'appraisal']
    return any(k in text.lower() for k in keywords)

def extract_from_table(table):
    """Extract multiple field-value pairs per row."""
    pairs = []
    for row in table.rows:
        cells = [normalize_text(c.text) for c in row.cells if normalize_text(c.text)]
        i = 0
        while i + 1 < len(cells):
            field, value = cells[i], cells[i + 1]
            if not is_probable_section_title(field):
                pairs.append((field, value))
            i += 2
    return pairs

def extract_from_paragraphs(paragraphs):
    """Extract field-value pairs from paragraphs."""
    pairs = []
    for p in paragraphs:
        line = normalize_text(p)
        if not line:
            continue
        for sep in [":", "-"]:
            if sep in line:
                field, value = line.split(sep, 1)
                field, value = normalize_text(field), normalize_text(value)
                if field and not is_probable_section_title(field):
                    pairs.append((field, value))
                break
    return pairs

def extract_docx_pairs(docx_file):
    """Extract cleaned field-value pairs from a DOCX."""
    doc = Document(docx_file)
    pairs = []

    # Tables
    for table in doc.tables:
        pairs.extend(extract_from_table(table))

    # Paragraphs
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    pairs.extend(extract_from_paragraphs(paragraphs))

    # Deduplicate, last value wins
    cleaned = {}
    for k, v in pairs:
        cleaned[k] = v

    return cleaned

# ---------- Streamlit UI ----------
uploaded_files = st.file_uploader("Upload one or more DOCX files", type=["docx"], accept_multiple_files=True)

if uploaded_files:
    all_rows = []

    for uploaded in uploaded_files:
        try:
            row_dict = extract_docx_pairs(uploaded)
            all_rows.append(row_dict)
        except Exception as e:
            st.error(f"Error reading {uploaded.name}: {e}")

    if all_rows:
        # Get all unique fields for columns
        all_fields = set()
        for row in all_rows:
            all_fields.update(row.keys())
        all_fields = list(all_fields)

        # Build dataframe
        final_rows = []
        for row in all_rows:
            final_row = [row.get(f, "") for f in all_fields]
            final_rows.append(final_row)

        final_df = pd.DataFrame(final_rows, columns=all_fields)
        st.markdown("### Extracted Data")
        st.dataframe(final_df)

        # Download CSV
        buffer = io.StringIO()
        final_df.to_csv(buffer, index=False)
        st.download_button(
            label="Download CSV",
            data=buffer.getvalue().encode("utf-8"),
            file_name="extracted_docx_data.csv",
            mime="text/csv"
        )
else:
    st.info("Upload one or more DOCX files to extract fields and values.")

st.markdown("""
**How this works:**  
- Extracts **tables and paragraphs** from DOCX  
- Handles **multiple field-value pairs per row**  
- Skips section headers automatically  
- Produces a **CSV**:
  - Columns = all fields  
  - Rows = one DOCX per row
""")
