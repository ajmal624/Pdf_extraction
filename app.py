import streamlit as st
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
import re
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="PDF Field Extractor", layout="wide")
st.title("📄 PDF Field Extractor → CSV")

# 1. Upload PDFs
uploaded_files = st.file_uploader(
    "Upload PDF files", type=["pdf"], accept_multiple_files=True
)

if not uploaded_files:
    st.warning("Please upload at least one PDF file.")
    st.stop()

rows = []
all_headers = set()

# --- Helper: Extract text from PDF (with OCR fallback) ---
def extract_text(file_bytes):
    text = ""
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    if text.strip():
        return text.strip()

    # OCR fallback
    images = convert_from_bytes(file_bytes)
    for img in images:
        text += pytesseract.image_to_string(img) + "\n"
    return text.strip() if text.strip() else None

# --- Helper: Clean values ---
def clean_value(value):
    value = value.strip()

    # Dates → YYYY-MM-DD
    if re.match(r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}", value):
        try:
            return pd.to_datetime(value, errors="coerce").strftime("%Y-%m-%d")
        except:
            return value

    # Currency → numeric only
    if "$" in value or value.replace(",", "").replace(".", "").isdigit():
        return value.replace("$", "").replace(",", "").strip()

    if value == "" or value.lower() in ["n/a", "na", "null", "none"]:
        return "NAN"

    return value

# --- Helper: Parse field:value pairs ---
def parse_fields(text):
    fields = {}
    # Regex finds all FIELD : VALUE pairs in a line
    pattern = re.compile(r"([A-Za-z0-9 ,()/-]+?)\s*:\s*([^:]+)")

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        matches = pattern.findall(line)
        for field, value in matches:
            field = field.strip().title()
            value = clean_value(value)
            if field not in fields:
                fields[field] = value
            else:
                # Append if duplicate field in same PDF
                fields[field] += f" | {value}"

    return fields

# --- Process uploaded PDFs ---
for file in uploaded_files:
    file_bytes = file.read()
    text = extract_text(file_bytes)

    if not text:
        st.error(f"❌ Could not extract text from {file.name}")
        continue

    data = {"Filename": file.name}
    parsed_fields = parse_fields(text)

    if not parsed_fields:
        st.warning(f"No fields found in {file.name}, filling with NAN.")
        data["NAN"] = "NAN"
    else:
        data.update(parsed_fields)

    rows.append(data)
    all_headers.update(data.keys())

# --- Build DataFrame with dynamic headers ---
all_headers = ["Filename"] + sorted([h for h in all_headers if h != "Filename"])
df = pd.DataFrame(rows, columns=all_headers).fillna("NAN")

# --- Preview table ---
st.subheader("📊 Extracted Data Preview")
st.dataframe(df, use_container_width=True)

# --- Download CSV ---
csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download CSV", data=csv, file_name="extracted_data.csv", mime="text/csv"
)
