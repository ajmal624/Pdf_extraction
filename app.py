import streamlit as st
import pandas as pd
from docx import Document
import io
import re

st.set_page_config(layout="wide")
st.title("DOCX → CSV Extractor (Fields Row 1, Values Row 2)")

# ---------- Helpers ----------
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

# Extract multiple field-value pairs from a table row
def extract_from_table(table):
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

# Extract from paragraphs
def extract_from_paragraphs(paragraphs):
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

# Main extraction function
def extract_docx_auto(docx_file):
    doc = Document(docx_file)
    pairs = []

    # Extract from tables
    for table in doc.tables:
        pairs.extend(extract_from_table(table))

    # Extract from paragraphs
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    pairs.extend(extract_from_paragraphs(paragraphs))

    # Deduplicate, last value wins
    cleaned = {}
    for k, v in pairs:
        cleaned[k] = v

    # Convert to ordered list
    final_pairs = [(k, cleaned[k]) for k in cleaned]
    return final_pairs, cleaned

# ---------- Streamlit UI ----------
uploaded = st.file_uploader("Upload a DOCX file", type=["docx"])
if uploaded:
    try:
        pairs, row_dict = extract_docx_auto(uploaded)
        if not pairs:
            st.warning("No fields/values were detected in this document.")
        else:
            # Build two-row table for CSV
            fields = [f for f, v in pairs]
            values = [v for f, v in pairs]
            final_df = pd.DataFrame([fields, values])
            final_df.index = ["Field", "Value"]

            st.markdown("### Extracted Fields and Values")
            st.dataframe(final_df)

            # Download CSV
            buffer = io.StringIO()
            final_df.to_csv(buffer, index=False, header=False)
            st.download_button(
                label="Download CSV",
                data=buffer.getvalue().encode("utf-8"),
                file_name="extracted_doc.csv",
                mime="text/csv"
            )
    except Exception as e:
        st.error(f"Error reading DOCX: {e}")
else:
    st.info("Upload a .docx file to extract fields and values.")

st.markdown("""
**How this works:**  
- Extracts text from **tables** and **paragraphs**  
- Handles tables with **multiple field-value pairs per row**  
- Skips section headers automatically  
- Produces a **two-row CSV**:
  - Row 1: Fields  
  - Row 2: Corresponding Values
""")
