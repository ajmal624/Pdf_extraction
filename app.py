import streamlit as st
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
import pandas as pd
from io import BytesIO
import re

st.set_page_config(page_title="PDF Field Extractor", layout="wide")
st.title("📄 PDF Field:Value Extractor → CSV")

uploaded_files = st.file_uploader(
    "Upload PDF files", type=["pdf"], accept_multiple_files=True
)

if not uploaded_files:
    st.warning("Please upload at least one PDF file.")
    st.stop()

rows = []
all_fields = set()


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

    # OCR fallback
    images = convert_from_bytes(file_bytes)
    for img in images:
        text += pytesseract.image_to_string(img) + "\n"

    return text.strip() if text.strip() else None


# -------- Enhanced Field:Value Parser --------
def parse_field_value_enhanced(text):
    """
    Parses PDF text to extract Field:Value pairs.
    Supports:
        - Lines with ':', '-', or multiple spaces
        - Multi-line values
    """
    fields = {}
    last_field = None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # Match line with Field:Value or Field - Value or Field  Value
        match = re.match(r"^(.*?)(?:\:|\-|\s{2,})(.*)$", line)
        if match:
            key = match.group(1).strip()
            value = match.group(2).strip()
            if key and value:
                fields[key] = value
                last_field = key
        else:
            # Append line to previous field (multi-line value)
            if last_field:
                fields[last_field] += " " + line

    return fields


# -------- Process Each Uploaded File --------
for file in uploaded_files:
    file_bytes = file.read()
    text = extract_text(file_bytes)

    if not text:
        st.error(f"❌ Could not extract text from {file.name}")
        continue

    parsed_fields = parse_field_value_enhanced(text)
    parsed_fields["Filename"] = file.name
    rows.append(parsed_fields)
    all_fields.update(parsed_fields.keys())

# -------- Build DataFrame with Dynamic Headers --------
dynamic_headers = ["Filename"] + sorted([f for f in all_fields if f != "Filename"])
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
