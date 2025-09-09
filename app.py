import streamlit as st
import pdfplumber
from pdf2image import convert_from_bytes
import pytesseract
import pandas as pd

st.title("PDF Field-Value Extractor (Multi-line support)")

uploaded_file = st.file_uploader("Upload PDF", type="pdf")

# Define your known fields (can be customized per PDF)
known_fields = [
    "Date", "Client Information", "Property Information",
    "Appraisal Information", "Name on report"
]

def extract_text(file):
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        if not text.strip():  # OCR fallback
            images = convert_from_bytes(file.getvalue())
            for img in images:
                text += pytesseract.image_to_string(img)
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
    return text

def parse_fields(text, fields):
    data = {}
    current_field = None
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        # Check if line is a known field
        if any(line.startswith(f) for f in fields):
            current_field = next(f for f in fields if line.startswith(f))
            # Initialize value
            data[current_field] = line[len(current_field):].strip() or ""
        elif current_field:
            # Append line to current field
            if data[current_field]:
                data[current_field] += "\n" + line
            else:
                data[current_field] = line
    return data

if uploaded_file:
    raw_text = extract_text(uploaded_file)
    st.subheader("📄 Extracted Text")
    st.text_area("PDF Text", raw_text, height=300)

    parsed_data = parse_fields(raw_text, known_fields)
    
    st.subheader("✅ Parsed Fields")
    df = pd.DataFrame([parsed_data])
    st.dataframe(df)

    csv = df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button("📥 Download CSV", csv, file_name=uploaded_file.name.replace(".pdf", ".csv"))
