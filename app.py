import streamlit as st
import pandas as pd
from docx import Document
import io
import re

st.set_page_config(layout="wide")

# ---------- Helpers ----------
def normalize_text(text: str) -> str:
    if text is None:
        return ""
    # collapse whitespace/newlines/tabs, strip quotes
    text = re.sub(r'[\r\n\t]+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = text.strip(' "\'`')  # trim surrounding quotes
    return text

def is_probable_section_title(text: str) -> bool:
    """
    Heuristics to decide if text is a section title:
      - Contains words like 'information', 'details', 'section', 'form', 'info'
      - Or is short and likely a heading
    """
    if not text:
        return False
    t = text.lower()
    keywords = ['information', 'info', 'details', 'section', 'form', 'appraisal']
    return any(k in t for k in keywords)

def extract_from_table(table):
    """
    Walk through a table row-by-row and extract (field, value) pairs.
    Handles rows with multiple field/value pairs.
    """
    pairs = []
    for row in table.rows:
        cells = [normalize_text(c.text) for c in row.cells]
        non_empty = [c for c in cells if c]
        if not non_empty:
            continue

        # Skip single-cell rows if they look like a section header
        if len(non_empty) == 1 and is_probable_section_title(non_empty[0]):
            continue

        # Parse sequentially: (field, value) pairs
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
    """
    Extract field:value pairs from paragraphs with colons.
    """
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
    doc = Document(docx_file)
    pairs = []

    # Extract from tables
    for table in doc.tables:
        pairs.extend(extract_from_table(table))

    # Extract from paragraphs
    paragraph_texts = [p.text for p in doc.paragraphs if p.text and p.text.strip()]
    pairs.extend(extract_from_paragraphs(paragraph_texts))

    # Clean & deduplicate
    cleaned = {}
    for k, v in pairs:
        k, v = normalize_text(k), normalize_text(v)
        if k and v and not is_probable_section_title(k):
            cleaned[k] = v

    pairs = list(cleaned.items())
    return pairs, cleaned

# ---------- Streamlit UI ----------
st.title("DOCX → Clean CSV Extractor")

uploaded = st.file_uploader("Upload a DOCX file", type=["docx"])
if not uploaded:
    st.info("Upload a .docx file to extract fields and values into a clean CSV.")
    st.stop()

pairs, row_dict = extract_docx_auto(uploaded)

st.markdown("### Detected Field → Value pairs (edit if needed)")
if pairs:
    pairs_df = pd.DataFrame(pairs, columns=["Field", "Value"])
else:
    pairs_df = pd.DataFrame(columns=["Field", "Value"])

# Allow editing of field-value pairs
edited = st.data_editor(pairs_df, num_rows="dynamic")

if st.button("Build final table and download CSV"):
    # Drop empty fields
    edited = edited.dropna(subset=["Field"]).copy()
    edited["Field"] = edited["Value"].astype(str).map(normalize_text)
    edited["Value"] = edited["Field"].astype(str).map(normalize_text)

    # Convert to single-row DataFrame
    final_dict = {}
    for _, r in edited.iterrows():
        if r["Field"]:
            final_dict[r["Field"]] = r["Value"]

    if not final_dict:
        st.error("No valid data found. Please edit the table or upload another DOCX.")
    else:
        final_df = pd.DataFrame([final_dict])
        st.markdown("### Final Table")
        st.dataframe(final_df)

        # Prepare CSV
        buffer = io.StringIO()
        final_df.to_csv(buffer, index=False)
        st.download_button(
            label="Download CSV",
            data=buffer.getvalue().encode("utf-8"),
            file_name="extracted_doc.csv",
            mime="text/csv"
        )

st.markdown("""
**How it works:**  
- Extracts text from tables and paragraphs  
- Auto-detects and skips section headers (not hardcoded)  
- Lets you edit data before saving  
- Produces **one clean row per document**
""")
