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

def extract_from_table(table):
    pairs = []
    for row in table.rows:
        # Take first 2 non-empty cells as field/value
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
        # Check for ':' or '-' separator
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

# ---------- Streamlit UI ----------
uploaded = st.file_uploader("Upload a DOCX file", type=["docx"])
if uploaded:
    try:
        pairs, row_dict = extract_docx_auto(uploaded)
        if not pairs:
            st.warning("No fields/values were detected in this document.")
        else:
            # Show editable table
            pairs_df = pd.DataFrame(pairs, columns=["Field", "Value"])
            edited = st.data_editor(pairs_df, num_rows="dynamic")

            if st.button("Build final table and download CSV"):
                edited = edited.dropna(subset=["Field"]).copy()
                fields = edited["Field"].map(normalize_text).tolist()
                values = edited["Value"].map(normalize_text).tolist()

                final_df = pd.DataFrame([fields, values])
                final_df.index = ["Field", "Value"]

                st.markdown("### Final Table (Row 1 = Fields, Row 2 = Values)")
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
