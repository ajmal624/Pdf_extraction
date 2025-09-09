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

def parse_field_value(text):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    fields = {}
    current_field = None

    for line in lines:
        if ":" in line:
            # Split at first colon only
            parts = line.split(":", 1)
            field_name = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else "NAN"
            fields[field_name] = value if value else "NAN"
            current_field = field_name
        elif current_field:
            # Multi-line value continuation
            fields[current_field] += " " + line

    # Clean all values
    for k, v in fields.items():
        if not v.strip():
            fields[k] = "NAN"
        else:
            fields[k] = " ".join(v.split())  # remove extra spaces/newlines
    return fields

for file in uploaded_files:
    file_bytes = file.read()
    text = extract_text(file_bytes)

    if not text:
        st.error(f"❌ Could not extract text from {file.name}")
        continue

    parsed_fields = parse_field_value(text)
    parsed_fields["Filename"] = file.name
    rows.append(parsed_fields)
    all_field_names.update(parsed_fields.keys())

# Build DataFrame with dynamic headers
dynamic_headers = ["Filename"] + sorted([h for h in all_field_names if h != "Filename"])
df = pd.DataFrame(rows, columns=dynamic_headers).fillna("NAN")

# Preview extracted data
st.subheader("📊 Extracted Data Preview")
st.dataframe(df, use_container_width=True)

# CSV download
csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download CSV",
    data=csv,
    file_name="extracted_data.csv",
    mime="text/csv"
)
