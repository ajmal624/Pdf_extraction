import streamlit as st
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="PDF Field Extractor", layout="wide")
st.title("📄 PDF Field:Value Extractor → CSV")

uploaded_files = st.file_uploader(
    "Upload PDF files", type=["pdf"], accept_multiple_files=True
)

if not uploaded_files:
    st.warning("Please upload at least one PDF file.")
    st.stop()

rows = []
all_field_names = set()

# -------- Text Extraction Function --------
def extract_text(file_bytes):
    text = ""
    try:
        with pdfplumber.open(BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except:
        text = ""

    if text.strip():
        return text.strip()

    # OCR fallback for scanned PDFs
    images = convert_from_bytes(file_bytes)
    for img in images:
        text += pytesseract.image_to_string(img) + "\n"

    return text.strip() if text.strip() else None

# -------- Strict Field:Value Parsing (no NAN fill) --------
def parse_field_value_no_nan(text):
    """
    Extract Field:Value pairs strictly from PDF text.
    - Only lines with ':' are considered.
    - Fields without values are ignored (no NAN).
    """
    fields = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        parts = line.split(":", 1)
        key = parts[0].strip()
        value = parts[1].strip()
        if value:  # only include if value exists
            fields[key] = value
    return fields

# -------- Process Each File --------
for file in uploaded_files:
    file_bytes = file.read()
    text = extract_text(file_bytes)

    if not text:
        st.error(f"❌ Could not extract text from {file.name}")
        continue

    parsed_fields = parse_field_value_no_nan(text)
    parsed_fields["Filename"] = file.name
    rows.append(parsed_fields)
    all_field_names.update(parsed_fields.keys())

# -------- Build DataFrame with Dynamic Headers --------
dynamic_headers = ["Filename"] + sorted([h for h in all_field_names if h != "Filename"])
df = pd.DataFrame(rows, columns=dynamic_headers)

# -------- Preview Table --------
st.subheader("📊 Extracted Data Preview")
st.dataframe(df, use_container_width=True)

# -------- CSV Download --------
csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download CSV",
    data=csv,
    file_name="extracted_data.csv",
    mime="text/csv"
)
