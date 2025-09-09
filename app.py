import streamlit as st
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
import re
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="PDF Field Extractor", layout="wide")

st.title("📄 PDF Field Extractor → CSV")

# 1. Upload Step
uploaded_files = st.file_uploader("Upload PDF files", type=["pdf"], accept_multiple_files=True)

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

    # Fallback: OCR for scanned PDFs
    images = convert_from_bytes(file_bytes)
    for img in images:
        text += pytesseract.image_to_string(img) + "\n"
    return text.strip() if text.strip() else None

# --- Helper: Clean and standardize extracted values ---
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

    # Blanks / placeholders → NAN
    if value == "" or value.lower() in ["n/a", "na", "null", "none"]:
        return "NAN"

    return value

# --- Process each uploaded PDF ---
for file in uploaded_files:
    file_bytes = file.read()
    text = extract_text(file_bytes)

    if not text:
        st.error(f"❌ Could not extract text from {file.name}")
        continue

    # 3. Parse Fields & Values
    field_pattern = re.compile(r"([A-Za-z0-9 ,()?/&\-\.\'\":]+):\s*([^\n]+)")
    matches = field_pattern.findall(text)

    data = {"Filename": file.name}  # Always include filename

    if not matches:
        st.warning(f"No field-value pairs found in {file.name}, filling with NAN.")
        data["NAN"] = "NAN"
    else:
        for field, value in matches:
            field_clean = field.strip().title()   # normalize headers
            value_clean = clean_value(value)

            # Prevent overwriting duplicate field names → append suffix if needed
            if field_clean in data:
                suffix = 1
                new_field = f"{field_clean}_{suffix}"
                while new_field in data:
                    suffix += 1
                    new_field = f"{field_clean}_{suffix}"
                field_clean = new_field

            data[field_clean] = value_clean

    rows.append(data)
    all_headers.update(data.keys())

# 4. Build Dynamic Headers
all_headers = ["Filename"] + sorted([h for h in all_headers if h != "Filename"])
df = pd.DataFrame(rows, columns=all_headers).fillna("NAN")

# 7. Preview Table
st.subheader("📊 Preview Extracted Data")
st.dataframe(df, use_container_width=True)

# 8. Download CSV
csv = df.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download CSV", data=csv, file_name="extracted_data.csv", mime="text/csv")
