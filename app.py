import streamlit as st
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Robust PDF Field Extractor", layout="wide")
st.title("📄 Robust PDF Field Extractor → CSV")

# Upload PDFs
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
    value = value.strip().replace("\n", " ")
    if value == "" or value.lower() in ["n/a", "na", "null", "none"]:
        return "NAN"
    # Remove extra spaces
    return " ".join(value.split())

# --- Robust field parser ---
def parse_fields_robust(text, known_fields=None):
    """
    text: raw PDF text
    known_fields: optional list of field names
    """
    fields = {}
    current_field = None
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    for line in lines:
        matched_field = None
        # Check against known fields first
        if known_fields:
            for field in known_fields:
                if line.lower().startswith(field.lower()):
                    matched_field = field
                    break

        # Field: Value pattern
        if ":" in line:
            parts = line.split(":", 1)
            matched_field = parts[0].strip()
            value = parts[1].strip()
            if matched_field not in fields:
                fields[matched_field] = clean_value(value)
            else:
                fields[matched_field] += " | " + clean_value(value)
            current_field = matched_field
        elif matched_field:
            current_field = matched_field
            fields[current_field] = clean_value(line[len(matched_field):].strip())
        elif current_field:
            # Append multi-line value
            fields[current_field] += " " + clean_value(line)
        else:
            continue

    return fields

# --- Process uploaded PDFs ---
all_field_names = set()
for file in uploaded_files:
    file_bytes = file.read()
    text = extract_text(file_bytes)

    if not text:
        st.error(f"❌ Could not extract text from {file.name}")
        continue

    # Use previous field names to improve parsing
    parsed_fields = parse_fields_robust(text, known_fields=list(all_field_names) if all_field_names else None)
    all_field_names.update(parsed_fields.keys())

    # Always include filename
    parsed_fields["Filename"] = file.name
    rows.append(parsed_fields)

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
