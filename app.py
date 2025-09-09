import streamlit as st
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
import re
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Dynamic PDF Field Extractor", layout="wide")
st.title("📄 Dynamic PDF Field Extractor → CSV")

# --- Upload PDFs ---
uploaded_files = st.file_uploader(
    "Upload PDF files", type=["pdf"], accept_multiple_files=True
)

if not uploaded_files:
    st.warning("Please upload at least one PDF file.")
    st.stop()

rows = []
dynamic_headers = set()

# --- Extract text from PDF (with OCR fallback) ---
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

# --- Clean extracted values ---
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

# --- Parse dynamic fields including multi-line values ---
def parse_fields(text):
    fields = {}
    current_field = None
    lines = text.splitlines()

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Find all Field:Value or Field - Value pairs
        matches = re.findall(r"([A-Za-z0-9 ,()&\-/]+?)\s*[:\-]\s*([^:^\-]+)", line)
        if matches:
            for field, value in matches:
                field_clean = field.strip().title()
                value_clean = clean_value(value)
                if field_clean not in fields:
                    fields[field_clean] = value_clean
                else:
                    fields[field_clean] += f" | {value_clean}"
                current_field = field_clean
        else:
            # Line without a colon → append to previous field
            if current_field:
                fields[current_field] += " " + line.strip()

    return fields

# --- Process each uploaded PDF ---
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
    dynamic_headers.update(data.keys())

# --- Build DataFrame with dynamic headers ---
dynamic_headers = ["Filename"] + sorted([h for h in dynamic_headers if h != "Filename"])
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
