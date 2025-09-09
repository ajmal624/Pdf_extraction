import streamlit as st
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
import re
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="PDF Field Extractor", layout="wide")
st.title("📄 PDF Field Extractor → CSV")

# File uploader
uploaded_files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)

if not uploaded_files:
    st.warning("Please upload a PDF file.")
    st.stop()

rows = []
all_headers = set()

# --- Extract text from PDF ---
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

# --- Clean values ---
def clean_value(value):
    value = value.strip()

    # Dates
    if re.match(r"\d{1,2}[-/]\d{1,2}[-/]\d{2,4}", value):
        try:
            return pd.to_datetime(value, errors="coerce").strftime("%Y-%m-%d")
        except:
            return value

    # Currency
    if "$" in value or value.replace(",", "").replace(".", "").isdigit():
        return value.replace("$", "").replace(",", "").strip()

    if value == "" or value.lower() in ["n/a", "na", "null", "none"]:
        return "NAN"

    return value

# --- Parse field:value pairs safely ---
def parse_fields(text):
    fields = {}

    for line in text.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue

        # split only on first colon
        field, value = line.split(":", 1)
        field = field.strip().title()
        value = value.strip()

        # Sometimes multiple "X: Y" pairs exist in same line → extract all
        while re.search(r"([A-Za-z0-9 ,()/-]+):", value):
            sub_match = re.search(r"([A-Za-z0-9 ,()/-]+):(.*)", value)
            if sub_match:
                sub_field = sub_match.group(1).strip().title()
                sub_value = sub_match.group(2).strip()
                fields[sub_field] = clean_value(sub_value)
                value = ""  # already consumed
                break

        if field not in fields:
            fields[field] = clean_value(value)

    return fields

# --- Process PDFs ---
for file in uploaded_files:
    file_bytes = file.read()
    text = extract_text(file_bytes)

    if not text:
        st.error(f"❌ Could not extract text from {file.name}")
        continue

    data = {"Filename": file.name}
    parsed = parse_fields(text)

    if not parsed:
        st.warning(f"No fields found in {file.name}, filling NANs.")
        data["NAN"] = "NAN"
    else:
        data.update(parsed)

    rows.append(data)
    all_headers.update(data.keys())

# --- Build CSV with all headers ---
all_headers = ["Filename"] + sorted([h for h in all_headers if h != "Filename"])
df = pd.DataFrame(rows, columns=all_headers).fillna("NAN")

# Show table
st.subheader("📊 Extracted Data Preview")
st.dataframe(df, use_container_width=True)

# Download CSV
csv = df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download CSV", data=csv, file_name="extracted_data.csv", mime="text/csv")
