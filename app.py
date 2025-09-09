import streamlit as st
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
import pandas as pd
from io import BytesIO
import re

st.set_page_config(page_title="Dynamic PDF Extractor", layout="wide")
st.title("📄 Dynamic PDF Field Extractor → CSV")

# --- Upload PDFs ---
uploaded_files = st.file_uploader(
    "Upload PDF files", type=["pdf"], accept_multiple_files=True
)

if not uploaded_files:
    st.warning("Please upload at least one PDF file.")
    st.stop()

rows = []
all_field_names = set()

# --- Extract text from PDF (OCR fallback included) ---
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

# --- Clean text value ---
def clean_value(value):
    value = value.replace("\n", " ").strip()
    if value == "" or value.lower() in ["na", "n/a", "none", "null"]:
        return "NAN"
    return " ".join(value.split())

# --- Dynamic field parser ---
def parse_fields_dynamic(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    fields = {}
    current_field = None

    for line in lines:
        # Detect field pattern: ends with ":" or looks like a field
        if line.endswith(":") or re.match(r'^[A-Z][A-Za-z0-9\s\?\(\)\-]{2,50}:?$', line):
            field_name = line.rstrip(":").strip()
            if field_name not in fields:
                fields[field_name] = ""
            current_field = field_name
        elif current_field:
            # Append to current field value (multi-line)
            fields[current_field] += " " + line
        else:
            continue

    # Clean values and replace empty with NAN
    for k, v in fields.items():
        fields[k] = clean_value(v)
    return fields

# --- Process each uploaded PDF ---
for file in uploaded_files:
    file_bytes = file.read()
    text = extract_text(file_bytes)

    if not text:
        st.error(f"❌ Could not extract text from {file.name}")
        continue

    parsed_fields = parse_fields_dynamic(text)
    parsed_fields["Filename"] = file.name
    rows.append(parsed_fields)
    all_field_names.update(parsed_fields.keys())

# --- Build DataFrame with dynamic headers ---
dynamic_headers = ["Filename"] + sorted([h for h in all_field_names if h != "Filename"])
df = pd.DataFrame(rows, columns=dynamic_headers).fillna("NAN")

# --- Preview table ---
st.subheader("📊 Extracted Data Preview")
st.dataframe(df, use_container_width=True)

# --- Download CSV ---
csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download CSV",
    data=csv,
    file_name="extracted_data.csv",
    mime="text/csv"
)
